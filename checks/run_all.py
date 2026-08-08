import json
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminals handling Devanagari text
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from checks.uptime import check_portal_uptime_with_page
from checks.accessibility import check_portal_accessibility_with_page
from checks.translation import check_portal_translation_with_page
from scoring.composite import calculate_composite_score
from checks.generate_report import generate_validation_report

load_dotenv()

def main():
    print("Starting Setu Sentinel Evaluation Engine...")
    print("=" * 60)
    
    # Load portals
    portals_path = os.path.join(os.path.dirname(__file__), "..", "data", "portals.json")
    with open(portals_path, "r", encoding="utf-8") as f:
        portals = json.load(f)
    
    total = len(portals)
    print(f"Loaded {total} portals to evaluate.\n")
        
    results = []
    is_headless = os.environ.get("HEADED", "").lower() != "true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        
        for i, portal in enumerate(portals, 1):
            url = portal["url"]
            name = portal["name"]
            target_lang = portal.get("languages", ["hi"])[0]
            print(f"[{i}/{total}] Checking {name} ({url})...")
            
            # Create fresh context per portal for state isolation
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ignore_https_errors=True,
                permissions=["geolocation", "notifications"],
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            
            # 1. Uptime & Link Audit Check
            try:
                uptime_data = check_portal_uptime_with_page(page, context, url)
            except Exception as e:
                print(f"  [!] Uptime check failed: {e}")
                uptime_data = {
                    "status": "error",
                    "error": str(e),
                    "total_links_found": 0,
                    "total_links_audited": 0,
                    "verified_working_links_count": 0,
                    "verified_working_links": [],
                    "broken_links": 0,
                    "broken_links_details": []
                }
            print(f"  Uptime: {uptime_data.get('status', 'unknown')} ({uptime_data.get('response_ms', '?')}ms) | Links: Discovered={uptime_data.get('total_links_found', 0)}, Audited={uptime_data.get('total_links_audited', 0)}, Working={uptime_data.get('verified_working_links_count', 0)}, Broken={uptime_data.get('broken_links', 0)}")
            
            # 2. Accessibility Check (axe-core + Native Fallback)
            try:
                accessibility_data = check_portal_accessibility_with_page(page, url)
            except Exception as e:
                print(f"  [!] Accessibility check failed: {e}")
                accessibility_data = {"axe_violations": 0, "critical": 0, "violation_details": [], "score": 70}
            print(f"  Accessibility: Violations={accessibility_data.get('axe_violations', 0)}, Critical={accessibility_data.get('critical', 0)}, Score={accessibility_data.get('score', 0)}/100")
            
            # 3. Continuous Translation Check (0-100)
            try:
                translation_data = check_portal_translation_with_page(page, url, target_lang=target_lang)
            except Exception as e:
                print(f"  [!] Translation check failed: {e}")
                translation_data = {"language": target_lang, "score": 0, "flagged_terms": [], "status": "error"}
            print(f"  Translation [{target_lang.upper()}]: Score={translation_data.get('score', 0)}/100, ScriptPct={translation_data.get('devanagari_ratio_pct', 0)}%, Status={translation_data.get('status', 'unknown')}")
            
            context.close()
            
            # 4. Composite Scoring
            comp_score = calculate_composite_score(uptime_data, accessibility_data, translation_data)
            print(f"  >> Composite Score: {comp_score}")
            print()
            
            results.append({
                "name": name,
                "url": url,
                "category": portal["category"],
                "subcategory": portal.get("subcategory", ""),
                "purpose": portal.get("purpose", ""),
                "priority": portal.get("priority", 3),
                "languages": portal["languages"],
                "uptime": uptime_data,
                "accessibility": accessibility_data,
                "translation": translation_data,
                "composite_score": comp_score
            })
            
        browser.close()
        
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
    
    from checks.generate_report import generate_history_manifest
    manifest_file = os.path.join(os.path.dirname(__file__), "..", "data", "history_manifest.json")
    generate_history_manifest(history_dir, manifest_file)

if __name__ == "__main__":
    main()
