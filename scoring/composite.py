def calculate_composite_score(uptime_data: dict, accessibility_data: dict, translation_data: dict) -> float:
    # If the site is temporarily down/unreachable, Uptime score is 0 (preserves Acc & Trans trend integrity)
    if uptime_data.get("status") != "up":
        uptime_score = 0
    else:
        uptime_score = 100
        broken_links = uptime_data.get("broken_links", 0)
        if broken_links > 0:
            uptime_score -= min(50, broken_links * 2) # -2 per broken link, max -50
    
    acc_score = accessibility_data.get("score", 0)
    if acc_score < 0:
        acc_score = 0
        
    trans_score = translation_data.get("score", 0)
    if trans_score < 0:
        trans_score = 0
        
    # Weighting Strategy:
    # Uptime/Liveness: 40% (Most critical, a broken site serves no one)
    # Accessibility: 30% (Inclusive access for all citizens)
    # Translation: 30% (Ensuring regional language accuracy)
    
    composite = (uptime_score * 0.4) + (acc_score * 0.3) + (trans_score * 0.3)
    
    return round(composite, 2)
