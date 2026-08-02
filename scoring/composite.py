def calculate_composite_score(uptime_data: dict, accessibility_data: dict, translation_data: dict) -> float:
    # If the site is completely down, composite score is 0
    if uptime_data.get("status") != "up":
        return 0.0
        
    uptime_score = 100
    broken_links = uptime_data.get("broken_links", 0)
    if broken_links > 0:
        uptime_score -= min(50, broken_links * 2) # -2 per broken link, max -50
    
    acc_score = accessibility_data.get("score", 0)
    if acc_score < 0:
        acc_score = 0
        
    trans_score = translation_data.get("score", 0)
    
    # If a portal doesn't have a language switcher or couldn't be evaluated
    # we penalize the translation score because multilingual access is a key goal.
    if translation_data.get("status") == "no_language_switcher_found":
        trans_score = 20 # Give 20 points as base so it's not 0, but it's a fail
    elif translation_data.get("status") != "success":
        trans_score = 0
        
    # Weighting Strategy:
    # Uptime/Liveness: 40% (Most critical, a broken site serves no one)
    # Accessibility: 30% (Inclusive access for all citizens)
    # Translation: 30% (Ensuring regional language accuracy)
    
    composite = (uptime_score * 0.4) + (acc_score * 0.3) + (trans_score * 0.3)
    
    return round(composite, 2)
