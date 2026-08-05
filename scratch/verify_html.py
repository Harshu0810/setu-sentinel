"""
Verifies that index.html contains all required IDs and DOM elements.
"""
from bs4 import BeautifulSoup

html_content = open("index.html", "r", encoding="utf-8").read()
soup = BeautifulSoup(html_content, "html.parser")

required_ids = [
    "snapshot-time", "stat-total", "stat-online", "stat-avg-score", "stat-violations",
    "search-input", "sort-select", "portal-table-body", "showing-count",
    "modal-title", "modal-category", "modal-url", "modal-url-text",
    "tab-btn-uptime", "tab-btn-accessibility", "tab-btn-translation",
    "tab-content-uptime", "tab-content-accessibility", "tab-content-translation",
    "detail-status-code", "detail-response-ms", "detail-broken-count", "broken-links-container",
    "detail-axe-count", "detail-critical-count", "wcag-violations-container", "detail-vision-notes",
    "detail-trans-switcher", "detail-trans-status", "detail-trans-score",
    "detail-trans-regional", "detail-trans-quality", "flagged-terms-container"
]

missing = []
for el_id in required_ids:
    if not soup.find(id=el_id):
        missing.append(el_id)

if missing:
    print(f"❌ Missing IDs in index.html: {missing}")
else:
    print(f"✅ All {len(required_ids)} required DOM element IDs found in index.html!")
