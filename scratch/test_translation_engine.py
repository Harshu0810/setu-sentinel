"""
Test script for upgraded translation engine across representative Indian government portals.
"""
import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')

from checks.translation import check_portal_translation

test_urls = [
    "https://india.gov.in",          # National Portal of India (Direct Multilingual)
    "https://parivahan.gov.in",       # Parivahan Sewa (Language Switcher)
    "https://edistrict.up.gov.in/edistrictup/", # e-District UP (Native Multilingual)
    "https://www.digitalgujarat.gov.in" # Digital Gujarat (No Switcher / English)
]

print("=" * 100)
print("TESTING UPGRADED TRANSLATION ENGINE")
print("=" * 100)

for url in test_urls:
    print(f"\nChecking: {url}")
    result = check_portal_translation(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))

print("\nDone!")
