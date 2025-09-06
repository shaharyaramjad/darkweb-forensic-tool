import streamlit as st
import sys
import os

# Fix tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime
from src.utils.db_insert import insert_into_db
from src.extract.extract_payment_addresses_from_html import extract_payment_addresses_from_html
from src.extract.email_extractor import extract_emails_from_html
from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
from src.extract.pgp_extractor import extract_pgp_from_html
from src.extract.financial_data_extractor import extract_financial_data_from_html
from src.extract.shipping_address_extractor import extract_shipping_addresses_from_html
from src.extract.username_extractor import extract_usernames_from_html
from src.extract.document_advertisement_detector import extract_document_advertisements_from_html
from src.utils.virus_detection_api import process_document_advertisements_for_virus_detection
from src.utils.hash_util import calculate_sha256
from src.risk.risk_score import calculate_risk_score
from src.report.pdf_report import generate_pdf_report
from src.report.json_report import generate_json_report
from src.llm.llm_classifier import classify_with_llm
from src.utils.security_scanner import secure_file_processing
import mysql.connector
from dotenv import load_dotenv
import pandas as pd
import json
import glob

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
tab1, tab2, tab3 = st.tabs(["🔍 Forensic Analysis", "🧑‍💻 SQL Query Interface", "🛡️ Tampering Detection"])

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
    
    # Add information about API requirements
    with st.expander("🔑 How to Enable AI/LLM Features"):
        st.markdown("""
        **To enable AI and LLM features, you need to set up API keys:**
        
        **Option 1: Create a .env file in your project root:**
        ```
        # For LLM features (OpenAI or Together.ai)
        OPENAI_API_KEY=your_openai_key_here
        # OR
        TOGETHER_API_KEY=your_together_key_here
        
        # For AI models (Hugging Face)
        HUGGINGFACE_API_KEY=your_huggingface_key_here
        ```
        
        **Option 2: Set environment variables:**
        ```bash
        export OPENAI_API_KEY="your_key_here"
        export HUGGINGFACE_API_KEY="your_key_here"
        ```
        
        **Get API Keys:**
        - **OpenAI**: https://platform.openai.com/api-keys
        - **Together.ai**: https://api.together.xyz/settings/api-keys  
        - **Hugging Face**: https://huggingface.co/settings/tokens
        
        **Without API keys, the tool will use regex-based extraction (which works great!).**
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        USE_LLM = st.checkbox("🤖 Use LLM Summary", value=False, help="Requires OPENAI_API_KEY or TOGETHER_API_KEY")
        USE_RAG = st.checkbox("🧠 Use RAG (knowledge-augmented fallback)", value=False, help="Requires OPENAI_API_KEY or TOGETHER_API_KEY")
        USE_AI = st.checkbox("🔍 Use AI Model (StarPII, Zero-shot, etc.)", value=False, help="Requires HUGGINGFACE_API_KEY")
    
    with col2:
        TRANSLATE = st.checkbox("🌐 Translate non-English content", value=True, help="Uses Google Translate API")
        USE_SQL = st.checkbox("💾 Insert results into SQL database", value=True, help="Saves results to MySQL database")
    ENABLE_VIRUS_LIVE_CHECKS = st.checkbox(
        "🛡️ Enable Live Virus Checks (VirusTotal/URLVoid)",
        value=False,
        help="When enabled and API keys are configured in .env, suspicious URLs are checked live. When disabled, the tool still prepares an API-ready payload and a manual investigation report."
    )
    ENABLE_SECURITY_SCAN = st.checkbox("🔒 Enable Security Scanning", value=True, help="Scan for malicious content before processing")
    
    # Status display
    st.subheader("📊 Current Configuration")
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.write("**🤖 AI Features:**")
        if USE_AI:
            st.success("✅ AI Models Enabled")
        else:
            st.info("ℹ️ AI Models Disabled (Regex only)")
            
    with status_col2:
        st.write("**🧠 LLM Features:**")
        if USE_LLM:
            st.success("✅ LLM Summary Enabled")
        else:
            st.info("ℹ️ LLM Summary Disabled")
            
    with status_col3:
        st.write("**🔧 Other Features:**")
        if TRANSLATE:
            st.success("✅ Translation Enabled")
        if USE_SQL:
            st.success("✅ Database Storage Enabled")

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

                # 🔒 SECURITY SCAN
                if ENABLE_SECURITY_SCAN:
                    st.info(f"🛡️ Scanning {file_name} for malicious content...")
                    success, safe_filepath, security_report, scan_result = secure_file_processing(temp_path)
                    
                    if not success:
                        st.error(f"❌ Security scan failed for {file_name}. Skipping file.")
                        continue
                    
                    # Display security report
                    with st.expander(f"🔒 Security Report for {file_name}"):
                        st.text(security_report)
                    
                    if not scan_result['safe']:
                        st.warning(f"⚠️ Threats detected in {file_name}! Using sanitized version.")
                        temp_path = safe_filepath
                    else:
                        st.success(f"✅ {file_name} passed security scan.")
                else:
                    st.warning("⚠️ Security scanning disabled!")

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
                pgp_content = extract_pgp_from_html(temp_path, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI, translate=TRANSLATE)
                financial_data = extract_financial_data_from_html(temp_path, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI, translate=TRANSLATE)
                shipping_addresses = extract_shipping_addresses_from_html(temp_path, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI, translate=TRANSLATE)
                usernames = extract_usernames_from_html(temp_path, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI, translate=TRANSLATE)
                
                # Document Advertisement Detection
                document_ads_result = extract_document_advertisements_from_html(
                    temp_path,
                    use_llm=USE_LLM,
                    use_rag=USE_RAG,
                    use_ai=USE_AI,
                    translate=TRANSLATE
                )

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
                score = calculate_risk_score(payments, emails, keywords, pgp_content, financial_data, shipping_addresses, usernames)
                label = "Low" if score < 50 else "Medium" if score < 100 else "High"
                
                # Process document advertisements for virus detection
                virus_detection_result = None
                if document_ads_result['total_found'] > 0:
                    try:
                        virus_detection_result = process_document_advertisements_for_virus_detection(
                            document_ads_result,
                            enable_live_checks=ENABLE_VIRUS_LIVE_CHECKS,
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Virus detection processing failed: {e}")

                # Timestamp + Reports
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"{case_id}_{os.path.splitext(file_name)[0]}_{timestamp}"

                # Generate reports and store paths
                pdf_path = generate_pdf_report(base_name, file_hash, payments, emails, keywords, pgp_content, financial_data, shipping_addresses, usernames, score, label, case_id, investigator, notes, llm_summary, document_ads_result=document_ads_result, virus_detection_result=virus_detection_result)
                json_path = generate_json_report(base_name, file_hash, payments, emails, keywords, pgp_content, financial_data, shipping_addresses, usernames, score, label, case_id, investigator, notes, llm_summary, document_ads_result=document_ads_result, virus_detection_result=virus_detection_result)

                generated_reports.append({
                    'file_name': file_name,
                    'base_name': base_name,
                    'pdf_path': pdf_path,
                    'json_path': json_path
                })

                # Display results
                with st.expander(f"📊 Analysis Results for {file_name}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**💰 Payment Addresses:**")
                        if payments:
                            for payment in payments:
                                st.write(f"- {payment}")
                        else:
                            st.write("- None found")
                        
                        st.write("**📧 Emails:**")
                        if emails:
                            for email in emails:
                                st.write(f"- {email}")
                        else:
                            st.write("- None found")
                    
                    with col2:
                        st.write("**⚠️ Risky Keywords:**")
                        if keywords:
                            for keyword in keywords:
                                st.write(f"- {keyword}")
                        else:
                            st.write("- None found")
                        
                        st.write("**🔐 PGP Content:**")
                        if pgp_content:
                            for pgp_item in pgp_content:
                                pgp_type = pgp_item.get('type', 'unknown')
                                content = pgp_item.get('content', '')[:50] + "..." if len(pgp_item.get('content', '')) > 50 else pgp_item.get('content', '')
                                st.write(f"- {pgp_type.upper()}: {content}")
                        else:
                            st.write("- None found")
                        
                        st.write("**💳 Financial Data:**")
                        if financial_data:
                            for financial_item in financial_data:
                                data_type = financial_item.get('type', 'unknown')
                                content = financial_item.get('content', '')[:50] + "..." if len(financial_item.get('content', '')) > 50 else financial_item.get('content', '')
                                st.write(f"- {data_type.upper()}: {content}")
                        else:
                            st.write("- None found")
                        
                        st.write("**📦 Shipping Addresses:**")
                        if shipping_addresses:
                            for shipping_item in shipping_addresses:
                                data_type = shipping_item.get('type', 'unknown')
                                content = shipping_item.get('content', '')[:50] + "..." if len(shipping_item.get('content', '')) > 50 else shipping_item.get('content', '')
                                st.write(f"- {data_type.upper()}: {content}")
                        else:
                            st.write("- None found")
                        
                        st.write("**👤 Usernames/Aliases:**")
                        if usernames:
                            for username_item in usernames:
                                data_type = username_item.get('type', 'unknown')
                                content = username_item.get('content', '')[:50] + "..." if len(username_item.get('content', '')) > 50 else username_item.get('content', '')
                                st.write(f"- {data_type.upper()}: {content}")
                        else:
                            st.write("- None found")
                    
                    # Document Advertisement Detection Results
                    st.write("**📄 Document Advertisements:**")
                    if document_ads_result['total_found'] > 0:
                        st.warning(f"⚠️ Found {document_ads_result['total_found']} suspicious items!")
                        
                        # Display document advertisements
                        if document_ads_result['document_advertisements']:
                            st.write("**Document Ads:**")
                            for ad in document_ads_result['document_advertisements']:
                                risk_color = "🔴" if ad['suspicious_level'] == 'high' else "🟡"
                                st.write(f"{risk_color} {ad['type']}: {ad['content']}")
                        
                        # Display suspicious URLs
                        if document_ads_result['suspicious_urls']:
                            st.write("**Suspicious URLs:**")
                            for url_data in document_ads_result['suspicious_urls']:
                                risk_color = "🔴" if url_data['risk_level'] == 'high' else "🟡"
                                st.write(f"{risk_color} {url_data['url']} ({url_data['suspicious_reason']})")
                        
                        # Display virus detection results
                        if virus_detection_result and virus_detection_result['success']:
                            st.write("**🛡️ Virus Detection Results:**")
                            api_results = virus_detection_result['api_results']
                            st.write(f"• URLs checked: {api_results['total_checked']}")
                            st.write(f"• Malicious URLs: {api_results['malicious_found']}")
                            st.write(f"• High risk URLs: {len(api_results['high_risk_urls'])}")
                            
                            # Display recommendations
                            if virus_detection_result['report']['recommendations']:
                                st.write("**💡 Recommendations:**")
                                for rec in virus_detection_result['report']['recommendations']:
                                    st.write(f"• {rec}")
                    else:
                        st.write("- None found")
                    
                    st.write(f"**🔥 Risk Score:** {score} ({label})")

                st.success(f"✅ {file_name} processed. PDF and JSON saved as: {base_name}")
                if USE_SQL:
                    # Prepare document advertisement data for database
                    document_ads_data = {
                        'document_advertisements': document_ads_result['document_advertisements'],
                        'suspicious_urls': document_ads_result['suspicious_urls'],
                        'actual_links': document_ads_result.get('actual_links', []),
                        'total_found': document_ads_result['total_found']
                    }
                    
                    insert_into_db(
                        case_id,
                        investigator,
                        notes,
                        emails,
                        payments,
                        keywords,
                        pgp_content,
                        financial_data,
                        shipping_addresses,
                        usernames,
                        score,
                        label,
                        file_hash,
                        llm_summary,
                        document_ads_data  # Add document advertisement data
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
    
    # Add helpful info about actual links
    st.success("💡 **Tip**: Most links are stored in the `actual_links` table, not `suspicious_urls`. Try 'View all actual links' or 'Count links by type' to see the extracted links!")

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

    query = st.text_area("Write your SQL query here:", height=200, placeholder="SELECT * FROM actual_links LIMIT 10;", value=default_query, key="query_input")

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
            "View all actual links": "SELECT * FROM actual_links;",
            "View recent actual links": """
SELECT 
    al.url,
    al.link_type,
    al.suspicious_level,
    c.case_id,
    c.created_at
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
ORDER BY c.created_at DESC
LIMIT 20;""",
            "Count links by type": """
SELECT 
    al.link_type,
    COUNT(*) as count
FROM actual_links al
GROUP BY al.link_type
ORDER BY count DESC;""",
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
            "View all PGP content with case info": """
SELECT 
    p.id,
    p.pgp_type,
    p.pgp_content,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM pgp_content p
JOIN case_metadata c ON p.case_id = c.id;""",
            "View all financial data with case info": """
SELECT 
    f.id,
    f.data_type,
    f.content,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM financial_data f
JOIN case_metadata c ON f.case_id = c.id;""",
            "View all shipping addresses with case info": """
SELECT 
    s.id,
    s.address_type,
    s.content,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM shipping_addresses s
JOIN case_metadata c ON s.case_id = c.id;""",
            "View all usernames with case info": """
SELECT 
    u.id,
    u.username_type,
    u.content as username,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM usernames u
JOIN case_metadata c ON u.case_id = c.id;""",
            "View all actual links with case info": """
SELECT 
    al.id,
    al.link_type,
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id;""",
            "View all document advertisements with case info": """
SELECT 
    da.id,
    da.ad_type,
    da.content,
    da.suspicious_level,
    da.method,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM document_advertisements da
JOIN case_metadata c ON da.case_id = c.id;""",
            "View all suspicious URLs with case info": """
SELECT 
    su.id,
    su.url,
    su.domain,
    su.suspicious_reason,
    su.risk_level,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM suspicious_urls su
JOIN case_metadata c ON su.case_id = c.id;""",
            "View drop locations only": """
SELECT 
    s.id,
    s.content,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM shipping_addresses s
JOIN case_metadata c ON s.case_id = c.id
WHERE s.address_type = 'drop_location';""",
            "View coordinates only": """
SELECT 
    s.id,
    s.content,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM shipping_addresses s
JOIN case_metadata c ON s.case_id = c.id
WHERE s.address_type = 'coordinates';""",
            "View postal addresses only": """
SELECT 
    s.id,
    s.content,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM shipping_addresses s
JOIN case_metadata c ON s.case_id = c.id
WHERE s.address_type = 'postal_address';""",
            "View dark web usernames only": """
SELECT 
    u.id,
    u.content as username,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM usernames u
JOIN case_metadata c ON u.case_id = c.id
WHERE u.username_type = 'dark_web_style';""",
            "View forum usernames only": """
SELECT 
    u.id,
    u.content as username,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM usernames u
JOIN case_metadata c ON u.case_id = c.id
WHERE u.username_type = 'forum_username';""",
            "View professional aliases only": """
SELECT 
    u.id,
    u.content as username,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM usernames u
JOIN case_metadata c ON u.case_id = c.id
WHERE u.username_type = 'professional_style';""",
            "View hyperlink links only": """
SELECT 
    al.id,
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.link_type = 'hyperlink';""",
            "View JavaScript links only": """
SELECT 
    al.id,
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.link_type = 'javascript';""",
            "View event handler links only": """
SELECT 
    al.id,
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.link_type = 'event_handler';""",
            "View high suspicious level links": """
SELECT 
    al.id,
    al.link_type,
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.suspicious_level = 'high';""",
            "Count links by type": """
SELECT 
    al.link_type,
    COUNT(*) as count,
    c.case_id,
    c.investigator_name
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
GROUP BY al.link_type, c.case_id, c.investigator_name
ORDER BY count DESC;""",
            "Find high suspicious level links": """
SELECT 
    al.url,
    al.link_type,
    al.suspicious_level,
    c.case_id,
    c.investigator_name
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.suspicious_level = 'high'
ORDER BY c.created_at DESC;""",
            "Find JavaScript links": """
SELECT 
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    c.case_id,
    c.investigator_name
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.link_type = 'javascript'
ORDER BY c.created_at DESC;""",
            "Find event handler links": """
SELECT 
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    c.case_id,
    c.investigator_name
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.link_type = 'event_handler'
ORDER BY c.created_at DESC;""",
            "Find hyperlink links": """
SELECT 
    al.url,
    al.link_text,
    al.suspicious_level,
    c.case_id,
    c.investigator_name
FROM actual_links al
JOIN case_metadata c ON al.case_id = c.id
WHERE al.link_type = 'hyperlink'
ORDER BY c.created_at DESC;""",
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
    k.keyword,
    pg.id AS pgp_id,
    pg.pgp_type,
    pg.pgp_content,
    f.id AS financial_id,
    f.data_type,
    f.content,
    s.id AS shipping_id,
    s.address_type,
    s.content,
    u.id AS username_id,
    u.username_type,
    u.content as username,
    al.id AS actual_link_id,
    al.link_type,
    al.url,
    al.link_text,
    al.extraction_method,
    al.suspicious_level,
    da.id AS document_ad_id,
    da.ad_type,
    da.content as ad_content,
    da.suspicious_level as ad_suspicious_level,
    da.method,
    su.id AS suspicious_url_id,
    su.url as suspicious_url,
    su.domain,
    su.suspicious_reason,
    su.risk_level
FROM case_metadata c
LEFT JOIN extracted_emails e ON c.id = e.case_id
LEFT JOIN extracted_payment_addresses p ON c.id = p.case_id
LEFT JOIN risk_keywords k ON c.id = k.case_id
LEFT JOIN pgp_content pg ON c.id = pg.case_id
LEFT JOIN financial_data f ON c.id = f.case_id
LEFT JOIN shipping_addresses s ON c.id = s.case_id
LEFT JOIN usernames u ON c.id = u.case_id
LEFT JOIN actual_links al ON c.id = al.case_id
LEFT JOIN document_advertisements da ON c.id = da.case_id
LEFT JOIN suspicious_urls su ON c.id = su.case_id
ORDER BY c.id;"""
        }

        col1, col2 = st.columns(2)

        with col1:
            st.write("**🔍 Basic Queries**")
            basic_queries = ["View all cases", "View all actual links", "View recent actual links", "High risk cases (score > 100)", "Recent cases (last 10)", "Cases by severity level"]
            for title in basic_queries:
                if st.button(f"📝 {title}", key=f"basic_{title}"):
                    st.session_state.selected_query = sample_queries[title]
                    st.rerun()

        with col2:
            st.write("**📊 Detailed Analysis**")
            detailed_queries = ["View all emails with case info", "View all payment addresses with case info", "View all risky keywords with case info", "View all PGP content with case info", "View all financial data with case info", "View all shipping addresses with case info", "View all usernames with case info", "View all actual links with case info", "View all document advertisements with case info", "View all suspicious URLs with case info"]
            for title in detailed_queries:
                if st.button(f"📝 {title}", key=f"detailed_{title}"):
                    st.session_state.selected_query = sample_queries[title]
                    st.rerun()

        st.write("**🔬 Advanced Queries**")
        advanced_queries = ["Full details for specific case", "Complete forensic analysis (all data)", "View drop locations only", "View coordinates only", "View postal addresses only", "View dark web usernames only", "View forum usernames only", "View professional aliases only", "Find high suspicious level links", "Find JavaScript links", "Find event handler links", "Find hyperlink links", "Count links by type"]
        for title in advanced_queries:
            if st.button(f"📝 {title}", key=f"advanced_{title}"):
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

