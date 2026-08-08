"""
Debug script to inspect translation checker on india.gov.in
"""
from checks.translation import check_portal_translation

res = check_portal_translation("https://india.gov.in")
print(f"Score: {res.get('score')}")
print(f"Status: {res.get('status')}")
print(f"Quality Breakdown: {res.get('quality_breakdown')}")
print(f"Switcher Found: {res.get('switcher_found')}")
