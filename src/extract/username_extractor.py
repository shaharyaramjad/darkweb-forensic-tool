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

# Load environment variables
load_dotenv()

# === Together.ai LLM ===
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=os.getenv("TOGETHER_API_KEY"),
)

# === Hugging Face client for AI model ===
hf_client = InferenceClient(
    provider="hf-inference",
    api_key="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",
)

# === Regex patterns for usernames/aliases ===
username_patterns = {
    'forum_username': [
        r'\b(?:user|username|handle|alias|nick|nickname|id|userid)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:posted\s+by|author|by|from)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:contact|message|pm|dm)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:vendor|seller|buyer|trader)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
    ],
    'social_media_style': [
        r'\b@([A-Za-z0-9_\-\.]{3,20})\b',  # Twitter/Instagram style
        r'\b(?:telegram|tg|signal|session)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:discord|discord\.gg)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:reddit|r/)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
    ],
    'cryptocurrency_style': [
        r'\b(?:btc|bitcoin|eth|ethereum|wallet)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:monero|xmr|privacy)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:crypto|cryptocurrency)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
    ],
    'dark_web_style': [
        r'\b(?:onion|tor|hidden|dark)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:market|forum|board)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:vendor|seller|buyer)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
    ],
    'gaming_style': [
        r'\b(?:gamer|player|steam|epic|origin)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:psn|xbox|nintendo)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:gaming|game)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
    ],
    'professional_style': [
        r'\b(?:admin|moderator|mod|staff|support)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:developer|dev|coder|hacker)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:security|sec|infosec)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
    ],
    'common_patterns': [
        r'\b([A-Za-z][A-Za-z0-9_\-\.]{2,19})\b',  # Starts with letter, 3-20 chars
        r'\b([A-Za-z0-9_\-\.]{3,20})\b',  # Any alphanumeric with underscore/dash/dot (but not starting with _)
        r'\b([A-Za-z0-9]{3,20})\b',  # Pure alphanumeric
    ],
    'quoted_usernames': [
        r'["\']([A-Za-z0-9_\-\.]{3,20})["\']',  # Usernames in quotes
        r'`([A-Za-z0-9_\-\.]{3,20})`',  # Usernames in code blocks
        r'\[([A-Za-z0-9_\-\.]{3,20})\]',  # Usernames in brackets
    ],
    'signature_style': [
        r'\b(?:signature|sig|contact)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:best\s+regards|sincerely|cheers)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
        r'\b(?:thanks|thx|ty)\s*[:\-]?\s*([A-Za-z0-9_\-\.]{3,20})\b',
    ]
}

# === Knowledge base for RAG ===
knowledge_texts = [
    "USERNAMES: Dark web users often use pseudonyms and aliases to maintain anonymity. Look for handles, usernames, and user IDs in forum posts and communications.",
    "FORUM HANDLES: Users on dark web forums typically have unique usernames or handles. These may appear in posts, signatures, or contact information.",
    "VENDOR ALIASES: Vendors often use consistent aliases across different platforms. Look for vendor names, seller IDs, and trader handles.",
    "SOCIAL MEDIA STYLE: Users may reference social media handles like @username or Telegram usernames. Look for @ symbols and platform-specific identifiers.",
    "CRYPTOCURRENCY HANDLES: Users may use cryptocurrency-related usernames or wallet identifiers. Look for BTC, ETH, or other crypto references.",
    "GAMING HANDLES: Some users adopt gaming-style usernames. Look for Steam, PSN, Xbox, or other gaming platform identifiers.",
    "PROFESSIONAL ALIASES: Users may use professional-sounding aliases like 'admin', 'moderator', 'developer', or 'hacker'.",
    "QUOTED USERNAMES: Usernames may appear in quotes, code blocks, or brackets. Look for special formatting around usernames.",
    "SIGNATURE USERNAMES: Users often include their username in forum signatures or contact information.",
    "CONTACT REFERENCES: Look for usernames in contact information, private messages, or communication channels.",
    "CROSS-PLATFORM TRACKING: The same username may appear across multiple platforms, forums, or marketplaces.",
    "ANONYMITY PATTERNS: Users may use patterns that suggest anonymity like 'anonymous', 'hidden', 'shadow', or 'ghost'.",
    "TECHNICAL HANDLES: Technical users may have handles related to their skills like 'coder', 'hacker', 'security', or 'dev'.",
    "MARKETPLACE IDS: Vendors on marketplaces often have unique vendor IDs or seller names.",
    "COMMUNICATION HANDLES: Users may reference their handles in private messages, emails, or other communication methods."
]

