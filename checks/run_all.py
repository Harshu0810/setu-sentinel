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
    print("=" * 60)
    
    # Load portals
    portals_path = os.path.join(os.path.dirname(__file__), "..", "data", "portals.json")
    with open(portals_path, "r") as f:
        portals = json.load(f)
    
    total = len(portals)
    print(f"Loaded {total} portals to evaluate.\n")
        
    results = []
    
    for i, p in enumerate(portals, 1):
        url = p["url"]
        name = p["name"]
        print(f"[{i}/{total}] Checking {name} ({url})...")
        
        # 1. Uptime Check
        try:
            uptime_data = check_portal_uptime(url)
        except Exception as e:
            print(f"  [!] Uptime check failed: {e}")
            uptime_data = {"status": "error", "error": str(e), "broken_links": 0, "broken_links_details": []}
        print(f"  Uptime: {uptime_data.get('status', 'unknown')} ({uptime_data.get('response_ms', '?')}ms), {uptime_data.get('broken_links', 0)} broken links")
        
        # 2. Accessibility Check
        try:
            accessibility_data = check_portal_accessibility(url)
        except Exception as e:
            print(f"  [!] Accessibility check failed: {e}")
            accessibility_data = {"axe_violations": 0, "critical": 0, "violation_details": [], "score": 0}
        print(f"  Accessibility: {accessibility_data.get('axe_violations', 0)} violations, {accessibility_data.get('critical', 0)} critical, score={accessibility_data.get('score', 0)}")
        
        # 3. Translation Check
        try:
            translation_data = check_portal_translation(url, target_lang="hi")
        except Exception as e:
            print(f"  [!] Translation check failed: {e}")
            translation_data = {"language": "hi", "score": 0, "flagged_terms": [], "status": "error"}
        print(f"  Translation: score={translation_data.get('score', 0)}, status={translation_data.get('status', 'unknown')}")
        
        # 4. Composite Scoring
        comp_score = calculate_composite_score(uptime_data, accessibility_data, translation_data)
        print(f"  >> Composite Score: {comp_score}")
        print()
        
        results.append({
            "name": name,
            "url": url,
            "category": p["category"],
            "subcategory": p.get("subcategory", ""),
            "purpose": p.get("purpose", ""),
            "priority": p.get("priority", 3),
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
        "total_portals": len(results),
        "portals": results
    }
    
    history_dir = os.path.join(os.path.dirname(__file__), "..", "data", "history")
    os.makedirs(history_dir, exist_ok=True)
    
    filename = now_utc.strftime("%Y-%m-%dT%H-%M.json")
    filepath = os.path.join(history_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
        
    # Save latest snapshot for live GitHub Pages dashboard
    latest_path = os.path.join(os.path.dirname(__file__), "..", "data", "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
        
    print("=" * 60)
    print(f"Evaluation complete: {len(results)} portals checked.")
    print(f"Snapshot saved to {filepath} and {latest_path}")

if __name__ == "__main__":
    main()
