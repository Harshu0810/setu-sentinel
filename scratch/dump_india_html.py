"""
Dump top html elements of india.gov.in
"""
import requests
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
}

r = requests.get("https://india.gov.in", headers=headers, verify=False, timeout=15)
print("Response Status:", r.status_code)
print("First 1500 chars of HTML:")
print(r.text[:1500])
