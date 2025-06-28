import os
from openai import OpenAI
from deep_translator import GoogleTranslator
from langdetect import detect

# === STATIC KEYWORDS ===
STATIC_RISK_KEYWORDS = [
    "buy drugs", "credit card dump", "exploit", "zero-day",
    "fake passport", "hitman", "weapon", "child abuse", "counterfeit"
]

# === LLM Client ===
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === Placeholder: Basic AI classifier (to be replaced or trained later) ===
def mock_ai_keyword_detector(text):
    risky_signals = ["dark market", "ransomware", "exploit kit", "dumps", "silk road", "hydra", "malware"]
    detected = []
    for kw in risky_signals:
        if kw in text.lower():
            detected.append(kw)
    return detected

def detect_risk_keywords_from_html(filepath, use_llm=True, use_ai=True, translate=True):
    found_keywords = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html_text = f.read().lower()

            # === Language detection and translation ===
            if translate:
                try:
                    lang = detect(html_text)
                    if lang != "en":
                        html_text = GoogleTranslator(source='auto', target='en').translate(html_text)
                        print(f"🌐 Translated content from {lang} to English.")
                except Exception as e:
                    print(f"⚠️ Language detection/translation error: {e}")

            # === Static keyword check ===
            for keyword in STATIC_RISK_KEYWORDS:
                if keyword in html_text:
                    found_keywords.append(keyword)

            # === AI fallback check ===
            if use_ai and not found_keywords:
                ai_detected = mock_ai_keyword_detector(html_text)
                found_keywords.extend(ai_detected)

            # === LLM fallback check ===
            if use_llm and not found_keywords and TOGETHER_API_KEY:
                prompt = f"""
You're an AI forensic assistant. Scan the following HTML content and extract any risky keywords indicating illegal activity such as drugs, weapons, fraud, child exploitation, hacking, or other crimes.

Return a list of single keywords only.

HTML CONTENT:
{html_text[:2000]}
"""
                response = client.chat.completions.create(
                    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                result_text = response.choices[0].message.content.strip()
                llm_keywords = [kw.strip() for kw in result_text.split("\n") if kw.strip()]
                found_keywords.extend(llm_keywords)

    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")

    return list(set(found_keywords))  # Remove duplicates
