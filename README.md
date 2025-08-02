# 🔐 DarkWeb Forensic Tool

This Python-based **offline forensic tool** processes `.html` pages extracted from dark web investigations. It automatically:

- ✅ Extracts Bitcoin (BTC) addresses  
- ✅ Detects email addresses  
- 🔐 Identifies PGP keys and encrypted content
- ⚠️ Flags risky keywords (e.g., "buy drugs", "zero-day", etc.)  
- 🔥 Calculates a risk score with severity label  
- 🧾 Generates PDF and JSON forensic reports  
- 🛡️ Verifies file integrity using SHA-256 hash
- 💾 Inserts all extracted data into a MySQL database

---

## 📦 Setup Instructions

### 1️⃣ Clone the repository

git clone https://github.com/shaharyaramjad/darkweb-forensic-tool.git
cd darkweb-forensic-tool


## 💻 Setup Instructions

## ⚡️ Database Setup

1️⃣ Install MySQL server on your machine (e.g., MySQL Community Server from https://dev.mysql.com/downloads/mysql/).

2️⃣ Start MySQL server (on Mac: System Preferences > MySQL > Start).

3️⃣ Open MySQL Workbench.

4️⃣ Connect to local MySQL server using root.

5️⃣ Copy and execute this SQL script to create database and tables:

```sql
CREATE DATABASE forensic_tool_db;
USE forensic_tool_db;

CREATE TABLE case_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(100),
    investigator_name VARCHAR(100),
    notes TEXT,
    score INT,
    severity VARCHAR(50),
    file_hash VARCHAR(255),
    llm_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE extracted_emails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    email VARCHAR(255),
    FOREIGN KEY (case_id) REFERENCES case_metadata(id)
);

CREATE TABLE extracted_payment_addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    address VARCHAR(255),
    FOREIGN KEY (case_id) REFERENCES case_metadata(id)
);

CREATE TABLE risk_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    keyword VARCHAR(255),
    FOREIGN KEY (case_id) REFERENCES case_metadata(id)
);


## 💡 Query 1: See all cases

SELECT * FROM case_metadata;


## 💡 Query 2: See all emails with case info

SELECT 
    e.id,
    e.email,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM extracted_emails e
JOIN case_metadata c ON e.case_id = c.id;

## 💡 Query 3: See all payment addresses with case info

SELECT 
    p.id,
    p.address,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM extracted_payment_addresses p
JOIN case_metadata c ON p.case_id = c.id;

## 💡 Query 4: See all risky keywords with case info

SELECT 
    k.id,
    k.keyword,
    c.case_id,
    c.investigator_name,
    c.severity,
    c.created_at
FROM risk_keywords k
JOIN case_metadata c ON k.case_id = c.id;

## 💡 Query 5: See full details for a specific case

SELECT * FROM case_metadata WHERE case_id = 'TEST-CASE-001';

## 💡 Big "full detail" query
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
ORDER BY c.id;

## Environment Setup

This project uses a `.env` file to securely store API keys and other secrets. You must create a `.env` file in the project root with the following variable:

```
TOGETHER_API_KEY=your_together_api_key_here
```

- Never commit your real `.env` file to version control. The `.env` file is already in `.gitignore`.
- You can use the provided `auto_venv.sh` script to activate your virtual environment automatically:

```bash
source auto_venv.sh
```

If you are on Windows Command Prompt or PowerShell, activate manually:
- Command Prompt: `venv\Scripts\activate.bat`
- PowerShell: `venv\Scripts\Activate.ps1`


