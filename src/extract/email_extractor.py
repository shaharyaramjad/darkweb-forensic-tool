import re
import os
from bs4 import BeautifulSoup
from huggingface_hub import InferenceClient
from langdetect import detect
from deep_translator import GoogleTranslator
from openai import OpenAI

TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"

# Together.ai LLM
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# Initialize StarPII client
client = InferenceClient(
    provider="hf-inference",
    api_key="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",
)

# Regex patterns
generic_email_re = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
obfuscated_email_re = re.compile(
    r'\b([a-zA-Z0-9._%+-]+)\s*(?:@|\[\s*at\s*\]|\s+at\s+)\s*([a-zA-Z0-9.-]+)\s*(?:\.|\[\s*dot\s*\]|\s+dot\s+)\s*([a-zA-Z]{2,})\b',
    re.IGNORECASE
)

def extract_emails_with_starpii(text):
    result = client.token_classification(text, model="bigcode/starpii")
    emails = []
    for entity in result:
        if entity['entity_group'].lower() == 'email':
            emails.append(entity['word'])
    return emails

def extract_emails(text):
    normal = generic_email_re.findall(text)
    obfuscated = [f"{m[0]}@{m[1]}.{m[2]}" for m in obfuscated_email_re.findall(text)]
    starpii_emails = extract_emails_with_starpii(text)
    return sorted(set(normal + obfuscated + starpii_emails))

def extract_emails_from_html(filepath, use_ai=True, use_llm=True, translate=True):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    # Extract visible text
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ')

    # Detect language
    try:
        detected_lang = detect(text)
    except:
        detected_lang = "unknown"

    # Translate if needed
    if translate and detected_lang != "en" and detected_lang != "unknown":
        try:
            translated_text = GoogleTranslator(source='auto', target='en').translate(text)
            print(f"🌐 Translated text from {detected_lang} to English.")
        except Exception as e:
            print(f"⚠️ Translation failed: {e}")
            translated_text = text  # fallback
    else:
        translated_text = text

    # AI & regex extraction
    extracted = []
    if use_ai:
        extracted = extract_emails(translated_text)
        if extracted:
            print("✅ Emails extracted using AI model & regex.")
        else:
            print("⚠️ No emails found using AI model & regex.")
    else:
        # Only regex fallback
        extracted = generic_email_re.findall(translated_text)
        if extracted:
            print("✅ Emails extracted using regex only.")
        else:
            print("⚠️ No emails found using regex.")

    # LLM fallback if enabled and no results
    if use_llm and not extracted:
        print("⚠️ No emails found. Trying LLM fallback...")
        try:
            llm_prompt = (
                "Extract all email addresses from the following text. "
                "Only provide the email addresses as a comma-separated list.\n\n"
                f"{translated_text}"
            )
            response = client.chat.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                messages=[{"role": "user", "content": llm_prompt}],
            )
            llm_output = response.choices[0].message.content.strip()
            llm_emails = [email.strip() for email in llm_output.split(",") if email.strip()]
            extracted = sorted(set(llm_emails))
            print("✅ Emails extracted using LLM fallback.")
        except Exception as e:
            print(f"❌ LLM fallback failed: {e}")

    return extracted
