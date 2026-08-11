import time
import os
import json
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from checks.llm_client import get_client_with_fallback

# ==============================================================================
# INDIC SCRIPT UNICODE BLOCK MAP — Maps ISO 639-1 codes to Unicode regex ranges
# ==============================================================================
INDIC_SCRIPTS = {
    "hi": r'[\u0900-\u097F]',   # Devanagari (Hindi, Marathi, Sanskrit)
    "mr": r'[\u0900-\u097F]',   # Devanagari (Marathi uses same script as Hindi)
    "gu": r'[\u0A80-\u0AFF]',   # Gujarati
    "ta": r'[\u0B80-\u0BFF]',   # Tamil
    "te": r'[\u0C00-\u0C7F]',   # Telugu
    "kn": r'[\u0C80-\u0CFF]',   # Kannada
    "ml": r'[\u0D00-\u0D7F]',   # Malayalam
    "bn": r'[\u0980-\u09FF]',   # Bengali
    "pa": r'[\u0A00-\u0A7F]',   # Gurmukhi (Punjabi)
    "or": r'[\u0B00-\u0B7F]',   # Odia
}

# Language display names for switcher discovery
LANG_LABELS = {
    "hi": ["हिंदी", "हिन्दी", "Hindi"],
    "mr": ["मराठी", "Marathi"],
    "gu": ["ગુજરાતી", "Gujarati"],
    "ta": ["தமிழ்", "Tamil"],
    "te": ["తెలుగు", "Telugu"],
    "kn": ["ಕನ್ನಡ", "Kannada"],
    "ml": ["മലയാളം", "Malayalam"],
    "bn": ["বাংলা", "Bengali", "Bangla"],
    "pa": ["ਪੰਜਾਬੀ", "Punjabi"],
    "or": ["ଓଡ଼ିଆ", "Odia"],
}

def get_script_regex(lang: str) -> str:
    """Returns the Unicode regex pattern for the given language's script."""
    return INDIC_SCRIPTS.get(lang, INDIC_SCRIPTS["hi"])

# ==============================================================================
# OFFICIAL GOVT OF INDIA PUNYCODE (.भारत / .xn--h2brj9c) IDN DOMAIN MAPPING
# ==============================================================================
INDIC_IDN_DOMAINS = {
    "india.gov.in": "https://xn--i1bj3fqcyde.xn--11b7cb3a6a.xn--h2brj9c",      # भारतसरकार.राष्ट्रीयपोर्टल.भारत
    "www.india.gov.in": "https://xn--i1bj3fqcyde.xn--11b7cb3a6a.xn--h2brj9c",  # भारतसरकार.राष्ट्रीयपोर्टल.भारत
}



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
    
    # Strict floor: if target script is under 5%, zero out quality score (cannot score English prose as Hindi)
    if dev_pct < 5.0:
        return {
            "quality_score": 0,
            "fluency_score": 0,
            "glossary_score": 0,
            "artifacts_score": 0,
            "flagged_terms": ["Insufficient Devanagari script content (<5% script ratio)"],
            "summary": "Rule-based GIGW Audit: 0/40 (Script content < 5%)"
        }
    
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
# DOM EXTRACTION & MULTI-REGION SCRIPT ANALYSIS
# ==============================================================================
# Combined regex matching ALL Indic script blocks for denominator calculation
ALL_INDIC_REGEX = r'[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F]'

