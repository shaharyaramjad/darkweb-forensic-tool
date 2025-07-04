import os
from openai import OpenAI
from deep_translator import GoogleTranslator
from langdetect import detect
from transformers import pipeline

# === LLM Client (Together.ai) ===
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === Hugging Face Zero-Shot Classifier ===
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# === Function ===
def detect_risk_keywords_from_html(filepath, use_llm, use_ai, translate):
    found_keywords = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html_text = f.read()

            # === Language detection and translation ===
            if translate:
                try:
                    lang = detect(html_text)
                    if lang != "en":
                        html_text = GoogleTranslator(source='auto', target='en').translate(html_text)
                        print(f"🌐 Translated content from {lang} to English.")
                except Exception as e:
                    print(f"⚠️ Language detection/translation error: {e}")

            # === AI Zero-shot classification check ===
            if use_ai:
                candidate_labels = ["drugs", "weapons", "hacking", "fraud", "child abuse", 
                                    "fake documents", "exploit", "ransomware", "credit card dump", 
                                    "botnet", "hitman", "forged passport", "zero-day"]
                result = zero_shot_classifier(html_text, candidate_labels=candidate_labels, multi_label=True)

                for label, score in zip(result["labels"], result["scores"]):
                    if score > 0.5:  # Threshold can be adjusted
                        found_keywords.append(label)

            # === LLM fallback ===
            if use_llm and not found_keywords and TOGETHER_API_KEY:
                print("⚠️ No keywords found via AI. Trying LLM fallback...")
                prompt = f"""
You're an AI forensic assistant. Scan the following HTML content and extract any risky keywords indicating illegal activity such as drugs, weapons, fraud, child exploitation, hacking, or other crimes.

Return a list of single keywords only (one per line).

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
