import json
import hashlib
import sys

def calculate_sha256(filepath):
    with open(filepath, "rb") as f:
        bytes = f.read()
        return hashlib.sha256(bytes).hexdigest()

def verify_hash(html_file_path, report_json_path):
    # Calculate the current SHA-256 hash of the file
    current_hash = calculate_sha256(html_file_path)

    # Load the stored hash from the JSON report
    with open(report_json_path, "r") as json_file:
        report_data = json.load(json_file)
        stored_hash = report_data.get("sha256_hash")

    print(f"\nFile: {html_file_path}")
    print(f"Current SHA-256: {current_hash}")
    print(f"Stored SHA-256 : {stored_hash}")

    if stored_hash == current_hash:
        print("✅ Hash match confirmed. File is authentic.")
    else:
        print("🚨 WARNING: File hash mismatch! Possible tampering detected.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 -m src.verify.verify_hash <html_file_path> <report_json_path>")
    else:
        verify_hash(sys.argv[1], sys.argv[2])
