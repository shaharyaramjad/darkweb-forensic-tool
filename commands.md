# 🔧 Common Developer Commands

## ✅ Virtual Environment
source venv/bin/activate

## 📦 Install/Track Dependencies
pip freeze > requirements.txt

## 🚀 Run Main Tool
python3 -m src.main

## 🔐 Verify File Hash
python3 -m src.verify.verify_hash data/test_btc.html reports/report_test_btc.json

## 🧪 Create & Push Branch (Example)
git checkout -b SCRUM-number
git add .
git commit -m "Fixes: SCRUM-5 - added report feature"
git pull --rebase origin main   
git push origin SCRUM-number

<!-- from writing and setting the branch this is the format -->
Fixes: Scrum-5 - description

## to run the web app
streamlit run src/ui/app.py   