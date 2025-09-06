import os
import sys
import random

# Fix tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_insert import insert_into_db
from datetime import datetime
from src.extract.extract_payment_addresses_from_html import extract_payment_addresses_from_html
from src.extract.email_extractor import extract_emails_from_html
from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
from src.extract.pgp_extractor import extract_pgp_from_html
from src.extract.financial_data_extractor import extract_financial_data_from_html
from src.extract.shipping_address_extractor import extract_shipping_addresses_from_html
from src.extract.username_extractor import extract_usernames_from_html
from src.extract.document_advertisement_detector import extract_document_advertisements_from_html
from src.utils.hash_util import calculate_sha256
from src.risk.risk_score import calculate_risk_score
from src.report.pdf_report import generate_pdf_report
from src.report.json_report import generate_json_report
from src.llm.llm_classifier import classify_with_llm
from src.utils.security_scanner import secure_file_processing
from src.extract.utils_visible_text import detect_suspicious_prompts

# ===== Toggle Integrations =====
USE_LLM = False      # 🔁 Toggle LLM summarization ON/OFF
USE_AI_MODEL = False # 🔁 Toggle spaCy local AI ON/OFF
TRANSLATE = True     # 🔁 Enable or disable translation step
USE_SQL = True   # 🔁 Set to True to enable MySQL insert
USE_RAG = False
ENABLE_SECURITY_SCAN = True  # 🔁 Enable security scanning

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
        
        print(f"\n{'='*80}")
        print(f"🔍 Processing: {filename}")
        print(f"{'='*80}")

        # 🔒 SECURITY SCAN
        if ENABLE_SECURITY_SCAN:
            print("🛡️ Running security scan...")
            success, safe_filepath, security_report, scan_result = secure_file_processing(filepath)
            
            if not success:
                print("❌ Security scan failed. Skipping file.")
                continue
                
            print(security_report)
            
            if not scan_result['safe']:
                print("⚠️ Threats detected! Using sanitized version.")
                filepath = safe_filepath
            else:
                print("✅ File passed security scan.")
        else:
            print("⚠️ Security scanning disabled!")

        # Read HTML content
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

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
        pgp_content = extract_pgp_from_html(filepath, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI_MODEL, translate=TRANSLATE)
        
        # Extract document advertisements
        document_ads_result = extract_document_advertisements_from_html(
            filepath, 
            use_llm=USE_LLM,
            use_rag=USE_RAG,
            use_ai=USE_AI_MODEL, 
            translate=TRANSLATE
        )
        
        # Process document advertisements for virus detection
        virus_detection_result = None
        if document_ads_result['total_found'] > 0:
            try:
                from src.utils.virus_detection_api import process_document_advertisements_for_virus_detection
                virus_detection_result = process_document_advertisements_for_virus_detection(document_ads_result)
            except Exception as e:
                print(f"⚠️ Virus detection processing failed: {e}")
                # Create a simple fallback structure for reports
                virus_detection_result = {
                    'success': False,
                    'api_results': {
                        'total_checked': len(document_ads_result.get('suspicious_urls', [])),
                        'malicious_found': 0,
                        'high_risk_urls': []
                    },
                    'note': 'Virus detection processing failed, using simplified data structure'
                }
        
        file_hash = calculate_sha256(filepath)

        # Collect suspicious prompts from all extractors
        suspicious_prompts = []
        suspicious_prompts += detect_suspicious_prompts(open(filepath, 'r', encoding='utf-8', errors='ignore').read())
        # (If you want to aggregate from each extractor, you can also return them from each extractor and merge here)
        suspicious_prompts = list(set(suspicious_prompts))

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

        if pgp_content:
            for pgp_item in pgp_content:
                pgp_type = pgp_item.get('type', 'unknown')
                content = pgp_item.get('content', '')[:100] + "..." if len(pgp_item.get('content', '')) > 100 else pgp_item.get('content', '')
                print(f"🔐 PGP {pgp_type.upper()} Found: {content}")
        else:
            print("✅ No PGP content detected.")

        # Extract financial data
        financial_data = extract_financial_data_from_html(filepath, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI_MODEL, translate=TRANSLATE)
        if financial_data:
            for financial_item in financial_data:
                data_type = financial_item.get('type', 'unknown')
                content = financial_item.get('content', '')[:100] + "..." if len(financial_item.get('content', '')) > 100 else financial_item.get('content', '')
                print(f"💳 Financial {data_type.upper()} Found: {content}")
        else:
            print("✅ No financial data detected.")

        # Extract shipping addresses
        shipping_addresses = extract_shipping_addresses_from_html(filepath, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI_MODEL, translate=TRANSLATE)
        if shipping_addresses:
            for shipping_item in shipping_addresses:
                data_type = shipping_item.get('type', 'unknown')
                content = shipping_item.get('content', '')[:100] + "..." if len(shipping_item.get('content', '')) > 100 else shipping_item.get('content', '')
                print(f"📦 Shipping {data_type.upper()} Found: {content}")
        else:
            print("✅ No shipping addresses detected.")

        # Extract usernames/aliases
        usernames = extract_usernames_from_html(filepath, use_llm=USE_LLM, use_rag=USE_RAG, use_ai=USE_AI_MODEL, translate=TRANSLATE)
        if usernames:
            for username_item in usernames:
                data_type = username_item.get('type', 'unknown')
                content = username_item.get('content', '')[:100] + "..." if len(username_item.get('content', '')) > 100 else username_item.get('content', '')
                print(f"👤 Username {data_type.upper()} Found: {content}")
        else:
            print("✅ No usernames detected.")

        # Display document advertisement results
        if document_ads_result['total_found'] > 0:
            print(f"📄 Document Advertisements Found: {document_ads_result['total_found']}")
            if document_ads_result.get('document_advertisements'):
                for ad in document_ads_result['document_advertisements']:
                    risk_icon = "🔴" if ad['suspicious_level'] == 'high' else "🟡"
                    print(f"{risk_icon} {ad['type']}: {ad['content']}")
            
            if document_ads_result.get('suspicious_urls'):
                print("🔗 Suspicious URLs:")
                for url_data in document_ads_result['suspicious_urls']:
                    risk_icon = "🔴" if url_data['risk_level'] == 'high' else "🟡"
                    print(f"{risk_icon} {url_data['url']} ({url_data['suspicious_reason']})")
        else:
            print("✅ No document advertisements detected.")
        
        # Display virus detection results
        if virus_detection_result and virus_detection_result.get('success'):
            print("🦠 Virus Detection Results:")
            api_results = virus_detection_result.get('api_results', {})
            print(f"  URLs Checked: {api_results.get('total_checked', 0)}")
            print(f"  Malicious URLs: {api_results.get('malicious_found', 0)}")
            print(f"  High Risk URLs: {len(api_results.get('high_risk_urls', []))}")
        else:
            print("✅ No virus detection results available.")

        print(f"🧠 LLM Summary: {llm_summary}")

        # 🔥 Risk Score
        score = calculate_risk_score(payment_addresses, emails_found, keywords_found, pgp_content, financial_data, shipping_addresses, usernames)
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
            pgp_content,
            financial_data,
            shipping_addresses,
            usernames,
            score,
            severity,
            case_id,
            investigator,
            notes,
            llm_summary,
            suspicious_prompts,
            document_ads_result,
            virus_detection_result
        )

        generate_json_report(
            report_name,
            file_hash,
            payment_addresses,
            emails_found,
            keywords_found,
            pgp_content,
            financial_data,
            shipping_addresses,
            usernames,
            score,
            severity,
            case_id,
            investigator,
            notes,
            llm_summary,
            suspicious_prompts,
            document_ads_result,
            virus_detection_result
        )

        if USE_SQL:
            insert_into_db(
                case_id,
                investigator,
                notes,
                emails_found,
                payment_addresses,
                keywords_found,
                pgp_content,
                financial_data,
                shipping_addresses,
                usernames,
                score,
                severity,
                file_hash,
                llm_summary,
                document_ads_result
            )
            print("✅ Data inserted into MySQL database successfully.")
        else:
            print("⚠️ SQL insertion is disabled. Skipping DB insert.")

