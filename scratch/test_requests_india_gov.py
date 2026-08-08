"""
Test requests.get on india.gov.in and hi.india.gov.in
"""
import requests
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
}

print("Fetching https://india.gov.in with requests...")
r1 = requests.get("https://india.gov.in", headers=headers, verify=False, timeout=10)
print(f"Status: {r1.status_code}, Length: {len(r1.text)}")

print("\nFetching https://hi.india.gov.in with requests...")
r2 = requests.get("https://hi.india.gov.in", headers=headers, verify=False, timeout=10)
print(f"Status: {r2.status_code}, Length: {len(r2.text)}")
if "भारत" in r2.text or "राष्ट्रीय" in r2.text or "हिन्दी" in r2.text or "हिंदी" in r2.text:
    print("MATCH: Devanagari text present in hi.india.gov.in response!")
