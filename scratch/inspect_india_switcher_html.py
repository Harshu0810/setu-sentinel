"""
Inspect header HTML of india.gov.in to find language switcher markup
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

print("Searching header/nav/utility elements...")
for tag in soup.find_all(["header", "nav", "div", "ul", "li"]):
    cls = " ".join(tag.get("class", []))
    id_attr = tag.get("id", "")
    if "header" in cls.lower() or "top" in cls.lower() or "menu" in cls.lower() or "lang" in cls.lower() or "header" in id_attr.lower():
        txt = tag.get_text(strip=True)[:150]
        if "Hindi" in txt or "हिन्दी" in txt or "हिंदी" in txt or "Language" in txt or "Translate" in txt or "English" in txt:
            print(f"<{tag.name} id='{id_attr}' class='{cls}'>")
            print(f"  text: '{txt}'")
            print(f"  HTML: {str(tag)[:300]}\n")
