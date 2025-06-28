import re
import os
import spacy
from bs4 import BeautifulSoup
from langdetect import detect
from deep_translator import GoogleTranslator
from openai import OpenAI

# Regex pattern for common crypto/payment addresses
payment_pattern = r"""
\b(
    [13][a-km-zA-HJ-NP-Z1-9]{25,34} |
    bc1[a-zA-HJ-NP-Z0-9]{11,71} |
    0x[a-fA-F0-9]{40} |
    T[a-zA-Z0-9]{33} |
    4[0-9AB][1-9A-HJ-NP-Za-km-z]{93} |
    ltc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59} |
    L[a-km-zA-HJ-NP-Z1-9]{26,33} |
    M[a-km-zA-HJ-NP-Z1-9]{26,33} |
    X[1-9A-HJ-NP-Za-km-z]{33} |
    t1[0-9A-Za-z]{33} |
    U[0-9]{6,10}
)\b
"""

# Initialize spaCy
nlp = spacy.load("en_core_web_sm")

# 🧪 For testing: Enter your Together.ai API key as a string
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"

# Together.ai LLM
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

def llm_fallback_classify(text):
    prompt = f"""
You are an AI trained to detect potential crypto or payment addresses in text, even if obfuscated.

Analyze and list suspicious address references.

TEXT:
{text[:2000]}
"""
    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip().split("\n")
    except Exception as e:
        return [f"❌ LLM Error: {e}"]

def extract_payment_addresses_from_html(file_path, use_llm=True, use_ai=True, translate=True):
    matches = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()

            # Detect language and translate if needed
            if translate:
                lang = detect(text)
                if lang != "en":
                    trans = GoogleTranslator(source='auto', target='en')
                    text = trans.translate(text)
                    print(f"[Translator] Detected: {lang}, translated to English.")

            # Regex
            pattern = re.compile(payment_pattern, re.VERBOSE | re.IGNORECASE)
            regex_matches = pattern.findall(text)
            matches.extend(regex_matches)

            # spaCy fallback
            if use_ai and not matches:
                doc = nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ["MONEY", "CARDINAL"] and len(ent.text) > 10:
                        matches.append(ent.text.strip())

            # LLM fallback
            if use_llm and not matches and TOGETHER_API_KEY:
                print(f"[LLM] Trying fallback on: {os.path.basename(file_path)}")
                llm_results = llm_fallback_classify(text)
                matches.extend(llm_results)

    except Exception as e:
        print(f"[ERROR] Failed to extract from {file_path}: {e}")

    return list(filter(None, set(matches)))
