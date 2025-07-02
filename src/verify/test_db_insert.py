from src.utils.db_insert import insert_into_db

# Example dummy data for testing
case_id = "TEST-CASE-001"
investigator = "Test Investigator"
notes = "This is a test insertion."
emails_found = ["test@example.com", "alice@darkweb.org"]
payment_addresses = ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]
keywords_found = ["zero-day", "buy drugs"]
score = 85
severity = "High"
file_hash = "dummyhashvalue1234567890"
llm_summary = "This is a dummy LLM summary."

# Insert into DB
insert_into_db(
    case_id,
    investigator,
    notes,
    emails_found,
    payment_addresses,
    keywords_found,
    score,
    severity,
    file_hash,
    llm_summary
)

print("✅ Test data inserted into MySQL successfully.")