# Initialize sentence transformer and FAISS index
model = SentenceTransformer('all-MiniLM-L6-v2')
knowledge_embeddings = model.encode(knowledge_texts)
dimension = knowledge_embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(knowledge_embeddings.astype('float32'))

def retrieve_context(query, knowledge_texts, top_k=3):
    """Retrieve relevant context from knowledge base using FAISS."""
    try:
        # Encode query
        query_embedding = model.encode([query])
        
        # Search
        scores, indices = index.search(query_embedding.astype('float32'), top_k)
        
        # Return relevant context
        retrieved_context = []
        for idx in indices[0]:
            if idx < len(knowledge_texts):
                retrieved_context.append(knowledge_texts[idx])
        
        return ' '.join(retrieved_context)
    except Exception as e:
        print(f"Error in retrieve_context: {e}")
        return knowledge_texts[0]  # Fallback to first knowledge text

def extract_usernames_with_regex(text):
    """Extract usernames using regex patterns."""
    try:
        usernames = []
        
                # Common false positive words to exclude during extraction
        false_positives = {
            'web', 'market', 'place', 'information', 'contact', 'shipping',
            'delivery', 'payment', 'escrow', 'bitcoin', 'ethereum', 'monero',
            'telegram', 'signal', 'pgp', 'public', 'key', 'begin', 'end',
            'signature', 'encryption', 'required', 'for', 'all', 'communications',
            'tracking', 'available', 'premium', 'orders', 'financial', 'services',
            'swift', 'product', 'description', 'customer', 'feedback', 'support',
            'help', 'backup', 'username', 'vendor', 'reliable', 'secure',
            'anonymous', 'stealth', 'vacuum', 'seal', 'decoy', 'package',
            'packaging', 'items', 'included', 'primary', 'handle', 'dark',
            'cannabis', 'weed', 'sample', 'pack', 'illegal', 'contraband',
            'restricted', 'dangerous', 'prohibited', 'normally', 'days',
            'ereum', 'dot', 'nal', 'nature', 'here', 'best', 'around',
            # Financial terms that are not usernames
            'credit', 'card', 'cvv', 'expiry', 'iban', 'bank', 'account',
            'routing', 'document', 'buy', 'fake', 'passport', 'high', 'quality',
            'replica', 'driver', 'license', 'authentic', 'looking', 'sale',
            'underage', 'friendly', 'counterfeit', 'service', 'social', 'security',
            'number', 'dumps', 'fresh', 'stolen', 'access', 'money', 'laundering',
            # Address components
            'main', 'street', 'new', 'york', 'oak', 'avenue', 'los', 'angeles',
            'pine', 'road', 'chicago', 'elm', 'drive', 'miami', 'drop', 'locations',
            'central', 'park', 'near', 'fountain', 'pickup', 'grand', 'station',
            'times', 'square', 'brooklyn', 'bridge', 'empire', 'state', 'building',
            'gps', 'coordinates', 'latitude', 'longitude', 'zip', 'manhattan',
            'beverly', 'hills', 'loop', 'area', 'downtown', 'london', 'canada',
            'toronto', 'landmark', 'references', 'old', 'red', 'blue', 'door',
            'coffee', 'shop', 'tree', 'behind', 'station', 'yellow', 'mailbox',
            'clock', 'tower', 'square', 'time', 'based', 'instructions', 'sharp',
            'during', 'business', 'hours', 'between', 'schedule', 'monday', 'friday',
            'ready', 'daily', 'above', 'deliver', 'via', 'courier', 'service',
            'send', 'drop', 'location', 'mail', 'specified', 'post', 'given',
            'safety', 'protocols', 'discrete', 'leave', 'answer', 'use', 'plain',
            'return', 'needed', 'alternative', 'queens', 'ave', 'fallback', 'bronx',
            'coded', 'house', 'usual', 'spot', 'friendly', 'factory', 'green',
            'email', 'darkmarket', 'onion', 'block', 'deliveries', 'are', 'discrete',
            'questions', 'asked',
            # Additional common words that are not usernames
            'names', 'wallet', 'address', 'users', 'currency', 'alpha', 'vendor',
            'operator', 'web_user', 'identity', 'trader', 'wallet', 'user',
            'contact', 'signature', 'thanks', 'regards', 'sincerely', 'cheers',
            'thx', 'ty', 'best', 'formal', 'sig', 'crypto', 'cryptocurrency',
            'bitcoin', 'ethereum', 'monero', 'xmr', 'btc', 'eth', 'privacy',
            'market', 'forum', 'board', 'onion', 'tor', 'hidden', 'dark',
            'gamer', 'player', 'steam', 'epic', 'origin', 'psn', 'xbox', 'nintendo',
            'gaming', 'game', 'admin', 'moderator', 'mod', 'staff', 'support',
            'developer', 'dev', 'coder', 'hacker', 'security', 'sec', 'infosec',
            'professional', 'professional_style', 'quoted', 'quoted_usernames',
            'signature_style', 'forum_username', 'social_media_style',
            'cryptocurrency_style', 'dark_web_style', 'gaming_style'
        }
        
        for data_type, patterns in username_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Clean and validate the match
                    matched_text = match.group(1) if match.groups() else match.group()
                    if matched_text and len(matched_text) >= 3 and len(matched_text) <= 20:
                        # Skip known false positives
                        if matched_text.lower() in false_positives:
                            continue
                            
                        # Skip usernames that start with underscore (incomplete)
                        if matched_text.startswith('_'):
                            continue
                            
                        # Skip if it's just a common word
                        if len(matched_text) <= 4 and matched_text.lower() in ['name', 'help', 'ure', 'web', 'dot']:
                            continue
                            
                        # Skip if it's a fragment
                        if len(matched_text) <= 2:
                            continue
                            
                        # Skip if it's just numbers
                        if re.match(r'^\d+$', matched_text):
                            continue
                            
                        # Additional validation
                        if re.match(r'^[A-Za-z0-9_\-\.]+$', matched_text):
                            usernames.append({
                                'type': data_type,
                                'content': matched_text,
                                'method': 'regex'
                            })
        
        return {"method": "regex", "results": usernames, "success": True}
    except Exception as e:
        return {"method": "regex", "results": [], "success": False, "error": str(e)}

