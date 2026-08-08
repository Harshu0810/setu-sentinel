"""
Find all links and routes in india.gov.in HTML
"""
import requests
import re
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

print("All hrefs in india.gov.in HTML:")
hrefs = set(a.get("href") for a in soup.find_all("a") if a.get("href"))
for h in sorted(hrefs):
    print("  -", h)

print("\nSearching scripts for language endpoints...")
for s in soup.find_all("script"):
    st = s.string or s.get_text()
    if st and any(k in st.lower() for k in ["lang", "hindi", "हिन्दी", "bhashini"]):
        matches = re.findall(r'https?://[^\s"\']+|/[a-zA-Z0-9_\-\?=/]+', st)
        print("Script match references:", matches[:10])
