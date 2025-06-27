import json
import hashlib
import sys
import os

def calculate_sha256(filepath):
    with open(filepath, "rb") as f:
        bytes = f.read()
        return hashlib.sha256(bytes).hexdigest()

def verify_hash(html_file_path, report_json_path):
    current_hash = calculate_sha256(html_file_path)

    with open(report_json_path, "r") as json_file:
        report_data = json.load(json_file)
        stored_hash = report_data.get("sha256_hash")

    print(f"\n📄 File: {html_file_path}")
    print(f"Current SHA-256: {current_hash}")
    print(f"Stored SHA-256 : {stored_hash}")

    if stored_hash == current_hash:
        print("✅ Hash match confirmed. File is authentic.")
    else:
        print("🚨 WARNING: File hash mismatch! Possible tampering detected.")

def verify_all():
    data_dir = "data"
    reports_dir = "reports"

    for filename in os.listdir(data_dir):
        if filename.endswith(".html"):
            html_path = os.path.join(data_dir, filename)
            base_name = os.path.splitext(filename)[0]

            # Find matching report JSON
            for report_file in os.listdir(reports_dir):
                if report_file.startswith("report_") and base_name in report_file and report_file.endswith(".json"):
                    report_path = os.path.join(reports_dir, report_file)
                    verify_hash(html_path, report_path)
                    break
            else:
                print(f"⚠️ No report found for {filename}")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        verify_hash(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        print("🔍 Verifying all HTML files in 'data/' with matching reports in 'reports/'...")
        verify_all()
    else:
        print("Usage:\n  Single file: python3 -m src.verify.verify_hash data/file.html reports/report_file.json\n  All files:   python3 -m src.verify.verify_hash")
