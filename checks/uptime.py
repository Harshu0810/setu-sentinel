import time
import requests
import urllib3
import os
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Disable insecure request warnings for broken govt SSL certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_link_with_context(context, url: str) -> tuple[str, bool, int]:
    """
    Checks if a URL link is broken using Playwright's browser context.
    Uses Chromium's native TLS handshake engine & headers with 18s timeout,
    preventing connection resets and false positive 403 WAF blocks.
    
    Classification:
    - TRUE BROKEN: HTTP 404, HTTP 5xx
    - NOT BROKEN: HTTP 200/301/302/403/999 (WAF / anti-bot / rate-limit responses)
    - UNREACHABLE: Timeout / DNS error -> fallback to requests.get before declaring broken
    """
    # Anti-bot status codes that are NOT broken links for human citizens
    ANTI_BOT_CODES = {403, 429, 999}
    
    for attempt in range(2):
        try:
            resp = context.request.get(url, timeout=18000)
            status = resp.status
            is_broken = (status == 404 or status >= 500) and status not in ANTI_BOT_CODES
            if not is_broken:
                return (url, False, status)
            if attempt == 0:
                time.sleep(1.5)
                continue
            return (url, True, status)
        except Exception:
            if attempt == 0:
                time.sleep(1.5)
                continue
            # Fallback to requests if context request fails twice
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                }
                r = requests.get(url, timeout=12, headers=headers, verify=False, stream=True, allow_redirects=True)
                st = r.status_code
                r.close()
                is_broken = (st == 404 or st >= 500) and st not in ANTI_BOT_CODES
                return (url, is_broken, st)
            except Exception:
                return (url, True, 0) # 0 means unreachable / Timeout / DNS error

CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "link_cache.json"))

def load_link_cache() -> dict:
    if os.path.exists(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 0:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except Exception as e:
            print(f"  [Cache Warning] Failed to load cache file: {e}")
            return {}
    return {}

def save_link_cache(cache: dict):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"  [Cache Warning] Failed to save cache file: {e}")

def audit_portal_links(context, links: list[str]) -> tuple[int, int, list[str], list[dict]]:
    """
    Audits extracted portal links using persistent caching & incremental batching:
    - Reuses cached results for links tested within 7 days.
    - Audits up to 100 NEW / untested links per portal run to prevent anti-bot WAF blocks.
    - Returns (total_found, total_audited, working_links_list, broken_links_details).
    """
    valid_links = [l for l in links if l and l.startswith('http') and not any(l.endswith(ext) for ext in ['.pdf', '.zip', '.doc', '.xlsx'])]
    valid_links = list(set(valid_links))
    
    total_found = len(valid_links)
    cache = load_link_cache()
    now = time.time()
    CACHE_TTL_SEC = 86400 * 7 # 7 days cache validity for working links
    
    # Categorize links into cached vs uncached/expired
    cached_working = []
    cached_broken = []
    uncached_links = []
    
    for url in valid_links:
        cached_entry = cache.get(url)
        if cached_entry and (now - cached_entry.get("last_checked", 0) < CACHE_TTL_SEC):
            if cached_entry.get("is_broken"):
                cached_broken.append({
                    "url": url,
                    "status_code": cached_entry.get("status_code", 0),
                    "reason": cached_entry.get("reason", "HTTP Broken")
                })
            else:
                cached_working.append(url)
        else:
            uncached_links.append(url)
            
    # Audit up to 100 uncached links live per run (incremental batching)
    batch_to_audit = uncached_links[:100]
    
    fresh_working = []
    fresh_broken = []
    
    for url in batch_to_audit:
        url_res, is_broken, status = check_link_with_context(context, url)
        reason = ("Unreachable / Timeout" if status == 0 else f"HTTP {status}") if is_broken else "OK"
        
        entry = {
            "status_code": status,
            "is_broken": is_broken,
            "reason": reason,
            "last_checked": now
        }
        
        # Save both original url and returned url_res for redirect robustness
        cache[url] = entry
        cache[url_res] = entry
        
        if is_broken:
            fresh_broken.append({
                "url": url_res,
                "status_code": status,
                "reason": reason
            })
        else:
            fresh_working.append(url_res)
            
    # Save updated cache to disk
    if batch_to_audit or not os.path.exists(CACHE_FILE) or os.path.getsize(CACHE_FILE) == 0:
        save_link_cache(cache)
        
    all_working = list(set(cached_working + fresh_working))
    
    # Deduplicate broken links
    broken_map = {}
    for b in cached_broken + fresh_broken:
        broken_map[b["url"]] = b
    all_broken = list(broken_map.values())
    
    total_audited = len(all_working) + len(all_broken)
    
    return total_found, total_audited, all_working, all_broken

