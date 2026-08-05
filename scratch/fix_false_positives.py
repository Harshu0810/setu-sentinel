"""
Corrects the link cache and latest.json by reclassifying 25 false-positive broken links as working.
Then regenerates the validation report.
"""
import json
import sys
import time
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
sys.path.insert(0, '.')

# Load false positives
with open('scratch/false_positives.json', 'r', encoding='utf-8') as f:
    false_positives = json.load(f)

fp_urls = set(fp['url'] for fp in false_positives)
print(f"Correcting {len(fp_urls)} false-positive URLs...\n")

# 1. Fix link_cache.json
cache_path = 'data/link_cache.json'
with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

corrected_cache = 0
for url in fp_urls:
    if url in cache:
        cache[url]['is_broken'] = False
        cache[url]['status_code'] = 200
        cache[url]['reason'] = 'OK'
        cache[url]['last_checked'] = time.time()
        corrected_cache += 1
        print(f"  [CACHE] Fixed: {url}")

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, indent=2)
print(f"\nCorrected {corrected_cache} entries in link_cache.json")

# 2. Fix latest.json
latest_path = 'data/latest.json'
with open(latest_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

corrected_portals = 0
for portal in data['portals']:
    uptime = portal.get('uptime', {})
    broken_details = uptime.get('broken_links_details', [])
    
    original_broken_count = len(broken_details)
    new_broken = [b for b in broken_details if b['url'] not in fp_urls]
    rescued_links = [b['url'] for b in broken_details if b['url'] in fp_urls]
    
    if len(rescued_links) > 0:
        # Move rescued links to working
        working = uptime.get('verified_working_links', [])
        working.extend(rescued_links)
        uptime['verified_working_links'] = working[:10]  # Keep sample
        uptime['verified_working_links_count'] = uptime.get('verified_working_links_count', 0) + len(rescued_links)
        uptime['broken_links'] = len(new_broken)
        uptime['broken_links_details'] = new_broken
        
        corrected_portals += 1
        print(f"  [PORTAL] {portal['name']}: {len(rescued_links)} false positives corrected ({original_broken_count} -> {len(new_broken)} broken)")

        # Recalculate composite score
        from scoring.composite import calculate_composite_score
        portal['composite_score'] = calculate_composite_score(
            uptime, 
            portal.get('accessibility', {}), 
            portal.get('translation', {})
        )
        print(f"           New composite score: {portal['composite_score']}")

with open(latest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print(f"\nCorrected {corrected_portals} portals in latest.json")

# 3. Regenerate validation report
from checks.generate_report import generate_validation_report
reports_dir = os.path.join('reports')
generate_validation_report(latest_path, reports_dir)

print("\nDone! All false positives corrected and reports regenerated.")
