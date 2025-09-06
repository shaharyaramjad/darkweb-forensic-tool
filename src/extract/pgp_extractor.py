import re
import os
import faiss
import numpy as np
from bs4 import BeautifulSoup
from langdetect import detect
from deep_translator import GoogleTranslator
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from src.extract.utils_visible_text import detect_suspicious_prompts
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# === Together.ai LLM ===
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === Hugging Face client for AI model ===
hf_client = InferenceClient(
    provider="hf-inference",
    api_key="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",
)

# === Regex patterns for PGP keys and blocks ===
pgp_patterns = {
    'public_key_block': [
        r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----',
        r'-----BEGIN PGP PUBLIC KEY-----[\s\S]*?-----END PGP PUBLIC KEY-----',
        r'-----BEGIN PUBLIC KEY-----[\s\S]*?-----END PUBLIC KEY-----'
    ],
    'private_key_block': [
        r'-----BEGIN PGP PRIVATE KEY BLOCK-----[\s\S]*?-----END PGP PRIVATE KEY BLOCK-----',
        r'-----BEGIN PGP SECRET KEY-----[\s\S]*?-----END PGP SECRET KEY-----',
        r'-----BEGIN PRIVATE KEY-----[\s\S]*?-----END PRIVATE KEY-----'
    ],
    'encrypted_message': [
        r'-----BEGIN PGP MESSAGE-----[\s\S]*?-----END PGP MESSAGE-----',
        r'-----BEGIN PGP ENCRYPTED MESSAGE-----[\s\S]*?-----END PGP ENCRYPTED MESSAGE-----',
        r'-----BEGIN ENCRYPTED MESSAGE-----[\s\S]*?-----END ENCRYPTED MESSAGE-----'
    ],
    'signature': [
        r'-----BEGIN PGP SIGNATURE-----[\s\S]*?-----END PGP SIGNATURE-----',
        r'-----BEGIN SIGNATURE-----[\s\S]*?-----END SIGNATURE-----'
    ],
    'armored_key': [
        r'-----BEGIN PGP ARMORED FILE-----[\s\S]*?-----END PGP ARMORED FILE-----',
        r'-----BEGIN ARMORED FILE-----[\s\S]*?-----END ARMORED FILE-----'
    ],
    'key_id': [
        r'\b[A-F0-9]{8}\b',  # 8-character key ID
        r'\b[A-F0-9]{16}\b',  # 16-character key ID
        r'\b[A-F0-9]{40}\b',  # 40-character fingerprint
        r'Key ID: [A-F0-9]{8,16}',
        r'Fingerprint: [A-F0-9]{40}'
    ],
    'pgp_mentions': [
        r'\bPGP\b',
        r'\bGPG\b',
        r'\bGnuPG\b',
        r'\bPretty Good Privacy\b',
        r'\bencrypted communication\b',
        r'\bsecure messaging\b',
        r'\bpublic key\b',
        r'\bprivate key\b',
        r'\bkey exchange\b',
        r'\bend-to-end encryption\b',
        r'\bzero-knowledge\b',
        r'\bencrypt\b',
        r'\bdecrypt\b',
        r'\bsign\b',
        r'\bverify\b',
        r'\bkeyring\b',
        r'\bkey server\b',
        r'\bkeyserver\b',
        r'\bpgp\.mit\.edu\b',
        r'\bkeys\.openpgp\.org\b',
        r'\bpgpkeys\.pca\.dfn\.de\b'
    ],
    'contact_info': [
        r'Contact:.*?PGP',
        r'PGP.*?Contact',
        r'Email.*?PGP',
        r'PGP.*?Email',
        r'Key:.*?[A-F0-9]{8,40}',
        r'Fingerprint:.*?[A-F0-9]{40}',
        r'Public Key:.*?[A-F0-9]{8,40}'
    ]
}

