import requests
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def test_india_fix():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        # Load via requests to bypass Akamai WAF 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        }
        r = requests.get("https://www.india.gov.in", headers=headers, verify=False, timeout=15)
        page.set_content(r.text, wait_until="domcontentloaded")
        
        # Test strict URL route /hi
        print("Testing URL route https://www.india.gov.in/hi ...")
        page.goto("https://www.india.gov.in/hi", timeout=15000, wait_until="commit")
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
            
        full_text = page.evaluate("() => document.body.innerText")
        dev_chars = len(re.findall(r'[\u0900-\u097F]', full_text))
        total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', full_text))
        pct = (dev_chars / max(1, total_alpha)) * 100
        
        print(f"URL /hi Loaded! Title: '{page.title()}'")
        print(f"Devanagari characters count: {dev_chars}")
        print(f"Devanagari script percentage: {pct:.2f}%")
        print(f"Sample text snippet: {full_text[:300]}...")
        
        browser.close()

if __name__ == "__main__":
    test_india_fix()
