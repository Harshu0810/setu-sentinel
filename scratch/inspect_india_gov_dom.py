"""
Inspects header and URL details on india.gov.in
"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True
    )
    page = context.new_page()
    print("Navigating to https://india.gov.in...")
    resp = page.goto("https://india.gov.in", timeout=30000, wait_until="commit")
    page.wait_for_timeout(3000)
    
    print(f"Final URL: {page.url}")
    print(f"Page Title: {page.title()}")
    
    # Extract all <a> tags
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a')).map(a => ({
            text: a.innerText.trim(),
            title: a.getAttribute('title') || '',
            href: a.getAttribute('href') || '',
            outer: a.outerHTML.substring(0, 150)
        })).filter(a => a.text || a.title || a.href);
    }""")
    
    print(f"\nTotal links found on page: {len(links)}")
    for l in links:
        if 'lang' in l['href'].lower() or 'hi' in l['href'].lower() or 'hindi' in l['text'].lower() or 'हिन्दी' in l['text'] or 'हिंदी' in l['text'] or 'हिन्दी' in l['title'] or 'हिंदी' in l['title']:
            print(f"MATCHED LINK -> text: '{l['text']}' | title: '{l['title']}' | href: '{l['href']}' | outer: {l['outer']}")

    # Print top header text
    header_text = page.evaluate("() => document.querySelector('header, .header, #header, body').innerText.substring(0, 1000)")
    print(f"\nHeader Text Sample:\n{header_text[:500]}")
    
    browser.close()
