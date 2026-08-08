"""
Test Akamai WAF bypass on india.gov.in in Playwright
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        },
        ignore_https_errors=True
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    
    print("Navigating to https://india.gov.in with Akamai stealth context...")
    resp = page.goto("https://india.gov.in", timeout=30000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    
    print(f"Status: {resp.status if resp else 'None'}")
    print(f"Title: {page.title()}")
    print(f"URL: {page.url}")
    
    dev_chars = len(page.evaluate("() => document.body.innerText").encode('utf-8'))
    print(f"Body text length: {dev_chars}")
    
    # Check language switchers
    switchers = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a, button')).map(a => ({
            text: a.innerText.trim(),
            title: a.getAttribute('title') || '',
            href: a.getAttribute('href') || '',
            outer: a.outerHTML.substring(0, 150)
        })).filter(a => a.text.includes('हिंदी') || a.text.includes('हिन्दी') || a.title.includes('हिंदी') || a.title.includes('हिन्दी') || a.href.includes('lang=hi') || a.href.includes('hi.'));
    }""")
    print(f"Switchers found: {switchers}")
    
    browser.close()
