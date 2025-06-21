import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from datetime import datetime
from src.extract.btc_extractor import extract_btc_from_html
from src.extract.email_extractor import extract_emails_from_html
from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
from src.risk.risk_score import calculate_risk_score
from src.report.pdf_report import generate_pdf_report
from src.report.json_report import generate_json_report
from src.utils.hash_util import calculate_sha256

# 1. Title
st.title("Dark Web Forensic Report Tool")

# 2. Upload
uploaded_files = st.file_uploader("Upload HTML files", type="html", accept_multiple_files=True)

# 3. Case Info
st.subheader("Case Information")
case_id = st.text_input("Case ID")
investigator = st.text_input("Investigator Name")
notes = st.text_area("Case Description / Notes")

# 4. Run Extraction
if st.button("Extract Data"):
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        html_content = uploaded_file.read().decode("utf-8")

        # Save file temporarily
        temp_path = os.path.join("data", file_name)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Extraction
        file_hash = calculate_sha256(temp_path)
        btc = extract_btc_from_html(temp_path)
        emails = extract_emails_from_html(temp_path)
        keywords = detect_risk_keywords_from_html(temp_path)
        score = calculate_risk_score(btc, emails, keywords)

        # Severity
        label = "Low" if score < 50 else "Medium" if score < 100 else "High"

        # Reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{case_id}_{file_name}_{timestamp}"
        generate_pdf_report(base_name, file_hash, btc, emails, keywords, score, label, case_id, investigator, notes)
        generate_json_report(base_name, file_hash, btc, emails, keywords, score, label, case_id, investigator, notes)

        st.success(f"{file_name} ✅ Report Generated!")

st.caption("Reports will be saved in the /reports directory.")
