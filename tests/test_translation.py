"""
Regression & Unit Tests for GIGW Translation Quality Engine
"""
import pytest
from checks.translation import check_portal_translation, rule_based_quality_check

def test_india_gov_in_never_zeros():
    """
    Regression Test: National Portal of India (india.gov.in) must NEVER post a false-negative 0/100 score.
    WAF 403 or SPA rendering must be handled via requests/stealth fallback.
    """
    res = check_portal_translation("https://india.gov.in")
    assert res is not None
    assert isinstance(res.get("score"), (int, float))
    assert res.get("score") > 0, "Regression detected: india.gov.in posted a false-negative 0/100 score!"

def test_rule_based_quality_check_valid_hindi():
    """
    Tests GIGW glossary rule-based evaluation with valid GIGW Hindi text.
    """
    eng_sample = "Welcome to the Government of India Ministry of Electronics and Information Technology. Access citizen services and download forms."
    hi_sample = "भारत सरकार इलेक्ट्रॉनिक्स और सूचना प्रौद्योगिकी मंत्रालय में आपका स्वागत है। नागरिक सेवाएं एक्सेस करें और फॉर्म डाउनलोड करें।"
    
    res = rule_based_quality_check(eng_sample, hi_sample)
    assert res["quality_score"] > 20
    assert res["fluency_score"] >= 10
    assert res["glossary_score"] >= 10

def test_rule_based_quality_check_mt_error():
    """
    Tests detection of literal machine translation errors (e.g. Home -> गृह).
    """
    eng_sample = "Home page for government scheme portal"
    hi_sample = "सरकारी योजना पोर्टल के लिए गृह पृष्ठ"
    
    res = rule_based_quality_check(eng_sample, hi_sample)
    assert any("Literal MT Error" in flag for flag in res["flagged_terms"])