def extract_usernames_with_ai(text):
    """Extract usernames using Hugging Face AI model"""
    try:
        # Use StarPII for person entity detection
        result = hf_client.token_classification(text, model="bigcode/starpii")
        usernames = []
        
        for entity in result:
            if entity['entity_group'].lower() in ['person', 'misc', 'org']:
                content = entity['word']
                # Check if it looks like a username
                if re.match(r'^[A-Za-z0-9_\-\.]{3,20}$', content):
                    # Determine type based on context
                    if re.search(r'\b(?:user|username|handle|alias)\b', text[max(0, entity['start']-20):entity['start']], re.IGNORECASE):
                        username_type = 'forum_username'
                    elif content.startswith('@'):
                        username_type = 'social_media_style'
                    elif re.search(r'\b(?:vendor|seller|buyer)\b', text[max(0, entity['start']-20):entity['start']], re.IGNORECASE):
                        username_type = 'dark_web_style'
                    else:
                        username_type = 'common_patterns'
                    
                    usernames.append({
                        'type': username_type,
                        'content': content,
                        'method': 'ai'
                    })
        
        return {"method": "ai", "results": usernames, "success": True}
    except Exception as e:
        return {"method": "ai", "results": [], "success": False, "error": str(e)}

def extract_usernames_with_llm_rag(text):
    """Extract usernames using LLM with RAG context"""
    try:
        retrieved_context = retrieve_context("username alias handle pseudonym", knowledge_texts)
        
        prompt = f"""
        You are an expert forensic analyst specializing in dark web username and alias extraction.
        
        KNOWLEDGE BASE:
        {retrieved_context}
        
        Extract usernames, aliases, handles, and pseudonyms from the text.
        
        Look for:
        - Forum usernames and handles
        - Social media style usernames (@username)
        - Cryptocurrency related handles
        - Dark web vendor aliases
        - Gaming style usernames
        - Professional aliases (admin, moderator, etc.)
        - Quoted usernames in quotes or brackets
        - Signature usernames
        - Contact usernames
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of usernames found.
        Format: type:username,type:username,type:username
        Examples: forum_username:hitman123,social_media_style:@codex123,dark_web_style:vendor_alpha
        """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        usernames = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        usernames.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_rag'
                        })
        
        return {"method": "llm_rag", "results": usernames, "success": True}
        
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_usernames_with_llm_only(text):
    """Extract usernames using LLM only."""
    try:
        prompt = f"""
        You are an expert forensic analyst. Extract usernames, aliases, and handles from the text.
        
        Look for:
        - Forum usernames and handles
        - Social media style usernames (@username)
        - Cryptocurrency related handles
        - Dark web vendor aliases
        - Gaming style usernames
        - Professional aliases (admin, moderator, etc.)
        - Quoted usernames in quotes or brackets
        - Signature usernames
        - Contact usernames
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of usernames found.
        Format: type:username,type:username,type:username
        Examples: forum_username:hitman123,social_media_style:@codex123,dark_web_style:vendor_alpha
        """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        usernames = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        usernames.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_only'
                        })
        
        return {"method": "llm_only", "results": usernames, "success": True}
        
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def deduplicate_results(all_results):
    """Remove duplicate username entries and organize by method."""
    seen = set()
    unique_results = []
    method_results = {}
    
    for result in all_results:
        method = result["method"]
        method_results[method] = []
        
        for item in result["results"]:
            # Create a unique identifier for each item
            identifier = f"{item['type']}:{item['content']}"
            if identifier not in seen:
                seen.add(identifier)
                unique_results.append(item)
                method_results[method].append(item)
    
    return {
        "unique_results": unique_results,
        "method_results": method_results,
        "total_found": len(unique_results)
    }

