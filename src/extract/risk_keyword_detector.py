def detect_risk_keywords_from_html(filepath):
    risk_keywords = [
        "buy drugs", "credit card dump", "exploit", "zero-day",
        "fake passport", "hitman", "weapon", "child abuse", "counterfeit"
    ]
    
    found_keywords = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            for keyword in risk_keywords:
                if keyword in content:
                    found_keywords.append(keyword)
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
    
    return found_keywords
