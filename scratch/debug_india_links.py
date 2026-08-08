import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def debug_india():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        print("Navigating to https://www.india.gov.in ...")
        resp = page.goto("https://www.india.gov.in", timeout=35000, wait_until="commit")
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
            
        print(f"Response status: {resp.status if resp else None}")
        print(f"Title: {page.title()}")
        
        # Check standard links
        links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        print(f"Standard a[href] links count: {len(links)}")
        
        # Check body inner HTML length and snippet
        body_html = page.evaluate("() => document.body.innerHTML")
        print(f"Body inner HTML length: {len(body_html)}")
        
        if len(body_html) < 500 or "access denied" in page.title().lower():
            print("WAF Blocked or empty DOM! Trying WAF requests fallback...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            }
            r = requests.get("https://www.india.gov.in", headers=headers, verify=False, timeout=15)
            print(f"Requests HTTP status: {r.status_code}, HTML length: {len(r.text)}")
            page.set_content(r.text, wait_until="domcontentloaded")
            links_after = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            print(f"Links count after set_content: {len(links_after)}")
            if len(links_after) > 0:
                print(f"Sample links: {links_after[:5]}")
                
        # Check language switchers on page
        print("\nSearching for Hindi link/switcher on india.gov.in...")
        hi_links = page.query_selector_all("a")
        for a in hi_links:
            txt = (a.inner_text() or "").strip()
            href = a.get_attribute("href") or ""
            if "hi" in txt.lower() or "hindi" in txt.lower() or "हिंदी" in txt or "हिन्दी" in txt or "/hi" in href:
                print(f"Found link -> Text: '{txt}', Href: '{href}'")

        browser.close()

if __name__ == "__main__":
    debug_india()
