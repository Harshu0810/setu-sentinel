import requests
import re
from bs4 import BeautifulSoup

def test_punycode():
    # Punycode for भारतसरकार.राष्ट्रीयपोर्टल.भारत
    url = "https://xn--i1bj3fqcyde.xn--11b7cb3a6a.xn--h2brj9c"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'hi,en-US;q=0.9,en;q=0.8',
    }
    print(f"Fetching {url} ...")
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    print(f"Status Code: {r.status_code}, Length: {len(r.text)}")
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text()
    dev_text_chars = len(re.findall(r'[\u0900-\u097F]', text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', text))
    pct = (dev_text_chars / max(1, total_alpha)) * 100
    
    print(f"Title: {soup.title.string if soup.title else 'No Title'}")
    print(f"Devanagari text characters: {dev_text_chars}")
    print(f"Devanagari percentage: {pct:.2f}%")
    print(f"Sample text snippet:\n{text[:500]}")

if __name__ == "__main__":
    test_punycode()
