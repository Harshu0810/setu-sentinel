import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

urls = [
    ("UIDAI", "https://uidai.gov.in"),
    ("PM-JAY", "https://pmjay.gov.in"),
    ("EPFO", "https://unifiedportal-epfo.epfindia.gov.in"),
    ("SARAL Haryana", "https://saralharyana.gov.in"),
    ("Startup India", "https://www.startupindia.gov.in")
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True,
        permissions=["geolocation", "notifications"]
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    
    for name, url in urls:
        print(f"Testing {name} ({url})...")
        try:
            start = time.time()
            resp = page.goto(url, timeout=35000, wait_until="commit")
            status = resp.status if resp else None
            elapsed = int((time.time() - start) * 1000)
            print(f"  -> {name}: status={status}, elapsed={elapsed}ms, url={page.url}")
        except Exception as e:
            print(f"  -> {name}: FAILED error={e}")
            
    browser.close()