def extract_dom_translation_data(page, script_pattern: str = r'[\u0900-\u097F]') -> dict:
    """Extracts visible text and measures target script density across structural DOM regions."""
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
            target_chars = len(re.findall(script_pattern, text))
            total_alpha = len(re.findall(r'[a-zA-Z]', text)) + len(re.findall(ALL_INDIC_REGEX, text))
            return target_chars / max(1, total_alpha)
            
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
        target_chars = len(re.findall(script_pattern, fallback_text))
        total_alpha = len(re.findall(r'[a-zA-Z]', fallback_text)) + len(re.findall(ALL_INDIC_REGEX, fallback_text))
        r = target_chars / max(1, total_alpha)
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
def find_and_click_language_switcher(page, target_lang: str = "hi", script_pattern: str = r'[\u0900-\u097F]') -> tuple[bool, str, str]:
    """
    Locates and executes language switcher for any target Indic language across 4 UI paradigms:
    1. Direct Link / Button / Image / ARIA (dynamically built from LANG_LABELS)
    2. GIGW Accessibility & Top Utility Bar
    3. Select / Dropdown Menu
    4. Google Translate / Bhashini AI Widgets
    
    Returns: (success, switcher_type, new_text)
    """
    labels = LANG_LABELS.get(target_lang, LANG_LABELS["hi"])
    native_labels = [l for l in labels if not l.isascii()]  # Script labels (e.g. हिंदी, தமிழ்)
    english_labels = [l for l in labels if l.isascii()]       # English labels (e.g. Hindi, Tamil)
    
    # Build locators dynamically from language labels
    direct_locators = []
    for native in native_labels:
        direct_locators.extend([
            (f"text={native}", f"Direct Text Link ('{native}')"),
            (f"a:has-text('{native}')", f"Navigation Link ('{native}')"),
            (f"button:has-text('{native}')", f"Button ('{native}')"),
            (f"[aria-label*='{native}']", f"ARIA Label Switcher ('{native}')"),
            (f"[title*='{native}']", f"Title Attribute Switcher ('{native}')"),
            (f"img[alt*='{native}']", f"Image Button (Alt '{native}')"),
            (f".accessibility-bar a:has-text('{native}')", "GIGW Accessibility Bar"),
            (f".top-bar a:has-text('{native}')", "Top Bar Utility Menu"),
        ])
    for eng in english_labels:
        direct_locators.extend([
            (f"a:has-text('{eng}')", f"Navigation Link ('{eng}')"),
            (f"button:has-text('{eng}')", f"Button ('{eng}')"),
            (f"[aria-label*='{eng}' i]", f"ARIA Label Switcher ('{eng}')"),
            (f"[title*='{eng}' i]", f"Title Attribute Switcher ('{eng}')"),
            (f"img[alt*='{eng}' i]", f"Image Button (Alt {eng})"),
            (f".accessibility-bar a:has-text('{eng}')", "GIGW Accessibility Bar"),
            (f".top-bar a:has-text('{eng}')", "Top Bar Utility Menu"),
        ])
    
    # Common structural selectors for the target language (strict word/path boundaries)
    direct_locators.extend([
        (f"a[href*='://{target_lang}.']", f"Subdomain Language Link ({target_lang}.*)"),
        (f"a[href*='//{target_lang}.']", f"Subdomain Language Link ({target_lang}.*)"),
        (f"a[href$='/{target_lang}']", f"Language Path Link (/{target_lang})"),
        (f"a[href*='/{target_lang}/']", f"Language Route Link (/{target_lang}/)"),
        (f"a[href*='lang={target_lang}']", f"URL Parameter Link (?lang={target_lang})"),
        (f"a[href*='locale={target_lang}']", f"URL Parameter Link (?locale={target_lang})"),
        (f"[data-lang='{target_lang}']", "Data Attribute Switcher"),
        (f".lang-{target_lang}", "Class-based Switcher"),
    ])
    # Hindi-specific legacy selectors
    if target_lang == "hi":
        direct_locators.extend([
            ("[data-lang='1']", "Data Attribute Switcher"),
            ("#langHindi", "ID-based Switcher"),
            ("a[href*='lang=1']", "URL Parameter Link (?lang=1)"),
            ("a[href*='lang_id=1']", "URL Parameter Link (?lang_id=1)"),
        ])
    
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
                
                dom_data = extract_dom_translation_data(page, script_pattern)
                return True, switcher_label, dom_data["full_text"]
        except Exception:
            continue
            
    # Paradigm 3: Select Dropdowns
    try:
        all_match_texts = native_labels + [e.lower() for e in english_labels]
        match_values = [target_lang, target_lang[:3]]
        if target_lang == "hi":
            match_values.extend(["1", "hin", "hindi"])
        
        selects = page.query_selector_all("select")
        for sel in selects:
            options = sel.query_selector_all("option")
            for opt in options:
                txt = opt.inner_text().strip()
                val = (opt.get_attribute("value") or "").strip()
                if any(m in txt for m in native_labels) or txt.lower() in all_match_texts or val.lower() in match_values:
                    sel.select_option(value=val if val else txt)
                    page.wait_for_timeout(2000)
                    dom_data = extract_dom_translation_data(page, script_pattern)
                    return True, "Dropdown Selection Menu", dom_data["full_text"]
    except Exception:
        pass

    # Paradigm 4: Google Translate & Bhashini Widgets
    try:
        gt_combo = page.query_selector("select.goog-te-combo, #google_translate_element select")
        if gt_combo and gt_combo.is_visible():
            gt_combo.select_option(value=target_lang)
            page.wait_for_timeout(2500)
            dom_data = extract_dom_translation_data(page, script_pattern)
            return True, "Google Translate Widget", dom_data["full_text"]
    except Exception:
        pass

    return False, "None", ""

