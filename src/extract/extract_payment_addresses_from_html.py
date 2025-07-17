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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

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
    "Litecoin addresses start with L or M or ltc1.",
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

def extract_with_regex(text):
    """Extract payment addresses using regex patterns"""
    try:
        pattern = re.compile(payment_pattern, re.VERBOSE | re.IGNORECASE)
        matches = pattern.findall(text)
        return {"method": "regex", "results": matches, "success": True}
    except Exception as e:
        return {"method": "regex", "results": [], "success": False, "error": str(e)}

def extract_with_spacy(text):
    """Extract payment addresses using spaCy NER"""
    try:
        doc = nlp(text)
        matches = []
        for ent in doc.ents:
            if ent.label_ in ["MONEY", "CARDINAL"] and len(ent.text) > 10:
                matches.append(ent.text.strip())
        return {"method": "spacy", "results": matches, "success": True}
    except Exception as e:
        return {"method": "spacy", "results": [], "success": False, "error": str(e)}

def extract_with_llm_rag(text):
    """Extract payment addresses using LLM with RAG context"""
    try:
        retrieved_context = retrieve_context(text)
        prompt = f"""
You are an AI trained to detect cryptocurrency or payment addresses in text.

Use the following knowledge base context to help you.

Knowledge base context:
{retrieved_context}

Return only a single comma-separated list of payment addresses. 

⚠️ Do NOT include explanations, bullet points, parentheses, or comments. No other text.

TEXT:
{text[:2000]}
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        llm_output = response.choices[0].message.content.strip()
        raw_addresses = [addr.strip() for addr in llm_output.split(",") if addr.strip()]
        pattern = re.compile(payment_pattern, re.VERBOSE | re.IGNORECASE)
        filtered_addresses = [addr for addr in raw_addresses if pattern.fullmatch(addr)]
        return {"method": "llm_rag", "results": filtered_addresses, "success": True}
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_with_llm_only(text):
    """Extract payment addresses using LLM without RAG context"""
    try:
        prompt = f"""
You are an AI trained to detect cryptocurrency or payment addresses in text.

Return only a single comma-separated list of payment addresses. 

⚠️ Do NOT include explanations, bullet points, parentheses, or comments. No other text.

TEXT:
{text[:2000]}
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        llm_output = response.choices[0].message.content.strip()
        raw_addresses = [addr.strip() for addr in llm_output.split(",") if addr.strip()]
        pattern = re.compile(payment_pattern, re.VERBOSE | re.IGNORECASE)
        filtered_addresses = [addr for addr in raw_addresses if pattern.fullmatch(addr)]
        return {"method": "llm_only", "results": filtered_addresses, "success": True}
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def deduplicate_results(all_results):
    """Deduplicate results from multiple methods"""
    all_addresses = []
    method_results = {}
    
    for result in all_results:
        method = result["method"]
        addresses = result["results"]
        method_results[method] = addresses
        all_addresses.extend(addresses)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_addresses = []
    for addr in all_addresses:
        if addr not in seen:
            seen.add(addr)
            unique_addresses.append(addr)
    
    return {
        "unique_results": unique_addresses,
        "method_results": method_results,
        "total_found": len(unique_addresses)
    }

def extract_payment_addresses_from_html(file_path, use_llm=True, use_rag=True, use_ai=True, translate=True):
    """Extract payment addresses using parallel processing and deduplication"""
    
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

            # Define extraction methods to run
            extraction_methods = []
            
            # Always run regex (fastest and most reliable)
            extraction_methods.append(("regex", lambda: extract_with_regex(text)))
            
            # Add AI methods if enabled
            if use_ai:
                extraction_methods.append(("spacy", lambda: extract_with_spacy(text)))
            
            # Add LLM methods if enabled
            if use_llm:
                if use_rag:
                    extraction_methods.append(("llm_rag", lambda: extract_with_llm_rag(text)))
                extraction_methods.append(("llm_only", lambda: extract_with_llm_only(text)))

            # Run methods in parallel
            all_results = []
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=len(extraction_methods)) as executor:
                # Submit all tasks
                future_to_method = {
                    executor.submit(method_func): method_name 
                    for method_name, method_func in extraction_methods
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_method):
                    method_name = future_to_method[future]
                    try:
                        result = future.result()
                        all_results.append(result)
                        
                        if result["success"]:
                            print(f"✅ {method_name.upper()}: Found {len(result['results'])} addresses")
                        else:
                            print(f"❌ {method_name.upper()}: Failed - {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        print(f"❌ {method_name.upper()}: Exception - {str(e)}")
                        all_results.append({
                            "method": method_name,
                            "results": [],
                            "success": False,
                            "error": str(e)
                        })

            # Deduplicate results
            final_results = deduplicate_results(all_results)
            
            processing_time = time.time() - start_time
            print(f"⏱️ Parallel processing completed in {processing_time:.2f} seconds")
            print(f"🎯 Total unique addresses found: {final_results['total_found']}")
            
            # Show method comparison
            print("\n📊 Method Comparison:")
            for method, addresses in final_results["method_results"].items():
                print(f"  {method.upper()}: {len(addresses)} addresses")
            
            return final_results["unique_results"]

    except Exception as e:
        print(f"[ERROR] Failed to extract from {file_path}: {e}")
        return []
