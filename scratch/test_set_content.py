"""
Test requests + page.set_content in Playwright for WAF-blocked portals like india.gov.in
"""
import requests
import urllib3
from playwright.sync_api import sync_playwright
from checks.translation import extract_dom_translation_data

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
}

url = "https://india.gov.in"
print(f"Fetching {url} via requests...")
r = requests.get(url, headers=headers, verify=False, timeout=15)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_content(r.text, wait_until="domcontentloaded")
    
    dom_data = extract_dom_translation_data(page)
    print("DOM translation data:")
    print(f"Full text length: {len(dom_data['full_text'])}")
    print(f"Sample text: {dom_data['full_text'][:300]}")
    
    browser.close()