# ==============================================================================
# MAIN ENTRY POINT: CHECK PORTAL TRANSLATION
# ==============================================================================
def check_portal_translation_with_page(page, url: str, target_lang: str = "hi") -> dict:
    """Core translation check using an externally-managed page (for browser consolidation)."""
    script_pattern = get_script_regex(target_lang)
    
    try:
        if not page.url or page.url == "about:blank" or url not in page.url:
            try:
                response = page.goto(url, timeout=35000, wait_until="commit")
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass
            except Exception:
                response = None
        else:
            response = None
            
        title_text = (page.title() or "").lower()
        init_dom = extract_dom_translation_data(page, script_pattern)
        initial_text = init_dom["full_text"]
        
        # WAF 403 / Access Denied fallback via requests
        if (response is not None and response.status in [403, 401]) or "access denied" in title_text or len(initial_text) < 50:
            try:
                import requests
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                }
                r = requests.get(url, headers=headers, verify=False, timeout=15)
                if r.status_code == 200 and len(r.text) > 200:
                    page.set_content(r.text, wait_until="domcontentloaded")
                    init_dom = extract_dom_translation_data(page, script_pattern)
                    initial_text = init_dom["full_text"]
            except Exception:
                pass
        
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
        
        # 1. Measure Target Script Ratio across DOM regions (0 to 30 pts)
        nav_r = init_dom["nav_ratio"]
        head_r = init_dom["headings_ratio"]
        body_r = init_dom["body_ratio"]
        weighted_ratio = (nav_r * 0.3) + (head_r * 0.3) + (body_r * 0.4)
        script_score = min(30, int(weighted_ratio * 80))
        
        # 2. Test Language Switcher Engine (0 to 30 pts)
        has_switcher = False
        switcher_works = False
        switcher_type = "None"
        translated_text = initial_text
        post_dom = init_dom
        
        target_char_count = len(re.findall(script_pattern, initial_text))
        
        if target_char_count > 100 or init_dom["full_ratio"] > 0.35:
            # Portal natively displays target script
            has_switcher = True
            switcher_works = True
            switcher_type = "Native Multilingual Portal"
            switcher_score = 30
            status = "native_multilingual_detected"
        else:
            clicked, sw_type, switched_text = find_and_click_language_switcher(page, target_lang, script_pattern)
            if clicked:
                post_dom = extract_dom_translation_data(page, script_pattern)
                new_target_chars = len(re.findall(script_pattern, post_dom["full_text"]))
                
                if (new_target_chars > target_char_count + 40 or post_dom["full_ratio"] > 0.10) and post_dom["full_ratio"] >= 0.05:
                    has_switcher = True
                    switcher_works = True
                    switcher_type = sw_type
                    switcher_score = 30
                    translated_text = post_dom["full_text"]
                    status = "switcher_success"
                else:
                    # Clicked link did NOT produce target script content (false positive click on unrelated English link)
                    has_switcher = False
                    switcher_works = False
                    switcher_type = "None"
                    switcher_score = 0
                    status = "no_language_switcher_found"
            
            if not has_switcher:
                # Paradigm 5: URL Navigation & Punycode (.भारत) IDN Fallbacks
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                idn_url = INDIC_IDN_DOMAINS.get(domain)
                
                subdomain_fb = url.replace("://www.", f"://{target_lang}.").replace("://", f"://{target_lang}.") if f"://{target_lang}." not in url else None
                fallback_urls = [
                    url.rstrip('/') + f'/{target_lang}',
                    url.rstrip('/') + f'?lang={target_lang}',
                    url.rstrip('/') + '?lang=1',
                    url.rstrip('/') + f'?locale={target_lang}'
                ]
                if subdomain_fb and subdomain_fb != url:
                    fallback_urls.insert(0, subdomain_fb)
                if idn_url:
                    fallback_urls.insert(0, idn_url)
                    
                found_fb = False
                for fb_url in fallback_urls:
                    try:
                        page.goto(fb_url, timeout=15000, wait_until="commit")
                        # Wait for JS hydration — critical for Next.js/React routes
                        try:
                            page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            try:
                                page.wait_for_load_state("domcontentloaded", timeout=5000)
                            except Exception:
                                pass
                        fb_dom = extract_dom_translation_data(page, script_pattern)
                        fb_target_chars = len(re.findall(script_pattern, fb_dom["full_text"]))
                        if fb_dom["full_ratio"] >= 0.05 and (fb_dom["full_ratio"] > 0.20 or fb_target_chars > 50):
                            has_switcher = True
                            switcher_works = True
                            switcher_type = f"URL Route ({fb_url})"
                            switcher_score = 25
                            translated_text = fb_dom["full_text"]
                            post_dom = fb_dom
                            status = "url_fallback_success"
                            found_fb = True
                            break
                    except Exception:
                        continue
                        
                if not found_fb:
                    switcher_score = 0
                    status = "no_language_switcher_found"
        
        # Recalculate script score based on active translated view
        active_ratio = post_dom["full_ratio"]
        script_score = min(30, int(((post_dom["nav_ratio"] * 0.3) + (post_dom["headings_ratio"] * 0.3) + (post_dom["body_ratio"] * 0.4)) * 80))
        
        # 3. LLM & GIGW Glossary Translation Quality Check (0 to 40 pts)
        flagged_terms = []
        quality_breakdown = {"fluency_score": 0, "glossary_score": 0, "artifacts_score": 0}
        
        if len(initial_text) >= 100:
            try:
                client, model = get_client_with_fallback()
                llm_res = score_translation_quality(client, model, initial_text, translated_text)
            except Exception:
                llm_res = rule_based_quality_check(initial_text, translated_text)
                
            quality_score = min(40, max(0, llm_res.get("quality_score", 15)))
            flagged_terms = llm_res.get("flagged_terms", [])
            quality_breakdown = {
                "fluency_score": llm_res.get("fluency_score", 5),
                "glossary_score": llm_res.get("glossary_score", 10),
                "artifacts_score": llm_res.get("artifacts_score", 5)
            }
        else:
            quality_score = 0
            
        # Total continuous 0-100 score
        total_score = min(100, script_score + switcher_score + quality_score)
        
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

def check_portal_translation(url: str, target_lang: str = "hi") -> dict:
    """Standalone translation check — launches its own browser context."""
    is_headless = os.environ.get("HEADED", "").lower() != "true"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            return check_portal_translation_with_page(page, url, target_lang=target_lang)
        finally:
            browser.close()

