import os
import random
from src.utils.db_insert import insert_into_db
from datetime import datetime
from src.extract.extract_payment_addresses_from_html import extract_payment_addresses_from_html
from src.extract.email_extractor import extract_emails_from_html
from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
from src.utils.hash_util import calculate_sha256
from src.risk.risk_score import calculate_risk_score
from src.report.pdf_report import generate_pdf_report
from src.report.json_report import generate_json_report
from src.llm.llm_classifier import classify_with_llm

# ===== Toggle Integrations =====
USE_LLM = False      # 🔁 Toggle LLM summarization ON/OFF
USE_AI_MODEL = True  # 🔁 Toggle spaCy local AI ON/OFF
TRANSLATE = True     # 🔁 Enable or disable translation step
USE_SQL = False  # 🔁 Set to False to disable MySQL insert
USE_RAG = False


# ===== Case metadata =====
case_id = int(datetime.now().strftime("%Y%m%d%H%M%S") + f"{random.randint(10,99)}")
print(f"🔍 Auto-generated Case ID: {case_id}")
investigator = input("👤 Investigator Name: ")
notes = input("📝 Notes / Description: ")

# ===== Process files =====
directory = 'data'

for filename in os.listdir(directory):
    if filename.endswith(".html"):
        filepath = os.path.join(directory, filename)

        # Run extractors
        payment_addresses = extract_payment_addresses_from_html(
            filepath, 
            use_llm=USE_LLM,
            use_rag=USE_RAG,
            use_ai=USE_AI_MODEL, 
            translate=TRANSLATE
        )
        emails_found = extract_emails_from_html(filepath, use_ai=USE_AI_MODEL, use_llm=USE_LLM, translate=TRANSLATE, use_rag=USE_RAG)
        keywords_found = detect_risk_keywords_from_html(filepath,use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI_MODEL,translate=TRANSLATE)
        file_hash = calculate_sha256(filepath)

        # LLM Summary (if enabled)
        llm_summary = "LLM disabled."
        if USE_LLM:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    html_text = f.read()
                    llm_summary = classify_with_llm(html_text)
            except Exception as e:
                print(f"❌ LLM Error: {e}")
                llm_summary = "⚠️ LLM failed to generate summary."

        # Print results
        print(f"\n📄 File: {filename}")
        print(f"🧾 SHA-256 Hash: {file_hash}")

        if payment_addresses:
            for addr in payment_addresses:
                print(f"💰 Payment Address Found: {addr}")
        else:
            print("❌ No payment addresses found.")

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

        print(f"🧠 LLM Summary: {llm_summary}")

        # 🔥 Risk Score
        score = calculate_risk_score(payment_addresses, emails_found, keywords_found)
        print(f"🔥 Risk Score: {score}")

        severity = "Low"
        if score > 70:
            severity = "High"
        elif score > 40:
            severity = "Medium"

        # 📄 Generate reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = os.path.splitext(filename)[0]
        report_name = f"{case_id}_{base_filename}_{timestamp}"

        generate_pdf_report(
            report_name,
            file_hash,
            payment_addresses,
            emails_found,
            keywords_found,
            score,
            severity,
            case_id,
            investigator,
            notes,
            llm_summary
        )

        generate_json_report(
            report_name,
            file_hash,
            payment_addresses,
            emails_found,
            keywords_found,
            score,
            severity,
            case_id,
            investigator,
            notes,
            llm_summary
        )

        if USE_SQL:
            insert_into_db(
                case_id,
                investigator,
                notes,
                emails_found,
                payment_addresses,
                keywords_found,
                score,
                severity,
                file_hash,
                llm_summary
            )
            print("✅ Data inserted into MySQL database successfully.")
        else:
            print("⚠️ SQL insertion is disabled. Skipping DB insert.")

