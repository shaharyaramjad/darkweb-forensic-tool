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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from src.extract.utils_visible_text import detect_suspicious_prompts

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

def extract_emails_with_regex(text):
    """Extract emails using regex patterns"""
    try:
        normal = generic_email_re.findall(text)
        obfuscated = [f"{m[0]}@{m[1]}.{m[2]}" for m in obfuscated_email_re.findall(text)]
        return {"method": "regex", "results": normal + obfuscated, "success": True}
    except Exception as e:
        return {"method": "regex", "results": [], "success": False, "error": str(e)}

def extract_emails_with_starpii(text):
    """Extract emails using StarPII AI model"""
    try:
        result = pii_client.token_classification(text, model="bigcode/starpii")
        emails = []
        for entity in result:
            if entity['entity_group'].lower() == 'email':
                emails.append(entity['word'])
        return {"method": "starpii", "results": emails, "success": True}
    except Exception as e:
        return {"method": "starpii", "results": [], "success": False, "error": str(e)}

def extract_emails_with_llm_rag(text):
    """Extract emails using LLM with RAG context"""
    try:
        retrieved_context = retrieve_context(text)
        llm_prompt = f"""
Use the following knowledge base context to help you find suspicious or hidden email addresses.

Knowledge base context:
{retrieved_context}

HTML CONTENT:
{text}

Return a comma-separated list of email addresses only.
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": llm_prompt}],
            temperature=0.1,
        )
        llm_output = response.choices[0].message.content.strip()
        llm_emails = [email.strip() for email in llm_output.split(",") if email.strip()]
        return {"method": "llm_rag", "results": llm_emails, "success": True}
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_emails_with_llm_only(text):
    """Extract emails using LLM without RAG context"""
    try:
        llm_prompt = f"""
HTML CONTENT:
{text}

Return a comma-separated list of email addresses only.
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": llm_prompt}],
            temperature=0.1,
        )
        llm_output = response.choices[0].message.content.strip()
        llm_emails = [email.strip() for email in llm_output.split(",") if email.strip()]
        return {"method": "llm_only", "results": llm_emails, "success": True}
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def deduplicate_results(all_results):
    """Deduplicate results from multiple methods"""
    all_emails = []
    method_results = {}
    
    for result in all_results:
        method = result["method"]
        emails = result["results"]
        method_results[method] = emails
        all_emails.extend(emails)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in all_emails:
        if email not in seen:
            seen.add(email)
            unique_emails.append(email)
    
    return {
        "unique_results": unique_emails,
        "method_results": method_results,
        "total_found": len(unique_emails)
    }

def clean_emails(email_list):
    cleaned = []
    for email in email_list:
        # Remove markdown links
        if re.match(r'^\[.*\]\(.*\)$', email):
            continue
        # Remove explanations or sentences
        if any(phrase in email.lower() for phrase in [
            'i have', 'as well as', 'can be used', 'certain contexts', 'why', 'included', 'note that', 'these are not', 'however', 'please note', 'assuming that', 'crooks', 'email addresses found in the bitcoin', 'monero addresses']):
            continue
        # Remove emails with spaces or too long
        if ' ' in email or len(email) > 60:
            continue
        # Remove crypto-address-like emails
        local = email.split('@')[0]
        if re.match(r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,}', local):
            continue
        if email.endswith('@bitcoinmail.org') or email.endswith('@moneromail.org'):
            continue
        cleaned.append(email)
    return cleaned

def extract_emails_from_html(filepath, use_ai=True, use_llm=True, translate=True, use_rag=True):
    """Extract emails using parallel processing and deduplication"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        # Detect suspicious prompt injection attempts
        suspicious = detect_suspicious_prompts(html)
        if suspicious:
            print(f"⚠️ Suspicious prompt injection detected in {filepath}: {suspicious}")
            # Optionally, you could log or return this for reporting

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

        # Define extraction methods to run
        extraction_methods = []
        
        # Always run regex (fastest and most reliable)
        extraction_methods.append(("regex", lambda: extract_emails_with_regex(translated_text)))
        
        # Add AI methods if enabled
        if use_ai:
            extraction_methods.append(("starpii", lambda: extract_emails_with_starpii(translated_text)))
        
        # Add LLM methods if enabled
        if use_llm:
            if use_rag:
                extraction_methods.append(("llm_rag", lambda: extract_emails_with_llm_rag(translated_text)))
            extraction_methods.append(("llm_only", lambda: extract_emails_with_llm_only(translated_text)))

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
                        print(f"✅ {method_name.upper()}: Found {len(result['results'])} emails")
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
        print(f"🎯 Total unique emails found: {final_results['total_found']}")
        
        # Show method comparison
        print("\n📊 Method Comparison:")
        for method, emails in final_results["method_results"].items():
            print(f"  {method.upper()}: {len(emails)} emails")
        
        # Clean emails before returning
        cleaned_emails = clean_emails(final_results["unique_results"])
        return cleaned_emails
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return []
