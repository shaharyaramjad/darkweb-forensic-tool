def calculate_risk_score(btc_addresses, emails, risky_keywords, pgp_content=None):
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

    # Score PGP content
    if pgp_content:
        for pgp_item in pgp_content:
            pgp_type = pgp_item.get('type', 'unknown')
            if pgp_type in ['public_key', 'private_key']:
                score += 25  # High risk for actual keys
            elif pgp_type in ['encrypted_message', 'signature']:
                score += 20  # Medium-high risk for encrypted content
            elif pgp_type in ['key_id', 'mention']:
                score += 10  # Lower risk for mentions
            else:
                score += 5   # Default risk for other PGP content

    # Bonus
    if len(risky_keywords) >= 3:
        score += 10
    if btc_addresses and emails:
        score += 15
    if pgp_content and len(pgp_content) >= 2:
        score += 20  # Bonus for multiple PGP items

    return score
