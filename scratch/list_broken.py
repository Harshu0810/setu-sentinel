import json

data = json.load(open('data/latest.json', 'r', encoding='utf-8'))

print("=" * 120)
print(f"{'PORTAL':35s} | {'CODE':>4s} | {'REASON':25s} | URL")
print("=" * 120)

total_broken = 0
for p in data['portals']:
    for b in p['uptime'].get('broken_links_details', []):
        total_broken += 1
        print(f"{p['name']:35s} | {b['status_code']:4d} | {b['reason']:25s} | {b['url']}")

print("=" * 120)
print(f"Total broken links across all portals: {total_broken}")
