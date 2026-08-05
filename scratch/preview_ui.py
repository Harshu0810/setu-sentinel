"""
Renders index.html in Playwright Chromium and saves a screenshot artifact.
"""
import sys
import os
from playwright.sync_api import sync_playwright

html_path = os.path.abspath("index.html")
file_url = f"file:///{html_path.replace('\\', '/')}"

print(f"Opening {file_url} in Chromium...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(file_url, wait_until="networkidle")
    page.wait_for_timeout(2500)
    
    artifact_dir = r"C:\Users\Harsh\.gemini\antigravity-ide\brain\b1edaa6d-324e-4651-9ed0-3436375e14ad"
    screenshot_path = os.path.join(artifact_dir, "ui_preview_dashboard.png")
    page.screenshot(path=screenshot_path, full_page=False)
    print(f"Saved preview screenshot to: {screenshot_path}")
    browser.close()
