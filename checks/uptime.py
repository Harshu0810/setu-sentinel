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

def check_link(url: str) -> bool:
    """Returns True if link is broken (4xx/5xx or timeout/error)."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.head(url, timeout=5, headers=headers, verify=False, allow_redirects=True)
        return resp.status_code >= 400
    except requests.RequestException:
        return True # broken or unreachable

def count_broken_links(links: list[str]) -> int:
    valid_links = [l for l in links if l and l.startswith('http')]
    valid_links = list(set(valid_links))
    
    # Cap at 30 links per page to avoid overloading portals
    to_check = valid_links[:30]
    
    broken_count = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(check_link, to_check)
        broken_count = sum(1 for r in results if r)
        
    return broken_count

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
            # If human intervened, assume it's up now
            if not is_ci and status in [403, 503]:
                status = 200
                
            links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            broken = count_broken_links(links)
            
            return {
                "status": "up" if status and status < 400 else "down",
                "response_ms": load_time_ms,
                "broken_links": broken,
                "broken_forms": 0, # Placeholder for Phase 1 forms
                "status_code": status
            }
        except Exception as e:
            return {"status": "down", "error": str(e)}
        finally:
            browser.close()
