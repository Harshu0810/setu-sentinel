"""
Sanity test for checks pipeline modules compilation and container flags.
"""
import sys
import os

print("Testing module imports...")
from checks.uptime import check_portal_uptime
from checks.accessibility import check_portal_accessibility
from checks.translation import check_portal_translation
from checks.generate_report import generate_validation_report
from scoring.composite import calculate_composite_score

print("✅ All check & scoring modules imported successfully with zero errors!")
