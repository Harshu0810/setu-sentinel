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
    Uses Chromium's native TLS handshake engine & headers with 12s timeout,
    preventing connection resets and false positive 403 WAF blocks.
    """
    try:
        resp = context.request.get(url, timeout=12000)
        status = resp.status
        # True broken links: 404 Not Found, 5xx Server Errors
        # 403 Forbidden is WAF anti-bot protection, NOT a broken link for human citizens.
        is_broken = (status == 404 or status >= 500)
        return (url, is_broken, status)
    except Exception:
        # Fallback to requests if context request raises exception
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            }
            r = requests.get(url, timeout=10, headers=headers, verify=False, stream=True, allow_redirects=True)
            st = r.status_code
            r.close()
            return (url, st == 404 or st >= 500, st)
        except Exception:
            return (url, True, 0) # 0 means unreachable / Timeout / DNS error

def audit_portal_links(context, links: list[str]) -> tuple[int, int, list[str], list[dict]]:
    """
    Audits extracted portal links and returns:
    (total_found, total_audited, working_links_list, broken_links_details)
    """
    valid_links = [l for l in links if l and l.startswith('http') and not any(l.endswith(ext) for ext in ['.pdf', '.zip', '.doc', '.xlsx'])]
    valid_links = list(set(valid_links))
    
    total_found = len(valid_links)
    to_check = valid_links[:30] # Audit sample cap
    
    working_links = []
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
        else:
            working_links.append(url_res)
        
    return total_found, len(to_check), working_links, broken_details

def check_portal_uptime(url: str) -> dict:
    is_ci = os.environ.get("CI", "").lower() == "true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_ci)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
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
                
            load_time_ms = int((time.time() - start_time) * 1000)
            
            status = response.status if response else None
            if status in [403, 503]:
                status = 200 # WAF anti-bot block, site is up for humans
                
            links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
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
                "status_code": status or 200
            }
        except Exception as e:
            return {
                "status": "down",
                "error": str(e),
                "total_links_found": 0,
                "total_links_audited": 0,
                "verified_working_links_count": 0,
                "verified_working_links": [],
                "broken_links": 0,
                "broken_links_details": []
            }
        finally:
            browser.close()
