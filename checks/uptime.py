import time
import requests
import urllib3
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Disable insecure request warnings for broken govt SSL certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_link_with_context(context, url: str) -> tuple[str, bool, int]:
    """
    Checks if a URL link is broken using Playwright's browser context.
    Uses Chromium's native TLS handshake engine & headers, preventing connection reset errors 
    on sites like ddnews.gov.in and avoiding false positive 403 WAF blocks.
    """
    try:
        resp = context.request.get(url, timeout=7000)
        status = resp.status
        # True broken links: 404 Not Found, 5xx Server Errors
        # 403 Forbidden is WAF anti-bot protection, NOT a broken link for human citizens.
        is_broken = (status == 404 or status >= 500)
        return (url, is_broken, status)
    except Exception:
        # Fallback to requests if context request raises exception
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = requests.get(url, timeout=5, headers=headers, verify=False, stream=True, allow_redirects=True)
            st = r.status_code
            r.close()
            return (url, st == 404 or st >= 500, st)
        except Exception:
            return (url, True, 0) # 0 means unreachable / Timeout / DNS error

def count_broken_links_context(context, links: list[str]) -> tuple[int, list[dict]]:
    valid_links = [l for l in links if l and l.startswith('http')]
    valid_links = list(set(valid_links))
    
    # Cap at 30 links per page to avoid overloading portals
    to_check = valid_links[:30]
    
    broken_details = []
    for url in to_check:
        url_res, is_broken, status = check_link_with_context(context, url)
        if is_broken:
            reason = "Unreachable / Timeout" if status == 0 else f"HTTP {status}"
            broken_details.append({
                "url": url_res,
                "status_code": status,
                "reason": reason
            })
        
    return len(broken_details), broken_details

def check_portal_uptime(url: str) -> dict:
    is_ci = os.environ.get("CI", "").lower() == "true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_ci)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            start_time = time.time()
            response = page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Anti-bot human-in-the-loop fallback
            if response and response.status in [403, 503] and not is_ci:
                print(f"\n[!] Blocked by {url} with status {response.status}.")
                print("    Please solve the CAPTCHA or wait for the page to load in the browser window.")
                input("    Press ENTER here once the page is fully loaded...")
                
            load_time_ms = int((time.time() - start_time) * 1000)
            
            status = response.status if response else None
            if not is_ci and status in [403, 503]:
                status = 200
                
            links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            broken_count, broken_details = count_broken_links_context(context, links)
            
            return {
                "status": "up" if status and status < 400 else "down",
                "response_ms": load_time_ms,
                "broken_links": broken_count,
                "broken_links_details": broken_details,
                "broken_forms": 0,
                "status_code": status
            }
        except Exception as e:
            return {"status": "down", "error": str(e), "broken_links": 0, "broken_links_details": []}
        finally:
            browser.close()
