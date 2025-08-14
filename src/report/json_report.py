import json
import os
from datetime import datetime

def generate_json_report(
    filename, hash_value, btc_list, email_list, keywords, pgp_content, financial_data, shipping_addresses, usernames, score,
    level, case_id, investigator, notes, llm_summary="", suspicious_prompts=None, document_ads_result=None, virus_detection_result=None
):
    os.makedirs("reports", exist_ok=True)
    report_filename = f"report_{filename.replace('.html', '')}.json"
    report_path = os.path.join("reports", report_filename)
    report_data = {
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "case_id": case_id,
        "investigator": investigator,
        "description": notes,
        "file": filename,
        "sha256": hash_value,
        "suspicious_prompts": suspicious_prompts or [],
        "payment_addresses": btc_list or [],
        "emails": email_list or [],
        "risky_keywords": keywords or [],
        "pgp_content": pgp_content or [],
        "financial_data": financial_data or [],
        "shipping_addresses": shipping_addresses or [],
        "usernames": usernames or [],
        "risk_score": score,
        "severity": level,
        "llm_summary": llm_summary or "None",
        "document_advertisements": document_ads_result or {},
        "virus_detection_results": virus_detection_result or {}
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"📄 JSON report generated: {report_filename}")
    return report_path
