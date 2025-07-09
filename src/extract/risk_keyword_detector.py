import os
import faiss
import numpy as np
from openai import OpenAI
from deep_translator import GoogleTranslator
from langdetect import detect
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# === LLM Client (Together.ai) ===
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === Hugging Face Zero-Shot Classifier ===
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# === Knowledge base for RAG ===
knowledge_texts = [
    "Common dark web crime keywords include: carding, dumps, fullz, cc, malware, exploit, 0day, botnet, ransomware, bulletproof hosting.",
    "Drugs keywords include: meth, cocaine, LSD, MDMA, fentanyl, prescription scam, darknet pharmacy.",
    "Weapons keywords include: guns, firearms, silencers, Glock, AK-47, ammo.",
    "Fraud keywords include: stolen PayPal accounts, fake IDs, forged passports, fake documents, SIM swapping.",
    "Vendors often use slang and hidden references to avoid detection."
]

# Embedding model for knowledge base
model = SentenceTransformer("all-MiniLM-L6-v2")
knowledge_embeddings = model.encode(knowledge_texts)
dimension = knowledge_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(knowledge_embeddings))

def retrieve_context(text, k=2):
    query_embedding = model.encode([text])
    distances, indices = index.search(np.array(query_embedding), k)
    retrieved_contexts = [knowledge_texts[i] for i in indices[0]]
    return "\n".join(retrieved_contexts)

def detect_risk_keywords_from_html(filepath, use_llm=True, use_rag=True, use_ai=True, translate=True):
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
                candidate_labels = [
                    "drugs", "weapons", "hacking", "fraud", "child abuse",
                    "fake documents", "exploit", "ransomware", "credit card dump",
                    "botnet", "hitman", "forged passport", "zero-day"
                ]
                result = zero_shot_classifier(html_text, candidate_labels=candidate_labels, multi_label=True)

                for label, score in zip(result["labels"], result["scores"]):
                    if score > 0.5:
                        found_keywords.append(label)

            # === RAG + LLM fallback ===
            if use_llm and use_rag and not found_keywords and TOGETHER_API_KEY:
                print("⚠️ No keywords found via AI. Trying RAG + LLM fallback...")

                retrieved_context = retrieve_context(html_text)

                prompt = f"""
You are an AI forensic assistant.

Use the following knowledge base context to help you analyze the HTML content and extract risky keywords.

Knowledge base context:
{retrieved_context}

Return only a single list of keywords separated by commas.

⚠️ Do NOT include any explanations, sentences, bullet points, or extra text. Only the keywords, nothing else.

HTML CONTENT:
{html_text[:2000]}
"""

                response = client.chat.completions.create(
                    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                llm_output = response.choices[0].message.content.strip()

                # Split by comma
                raw_keywords = [kw.strip() for kw in llm_output.split(",") if kw.strip()]

                # Extra cleanup: Remove any entries that look like sentences
                cleaned_keywords = [kw for kw in raw_keywords if " " not in kw and len(kw) < 30]

                found_keywords.extend(cleaned_keywords)

    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")

    return list(set(found_keywords))  # Remove duplicates
