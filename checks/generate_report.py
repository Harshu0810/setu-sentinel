import json
import os
from datetime import datetime, timezone

def generate_validation_report(latest_data_path: str, output_dir: str):
    """
    Generates structured Validation & Verification Reports (JSON and Markdown)
    proving link verification audits, WCAG accessibility metrics, and translation scores.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    with open(latest_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    portals = data.get("portals", [])
    run_at = data.get("run_at", datetime.now(timezone.utc).isoformat())
    
    total_portals = len(portals)
    portals_up = sum(1 for p in portals if p.get("uptime", {}).get("status") == "up")
    total_links_found = sum(p.get("uptime", {}).get("total_links_found", 0) for p in portals)
    total_links_audited = sum(p.get("uptime", {}).get("total_links_audited", 0) for p in portals)
    total_broken_links = sum(p.get("uptime", {}).get("broken_links", 0) for p in portals)
    total_verified_working = sum(p.get("uptime", {}).get("verified_working_links_count", 0) for p in portals)
    
    # 1. Generate JSON Verification Report
    report_json = {
        "report_title": "Setu Sentinel — Comprehensive Validation & Verification Report",
        "generated_at": run_at,
        "summary": {
            "total_portals_configured": total_portals,
            "portals_online": portals_up,
            "portals_offline": total_portals - portals_up,
            "total_links_discovered": total_links_found,
            "total_links_audited": total_links_audited,
            "verified_working_links": total_verified_working,
            "total_broken_links_confirmed": total_broken_links,
            "average_composite_score": round(sum(p.get("composite_score", 0) for p in portals) / max(1, total_portals), 2)
        },
        "portal_verifications": []
    }
    
    md_lines = [
        "# 🛡️ Setu Sentinel — Validation & Verification Report",
        f"**Generated:** {run_at} | **Target Portals:** {total_portals} | **Independent Audit**",
        "",
        "## 📊 Executive Audit Summary",
        f"- **Portals Evaluated:** {total_portals} ({portals_up} Online, {total_portals - portals_up} Offline)",
        f"- **Total Links Discovered Across Homepages:** {total_links_found}",
        f"- **Sampled Links Audited with Chromium TLS:** {total_links_audited}",
        f"- **Verified Working Links:** {total_verified_working} (HTTP 200/203/301/302)",
        f"- **Confirmed Broken Links (True 404/5xx):** {total_broken_links}",
        "",
        "---",
        "",
        "## 🔍 Portal-by-Portal Link Verification & Pillar Audit Log",
        "",
        "| Portal Name | Category | Uptime | Links Discovered | Links Audited | Working Links | Broken Links | WCAG Score | Hindi Score | Composite Score |",
        "|---|---|---|---|---|---|---|---|---|---|"
    ]
    
    for p in portals:
        name = p.get("name", "Unknown")
        cat = p.get("category", "General")
        up = p.get("uptime", {})
        acc = p.get("accessibility", {})
        trans = p.get("translation", {})
        
        status_str = "✅ UP" if up.get("status") == "up" else "❌ DOWN"
        links_found = up.get("total_links_found", 0)
        links_audited = up.get("total_links_audited", 0)
        working_count = up.get("verified_working_links_count", 0)
        broken_count = up.get("broken_links", 0)
        
        acc_score = acc.get("score", 0)
        trans_score = trans.get("score", 0)
        comp_score = p.get("composite_score", 0)
        
        md_lines.append(f"| **{name}** | {cat} | {status_str} | {links_found} | {links_audited} | {working_count} | {broken_count} | {acc_score}/100 | {trans_score}/100 | **{comp_score}** |")
        
        report_json["portal_verifications"].append({
            "name": name,
            "url": p.get("url"),
            "status": up.get("status"),
            "links_summary": {
                "discovered": links_found,
                "audited": links_audited,
                "verified_working": working_count,
                "broken": broken_count
            },
            "verified_working_sample": up.get("verified_working_links", []),
            "broken_details": up.get("broken_links_details", []),
            "accessibility": {
                "score": acc_score,
                "violations": acc.get("axe_violations", 0),
                "critical": acc.get("critical", 0)
            },
            "translation": {
                "score": trans_score,
                "devanagari_pct": trans.get("devanagari_ratio_pct", 0),
                "switcher_found": trans.get("switcher_found", False),
                "switcher_type": trans.get("switcher_type", "None"),
                "status": trans.get("status"),
                "regional_breakdown": trans.get("regional_breakdown", {}),
                "quality_breakdown": trans.get("quality_breakdown", {}),
                "flagged_terms": trans.get("flagged_terms", [])
            },
            "composite_score": comp_score
        })
        
    md_lines.extend([
        "",
        "---",
        "",
        "## 🔬 Methodology & Verification Transparency",
        "1. **Link Validation**: Executed directly within Playwright Chromium browser context using native TLS engines, bypassing non-browser WAF blocks (HTTP 403) while detecting true 404/5xx dead links.",
        "2. **WCAG Accessibility**: Audited via axe-core with direct CSP script execution fallback to a native 10-point DOM scanner.",
        "3. **Hindi Translation Score**: Continuous 0-100 metric calculated via Multi-Region Devanagari Script Density (30 pts), Multi-Strategy Language Switcher Discovery across 5 UI paradigms (30 pts), and GIGW Official Terminology & LLM Semantic Quality Audit (40 pts)."
    ])
    
    # Save JSON report
    json_path = os.path.join(output_dir, "validation_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)
        
    # Save Markdown report
    md_path = os.path.join(output_dir, "validation_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print(f"Validation & Verification Reports generated at:\n  - {json_path}\n  - {md_path}")

if __name__ == "__main__":
    latest_path = os.path.join(os.path.dirname(__file__), "..", "data", "latest.json")
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    generate_validation_report(latest_path, reports_dir)
