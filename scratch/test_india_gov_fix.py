"""
Test translation checker fix for india.gov.in
"""
import requests
import re
import urllib3
from playwright.sync_api import sync_playwright
from checks.translation import extract_dom_translation_data, rule_based_quality_check, score_translation_quality

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
}

url = "https://india.gov.in"
print(f"1. Fetching {url} via requests...")
r = requests.get(url, headers=headers, verify=False, timeout=15)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_content(r.text, wait_until="domcontentloaded")
    
    dom_data = extract_dom_translation_data(page)
    full_text = dom_data["full_text"]
    
    print(f"\nExtracted DOM full text length: {len(full_text)}")
    dev_chars = len(re.findall(r'[\u0900-\u097F]', full_text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', full_text))
    pct = (dev_chars / max(1, total_alpha)) * 100
    print(f"Devanagari characters: {dev_chars}/{total_alpha} ({pct:.2f}%)")
    
    # Run rule-based quality check
    res = rule_based_quality_check(full_text, full_text)
    print("\nRule-based quality check result:")
    print(res)
    
    browser.close()