from src.extract.dynamic_validator import dynamic_validator

def clean_usernames(username_data, text_context=""):
    """Clean and validate username data using dynamic validation."""
    # Use dynamic validator instead of static lists
    return dynamic_validator.validate_usernames(username_data, text_context)

def extract_usernames_from_html(file_path, use_llm=True, use_rag=True, use_ai=True, translate=True):
    """Extract usernames using parallel processing and deduplication"""
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()

            # Detect suspicious prompt injection attempts
            suspicious = detect_suspicious_prompts(content)
            if suspicious:
                print(f"⚠️ Suspicious prompt injection detected in {file_path}: {suspicious}")

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
            extraction_methods.append(("regex", lambda: extract_usernames_with_regex(text)))
            
            # Add AI methods if enabled
            if use_ai:
                extraction_methods.append(("ai", lambda: extract_usernames_with_ai(text)))
            
            # Add LLM methods if enabled
            if use_llm:
                if use_rag:
                    extraction_methods.append(("llm_rag", lambda: extract_usernames_with_llm_rag(text)))
                extraction_methods.append(("llm_only", lambda: extract_usernames_with_llm_only(text)))

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
                            print(f"✅ {method_name.upper()}: Found {len(result['results'])} usernames")
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
            print(f"🎯 Total unique usernames found: {final_results['total_found']}")
            
            # Show method comparison
            print("\n📊 Method Comparison:")
            for method, items in final_results["method_results"].items():
                print(f"  {method.upper()}: {len(items)} items")
            
            # Clean and validate results
            cleaned_results = clean_usernames(final_results["unique_results"], text)
            return cleaned_results

    except Exception as e:
        print(f"[ERROR] Failed to extract from {file_path}: {e}")
        return [] 