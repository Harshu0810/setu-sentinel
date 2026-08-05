"""
Re-verify ALL 114 broken links from latest.json using Playwright Chromium browser context.
Identify false positives (links marked broken but actually working).
"""
import json
import sys
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


data = json.load(open('data/latest.json', 'r', encoding='utf-8'))

# Collect all broken links
broken_links = []
for p in data['portals']:
    for b in p['uptime'].get('broken_links_details', []):
        broken_links.append({
            'portal': p['name'],
            'url': b['url'],
            'original_status': b['status_code'],
            'original_reason': b['reason']
        })

print(f"Re-verifying {len(broken_links)} broken links...\n")

false_positives = []
true_broken = []

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True
    )
    
    for i, link in enumerate(broken_links, 1):
        url = link['url']
        portal = link['portal']
        print(f"[{i}/{len(broken_links)}] {url[:80]}...", end=" ")
        
        try:
            # Method 1: Playwright page.goto (full browser navigation with JS)
            page = context.new_page()
            resp = page.goto(url, timeout=15000, wait_until="commit")
            status = resp.status if resp else 0
            final_url = page.url
            page.close()
            
            if status > 0 and status < 500 and status != 404:
                print(f"✅ WORKING (HTTP {status}, final={final_url[:60]})")
                false_positives.append({**link, 'recheck_status': status, 'recheck_url': final_url})
            else:
                print(f"❌ BROKEN (HTTP {status})")
                true_broken.append({**link, 'recheck_status': status})
        except Exception as e1:
            # Method 2: Playwright context.request.get (lighter weight)
            try:
                resp2 = context.request.get(url, timeout=12000)
                status2 = resp2.status
                if status2 > 0 and status2 < 500 and status2 != 404:
                    print(f"✅ WORKING via API (HTTP {status2})")
                    false_positives.append({**link, 'recheck_status': status2, 'recheck_url': url})
                else:
                    print(f"❌ BROKEN via API (HTTP {status2})")
                    true_broken.append({**link, 'recheck_status': status2})
            except Exception as e2:
                print(f"❌ UNREACHABLE ({str(e1)[:50]})")
                true_broken.append({**link, 'recheck_status': 0})
    
    browser.close()

print("\n" + "=" * 120)
print(f"\n🟢 FALSE POSITIVES (marked broken but actually WORKING): {len(false_positives)}")
print("=" * 120)
for fp in false_positives:
    print(f"  {fp['portal']:35s} | was={fp['original_status']:4d} | now={fp['recheck_status']:4d} | {fp['url']}")

print(f"\n🔴 CONFIRMED TRULY BROKEN: {len(true_broken)}")
print("=" * 120)
for tb in true_broken:
    print(f"  {tb['portal']:35s} | was={tb['original_status']:4d} | now={tb['recheck_status']:4d} | {tb['url']}")

# Save false positives to JSON for cache correction
with open('scratch/false_positives.json', 'w', encoding='utf-8') as f:
    json.dump(false_positives, f, indent=2)

print(f"\nSaved {len(false_positives)} false positives to scratch/false_positives.json")
