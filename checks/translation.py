import time
import os
import json
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from checks.llm_client import get_client

# ==============================================================================
# GIGW OFFICIAL GOVERNMENT TERMINOLOGY GLOSSARY & RULE-BASED AUDITOR
# ==============================================================================
GIGW_GLOSSARY = [
    {"en": "Government of India", "hi_expected": ["भारत सरकार"], "category": "Official Entity"},
    {"en": "Ministry", "hi_expected": ["मंत्रालय"], "category": "Official Entity"},
    {"en": "Department", "hi_expected": ["विभाग"], "category": "Official Entity"},
    {"en": "Services", "hi_expected": ["सेवाएं", "सेवाएँ", "सेवा"], "category": "Core Navigation"},
    {"en": "Grievance", "hi_expected": ["शिकायत", "लोक शिकायत"], "category": "Public Services"},
    {"en": "Portal", "hi_expected": ["पोर्टल"], "category": "General"},
    {"en": "Contact Us", "hi_expected": ["संपर्क करें", "संपर्क"], "category": "Core Navigation"},
    {"en": "About Us", "hi_expected": ["हमारे बारे में", "परिचय"], "category": "Core Navigation"},
    {"en": "Home", "hi_expected": ["मुख्य पृष्ठ", "होम", "मुख्य"], "category": "Core Navigation"},
    {"en": "Citizen", "hi_expected": ["नागरिक"], "category": "Public Services"},
    {"en": "National", "hi_expected": ["राष्ट्रीय"], "category": "General"},
    {"en": "State", "hi_expected": ["राज्य"], "category": "General"},
    {"en": "Scheme", "hi_expected": ["योजना", "योजनाएं", "योजनाएँ"], "category": "Public Services"},
    {"en": "Download", "hi_expected": ["डाउनलोड"], "category": "Action"},
    {"en": "Login", "hi_expected": ["लॉगिन", "साइन इन", "प्रवेश"], "category": "Action"},
]

UNTRANSLATED_BOILERPLATE = [
    "Skip to Main Content", "Screen Reader Access", "Copyright", "All Rights Reserved",
    "Privacy Policy", "Terms of Use", "Disclaimer", "Accessibility Statement"
]

def rule_based_quality_check(english_text: str, hindi_text: str) -> dict:
    """
    Deterministically audits Hindi translation quality against official GIGW terminology,
    Devanagari fluency rules, and machine-translation artifacts.
    Returns score out of 40 and list of flagged terms.
    """
    flagged_terms = []
    
    # 1. Fluency & Script Check (0-15 pts)
    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', hindi_text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', hindi_text))
    dev_pct = (devanagari_chars / max(1, total_alpha)) * 100
    
    if dev_pct >= 60:
        fluency_score = 15
    elif dev_pct >= 30:
        fluency_score = 11
    elif dev_pct >= 10:
        fluency_score = 7
    else:
        fluency_score = 3
        
    # 2. GIGW Terminology & Glossary Check (0-15 pts)
    glossary_score = 15
    found_matches = 0
    checked_terms = 0
    
    for term in GIGW_GLOSSARY:
        en_pattern = re.compile(r'\b' + re.escape(term["en"]) + r'\b', re.IGNORECASE)
        if en_pattern.search(english_text):
            checked_terms += 1
            matched = any(exp in hindi_text for exp in term["hi_expected"])
            if matched:
                found_matches += 1
            else:
                # Check for literal machine translation fails (e.g. Home -> गृह)
                if term["en"].lower() == "home" and "गृह" in hindi_text:
                    flagged_terms.append("Literal MT Error: 'Home' translated as 'गृह' instead of 'मुख्य पृष्ठ'")
                else:
                    flagged_terms.append(f"Missing GIGW Term: '{term['en']}' (Expected: {term['hi_expected'][0]})")
                    
    if checked_terms > 0:
        match_ratio = found_matches / checked_terms
        glossary_score = int(match_ratio * 15)
        
    # 3. Machine Translation Artifacts & Untranslated Elements Check (0-10 pts)
    artifacts_score = 10
    untranslated_found = []
    
    for bp in UNTRANSLATED_BOILERPLATE:
        if bp in hindi_text and dev_pct > 20:
            untranslated_found.append(bp)
            
    if len(untranslated_found) > 0:
        artifacts_score -= min(6, len(untranslated_found) * 2)
        flagged_terms.append(f"Untranslated UI Elements: {', '.join(untranslated_found[:3])}")
        
    # Check for raw code or broken MT strings
    if "NaN" in hindi_text or "undefined" in hindi_text or "[[translation]]" in hindi_text:
        artifacts_score -= 4
        flagged_terms.append("MT Code Artifacts: Raw JS/template tokens present in translated view")
        
    artifacts_score = max(0, artifacts_score)
    total_quality = min(40, fluency_score + glossary_score + artifacts_score)
    
    return {
        "quality_score": total_quality,
        "fluency_score": fluency_score,
        "glossary_score": glossary_score,
        "artifacts_score": artifacts_score,
        "flagged_terms": flagged_terms[:5],
        "summary": f"Rule-based GIGW Audit: {total_quality}/40 (Devanagari: {dev_pct:.1f}%, Term Matches: {found_matches}/{max(1, checked_terms)})"
    }

