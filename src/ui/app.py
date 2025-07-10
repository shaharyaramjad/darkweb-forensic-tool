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
from src.llm.llm_classifier import classify_with_llm
import mysql.connector
from dotenv import load_dotenv
import pandas as pd

# Load .env for database connection
load_dotenv()

# Database connection config
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# ========== UI ==========
st.title("🕵️‍♀️ Dark Web Forensic Report Tool")

# Create tabs
tab1, tab2 = st.tabs(["🔍 Forensic Analysis", "🧑‍💻 SQL Query Interface"])

# ========== TAB 1: Forensic Analysis ==========
with tab1:
    uploaded_files = st.file_uploader("Upload HTML files", type="html", accept_multiple_files=True)

    st.subheader("Case Information")
    # Generate auto case ID
    case_id = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    st.text_input("Case ID (Auto-generated)", value=str(case_id), disabled=True)
    investigator = st.text_input("Investigator Name")
    notes = st.text_area("Case Description / Notes")

    # ========== Analysis Options ==========
    st.subheader("⚙️ Analysis Options")

    USE_LLM = st.checkbox("Use LLM Summary", value=True)
    USE_RAG = st.checkbox("Use RAG (knowledge-augmented fallback)", value=False)
    USE_AI = st.checkbox("Use AI Model (StarPII, Zero-shot, etc.)", value=True)
    TRANSLATE = st.checkbox("Translate non-English content", value=True)
    USE_SQL = st.checkbox("Insert results into SQL database", value=True)

    # ========== Process Button ==========
    if st.button("Extract Data"):
        if not uploaded_files:
            st.warning("Please upload at least one HTML file.")
        else:
            generated_reports = []  # Store generated report paths

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
                    use_rag=USE_RAG,
                    use_ai=USE_AI,
                    translate=TRANSLATE
                )
                emails = extract_emails_from_html(temp_path, use_ai=USE_AI, use_llm=USE_LLM, translate=TRANSLATE, use_rag=USE_RAG)
                keywords = detect_risk_keywords_from_html(temp_path, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI, translate=TRANSLATE)

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

                # Generate reports and store paths
                pdf_path = generate_pdf_report(base_name, file_hash, payments, emails, keywords, score, label, case_id, investigator, notes, llm_summary)
                json_path = generate_json_report(base_name, file_hash, payments, emails, keywords, score, label, case_id, investigator, notes, llm_summary)

                generated_reports.append({
                    'file_name': file_name,
                    'base_name': base_name,
                    'pdf_path': pdf_path,
                    'json_path': json_path
                })

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

            # Store generated reports in session state for download
            st.session_state.generated_reports = generated_reports
            st.session_state.reports_ready = True

    # ========== Download Section ==========
    if hasattr(st.session_state, 'reports_ready') and st.session_state.reports_ready:
        st.subheader("📥 Download Reports")
        st.info("Reports have been generated successfully! Click the buttons below to download them to your system.")

        for report in st.session_state.generated_reports:
            st.write(f"**{report['file_name']}**")

            col1, col2 = st.columns(2)

            with col1:
                # Download PDF
                if os.path.exists(report['pdf_path']):
                    with open(report['pdf_path'], "rb") as pdf_file:
                        st.download_button(
                            label=f"📄 Download PDF Report",
                            data=pdf_file.read(),
                            file_name=f"{report['base_name']}.pdf",
                            mime="application/pdf",
                            help="Download the PDF forensic report"
                        )
                else:
                    st.error("PDF report not found")

            with col2:
                # Download JSON
                if os.path.exists(report['json_path']):
                    with open(report['json_path'], "rb") as json_file:
                        st.download_button(
                            label=f"📊 Download JSON Report",
                            data=json_file.read(),
                            file_name=f"{report['base_name']}.json",
                            mime="application/json",
                            help="Download the JSON forensic report"
                        )
                else:
                    st.error("JSON report not found")

            st.divider()

    st.caption("📁 Reports are saved to the `reports/` directory.")

