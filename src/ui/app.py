import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime
from src.utils.db_insert import insert_into_db
from src.extract.extract_payment_addresses_from_html import extract_payment_addresses_from_html
from src.extract.email_extractor import extract_emails_from_html
from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
from src.utils.hash_util import calculate_sha256
from src.risk.risk_score import calculate_risk_score
from src.report.pdf_report import generate_pdf_report
from src.report.json_report import generate_json_report
from src.llm.llm_classifier import classify_with_llm  # ✅ LLM summary integration

# ========== SETTINGS ==========
USE_LLM = False  # ✅ Toggle LLM ON/OFF
USE_AI = True    # ✅ Toggle AI fallback ON/OFF
TRANSLATE = True # ✅ Translate non-English content
USE_SQL = True  # ✅ Toggle SQL insertion ON/OFF


# ========== UI ==========
st.title("🕵️‍♀️ Dark Web Forensic Report Tool")

uploaded_files = st.file_uploader("Upload HTML files", type="html", accept_multiple_files=True)

st.subheader("Case Information")
case_id = st.text_input("Case ID")
investigator = st.text_input("Investigator Name")
notes = st.text_area("Case Description / Notes")

# ========== Process Button ==========
if st.button("Extract Data"):
    if not uploaded_files:
        st.warning("Please upload at least one HTML file.")
    else:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            html_content = uploaded_file.read().decode("utf-8")

            # Save temp file
            temp_path = os.path.join("data", file_name)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Extraction
            file_hash = calculate_sha256(temp_path)
            payments = extract_payment_addresses_from_html(
                temp_path,
                use_llm=USE_LLM,
                use_ai=USE_AI,
                translate=TRANSLATE
            )
            emails = extract_emails_from_html(temp_path)
            keywords = detect_risk_keywords_from_html(temp_path,use_llm=USE_LLM,use_ai=USE_AI,translate=TRANSLATE)

            # LLM Summary
            llm_summary = "LLM disabled."
            if USE_LLM:
                try:
                    llm_summary = classify_with_llm(html_content)
                    if not payments and "bitcoin" in llm_summary.lower():
                        payments.append("⚠️ Suspected BTC (via LLM)")
                except Exception as e:
                    llm_summary = f"⚠️ LLM error: {e}"

            # Risk Score
            score = calculate_risk_score(payments, emails, keywords)
            label = "Low" if score < 50 else "Medium" if score < 100 else "High"

            # Timestamp + Reports
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{case_id}_{os.path.splitext(file_name)[0]}_{timestamp}"

            generate_pdf_report(base_name, file_hash, payments, emails, keywords, score, label, case_id, investigator, notes, llm_summary)
            generate_json_report(base_name, file_hash, payments, emails, keywords, score, label, case_id, investigator, notes, llm_summary)
            st.success(f"✅ {file_name} processed. PDF and JSON saved as: {base_name}")
            if USE_SQL:
                insert_into_db(
                    case_id,
                    investigator,
                    notes,
                    emails,
                    payments,
                    keywords,
                    score,
                    label,
                    file_hash,
                    llm_summary
                )
                st.info("✅ Data inserted into MySQL database.")
            else:
                st.warning("⚠️ SQL insertion disabled. Skipping DB insert.")

st.caption("📁 Reports are saved to the `reports/` directory.")
