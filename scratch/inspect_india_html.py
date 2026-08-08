"""
Search all elements on india.gov.in for language triggers
"""
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
}

r = requests.get("https://india.gov.in", headers=headers, verify=False, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")

for tag in soup.find_all(["button", "select", "div", "span", "a"]):
    txt = tag.get_text(strip=True)
    cls = " ".join(tag.get("class", []))
    id_attr = tag.get("id", "")
    
    if any(k in txt.lower() for k in ["translation", "language", "bhashini", "select language", "translate"]) or \
       any(k in cls.lower() for k in ["lang", "translate", "bhashini"]) or \
       any(k in id_attr.lower() for k in ["lang", "translate", "bhashini"]):
        print(f"<{tag.name} id='{id_attr}' class='{cls}'>")
        print(f"  text: '{txt[:100]}'")
        print(f"  outerHTML: {str(tag)[:200]}\n")
