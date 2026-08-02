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

def check_link(url: str) -> tuple[str, bool, int]:
    """
    Checks if a URL link is broken.
    Uses HTTP GET with stream=True (only fetches response headers) instead of HTTP HEAD,
    because many Indian Govt servers return 405 Method Not Allowed or 404 to HEAD requests.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    try:
        # Use GET with stream=True so we only fetch headers without downloading body payload
        resp = requests.get(url, timeout=6, headers=headers, verify=False, stream=True, allow_redirects=True)
        status = resp.status_code
        resp.close() # Close socket immediately
        return (url, status >= 400, status)
    except requests.RequestException:
        # Fallback to HEAD if GET raises a connection error
        try:
            r_head = requests.head(url, timeout=5, headers=headers, verify=False, allow_redirects=True)
            return (url, r_head.status_code >= 400, r_head.status_code)
        except requests.RequestException:
            return (url, True, 0) # 0 means unreachable / Timeout / DNS error

def count_broken_links(links: list[str]) -> tuple[int, list[dict]]:
    valid_links = [l for l in links if l and l.startswith('http')]
    valid_links = list(set(valid_links))
    
    # Cap at 30 links per page to avoid overloading portals
    to_check = valid_links[:30]
    
    broken_details = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(check_link, to_check)
        for url, is_broken, status in results:
            if is_broken:
                reason = "Unreachable / Timeout" if status == 0 else f"HTTP {status}"
                broken_details.append({
                    "url": url,
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
            broken_count, broken_details = count_broken_links(links)
            
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
