import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from checks.uptime import check_portal_uptime

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
        
        # We will add accessibility and translation checks here later
        
        results.append({
            "name": p["name"],
            "url": url,
            "category": p["category"],
            "languages": p["languages"],
            "uptime": uptime_data,
            # Placeholders for future phases
            "accessibility": {},
            "translation": {},
            "composite_score": 0
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
