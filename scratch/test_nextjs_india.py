"""
Test Playwright on Next.js powered india.gov.in
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
        ignore_https_errors=True
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)
    
    print("Navigating to https://www.india.gov.in...")
    page.goto("https://www.india.gov.in", timeout=30000, wait_until="commit")
    
    # Wait for Next.js hydration
    print("Waiting 5s for Next.js SPA hydration...")
    page.wait_for_timeout(5000)
    
    title = page.title()
    print("Page Title:", title)
    
    body_text = page.evaluate("() => document.body.innerText")
    print(f"Hydrated text length: {len(body_text)}")
    print("First 300 chars of body text:\n", body_text[:300])
    
    # Search for all clickable elements or language buttons
    buttons = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, a, select, option, span, div')).map(el => ({
            text: el.innerText ? el.innerText.trim() : '',
            aria: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            href: el.getAttribute('href') || ''
        })).filter(x => x.text.includes('हिंदी') || x.text.includes('हिन्दी') || x.text.includes('Hindi') || x.aria.includes('Hindi') || x.title.includes('Hindi'));
    }""")
    print("Language elements found:", buttons)
    
    browser.close()