# ==============================================================================
# DOM EXTRACTION & MULTI-REGION DEVANAGARI ANALYSIS
# ==============================================================================
def extract_dom_translation_data(page) -> dict:
    """Extracts visible text and measures Devanagari script density across structural DOM regions."""
    try:
        data = page.evaluate("""() => {
            const cleanText = (el) => {
                if (!el) return '';
                const clone = el.cloneNode(true);
                const scripts = clone.querySelectorAll('script, style, noscript, iframe, svg');
                scripts.forEach(s => s.remove());
                return clone.innerText.trim();
            };

            const navElements = document.querySelectorAll('nav, header, .navbar, .menu, #header, .top-bar, .accessibility-bar');
            let navText = '';
            navElements.forEach(el => { navText += ' ' + cleanText(el); });

            const headingElements = document.querySelectorAll('h1, h2, h3');
            let headingsText = '';
            headingElements.forEach(el => { headingsText += ' ' + cleanText(el); });

            const bodyElements = document.querySelectorAll('main, article, .content, #content, p');
            let bodyText = '';
            bodyElements.forEach(el => { bodyText += ' ' + cleanText(el); });

            const fullText = cleanText(document.body);

            return {
                nav_text: navText.trim(),
                headings_text: headingsText.trim(),
                body_text: bodyText.trim(),
                full_text: fullText
            };
        }""")
        
        def calc_ratio(text: str) -> float:
            dev_chars = len(re.findall(r'[\u0900-\u097F]', text))
            total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', text))
            return dev_chars / max(1, total_alpha)
            
        nav_ratio = calc_ratio(data["nav_text"])
        headings_ratio = calc_ratio(data["headings_text"])
        body_ratio = calc_ratio(data["body_text"])
        full_ratio = calc_ratio(data["full_text"])
        
        return {
            "full_text": data["full_text"],
            "full_ratio": full_ratio,
            "nav_ratio": nav_ratio,
            "headings_ratio": headings_ratio,
            "body_ratio": body_ratio,
            "regional_breakdown": {
                "nav_pct": round(nav_ratio * 100, 1),
                "headings_pct": round(headings_ratio * 100, 1),
                "body_pct": round(body_ratio * 100, 1)
            }
        }
    except Exception:
        fallback_text = ""
        try:
            fallback_text = page.evaluate("() => document.body.innerText.trim()")
        except Exception:
            pass
        dev_chars = len(re.findall(r'[\u0900-\u097F]', fallback_text))
        total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', fallback_text))
        r = dev_chars / max(1, total_alpha)
        return {
            "full_text": fallback_text,
            "full_ratio": r,
            "nav_ratio": r,
            "headings_ratio": r,
            "body_ratio": r,
            "regional_breakdown": {
                "nav_pct": round(r * 100, 1),
                "headings_pct": round(r * 100, 1),
                "body_pct": round(r * 100, 1)
            }
        }

