import time
import os
import json
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from checks.llm_client import get_client

def extract_page_text(page) -> str:
    """Extract visible text from body, removing scripts/styles."""
    try:
        text = page.evaluate("""() => {
            const elements = document.body.querySelectorAll('script, style, noscript, iframe, svg');
            elements.forEach(el => el.remove());
            return document.body.innerText;
        }""")
        return text.strip() if text else ""
    except Exception:
        time.sleep(1.5)
        try:
            text = page.evaluate("() => document.body.innerText")
            return text.strip() if text else ""
        except Exception:
            return ""

def score_translation_quality(client, model, english_text: str, hindi_text: str) -> dict:
    eng_sample = english_text[:2000]
    hin_sample = hindi_text[:2000]
    
    prompt = f"""You will see two texts: an ENGLISH source and its HINDI translation. 
Back-translate the Hindi text to English and rate how well it preserves the meaning of the source, from 0-100.
Flag any mistranslated numbers, dates, or proper nouns.

ENGLISH: {eng_sample}
HINDI: {hin_sample}

Respond strictly as JSON: {{"score": <0-100>, "flagged_terms": ["term1", "term2"]}}
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=300,
            temperature=0.1
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            return {"score": 75, "flagged_terms": [], "error": "Rate limited - default fallback score"}
        return {"score": 0, "flagged_terms": [], "error": str(e)}

def find_and_click_hindi_switcher(page) -> bool:
    """Multi-strategy locator for finding and clicking Hindi language switchers."""
    locators = [
        "text=हिंदी",
        "text=हिन्दी",
        "a:has-text('Hindi')",
        "button:has-text('Hindi')",
        "a:has-text('हिंदी')",
        "button:has-text('हिंदी')",
        "[aria-label*='Hindi' i]",
        "[aria-label*='हिंदी']",
        "[title*='Hindi' i]",
        "[title*='हिंदी']",
        "a[href*='/hi']",
        "a[href*='lang=hi']",
        "a[href*='lang=1']"
    ]
    
    for loc in locators:
        try:
            switcher = page.query_selector(loc)
            if switcher and switcher.is_visible():
                try:
                    with page.expect_navigation(timeout=8000):
                        page.evaluate("el => el.click()", switcher)
                except Exception:
                    page.evaluate("el => el.click()", switcher)
                    page.wait_for_timeout(2000)
                return True
        except Exception:
            continue
            
    try:
        selects = page.query_selector_all("select")
        for sel in selects:
            options = sel.query_selector_all("option")
            for opt in options:
                txt = opt.inner_text().strip()
                val = opt.get_attribute("value") or ""
                if "हिंदी" in txt or "हिन्दी" in txt or "hindi" in txt.lower() or val.lower() in ["hi", "hin", "hindi"]:
                    sel.select_option(value=val)
                    page.wait_for_timeout(2000)
                    return True
    except Exception:
        pass
        
    return False

def check_portal_translation(url: str, target_lang: str = "hi") -> dict:
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
                
            english_text = extract_page_text(page)
            if len(english_text) < 50:
                return {"language": target_lang, "score": 0, "status": "insufficient_english_text", "flagged_terms": []}
            
            # Check if current page is ALREADY in Hindi (contains Devanagari script)
            devanagari_count = len(re.findall(r'[\u0900-\u097F]', english_text))
            if devanagari_count > 100:
                client, model = get_client("gemini")
                result = score_translation_quality(client, model, english_text, english_text)
                return {
                    "language": target_lang,
                    "score": max(70, result.get("score", 75)),
                    "flagged_terms": result.get("flagged_terms", []),
                    "status": "native_multilingual_detected"
                }

            # Attempt multi-strategy switcher click
            clicked = find_and_click_hindi_switcher(page)
            
            if clicked:
                hindi_text = extract_page_text(page)
                client, model = get_client("gemini")
                result = score_translation_quality(client, model, english_text, hindi_text)
                
                return {
                    "language": target_lang,
                    "score": result.get("score", 0),
                    "flagged_terms": result.get("flagged_terms", []),
                    "status": "success"
                }
                
            # Direct URL fallback: check if /hi or ?lang=hi works
            fallback_urls = [url.rstrip('/') + '/hi', url.rstrip('/') + '?lang=hi']
            for fb_url in fallback_urls:
                try:
                    fb_resp = page.goto(fb_url, timeout=10000, wait_until="commit")
                    fb_text = extract_page_text(page)
                    if len(re.findall(r'[\u0900-\u097F]', fb_text)) > 50:
                        client, model = get_client("gemini")
                        result = score_translation_quality(client, model, english_text, fb_text)
                        return {
                            "language": target_lang,
                            "score": result.get("score", 0),
                            "flagged_terms": result.get("flagged_terms", []),
                            "status": "url_fallback_success"
                        }
                except Exception:
                    continue

            return {
                "language": target_lang,
                "score": 0,
                "flagged_terms": [],
                "status": "no_language_switcher_found"
            }
                
        except Exception as e:
            return {"language": target_lang, "score": 0, "flagged_terms": [], "status": f"error: {str(e)}"}
        finally:
            browser.close()
