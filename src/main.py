import os
from src.extract.btc_extractor import extract_btc_from_html
from src.extract.email_extractor import extract_emails_from_html
from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
from src.utils.hash_util import calculate_sha256
from src.risk.risk_score import calculate_risk_score
from src.report.pdf_report import generate_pdf_report
from src.report.json_report import generate_json_report





directory = 'data'

for filename in os.listdir(directory):
    if filename.endswith(".html"):
        filepath = os.path.join(directory, filename)


        # Run extractors
        btc_found = extract_btc_from_html(filepath)
        emails_found = extract_emails_from_html(filepath)
        keywords_found = detect_risk_keywords_from_html(filepath)
        file_hash = calculate_sha256(filepath)

        # Print results
        print(f"\n📄 File: {filename}")
        print(f"🧾 SHA-256 Hash: {file_hash}")

        if btc_found:
            for btc in btc_found:
                print(f"✅ BTC Address Found: {btc}")
        else:
            print("❌ No BTC addresses found.")
        
        if emails_found:
            for email in emails_found:
                print(f"✅ Email Found: {email}")
        else:
            print("❌ No email addresses found.")

        if keywords_found:
            for keyword in keywords_found:
                print(f"⚠️ Risky Keyword Detected: '{keyword}'")
        else:
            print("✅ No risky keywords detected.")
    # 🔥 Risk Score
    score = calculate_risk_score(btc_found, emails_found, keywords_found)
    print(f"🔥 Risk Score: {score}")

    severity = "Low"
    if score > 70:
        severity = "High"
    elif score > 40:
        severity = "Medium"
        
    generate_pdf_report(
        filename,
        file_hash,
        btc_found,
        emails_found,
        keywords_found,
        score,
        severity
    )
    generate_json_report(
    filename,
    file_hash,
    btc_found,
    emails_found,
    keywords_found,
    score,
    severity
    )



    
