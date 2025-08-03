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

CREATE TABLE pgp_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    pgp_type VARCHAR(100),
    pgp_content TEXT,
    FOREIGN KEY (case_id) REFERENCES case_metadata(id)
);

CREATE TABLE financial_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    data_type VARCHAR(100),
    content TEXT,
    FOREIGN KEY (case_id) REFERENCES case_metadata(id)
);

CREATE TABLE shipping_addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    address_type VARCHAR(100),
    content TEXT,
    FOREIGN KEY (case_id) REFERENCES case_metadata(id)
);

CREATE TABLE usernames (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT,
    username_type VARCHAR(100),
    content TEXT,
    FOREIGN KEY (case_id) REFERENCES case_metadata(id)
);
