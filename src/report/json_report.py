import json
import os

def generate_json_report(file_name, sha256_hash, btc_addresses, emails, risky_keywords, risk_score, severity_label, case_id, investigator, notes):
    report_data = {
        "file_name": file_name,
        "sha256_hash": sha256_hash,
        "btc_addresses": btc_addresses,
        "emails": emails,
        "risky_keywords": risky_keywords,
        "risk_score": risk_score,
        "severity_label": severity_label,
        "case_id": case_id,
        "investigator": investigator,
        "notes": notes
    }

    os.makedirs("reports", exist_ok=True)

    # Remove file extension from file_name (e.g., "test_btc.html" → "test_btc")
    base_filename = os.path.splitext(file_name)[0]
    report_path = os.path.join("reports", f"report_{base_filename}.json")

    with open(report_path, "w") as json_file:
        json.dump(report_data, json_file, indent=4)

    print(f"📄 JSON report generated: {os.path.basename(report_path)}")
