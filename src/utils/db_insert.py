import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def insert_into_db(case_id, investigator, notes, emails, payment_addresses, keywords, pgp_content, financial_data, score, severity, file_hash, llm_summary):
    # Connect to database
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()

    # Insert into case_metadata
    cursor.execute("""
        INSERT INTO case_metadata (case_id, investigator_name, notes, score, severity, file_hash, llm_summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (case_id, investigator, notes, score, severity, file_hash, llm_summary))
    case_db_id = cursor.lastrowid

    # Insert emails
    for email in emails:
        cursor.execute("""
            INSERT INTO extracted_emails (case_id, email)
            VALUES (%s, %s)
        """, (case_db_id, email))

    # Insert payment addresses
    for addr in payment_addresses:
        cursor.execute("""
            INSERT INTO extracted_payment_addresses (case_id, address)
            VALUES (%s, %s)
        """, (case_db_id, addr))

    # Insert risk keywords
    for keyword in keywords:
        cursor.execute("""
            INSERT INTO risk_keywords (case_id, keyword)
            VALUES (%s, %s)
        """, (case_db_id, keyword))

    # Insert PGP content
    for pgp_item in pgp_content:
        pgp_type = pgp_item.get('type', 'unknown')
        pgp_content_text = pgp_item.get('content', '')
        cursor.execute("""
            INSERT INTO pgp_content (case_id, pgp_type, pgp_content)
            VALUES (%s, %s, %s)
        """, (case_db_id, pgp_type, pgp_content_text))

    # Insert financial data
    for financial_item in financial_data:
        data_type = financial_item.get('type', 'unknown')
        content = financial_item.get('content', '')
        cursor.execute("""
            INSERT INTO financial_data (case_id, data_type, content)
            VALUES (%s, %s, %s)
        """, (case_db_id, data_type, content))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Data inserted into MySQL successfully.")
