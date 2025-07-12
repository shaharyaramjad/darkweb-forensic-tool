import re
import os
import spacy
import faiss
import numpy as np
from bs4 import BeautifulSoup
from langdetect import detect
from deep_translator import GoogleTranslator
from openai import OpenAI
from sentence_transformers import SentenceTransformer

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

# Together.ai LLM
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === Knowledge base for RAG ===
knowledge_texts = [
    "BTC addresses often start with 1 or 3 or bc1.",
    "Ethereum addresses start with 0x and have 40 hex characters.",
    "Monero addresses start with 4 and are about 95 characters long.",
    "Some dark web vendors use obfuscated addresses hidden in text or broken with spaces.",
    "Always check for long alphanumeric strings resembling crypto addresses when scanning dark web pages.",
    "Litecoin addresses may start with L or M or ltc1.",
    "Bitcoin Cash addresses start with bitcoincash: or q or p.",
    "Dash addresses start with X and are 34 characters long.",
    "Zcash addresses start with z or t and are 95 characters long.",
    "Look for addresses in hidden elements, comments, or obfuscated text.",
    "Vendors often use multiple payment methods: Bitcoin, Monero, Ethereum, Litecoin.",
    "Some addresses may be split across multiple lines or contain spaces."
]

# Embedding model
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

def llm_fallback_classify(text, context):
    if context:
        prompt = f"""
You are an AI trained to detect cryptocurrency or payment addresses in text.

Use the following knowledge base context to help you.

Knowledge base context:
{context}

Return only a single comma-separated list of payment addresses. 

⚠️ Do NOT include explanations, bullet points, parentheses, or comments. No other text.

TEXT:
{text[:2000]}
"""
    else:
        prompt = f"""
You are an AI trained to detect cryptocurrency or payment addresses in text.

Return only a single comma-separated list of payment addresses. 

⚠️ Do NOT include explanations, bullet points, parentheses, or comments. No other text.

TEXT:
{text[:2000]}
"""
    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        llm_output = response.choices[0].message.content.strip()

        # Split by comma first
        raw_addresses = [addr.strip() for addr in llm_output.split(",") if addr.strip()]

        # Extra cleanup: keep only strings matching regex
        pattern = re.compile(payment_pattern, re.VERBOSE | re.IGNORECASE)
        filtered_addresses = [addr for addr in raw_addresses if pattern.fullmatch(addr)]

        return filtered_addresses

    except Exception as e:
        return [f"❌ LLM Error: {e}"]

def extract_payment_addresses_from_html(file_path, use_llm=True, use_rag=True, use_ai=True, translate=True):
    matches = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()

            # Detect language and translate if needed
            if translate:
                try:
                    lang = detect(text)
                    if lang != "en":
                        trans = GoogleTranslator(source='auto', target='en')
                        text = trans.translate(text)
                        print(f"[Translator] Detected: {lang}, translated to English.")
                except Exception as e:
                    print(f"⚠️ Translation failed: {e}")

            # Regex extraction
            pattern = re.compile(payment_pattern, re.VERBOSE | re.IGNORECASE)
            regex_matches = pattern.findall(text)
            matches.extend(regex_matches)
            
            if regex_matches:
                print("✅ Payment addresses found using regex patterns.")

            # spaCy AI fallback
            if use_ai and not matches:
                try:
                    doc = nlp(text)
                    for ent in doc.ents:
                        if ent.label_ in ["MONEY", "CARDINAL"] and len(ent.text) > 10:
                            matches.append(ent.text.strip())
                    
                    if matches:
                        print("✅ Payment addresses found using spaCy NER.")
                except Exception as e:
                    print(f"⚠️ spaCy extraction failed: {e}")

            # RAG + LLM fallback
            if use_llm and not matches:
                print(f"⚠️ No payment addresses found. Trying LLM fallback..." + (" (with RAG context)" if use_rag else " (no RAG context)"))
                
                try:
                    if use_rag:
                        retrieved_context = retrieve_context(text)
                        llm_results = llm_fallback_classify(text, retrieved_context)
                    else:
                        # LLM-only without RAG context
                        llm_results = llm_fallback_classify(text, "")
                    
                    matches.extend(llm_results)
                    if llm_results:
                        print("✅ Payment addresses found using LLM fallback." + (" (with RAG context)" if use_rag else " (no RAG context)"))
                except Exception as e:
                    print(f"❌ LLM fallback failed: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to extract from {file_path}: {e}")

    return list(filter(None, set(matches)))
