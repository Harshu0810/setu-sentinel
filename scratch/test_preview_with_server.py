"""
Starts a temporary HTTP server, renders index.html with live data in Playwright, and takes a full dashboard screenshot artifact.
"""
import sys
import os
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def run_server(httpd):
    httpd.serve_forever()

server = HTTPServer(('127.0.0.1', 8090), QuietHandler)
t = threading.Thread(target=run_server, args=(server,), daemon=True)
t.start()

print("Local server running at http://127.0.0.1:8090/index.html")

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto("http://127.0.0.1:8090/index.html", wait_until="networkidle")
        page.wait_for_timeout(3000)
        
        artifact_dir = r"C:\Users\Harsh\.gemini\antigravity-ide\brain\b1edaa6d-324e-4651-9ed0-3436375e14ad"
        screenshot_path = os.path.join(artifact_dir, "ui_live_dashboard_full.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Saved live screenshot to: {screenshot_path}")
        browser.close()
finally:
    server.shutdown()
    print("Server stopped.")
