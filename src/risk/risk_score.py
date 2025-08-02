def calculate_risk_score(btc_addresses, emails, risky_keywords, pgp_content=None, financial_data=None, shipping_addresses=None):
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

    # Score financial data
    if financial_data:
        for financial_item in financial_data:
            data_type = financial_item.get('type', 'unknown')
            if data_type == 'credit_card':
                score += 30  # High risk for credit card numbers
            elif data_type == 'cvv':
                score += 25  # High risk for CVV codes
            elif data_type == 'expiry_date':
                score += 15  # Medium risk for expiry dates
            elif data_type in ['iban', 'swift_code']:
                score += 20  # Medium-high risk for bank codes
            elif data_type == 'bank_account':
                score += 25  # High risk for account numbers
            else:
                score += 10  # Default risk for other financial data

    # Bonus
    if len(risky_keywords) >= 3:
        score += 10
    if btc_addresses and emails:
        score += 15
    if pgp_content and len(pgp_content) >= 2:
        score += 20  # Bonus for multiple PGP items
    if financial_data and len(financial_data) >= 2:
        score += 25  # Bonus for multiple financial items
    
    # Score shipping addresses
    if shipping_addresses:
        for shipping_item in shipping_addresses:
            data_type = shipping_item.get('type', 'unknown')
            if data_type == 'postal_address':
                score += 30  # High risk for physical addresses
            elif data_type == 'drop_location':
                score += 40  # Very high risk for drop locations
            elif data_type == 'coordinates':
                score += 35  # High risk for GPS coordinates
            elif data_type == 'postal_code':
                score += 15  # Medium risk for postal codes
            elif data_type == 'city_state':
                score += 20  # Medium risk for city/state
            elif data_type == 'shipping_instructions':
                score += 25  # Medium-high risk for delivery instructions
            elif data_type == 'landmark_references':
                score += 20  # Medium risk for landmarks
            elif data_type == 'time_instructions':
                score += 15  # Medium risk for time-based instructions
            else:
                score += 10  # Default risk for other shipping data
    
    # Bonus for multiple shipping items
    if shipping_addresses and len(shipping_addresses) >= 2:
        score += 30  # Bonus for multiple shipping items

    return score
