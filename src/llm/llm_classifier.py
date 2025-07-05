import os
import faiss
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# === Together.ai LLM ===
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"

client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === Knowledge base for RAG ===
knowledge_texts = [
    "Illicit marketplaces on the dark web include markets for drugs, weapons, counterfeit documents, and stolen data.",
    "Common fraud services: carding, SIM swapping, stolen PayPal accounts, fake IDs.",
    "Violence and extremist content often involves hitman services, extremist propaganda, and illegal firearms.",
    "Abuse materials include child exploitation and sexual abuse content.",
    "Hacking tools and guides include exploit kits, malware, ransomware-as-a-service, zero-day exploits.",
    "Counterfeit services involve forged passports, fake driver licenses, and fake government IDs."
]

# Embedding model
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

def classify_with_llm(html_text):
    if not TOGETHER_API_KEY:
        return "⚠️ No API Key found."

    # Retrieve RAG context first
    retrieved_context = retrieve_context(html_text)

    prompt = f"""
You are an AI forensic assistant helping to analyze HTML content extracted from dark web sources.

Use the following knowledge base context to help you summarize.

Knowledge base context:
{retrieved_context}

Please identify and summarize **any potentially illegal, suspicious, unethical, or harmful activity** mentioned in the following HTML. Focus on identifying categories such as:

- Illicit marketplaces
- Violence or extremist content
- Illegal services or offers
- Fraud, financial scams, or stolen data
- Weapons, drugs, counterfeit documents
- Abuse material or exploitation
- Hacking tools or guides

Only return **relevant category labels or very short descriptions**. If no suspicious content is detected, return "None".

HTML CONTENT:
{html_text[:2000]}
"""

    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error from LLM API: {str(e)}"