# ========== TAB 2: SQL Query Interface ==========
with tab2:
    st.subheader("🧑‍💻 SQL Query Interface")
    st.info("Run SQL queries to analyze the forensic data stored in the database.")

    if st.button("🔗 Test Database Connection"):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            cursor.execute("SELECT 1")
            st.success("✅ Database connection successful!")

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            if tables:
                st.write("**📋 Available tables:**")
                for table in tables:
                    st.write(f"- {table[0]}")
            else:
                st.warning("⚠️ No tables found in database. Make sure to run some forensic analysis first.")

            cursor.close()
            conn.close()

        except mysql.connector.Error as e:
            st.error(f"❌ Database connection failed: {e}")
            st.info("💡 Make sure your .env file has correct credentials:")
            st.code("""
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database_name
            """)
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

    if 'selected_query' in st.session_state:
        default_query = st.session_state.selected_query
    else:
        default_query = ""

    query = st.text_area("Write your SQL query here:", height=200, placeholder="SELECT * FROM case_metadata;", value=default_query, key="query_input")

    col1, col2 = st.columns([1, 4])
    with col1:
        run_query = st.button("🔍 Run Query")
    with col2:
        if st.button("📋 Show Sample Queries"):
            st.session_state.show_samples = True

    if hasattr(st.session_state, 'show_samples') and st.session_state.show_samples:
        st.subheader("📋 Sample Queries")
        sample_queries = {
            "View all cases": "SELECT * FROM case_metadata;",
            "View all emails with case info": """
SELECT 
    e.id,
    e.email,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM extracted_emails e
JOIN case_metadata c ON e.case_id = c.id;""",
            "View all payment addresses with case info": """
SELECT 
    p.id,
    p.address,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM extracted_payment_addresses p
JOIN case_metadata c ON p.case_id = c.id;""",
            "View all risky keywords with case info": """
SELECT 
    k.id,
    k.keyword,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM risk_keywords k
JOIN case_metadata c ON k.case_id = c.id;""",
            "High risk cases (score > 100)": "SELECT * FROM case_metadata WHERE score > 100;",
            "Recent cases (last 10)": "SELECT * FROM case_metadata ORDER BY created_at DESC LIMIT 10;",
            "Cases by severity level": "SELECT severity, COUNT(*) as count FROM case_metadata GROUP BY severity;",
            "Full details for specific case": "SELECT * FROM case_metadata WHERE case_id = 'TEST-CASE-001';",
            "Complete forensic analysis (all data)": """
SELECT
    c.id AS case_metadata_id,
    c.case_id,
    c.investigator_name,
    c.notes,
    c.score,
    c.severity,
    c.file_hash,
    c.llm_summary,
    c.created_at,
    e.id AS email_id,
    e.email,
    p.id AS payment_address_id,
    p.address,
    k.id AS keyword_id,
    k.keyword
FROM case_metadata c
LEFT JOIN extracted_emails e ON c.id = e.case_id
LEFT JOIN extracted_payment_addresses p ON c.id = p.case_id
LEFT JOIN risk_keywords k ON c.id = k.case_id
ORDER BY c.id;"""
        }

        col1, col2 = st.columns(2)

        with col1:
            st.write("**🔍 Basic Queries**")
            basic_queries = ["View all cases", "High risk cases (score > 100)", "Recent cases (last 10)", "Cases by severity level"]
            for title in basic_queries:
                if st.button(f"📝 {title}", key=f"sample_{title}"):
                    st.session_state.selected_query = sample_queries[title]
                    st.rerun()

        with col2:
            st.write("**📊 Detailed Analysis**")
            detailed_queries = ["View all emails with case info", "View all payment addresses with case info", "View all risky keywords with case info"]
            for title in detailed_queries:
                if st.button(f"📝 {title}", key=f"sample_{title}"):
                    st.session_state.selected_query = sample_queries[title]
                    st.rerun()

        st.write("**🔬 Advanced Queries**")
        advanced_queries = ["Full details for specific case", "Complete forensic analysis (all data)"]
        for title in advanced_queries:
            if st.button(f"📝 {title}", key=f"sample_{title}"):
                st.session_state.selected_query = sample_queries[title]
                st.rerun()

    query = st.session_state.query_input

    if run_query:
        if not query.strip():
            st.warning("⚠️ Please enter a query before running.")
        else:
            try:
                st.write("**🔍 Executing query:**")
                st.code(query)

                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()

                cursor.execute(query)

                if query.strip().lower().startswith("select"):
                    rows = cursor.fetchall()
                    columns = cursor.column_names

                    if rows:
                        df = pd.DataFrame(rows, columns=columns)

                        st.subheader("📊 Query Results")
                        st.dataframe(df, use_container_width=True)

                        st.success(f"✅ Query returned {len(df)} rows with {len(df.columns)} columns")

                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results as CSV",
                            data=csv_data,
                            file_name="query_results.csv",
                            mime="text/csv",
                            help="Download the query results as a CSV file"
                        )
                    else:
                        st.info("ℹ️ Query executed successfully but returned no results.")
                        st.write("**Columns:**", columns)
                else:
                    conn.commit()
                    st.success("✅ Query executed successfully (non-select).")

                cursor.close()
                conn.close()

            except mysql.connector.Error as e:
                st.error(f"❌ MySQL Error: {e}")
                st.info("💡 Common issues:")
                st.write("- Check if database exists and is accessible")
                st.write("- Verify table names match your schema")
                st.write("- Ensure database credentials are correct")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                st.write("**Error details:**", str(e))
