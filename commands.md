# 🛠️ DarkWeb Forensic Tool – Developer Command Guide

A collection of essential commands for developing, running, verifying, and contributing to the tool.

---

## ✅ 1. Activate Virtual Environment
source venv/bin/activate

## 📦 2. Manage Dependencies

## 2.1 Freeze installed packages for collaboration:
pip freeze > requirements.txt

## 2.2 Install from requirements.txt (for new team members):
pip install -r requirements.txt

## 🚀 3. Run Main Forensic Tool (CLI)

## Execute analysis on all .html files inside /data:
python3 -m src.main

## 🔐 4. Verify File Authenticity (Hash Matching)

## 🔄 4.1. Verify All Files

python3 -m src.verify.verify_hash

## 🔍 4.2. Verify a Single File

python3 -m src.verify.verify_hash data/test_btc.html reports/report_test_btc.json

## 🧪 5. Branching & Git Workflow

## 5.1. 🔧 Create & Push Feature Branch

git checkout -b SCRUM-5
git add .
git commit -m "Fixes: SCRUM-5 - added report feature"
git pull --rebase origin main
git push origin SCRUM-5

## 5.2. ✅ Use commit format:

Fixes: SCRUM-<ticket> - <brief-description>

## 🌐 6. Run Web App Interface (Streamlit)
## Launch the integrated Streamlit web app (includes both Forensic Analysis and SQL Query Interface):
streamlit run src/ui/app.py

## Launch the standalone SQL web interface to execute queries and view results:
streamlit run src/ui/sql_query_interface.py

## 🧪 7. Testing & Data Generation

## 7.1. Generate Test HTML Pages from Dataset
# Create realistic dark web HTML pages from your dataset for testing:
python create_darkweb_pages.py

## 7.2. Run Comprehensive RAG vs LLM Testing
# Test all extraction methods (AI Models, RAG+LLM, LLM-only) on all HTML pages:
python test_rag_vs_llm.py

## 7.3. Test Single File in Streamlit
# Upload a test file in the Streamlit app and compare RAG vs LLM results
# Recommended test file: data/darkweb_test_pages/forum_page_8.html

## 📊 8. Understanding Test Results

## 8.1. Test Output Files:
- `comprehensive_extraction_methods_TIMESTAMP.csv` - Detailed results
- `Comprehensive_Extraction_Methods_Report_TIMESTAMP.pdf` - Professional report

## 8.2. What Each Method Tests:
- **AI Models:** StarPII (emails), Zero-shot (keywords), spaCy (payments)
- **RAG+LLM:** Knowledge-augmented LLM with dark web context
- **LLM-only:** Standard LLM without knowledge base

## 8.3. Expected Results:
- RAG+LLM should find the most items (emails, keywords, payments)
- AI Models are fastest but may miss complex patterns
- LLM-only provides moderate improvement over AI Models