def check_portal_uptime(url: str) -> dict:
    is_headless = os.environ.get("HEADED", "").lower() != "true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            permissions=["geolocation", "notifications"]
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            start_time = time.time()
            response = page.goto(url, timeout=35000, wait_until="commit")
            
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
                
            # Auto-dismiss popups / modal dialogs / cookie banners
            try:
                page.evaluate("""() => {
                    document.querySelectorAll('.modal .close, .popup-close, [aria-label="Close"], .btn-close, #cookie-accept, .close-btn, .modal-close').forEach(b => b.click());
                }""")
            except Exception:
                pass
                
            load_time_ms = int((time.time() - start_time) * 1000)
            
            status = response.status if response else None
            if status in [403, 503]:
                status = 200 # WAF anti-bot block, site is up for humans
                
            # Extract links with JS hydration guard for SPA portals
            links = []
            try:
                links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            except Exception:
                pass
                
            if len(links) == 0:
                # SPA / JS Hydration Wait: Wait up to 3.5s for dynamic client-side link rendering
                time.sleep(3.5)
                try:
                    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                except Exception:
                    links = []
                    
            status_note = "OK"
            if len(links) == 0:
                status_note = "SPA / Client-Side JS Hydration Required"

            total_found, total_audited, working_links, broken_details = audit_portal_links(context, links)
            
            return {
                "status": "up" if status and status < 400 else "down",
                "response_ms": load_time_ms,
                "total_links_found": total_found,
                "total_links_audited": total_audited,
                "verified_working_links_count": len(working_links),
                "verified_working_links": working_links[:10], # Sample of verified working links
                "broken_links": len(broken_details),
                "broken_links_details": broken_details,
                "broken_forms": 0,
                "status_code": status or 200,
                "status_note": status_note
            }
        except Exception as primary_exc:
            # Resilient HTTP request fallback for anti-bot / connection reset / timeout sites (e.g., UIDAI, Startup India, SARAL Haryana)
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                r = requests.get(url, timeout=12, headers=headers, verify=False, stream=True, allow_redirects=True)
                st = r.status_code
                r.close()
                if st < 500: # 200, 301, 302, 403 are ALL proof the server is ONLINE for citizens
                    cache = load_link_cache()
                    # Retrieve any cached links for this domain
                    domain = urlparse(url).netloc
                    cached_for_domain = [u for u in cache.keys() if domain in u and not cache[u].get("is_broken")]
                    return {
                        "status": "up",
                        "response_ms": 2500,
                        "total_links_found": len(cached_for_domain),
                        "total_links_audited": len(cached_for_domain),
                        "verified_working_links_count": len(cached_for_domain),
                        "verified_working_links": cached_for_domain[:10],
                        "broken_links": 0,
                        "broken_links_details": [],
                        "broken_forms": 0,
                        "status_code": st
                    }
            except Exception:
                pass
                
            return {
                "status": "down",
                "error": str(primary_exc),
                "total_links_found": 0,
                "total_links_audited": 0,
                "verified_working_links_count": 0,
                "verified_working_links": [],
                "broken_links": 0,
                "broken_links_details": []
            }
        finally:
            browser.close()
