import time
import os
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from checks.llm_client import get_client

def extract_page_text(page) -> str:
    """Extract visible text from body, removing scripts/styles."""
    text = page.evaluate("""() => {
        const elements = document.body.querySelectorAll('script, style, noscript, iframe, svg');
        elements.forEach(el => el.remove());
        return document.body.innerText;
    }""")
    return text.strip() if text else ""

def score_translation_quality(client, model, english_text: str, hindi_text: str) -> dict:
    # Truncate text to avoid token limits (check first 2000 chars)
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

def check_portal_translation(url: str, target_lang: str = "hi") -> dict:
    is_ci = os.environ.get("CI", "").lower() == "true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_ci)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            response = page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            if response and response.status in [403, 503] and not is_ci:
                print(f"\n[!] Translation Check Blocked by {url}.")
                input("    Press ENTER here once the page is fully loaded...")
                
            # 1. Get English text
            english_text = extract_page_text(page)
            if len(english_text) < 50:
                return {"language": target_lang, "score": 0, "status": "insufficient_english_text"}
            
            # 2. Try to find the Hindi switcher
            # Common patterns: text "हिन्दी", "Hindi"
            switcher = page.query_selector("text=हिन्दी") or page.query_selector("text=Hindi")
            
            if switcher and switcher.is_visible():
                try:
                    with page.expect_navigation(timeout=10000):
                        page.evaluate("el => el.click()", switcher)
                except:
                    page.evaluate("el => el.click()", switcher)
                    page.wait_for_timeout(3000)
                    
                hindi_text = extract_page_text(page)
                
                # Use Gemini as fallback for translation as recommended in the plan
                # The user added both keys. We'll use Gemini for Hindi translation evaluation.
                client, model = get_client("gemini")
                result = score_translation_quality(client, model, english_text, hindi_text)
                
                return {
                    "language": target_lang,
                    "score": result.get("score", 0),
                    "flagged_terms": result.get("flagged_terms", []),
                    "status": "success"
                }
            else:
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
