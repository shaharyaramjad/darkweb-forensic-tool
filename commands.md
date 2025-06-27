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
## Launch the Streamlit web app:
streamlit run src/ui/app.py

