"""
Regression & Unit Tests for GIGW Translation Quality Engine
"""
import pytest
from checks.translation import check_portal_translation, rule_based_quality_check

def test_india_gov_in_execution():
    """
    Unit Test: National Portal of India (india.gov.in) audit execution runs without error
    and correctly handles WAF 403 / stealth page state.
    """
    res = check_portal_translation("https://india.gov.in")
    assert res is not None
    assert isinstance(res.get("score"), (int, float))
    assert "status" in res

def test_rule_based_quality_check_floor():
    """
    Tests that text with < 5% Devanagari script (e.g. English text) scores 0 for quality.
    """
    eng_sample = "Welcome to the National Portal of India. Access citizen services online."
    en_only_sample = "Welcome to the National Portal of India. Access citizen services online."
    
    res = rule_based_quality_check(eng_sample, en_only_sample)
    assert res["quality_score"] == 0
    assert res["fluency_score"] == 0
    assert res["glossary_score"] == 0

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
