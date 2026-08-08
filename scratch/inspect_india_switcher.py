import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
}
r = requests.get("https://www.india.gov.in", headers=headers, verify=False, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

print("All elements with 'lang' or 'hi' or 'hindi' or 'हिंदी' or 'हिन्दी':")
for tag in soup.find_all(['a', 'button', 'select', 'li', 'div']):
    txt = tag.get_text().strip()
    href = tag.get('href', '')
    title = tag.get('title', '')
    aria = tag.get('aria-label', '')
    cl = tag.get('class', [])
    cl_str = ' '.join(cl) if isinstance(cl, list) else str(cl)
    
    if any(k in txt.lower() or k in href.lower() or k in title.lower() or k in aria.lower() or k in cl_str.lower() for k in ['hindi', 'हिंदी', 'हिन्दी', 'lang']):
        if len(txt) < 100:
            print(f"Tag: <{tag.name}> | Text: '{txt}' | Href: '{href}' | Class: '{cl_str}' | Title: '{title}' | Aria: '{aria}'")
