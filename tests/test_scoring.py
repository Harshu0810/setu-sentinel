"""
Unit Tests for Composite Scoring Engine and Link Classification Contracts
"""
import pytest
from scoring.composite import calculate_composite_score

def test_composite_score_calculation():
    """
    Tests weighted composite score calculation contract (40% Uptime, 30% WCAG, 30% Translation).
    """
    uptime_data = {"status": "up", "broken_links": 0}
    acc_data = {"score": 80}
    trans_data = {"score": 70}
    
    score = calculate_composite_score(uptime_data, acc_data, trans_data)
    # Expected: (100 * 0.40) + (80 * 0.30) + (70 * 0.30) = 40 + 24 + 21 = 85.0
    assert score == 85.0

def test_composite_score_zero_uptime():
    """
    Tests zero composite score behavior when portal is completely down.
    """
    uptime_data = {"status": "down", "broken_links": 0}
    acc_data = {"score": 80}
    trans_data = {"score": 70}
    
    score = calculate_composite_score(uptime_data, acc_data, trans_data)
    assert score == 0.0
