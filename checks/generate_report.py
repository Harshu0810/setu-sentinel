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

    # Save Beautiful Rendered HTML Report
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='en' class='dark'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "  <title>Setu Sentinel — Comprehensive Validation & Verification Report</title>",
        "  <script src='https://cdn.tailwindcss.com'></script>",
        "  <link href='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap' rel='stylesheet'>",
        "  <style>body{background-color:#080c14;color:#f1f5f9;font-family:'Plus Jakarta Sans',sans-serif;}.glass-panel{background:rgba(15,23,42,0.7);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.08);}</style>",
        "</head>",
        "<body class='min-h-screen p-6 sm:p-10 max-w-7xl mx-auto space-y-8'>",
        "  <header class='glass-panel p-6 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 border border-slate-800 shadow-xl'>",
        "    <div>",
        "      <h1 class='text-2xl font-extrabold text-white tracking-tight flex items-center gap-2'>🛡️ Setu Sentinel Verification Report</h1>",
        f"      <p class='text-xs text-slate-400 mt-1 font-mono'>Generated: {run_at} | Target Portals: {total_portals} | Independent Audit</p>",
        "    </div>",
        "    <div class='flex items-center space-x-3 text-xs'>",
        "      <a href='../index.html' class='px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition shadow-lg'>Back to Dashboard</a>",
        "      <a href='./validation_report.md' target='_blank' class='px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-xl border border-slate-700 transition'>Raw Markdown</a>",
        "    </div>",
        "  </header>",
        "",
        "  <section class='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4'>",
        "    <div class='glass-panel p-4 rounded-xl border border-slate-800'><p class='text-xs text-slate-400'>Evaluated Portals</p><h3 class='text-xl font-bold text-white mt-1'>" + f"{total_portals} ({portals_up} Online, {total_portals - portals_up} Offline)" + "</h3></div>",
        "    <div class='glass-panel p-4 rounded-xl border border-slate-800'><p class='text-xs text-slate-400'>Total Homepage Links Discovered</p><h3 class='text-xl font-bold text-indigo-400 mt-1'>" + str(total_links_found) + "</h3></div>",
        "    <div class='glass-panel p-4 rounded-xl border border-slate-800'><p class='text-xs text-slate-400'>Verified Working Links</p><h3 class='text-xl font-bold text-emerald-400 mt-1'>" + str(total_verified_working) + "</h3></div>",
        "    <div class='glass-panel p-4 rounded-xl border border-slate-800'><p class='text-xs text-slate-400'>Confirmed Broken Links (404/5xx)</p><h3 class='text-xl font-bold text-rose-400 mt-1'>" + str(total_broken_links) + "</h3></div>",
        "  </section>",
        "",
        "  <section class='glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl'>",
        "    <div class='px-6 py-4 border-b border-slate-800 bg-slate-900/60'><h2 class='text-base font-bold text-white'>🔍 Portal-by-Portal Link Verification & Pillar Audit Log</h2></div>",
        "    <div class='overflow-x-auto'>",
        "      <table class='w-full text-left text-xs'>",
        "        <thead><tr class='bg-slate-900 text-slate-400 font-semibold border-b border-slate-800 uppercase text-[11px]'><th class='p-3.5 px-6'>Portal Name</th><th class='p-3.5'>Category</th><th class='p-3.5'>Uptime</th><th class='p-3.5'>Discovered</th><th class='p-3.5'>Audited</th><th class='p-3.5'>Working</th><th class='p-3.5'>Broken</th><th class='p-3.5'>WCAG</th><th class='p-3.5'>Hindi</th><th class='p-3.5 px-6 text-right'>Composite</th></tr></thead>",
        "        <tbody class='divide-y divide-slate-800/60'>"
    ]

    for p in portals:
        name = p.get("name", "Unknown")
        cat = p.get("category", "General")
        up = p.get("uptime", {})
        acc = p.get("accessibility", {})
        trans = p.get("translation", {})
        status_badge = "<span class='px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'>✅ UP</span>" if up.get("status") == "up" else "<span class='px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20'>❌ DOWN</span>"
        comp = p.get("composite_score", 0)
        
        html_lines.append(f"<tr class='hover:bg-slate-800/40 transition'><td class='p-3.5 px-6 font-bold text-white'>{name}</td><td class='p-3.5 text-slate-400'>{cat}</td><td class='p-3.5'>{status_badge}</td><td class='p-3.5 font-mono'>{up.get('total_links_found', 0)}</td><td class='p-3.5 font-mono'>{up.get('total_links_audited', 0)}</td><td class='p-3.5 font-mono text-emerald-400'>{up.get('verified_working_links_count', 0)}</td><td class='p-3.5 font-mono text-rose-400'>{up.get('broken_links', 0)}</td><td class='p-3.5 font-mono'>{acc.get('score', 0)}/100</td><td class='p-3.5 font-mono'>{trans.get('score', 0)}/100</td><td class='p-3.5 px-6 text-right font-bold text-indigo-400'>{comp}</td></tr>")

    html_lines.extend([
        "        </tbody>",
        "      </table>",
        "    </div>",
        "  </section>",
        "",
        "  <footer class='glass-panel p-6 rounded-2xl border border-slate-800 text-xs space-y-2'>",
        "    <h3 class='font-bold text-white text-sm'>🔬 Methodology & Verification Transparency</h3>",
        "    <p class='text-slate-400'>1. <strong>Link Validation</strong>: Executed directly within Playwright Chromium browser context using native TLS engines, bypassing non-browser WAF blocks (HTTP 403) while detecting true 404/5xx dead links.</p>",
        "    <p class='text-slate-400'>2. <strong>WCAG Accessibility</strong>: Audited via axe-core with direct CSP script execution fallback to a native 10-point DOM scanner.</p>",
        "    <p class='text-slate-400'>3. <strong>Hindi Translation Score</strong>: Continuous 0-100 metric calculated via Multi-Region Devanagari Script Density (30 pts), Multi-Strategy Language Switcher Discovery across 5 UI paradigms (30 pts), and GIGW Official Terminology & LLM Semantic Quality Audit (40 pts).</p>",
        "  </footer>",
        "</body>",
        "</html>"
    ])

    html_path = os.path.join(output_dir, "validation_report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))
        
    print(f"Validation & Verification Reports generated at:\n  - {json_path}\n  - {md_path}\n  - {html_path}")

def generate_history_manifest(history_dir: str, output_manifest_path: str):
    """
    Aggregates all historical snapshot JSON files in data/history/ into a lightweight
    time-series manifest (data/history_manifest.json) for sparkline trend charts in UI.
    """
    if not os.path.exists(history_dir):
        return
        
    history_entries = []
    files = sorted([f for f in os.listdir(history_dir) if f.endswith(".json")])
    
    for fname in files:
        fpath = os.path.join(history_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                snap = json.load(f)
            ts = snap.get("run_at", fname.replace(".json", ""))
            scores = {}
            for p in snap.get("portals", []):
                pname = p.get("name")
                if pname:
                    scores[pname] = {
                        "score": p.get("composite_score", 0),
                        "status": p.get("uptime", {}).get("status", "down"),
                        "broken": p.get("uptime", {}).get("broken_links", 0),
                        "wcag": p.get("accessibility", {}).get("axe_violations", 0)
                    }
            history_entries.append({
                "timestamp": ts,
                "scores": scores
            })
        except Exception:
            continue
            
    manifest_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshots_count": len(history_entries),
        "history": history_entries
    }
    
    with open(output_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
        
    print(f"History Manifest compiled ({len(history_entries)} snapshots) -> {output_manifest_path}")

if __name__ == "__main__":
    latest_path = os.path.join(os.path.dirname(__file__), "..", "data", "latest.json")
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    generate_validation_report(latest_path, reports_dir)
    
    hist_dir = os.path.join(os.path.dirname(__file__), "..", "data", "history")
    manifest_file = os.path.join(os.path.dirname(__file__), "..", "data", "history_manifest.json")
    generate_history_manifest(hist_dir, manifest_file)