# === Knowledge base for RAG ===
knowledge_texts = [
    "PGP (Pretty Good Privacy) is commonly used on dark web marketplaces for secure communication between vendors and buyers.",
    "Dark web vendors often include their PGP public key in vendor profiles or contact information.",
    "PGP keys are typically displayed in armored format with BEGIN and END markers.",
    "Common PGP key formats include: -----BEGIN PGP PUBLIC KEY BLOCK----- and -----END PGP PUBLIC KEY BLOCK-----.",
    "Vendors may include PGP fingerprints (40-character hex strings) for key verification.",
    "PGP is used for encrypted messaging, file encryption, and digital signatures on dark web platforms.",
    "Look for PGP keys in vendor profiles, contact pages, or communication instructions.",
    "Dark web users often mention 'PGP', 'GPG', or 'encrypted communication' when discussing secure messaging.",
    "PGP keys may be embedded in HTML comments or hidden elements to avoid detection.",
    "Vendors sometimes provide PGP key IDs (8 or 16 character hex strings) for easy lookup.",
    "PGP encrypted messages are often shared in base64 encoded format with armor headers.",
    "Dark web marketplaces often require PGP verification for vendor accounts.",
    "Look for mentions of 'secure communication', 'encrypted messaging', or 'PGP only' in vendor descriptions.",
    "PGP keys may be split across multiple lines or obfuscated to avoid automated detection.",
    "Vendors often provide PGP contact information alongside other communication methods like email or messaging apps."
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

def extract_pgp_with_regex(text):
    """Extract PGP content using regex patterns"""
    try:
        results = []
        for category, patterns in pgp_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    results.append({
                        'type': category,
                        'content': match.strip(),
                        'method': 'regex'
                    })
        return {"method": "regex", "results": results, "success": True}
    except Exception as e:
        return {"method": "regex", "results": [], "success": False, "error": str(e)}

def extract_pgp_with_llm_rag(text):
    """Extract PGP content using LLM with RAG context"""
    try:
        retrieved_context = retrieve_context(text)
        prompt = f"""
You are an AI trained to detect PGP (Pretty Good Privacy) keys, encrypted messages, and related content in dark web pages.

Knowledge base context:
{retrieved_context}

HTML CONTENT:
{text}

Return a JSON array of PGP-related items found. For each item, include:
- type: "public_key", "private_key", "encrypted_message", "signature", "key_id", "mention", or "contact_info"
- content: the actual PGP content or mention
- confidence: "high", "medium", or "low"

Format: [{{"type": "...", "content": "...", "confidence": "..."}}]

Return only the JSON array, no other text.
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        llm_output = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            import json
            results = json.loads(llm_output)
            if isinstance(results, list):
                return {"method": "llm_rag", "results": results, "success": True}
        except:
            pass
        
        # Fallback: extract any PGP-like content from LLM response
        pgp_indicators = re.findall(r'(PGP|GPG|-----BEGIN|-----END|Key ID|Fingerprint)', llm_output, re.IGNORECASE)
        if pgp_indicators:
            return {"method": "llm_rag", "results": [{"type": "mention", "content": llm_output, "confidence": "medium"}], "success": True}
        
        return {"method": "llm_rag", "results": [], "success": True}
        
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_pgp_with_llm_only(text):
    """Extract PGP content using LLM without RAG context"""
    try:
        prompt = f"""
Analyze this HTML content and extract any PGP (Pretty Good Privacy) related information.

Look for:
- PGP public/private key blocks
- Encrypted messages
- Digital signatures
- Key IDs or fingerprints
- Mentions of PGP, GPG, or encrypted communication
- Contact information with PGP keys

HTML CONTENT:
{text}

Return a JSON array of PGP-related items found. For each item, include:
- type: "public_key", "private_key", "encrypted_message", "signature", "key_id", "mention", or "contact_info"
- content: the actual PGP content or mention
- confidence: "high", "medium", or "low"

Format: [{{"type": "...", "content": "...", "confidence": "..."}}]

Return only the JSON array, no other text.
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        llm_output = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            import json
            results = json.loads(llm_output)
            if isinstance(results, list):
                return {"method": "llm_only", "results": results, "success": True}
        except:
            pass
        
        # Fallback: extract any PGP-like content from LLM response
        pgp_indicators = re.findall(r'(PGP|GPG|-----BEGIN|-----END|Key ID|Fingerprint)', llm_output, re.IGNORECASE)
        if pgp_indicators:
            return {"method": "llm_only", "results": [{"type": "mention", "content": llm_output, "confidence": "medium"}], "success": True}
        
        return {"method": "llm_only", "results": [], "success": True}
        
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def extract_pgp_with_ai(text):
    """Extract PGP content using Hugging Face AI model"""
    try:
        # Use StarPII for PII detection to find potential PGP-related entities
        result = hf_client.token_classification(text, model="bigcode/starpii")
        pgp_data = []
        
        for entity in result:
            if entity['entity_group'].lower() in ['org', 'misc']:
                content = entity['word']
                # Check if it looks like PGP content
                if re.search(r'\b(?:PGP|GPG|-----BEGIN|-----END|Key ID|Fingerprint)\b', content, re.IGNORECASE):
                    pgp_data.append({
                        'type': 'mention',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.match(r'^[A-F0-9]{8,40}$', content, re.IGNORECASE):
                    # Looks like a key ID or fingerprint
                    pgp_data.append({
                        'type': 'key_id',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.search(r'-----BEGIN.*-----', content):
                    # Looks like PGP armor
                    pgp_data.append({
                        'type': 'public_key',
                        'content': content,
                        'method': 'ai'
                    })
        
        return {"method": "ai", "results": pgp_data, "success": True}
    except Exception as e:
        return {"method": "ai", "results": [], "success": False, "error": str(e)}

def deduplicate_results(all_results):
    """Deduplicate PGP results across different methods"""
    seen_content = set()
    unique_results = []
    
    for result in all_results:
        if result.get('content'):
            # Normalize content for comparison
            normalized = re.sub(r'\s+', ' ', result['content'].strip())
            if normalized not in seen_content:
                seen_content.add(normalized)
                unique_results.append(result)
    
    return unique_results

def clean_pgp_content(pgp_list):
    """Clean and validate PGP content"""
    cleaned = []
    
    for item in pgp_list:
        if not item.get('content'):
            continue
            
        content = item['content'].strip()
        pgp_type = item.get('type', 'unknown')
        
        # Validate PGP content based on type
        if pgp_type in ['public_key', 'private_key', 'encrypted_message', 'signature']:
            if '-----BEGIN' in content and '-----END' in content:
                cleaned.append(item)
        elif pgp_type == 'key_id':
            if re.match(r'^[A-F0-9]{8,40}$', content, re.IGNORECASE):
                cleaned.append(item)
        elif pgp_type in ['mention', 'contact_info']:
            if any(keyword in content.upper() for keyword in ['PGP', 'GPG', 'ENCRYPT', 'KEY']):
                cleaned.append(item)
    
    return cleaned

def extract_pgp_from_html(filepath, use_llm=True, use_rag=True, use_ai=True, translate=True):
    """
    Extract PGP content from HTML file using multiple methods
    
    Args:
        filepath (str): Path to HTML file
        use_llm (bool): Use LLM for extraction
        use_rag (bool): Use RAG-enhanced LLM
        use_ai (bool): Use AI models (placeholder for future)
        translate (bool): Translate non-English content
    
    Returns:
        list: List of extracted PGP items
    """
    print(f"🔐 Extracting PGP content from: {filepath}")
    
    try:
        # Read HTML file
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator=' ')
        
        # Detect language and translate if needed
        if translate:
            try:
                detected_lang = detect(text_content[:1000])
                if detected_lang != 'en':
                    print(f"🌐 Detected language: {detected_lang}, translating...")
                    translator = GoogleTranslator(source=detected_lang, target='en')
                    text_content = translator.translate(text_content)
            except Exception as e:
                print(f"⚠️ Translation failed: {e}")
        
        # Collect results from different methods using parallel execution
        all_results = []
        
        # Define extraction tasks
        extraction_tasks = []
        
        # Task 1: Regex extraction (always runs)
        extraction_tasks.append(("regex", lambda: extract_pgp_with_regex(text_content)))
        
        # Task 2: AI model extraction (if enabled)
        if use_ai:
            extraction_tasks.append(("ai", lambda: extract_pgp_with_ai(text_content)))
        
        # Task 3: LLM with RAG (if enabled)
        if use_llm and use_rag:
            extraction_tasks.append(("llm_rag", lambda: extract_pgp_with_llm_rag(text_content)))
        
        # Task 4: LLM only (if enabled and RAG is not)
        elif use_llm:
            extraction_tasks.append(("llm_only", lambda: extract_pgp_with_llm_only(text_content)))
        
        # Run all tasks in parallel
        print(f"🚀 Running {len(extraction_tasks)} extraction methods in parallel...")
        
        with ThreadPoolExecutor(max_workers=len(extraction_tasks)) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(task_func): task_name 
                for task_name, task_func in extraction_tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result()
                    if result['success']:
                        all_results.extend(result['results'])
                        print(f"✅ {task_name.upper()} found {len(result['results'])} items")
                    else:
                        print(f"❌ {task_name.upper()} extraction failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ {task_name.upper()} extraction failed with exception: {e}")
        
        # Deduplicate and clean results
        unique_results = deduplicate_results(all_results)
        cleaned_results = clean_pgp_content(unique_results)
        
        print(f"🎯 Final PGP extraction results: {len(cleaned_results)} unique items")
        
        return cleaned_results
        
    except Exception as e:
        print(f"❌ PGP extraction failed: {e}")
        return [] 