# ========== TAB 3: Tampering Detection ==========
with tab3:
    st.subheader("🛡️ Tampering Detection")
    st.info("Verify file integrity by comparing current file hashes with stored hashes in reports.")
    
    # Function to verify hash
    def verify_hash(html_file_path, report_json_path):
        try:
            current_hash = calculate_sha256(html_file_path)
            
            with open(report_json_path, "r") as json_file:
                report_data = json.load(json_file)
                stored_hash = report_data.get("sha256")
            
            return {
                'file': os.path.basename(html_file_path),
                'current_hash': current_hash,
                'stored_hash': stored_hash,
                'match': current_hash == stored_hash,
                'status': "✅ Authentic" if current_hash == stored_hash else "🚨 TAMPERED"
            }
        except Exception as e:
            return {
                'file': os.path.basename(html_file_path),
                'current_hash': "Error",
                'stored_hash': "Error",
                'match': False,
                'status': f"❌ Error: {str(e)}"
            }
    
    # Function to find matching reports
    def find_matching_reports():
        data_dir = "data"
        reports_dir = "reports"
        verification_results = []
        
        if not os.path.exists(data_dir):
            return [], "❌ Data directory not found"
        
        if not os.path.exists(reports_dir):
            return [], "❌ Reports directory not found"
        
        html_files = [f for f in os.listdir(data_dir) if f.endswith('.html')]
        report_files = [f for f in os.listdir(reports_dir) if f.endswith('.json')]
        
        if not html_files:
            return [], "❌ No HTML files found in data directory"
        
        if not report_files:
            return [], "❌ No JSON reports found in reports directory"
        
        for html_file in html_files:
            base_name = os.path.splitext(html_file)[0]
            html_path = os.path.join(data_dir, html_file)
            
            # Find matching report
            matching_report = None
            for report_file in report_files:
                if base_name in report_file:
                    matching_report = os.path.join(reports_dir, report_file)
                    break
            
            if matching_report:
                result = verify_hash(html_path, matching_report)
                verification_results.append(result)
            else:
                verification_results.append({
                    'file': html_file,
                    'current_hash': "N/A",
                    'stored_hash': "N/A",
                    'match': False,
                    'status': "⚠️ No matching report found"
                })
        
        return verification_results, None
    
    # UI for tampering detection
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔍 Verify All Files", type="primary"):
            with st.spinner("Verifying file integrity..."):
                results, error = find_matching_reports()
                
                if error:
                    st.error(error)
                else:
                    st.session_state.verification_results = results
                    st.success(f"✅ Verification completed for {len(results)} files")
    
    with col2:
        if st.button("📊 Show Verification Summary"):
            if hasattr(st.session_state, 'verification_results'):
                results = st.session_state.verification_results
                
                # Count results
                authentic_count = sum(1 for r in results if r['match'])
                tampered_count = sum(1 for r in results if not r['match'] and 'Error' not in r['status'])
                error_count = sum(1 for r in results if 'Error' in r['status'])
                no_report_count = sum(1 for r in results if 'No matching report' in r['status'])
                
                # Display summary
                st.subheader("📊 Verification Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("✅ Authentic", authentic_count)
                with col2:
                    st.metric("🚨 Tampered", tampered_count)
                with col3:
                    st.metric("❌ Errors", error_count)
                with col4:
                    st.metric("⚠️ No Report", no_report_count)
    
    # Display detailed results
    if hasattr(st.session_state, 'verification_results'):
        st.subheader("🔍 Detailed Verification Results")
        
        # Create DataFrame for better display
        results_df = pd.DataFrame(st.session_state.verification_results)
        
        # Color code the status column
        def color_status(val):
            if "✅ Authentic" in val:
                return "background-color: #d4edda; color: #155724;"
            elif "🚨 TAMPERED" in val:
                return "background-color: #f8d7da; color: #721c24;"
            elif "❌ Error" in val:
                return "background-color: #fff3cd; color: #856404;"
            else:
                return "background-color: #d1ecf1; color: #0c5460;"
        
        # Display styled dataframe
        st.dataframe(
            results_df.style.applymap(color_status, subset=['status']),
            use_container_width=True
        )
        
        # Download results
        csv_data = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Verification Results",
            data=csv_data,
            file_name="tampering_verification_results.csv",
            mime="text/csv"
        )
        
        # Show detailed hash comparison for tampered files
        tampered_files = [r for r in st.session_state.verification_results if not r['match'] and 'Error' not in r['status']]
        
        if tampered_files:
            st.subheader("🚨 Tampered Files Details")
            st.warning("The following files have been modified since analysis:")
            
            for file_info in tampered_files:
                with st.expander(f"🔍 {file_info['file']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Current Hash:**")
                        st.code(file_info['current_hash'])
                    with col2:
                        st.write("**Stored Hash:**")
                        st.code(file_info['stored_hash'])
                    
                    st.error("⚠️ Hash mismatch detected! File may have been tampered with.")
    
    # Manual verification section
    st.subheader("🔧 Manual Verification")
    st.info("Manually verify a specific file against its report.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Upload HTML file for verification", type="html")
    
    with col2:
        uploaded_report = st.file_uploader("Upload JSON report file", type="json")
    
    if uploaded_file and uploaded_report:
        if st.button("🔍 Verify This File"):
            try:
                # Save uploaded files temporarily
                temp_html_path = os.path.join("data", uploaded_file.name)
                temp_json_path = os.path.join("reports", uploaded_report.name)
                
                with open(temp_html_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                with open(temp_json_path, "wb") as f:
                    f.write(uploaded_report.getvalue())
                
                # Verify
                result = verify_hash(temp_html_path, temp_json_path)
                
                # Display result
                st.subheader("🔍 Verification Result")
                
                if result['match']:
                    st.success("✅ File is authentic - no tampering detected!")
                else:
                    st.error("🚨 File has been tampered with!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Current Hash:**")
                    st.code(result['current_hash'])
                with col2:
                    st.write("**Stored Hash:**")
                    st.code(result['stored_hash'])
                
                # Clean up temp files
                os.remove(temp_html_path)
                os.remove(temp_json_path)
                
            except Exception as e:
                st.error(f"❌ Verification failed: {str(e)}")
    
    # Information section
    st.subheader("ℹ️ About Tampering Detection")
    st.info("""
    **How it works:**
    - Each HTML file is hashed using SHA-256 during analysis
    - The hash is stored in the JSON report
    - This tool compares current file hash with stored hash
    - If hashes don't match, the file has been modified
    
    **Forensic importance:**
    - Maintains chain of custody
    - Ensures evidence integrity
    - Critical for legal proceedings
    - Prevents tampering accusations
    """)
