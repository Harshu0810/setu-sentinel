import base64
import time
import os
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from checks.llm_client import get_client

def get_base64_screenshot(element) -> str:
    """Takes a screenshot of a specific element and returns it as base64 string."""
    image_bytes = element.screenshot()
    return base64.b64encode(image_bytes).decode('utf-8')

def evaluate_alt_text(client, model, alt_text: str, base64_image: str) -> dict:
    """Uses LLM Vision model to evaluate if alt text matches the image."""
    prompt = f"Does the following alt text accurately and descriptively describe the image? Alt text: '{alt_text}'. Answer strictly in JSON format: {{\"accurate\": true/false, \"reason\": \"short reason\"}}"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
            temperature=0.1
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            return {"accurate": True, "reason": "Rate limited - skipping vision check"}
        return {"accurate": False, "reason": f"API Error: {err_msg}"}

def check_portal_accessibility(url: str) -> dict:
    is_ci = os.environ.get("CI", "").lower() == "true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_ci)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            response = page.goto(url, timeout=35000, wait_until="commit")
            
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            
            # Run axe-core via local bundled script to bypass Content Security Policy domain restrictions
            axe_path = os.path.join(os.path.dirname(__file__), "axe.min.js")
            if os.path.exists(axe_path):
                with open(axe_path, "r", encoding="utf-8") as f:
                    axe_script = f.read()
                try:
                    page.add_script_tag(content=axe_script)
                except Exception:
                    time.sleep(1.5) # Wait if redirect in progress
                    page.add_script_tag(content=axe_script)
            else:
                page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.0/axe.min.js")
                
            try:
                results = page.evaluate("async () => await axe.run()")
            except Exception:
                time.sleep(2) # Retry after redirect completes
                results = page.evaluate("async () => await axe.run()")
            
            violations = results.get("violations", [])
            axe_violations_count = sum(len(v.get("nodes", [])) for v in violations)
            critical_count = sum(len(v.get("nodes", [])) for v in violations if v.get("impact") == "critical")
            
            # Detailed violation breakdown
            violation_details = []
            for v in violations:
                violation_details.append({
                    "id": v.get("id"),
                    "impact": v.get("impact", "minor"),
                    "description": v.get("description"),
                    "help": v.get("help"),
                    "nodes": len(v.get("nodes", []))
                })
            
            # Find images for alt text validation (sample up to 3)
            images = page.query_selector_all("img")
            images_checked = 0
            vision_notes = []
            
            client, model = get_client("gemini")
            
            for img in images:
                if images_checked >= 3:
                    break
                    
                alt_text = img.get_attribute("alt")
                if not alt_text or alt_text.strip() == "":
                    continue
                
                if not img.is_visible():
                    continue
                    
                try:
                    box = img.bounding_box()
                    if not box or box['width'] < 10 or box['height'] < 10:
                        continue
                        
                    b64_img = get_base64_screenshot(img)
                    eval_result = evaluate_alt_text(client, model, alt_text, b64_img)
                    
                    if not eval_result.get("accurate", True):
                        vision_notes.append(f"Inaccurate alt text '{alt_text}': {eval_result.get('reason')}")
                    
                    images_checked += 1
                except Exception:
                    pass
            
            inaccurate_alts = len(vision_notes)
            score = 100 - (critical_count * 5) - ((axe_violations_count - critical_count) * 1) - (inaccurate_alts * 10)
            score = max(0, min(100, score))
            
            return {
                "axe_violations": axe_violations_count,
                "critical": critical_count,
                "violation_details": violation_details,
                "vision_notes": "; ".join(vision_notes) if vision_notes else "Alt texts appear accurate or no descriptive images found.",
                "score": score
            }
            
        except Exception as e:
            return {"axe_violations": -1, "critical": -1, "violation_details": [], "vision_notes": f"Error: {str(e)}", "score": 0}
        finally:
            browser.close()