# ==============================================================================
# LLM SEMANTIC PRESERVATION & QUALITY EVALUATOR
# ==============================================================================
def score_translation_quality(client, model, english_text: str, hindi_text: str) -> dict:
    """Evaluates Hindi text quality using LLM with deterministic GIGW fallback."""
    rule_res = rule_based_quality_check(english_text, hindi_text)
    
    if not client:
        return rule_res
        
    eng_sample = english_text[:1500]
    hin_sample = hindi_text[:1500]
    
    prompt = f"""Rate the quality of the following HINDI text from an Indian Government website on a scale of 0 to 40.
Evaluate strictly across 3 pillars:
1. Devanagari grammar & fluency (0-15 pts)
2. Accurate GIGW terminology for official Indian Government terms (0-15 pts)
3. Absence of broken machine-translation artifacts or untranslated blocks (0-10 pts)

ENGLISH CONTEXT: {eng_sample}
HINDI TEXT: {hin_sample}

Respond strictly as JSON:
{{
  "quality_score": <0-40>,
  "fluency_score": <0-15>,
  "glossary_score": <0-15>,
  "artifacts_score": <0-10>,
  "flagged_terms": ["issue 1", "issue 2"],
  "summary": "short 1 sentence evaluation summary"
}}
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
        # Merge flagged terms with rule-based findings for maximum rigor
        combined_flags = list(dict.fromkeys(result.get("flagged_terms", []) + rule_res.get("flagged_terms", [])))
        result["flagged_terms"] = combined_flags[:5]
        return result
    except Exception:
        # Seamless fallback to GIGW rule-based auditor
        return rule_res

# ==============================================================================
# MULTI-STRATEGY LANGUAGE SWITCHER DISCOVERY ENGINE
# ==============================================================================
def find_and_click_hindi_switcher(page) -> tuple[bool, str, str]:
    """
    Locates and executes Hindi language switcher across 5 web UI paradigms:
    1. Direct Link / Button / Image / ARIA
    2. GIGW Accessibility & Top Utility Bar
    3. Select / Dropdown Menu
    4. Google Translate / Bhashini AI Widgets
    5. URL Navigation Fallback
    
    Returns: (success, switcher_type, new_text)
    """
    # Paradigm 1 & 2: Direct Selectors & GIGW Utility Bars
    direct_locators = [
        ("text=हिंदी", "Direct Text Link ('हिंदी')"),
        ("text=हिन्दी", "Direct Text Link ('हिन्दी')"),
        ("a:has-text('Hindi')", "Navigation Link ('Hindi')"),
        ("button:has-text('Hindi')", "Button ('Hindi')"),
        ("a:has-text('हिंदी')", "Navigation Link ('हिंदी')"),
        ("button:has-text('हिंदी')", "Button ('हिंदी')"),
        ("a:has-text('हिन्दी')", "Navigation Link ('हिन्दी')"),
        ("button:has-text('हिन्दी')", "Button ('हिन्दी')"),
        ("a[href*='hi.']", "Subdomain Language Link (hi.*)"),
        ("a[href*='hindi']", "Language Route Link (hindi)"),
        ("[aria-label*='Hindi' i]", "ARIA Label Switcher"),
        ("[aria-label*='हिंदी']", "ARIA Label Switcher"),
        ("[title*='Hindi' i]", "Title Attribute Switcher"),
        ("[title*='हिंदी']", "Title Attribute Switcher"),
        ("img[alt*='Hindi' i]", "Image Button (Alt Hindi)"),
        ("img[alt*='हिंदी']", "Image Button (Alt हिंदी)"),
        ("[data-lang='hi']", "Data Attribute Switcher"),
        ("[data-lang='1']", "Data Attribute Switcher"),
        (".lang-hi", "Class-based Switcher"),
        ("#langHindi", "ID-based Switcher"),
        (".accessibility-bar a:has-text('Hindi')", "GIGW Accessibility Bar"),
        (".accessibility-bar a:has-text('हिंदी')", "GIGW Accessibility Bar"),
        (".top-bar a:has-text('Hindi')", "Top Bar Utility Menu"),
        (".top-bar a:has-text('हिंदी')", "Top Bar Utility Menu"),
        ("a[href*='lang=hi']", "URL Parameter Link (?lang=hi)"),
        ("a[href*='lang=1']", "URL Parameter Link (?lang=1)"),
        ("a[href*='lang_id=1']", "URL Parameter Link (?lang_id=1)"),
        ("a[href*='/hi']", "Relative Path Link (/hi)"),
    ]
    
    for loc, switcher_label in direct_locators:
        try:
            switcher = page.query_selector(loc)
            if switcher and switcher.is_visible():
                href = switcher.get_attribute("href")
                try:
                    with page.expect_navigation(timeout=8000):
                        page.evaluate("el => el.click()", switcher)
                except Exception:
                    if href and not href.startswith("javascript:"):
                        try:
                            page.goto(href if href.startswith("http") else page.url.rstrip('/') + '/' + href.lstrip('/'), timeout=10000, wait_until="commit")
                        except Exception:
                            page.evaluate("el => el.click()", switcher)
                            page.wait_for_timeout(2000)
                    else:
                        page.evaluate("el => el.click()", switcher)
                        page.wait_for_timeout(2000)
                
                dom_data = extract_dom_translation_data(page)
                return True, switcher_label, dom_data["full_text"]
        except Exception:
            continue
            
    # Paradigm 3: Select Dropdowns
    try:
        selects = page.query_selector_all("select")
        for sel in selects:
            options = sel.query_selector_all("option")
            for opt in options:
                txt = opt.inner_text().strip()
                val = (opt.get_attribute("value") or "").strip()
                if "हिंदी" in txt or "हिन्दी" in txt or "hindi" in txt.lower() or val.lower() in ["hi", "hin", "hindi", "1"]:
                    sel.select_option(value=val if val else txt)
                    page.wait_for_timeout(2000)
                    dom_data = extract_dom_translation_data(page)
                    return True, "Dropdown Selection Menu", dom_data["full_text"]
    except Exception:
        pass

    # Paradigm 4: Google Translate & Bhashini Widgets
    try:
        gt_combo = page.query_selector("select.goog-te-combo, #google_translate_element select")
        if gt_combo and gt_combo.is_visible():
            gt_combo.select_option(value="hi")
            page.wait_for_timeout(2500)
            dom_data = extract_dom_translation_data(page)
            return True, "Google Translate Widget", dom_data["full_text"]
    except Exception:
        pass

    return False, "None", ""

# ==============================================================================
# MAIN ENTRY POINT: CHECK PORTAL TRANSLATION
# ==============================================================================
def check_portal_translation(url: str, target_lang: str = "hi") -> dict:
    """
    Computes a continuous 0-100 Hindi Translation & Multilingual Access Score:
    - Multi-Region Devanagari Script Density (0-30 pts): Measures Devanagari presence in Nav, Headings, and Body.
    - Multi-Strategy Language Switcher Discovery (0-30 pts): Tests 5 UI paradigms for language switching.
    - GIGW Official Terminology & LLM Semantic Quality Audit (0-40 pts): Evaluates grammar, official glossary, and MT artifacts.
    """
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
                
            init_dom = extract_dom_translation_data(page)
            initial_text = init_dom["full_text"]
            
            if len(initial_text) < 30:
                return {
                    "language": target_lang,
                    "score": 0,
                    "devanagari_ratio_pct": 0.0,
                    "switcher_found": False,
                    "switcher_type": "None",
                    "status": "insufficient_text",
                    "flagged_terms": []
                }
            
            # 1. Measure Devanagari Script Ratio across DOM regions (0 to 30 pts)
            # Weighted ratio: Nav (30%), Headings (30%), Body (40%)
            nav_r = init_dom["nav_ratio"]
            head_r = init_dom["headings_ratio"]
            body_r = init_dom["body_ratio"]
            weighted_ratio = (nav_r * 0.3) + (head_r * 0.3) + (body_r * 0.4)
            devanagari_score = min(30, int(weighted_ratio * 80)) # e.g. 37.5% weighted = 30 pts
            
            # 2. Test Language Switcher Engine (0 to 30 pts)
            has_switcher = False
            switcher_works = False
            switcher_type = "None"
            hindi_text = initial_text
            post_dom = init_dom
            
            devanagari_char_count = len(re.findall(r'[\u0900-\u097F]', initial_text))
            
            if devanagari_char_count > 100 or init_dom["full_ratio"] > 0.35:
                # Portal is natively Hindi / Multilingual
                has_switcher = True
                switcher_works = True
                switcher_type = "Native Multilingual Portal"
                switcher_score = 30
                status = "native_multilingual_detected"
            else:
                clicked, sw_type, switched_text = find_and_click_hindi_switcher(page)
                if clicked:
                    has_switcher = True
                    switcher_type = sw_type
                    switcher_score = 15
                    
                    post_dom = extract_dom_translation_data(page)
                    new_dev_chars = len(re.findall(r'[\u0900-\u097F]', post_dom["full_text"]))
                    
                    if new_dev_chars > devanagari_char_count + 40 or post_dom["full_ratio"] > 0.25:
                        switcher_works = True
                        switcher_score = 30
                        hindi_text = post_dom["full_text"]
                        status = "switcher_success"
                    else:
                        status = "switcher_clicked_low_hindi"
                else:
                    # Paradigm 5: URL Navigation Fallbacks (/hi, ?lang=hi, hi.domain)
                    subdomain_fb = url.replace("://www.", "://hi.").replace("://", "://hi.") if "://hi." not in url else None
                    fallback_urls = [
                        url.rstrip('/') + '/hi',
                        url.rstrip('/') + '?lang=hi',
                        url.rstrip('/') + '?lang=1',
                        url.rstrip('/') + '?locale=hi'
                    ]
                    if subdomain_fb and subdomain_fb != url:
                        fallback_urls.insert(0, subdomain_fb)
                        
                    found_fb = False
                    for fb_url in fallback_urls:
                        try:
                            page.goto(fb_url, timeout=10000, wait_until="commit")
                            fb_dom = extract_dom_translation_data(page)
                            if fb_dom["full_ratio"] > 0.25 or len(re.findall(r'[\u0900-\u097F]', fb_dom["full_text"])) > 80:
                                has_switcher = True
                                switcher_works = True
                                switcher_type = f"URL Route ({fb_url})"
                                switcher_score = 25
                                hindi_text = fb_dom["full_text"]
                                post_dom = fb_dom
                                status = "url_fallback_success"
                                found_fb = True
                                break
                        except Exception:
                            continue
                            
                    if not found_fb:
                        switcher_score = 0
                        status = "no_language_switcher_found"
            
            # Recalculate Devanagari score based on active Hindi view
            active_ratio = post_dom["full_ratio"]
            devanagari_score = min(30, int(((post_dom["nav_ratio"] * 0.3) + (post_dom["headings_ratio"] * 0.3) + (post_dom["body_ratio"] * 0.4)) * 80))
            
            # 3. LLM & GIGW Glossary Translation Quality Check (0 to 40 pts)
            flagged_terms = []
            quality_breakdown = {"fluency_score": 0, "glossary_score": 0, "artifacts_score": 0}
            
            if devanagari_char_count > 30 or switcher_works or active_ratio > 0.15:
                try:
                    client, model = get_client("gemini")
                    llm_res = score_translation_quality(client, model, initial_text, hindi_text)
                except Exception:
                    llm_res = rule_based_quality_check(initial_text, hindi_text)
                    
                quality_score = min(40, max(0, llm_res.get("quality_score", 25)))
                flagged_terms = llm_res.get("flagged_terms", [])
                quality_breakdown = {
                    "fluency_score": llm_res.get("fluency_score", 12),
                    "glossary_score": llm_res.get("glossary_score", 12),
                    "artifacts_score": llm_res.get("artifacts_score", 8)
                }
            else:
                quality_score = 0
                
            # Total continuous 0-100 score
            total_score = min(100, devanagari_score + switcher_score + quality_score)
            
            return {
                "language": target_lang,
                "score": total_score,
                "devanagari_ratio_pct": round(active_ratio * 100, 1),
                "switcher_found": has_switcher,
                "switcher_type": switcher_type,
                "status": status,
                "regional_breakdown": post_dom["regional_breakdown"],
                "quality_breakdown": quality_breakdown,
                "flagged_terms": flagged_terms
            }
                
        except Exception as e:
            return {"language": target_lang, "score": 0, "status": f"error: {str(e)}", "flagged_terms": []}
        finally:
            browser.close()
