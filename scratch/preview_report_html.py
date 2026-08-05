"""
Renders reports/validation_report.html in Playwright and saves a screenshot artifact.
"""
import os
from playwright.sync_api import sync_playwright

report_path = os.path.abspath("reports/validation_report.html")
file_url = f"file:///{report_path.replace('\\', '/')}"

print(f"Opening {file_url} in Chromium...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(file_url, wait_until="networkidle")
    
    artifact_dir = r"C:\Users\Harsh\.gemini\antigravity-ide\brain\b1edaa6d-324e-4651-9ed0-3436375e14ad"
    screenshot_path = os.path.join(artifact_dir, "report_html_rendered.png")
    page.screenshot(path=screenshot_path, full_page=False)
    print(f"Saved report screenshot to: {screenshot_path}")
    browser.close()
