import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Setu Sentinel — Public Health Scorecard",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Setu Sentinel")
st.subheader("Live Health & Accessibility Scorecard for Indian Government Portals")
st.caption("Tracking uptime, WCAG accessibility violations, and translation quality on entirely free infrastructure.")

# Load historical snapshots
history_dir = os.path.join(os.path.dirname(__file__), "..", "data", "history")

@st.cache_data(ttl=60)
def load_latest_snapshot():
    if not os.path.exists(history_dir):
        return None, []
        
    files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
    if not files:
        return None, []
        
    files.sort(reverse=True)
    latest_file = files[0]
    
    with open(os.path.join(history_dir, latest_file), "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return latest_file, data.get("portals", [])

latest_file, portals = load_latest_snapshot()

if not portals:
    st.warning("No snapshot data available yet. Please run `python -m checks.run_all` to generate the first report.")
else:
    # Summary Metrics
    total_portals = len(portals)
    up_count = sum(1 for p in portals if p.get("uptime", {}).get("status") == "up")
    avg_score = sum(p.get("composite_score", 0) for p in portals) / total_portals if total_portals > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Portals Tracked", total_portals)
    col2.metric("Portals Online", f"{up_count} / {total_portals}")
    col3.metric("Average Health Score", f"{avg_score:.1f} / 100")
    col4.metric("Last Refreshed", latest_file.replace(".json", ""))

    st.markdown("---")

    # Portal Health Table
    st.write("### 📊 Portal Scorecard Leaderboard")
    
    table_data = []
    for p in portals:
        table_data.append({
            "Portal Name": p["name"],
            "Category": p["category"],
            "Composite Score": p.get("composite_score", 0),
            "Status": "🟢 UP" if p.get("uptime", {}).get("status") == "up" else "🔴 DOWN",
            "Response Time (ms)": p.get("uptime", {}).get("response_ms", 0),
            "Broken Links": p.get("uptime", {}).get("broken_links", 0),
            "Accessibility Violations": p.get("accessibility", {}).get("axe_violations", 0),
            "Translation Score": p.get("translation", {}).get("score", 0)
        })
        
    df = pd.DataFrame(table_data)
    df = df.sort_values(by="Composite Score", ascending=False)
    
    st.dataframe(
        df,
        column_config={
            "Composite Score": st.column_config.ProgressColumn(
                "Health Score",
                help="Composite score combining uptime, WCAG accessibility, and translation fidelity",
                format="%d",
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Detailed Breakdown per Portal
    st.write("### 🔍 Detailed Inspection")
    selected_portal_name = st.selectbox("Select a portal to view breakdown:", [p["name"] for p in portals])
    
    selected_portal = next((p for p in portals if p["name"] == selected_portal_name), None)
    
    if selected_portal:
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.write("#### ⚡ Uptime & Performance")
            st.json(selected_portal.get("uptime", {}))
            
        with c2:
            st.write("#### ♿ Accessibility (axe-core)")
            st.json(selected_portal.get("accessibility", {}))
            
        with c3:
            st.write("#### 🌐 Translation Quality (Hindi)")
            st.json(selected_portal.get("translation", {}))

st.markdown("---")
st.caption("⚡ Independent civic-tech project. Not affiliated with the Government of India.")
