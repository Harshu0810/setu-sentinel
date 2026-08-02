import json
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminals handling Devanagari text
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from checks.uptime import check_portal_uptime
from checks.accessibility import check_portal_accessibility
from checks.translation import check_portal_translation
from scoring.composite import calculate_composite_score

load_dotenv()

def main():
    print("Starting Setu Sentinel Checks...")
    
    # Load portals
    portals_path = os.path.join(os.path.dirname(__file__), "..", "data", "portals.json")
    with open(portals_path, "r") as f:
        portals = json.load(f)
        
    results = []
    
    for p in portals:
        url = p["url"]
        print(f"Checking {p['name']} ({url})...")
        
        # 1. Uptime Check
        uptime_data = check_portal_uptime(url)
        print(f"  Uptime result: {uptime_data}")
        
        # 2. Accessibility Check
        accessibility_data = check_portal_accessibility(url)
        print(f"  Accessibility result: {accessibility_data}")
        
        # 3. Translation Check
        translation_data = check_portal_translation(url, target_lang="hi")
        print(f"  Translation result: {translation_data}")
        
        # 4. Composite Scoring
        comp_score = calculate_composite_score(uptime_data, accessibility_data, translation_data)
        print(f"  Composite Score: {comp_score}")
        
        results.append({
            "name": p["name"],
            "url": url,
            "category": p["category"],
            "languages": p["languages"],
            "uptime": uptime_data,
            "accessibility": accessibility_data,
            "translation": translation_data,
            "composite_score": comp_score
        })
        
    # Generate timestamped snapshot
    now_utc = datetime.now(timezone.utc)
    snapshot = {
        "run_at": now_utc.isoformat(),
        "portals": results
    }
    
    history_dir = os.path.join(os.path.dirname(__file__), "..", "data", "history")
    os.makedirs(history_dir, exist_ok=True)
    
    filename = now_utc.strftime("%Y-%m-%dT%H-%M.json")
    filepath = os.path.join(history_dir, filename)
    
    with open(filepath, "w") as f:
        json.dump(snapshot, f, indent=2)
        
    print(f"Snapshot saved to {filepath}")

if __name__ == "__main__":
    main()
