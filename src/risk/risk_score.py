def calculate_risk_score(btc_addresses, emails, risky_keywords):
    score = 0

    # Score BTC
    if btc_addresses:
        score += 30 * len(btc_addresses)

    # Score emails
    for email in emails:
        if email.endswith(".onion"):
            score += 10
        else:
            score += 5

    # Score risky keywords
    score += 10 * len(risky_keywords)

    # Bonus
    if len(risky_keywords) >= 3:
        score += 10
    if btc_addresses and emails:
        score += 15

    return score
