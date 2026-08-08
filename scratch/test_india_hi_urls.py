"""
Test Hindi URL routes on india.gov.in via requests
"""
import requests
import re
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
}

urls = [
    "https://india.gov.in/hi",
    "https://www.india.gov.in/hi",
    "https://india.gov.in/?lang=hi",
    "https://india.gov.in/hindi",
    "https://www.india.gov.in/?lang=hi"
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        dev_chars = len(re.findall(r'[\u0900-\u097F]', r.text))
        print(f"URL: {url} -> Status: {r.status_code}, Devanagari Chars: {dev_chars}, Length: {len(r.text)}")
    except Exception as e:
        print(f"URL: {url} -> Error: {e}")
