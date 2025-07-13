import re
import os
import faiss
import numpy as np
from bs4 import BeautifulSoup
from huggingface_hub import InferenceClient
from langdetect import detect
from deep_translator import GoogleTranslator
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# === Together.ai LLM ===
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === StarPII client ===
pii_client = InferenceClient(
    provider="hf-inference",
    api_key="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",
)

# === Regex patterns ===
generic_email_re = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
obfuscated_email_re = re.compile(
    r'\b([a-zA-Z0-9._%+-]+)\s*(?:@|\[\s*at\s*\]|\s+at\s+)\s*([a-zA-Z0-9.-]+)\s*(?:\.|\[\s*dot\s*\]|\s+dot\s+)\s*([a-zA-Z]{2,})\b',
    re.IGNORECASE
)

# === Knowledge base for RAG ===
knowledge_texts = [
    "Suspicious emails often use protonmail.com, onionmail.org, or tutanota.com domains.",
    "Dark web vendors use random strings and temporary domains for emails.",
    "Emails with hidden or obfuscated words such as user[at]domain[dot]com are common.",
    "Vendors often advertise contact emails in unusual formats to avoid detection.",
    "Look for mentions of disposable emails or encrypted communication instructions.",
    "Common obfuscation patterns: [at] for @, [dot] for ., (at) for @, (dot) for .",
    "Dark web vendors use temporary email services like 10minutemail, guerrillamail.",
    "Look for email addresses in hidden divs, comments, or obfuscated text.",
    "Vendors often use multiple contact methods: email, PGP, encrypted messaging.",
    "Suspicious domains include .onion, .bit, and other alternative TLDs."
]

model = SentenceTransformer("all-MiniLM-L6-v2")
knowledge_embeddings = model.encode(knowledge_texts)
dimension = knowledge_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(knowledge_embeddings))

def retrieve_context(text, k=3):
    query_embedding = model.encode([text])
    distances, indices = index.search(np.array(query_embedding), k)
    retrieved_contexts = [knowledge_texts[i] for i in indices[0]]
    return "\n".join(retrieved_contexts)

def extract_emails_with_starpii(text):
    result = pii_client.token_classification(text, model="bigcode/starpii")
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

def extract_emails_from_html(filepath, use_ai=True, use_llm=True, translate=True, use_rag=True):
    try:
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
            try:
                extracted = extract_emails(translated_text)
                if extracted:
                    print("✅ Emails extracted using AI model & regex.")
                else:
                    print("⚠️ No emails found using AI model & regex.")
            except Exception as e:
                print(f"⚠️ AI extraction failed: {e}")
                extracted = []
        else:
            extracted = generic_email_re.findall(translated_text)

        # === RAG + LLM fallback ===
        if use_llm and not extracted:
            print("⚠️ No emails found. Trying LLM fallback..." + (" (with RAG context)" if use_rag else " (no RAG context)"))

            try:
                if use_rag:
                    retrieved_context = retrieve_context(translated_text)
                    llm_prompt = f"""
Use the following knowledge base context to help you find suspicious or hidden email addresses.

Knowledge base context:
{retrieved_context}

HTML CONTENT:
{translated_text}

Return a comma-separated list of email addresses only.
"""
                else:
                    llm_prompt = f"""
HTML CONTENT:
{translated_text}

Return a comma-separated list of email addresses only.
"""
                response = client.chat.completions.create(
                    model="mistralai/Mixtral-8x7B-Instruct-v0.1",  # Consistent model
                    messages=[{"role": "user", "content": llm_prompt}],
                    temperature=0.1,
                )
                llm_output = response.choices[0].message.content.strip()
                llm_emails = [email.strip() for email in llm_output.split(",") if email.strip()]
                extracted = sorted(set(llm_emails))
                print("✅ Emails extracted using LLM fallback." + (" (with RAG context)" if use_rag else " (no RAG context)"))
            except Exception as e:
                print(f"❌ LLM fallback failed: {e}")

        return extracted
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return []
