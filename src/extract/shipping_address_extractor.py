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

# === Regex patterns for shipping/drop addresses ===
shipping_patterns = {
    'postal_address': [
        r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl|Court|Ct|Circle|Cir|Terrace|Ter)\b',
        r'\b[A-Za-z\s]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl|Court|Ct|Circle|Cir|Terrace|Ter)\s+\d+\b',
        r'\b\d+\s+[A-Za-z\s]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl|Court|Ct|Circle|Cir|Terrace|Ter)\b',
        r'\b[A-Za-z\s]+\s+\d+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl|Court|Ct|Circle|Cir|Terrace|Ter)\b',
    ],
    'drop_location': [
        r'\b(?:drop|delivery|pickup|meet|location|address)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:ship\s+to|deliver\s+to|send\s+to|mail\s+to)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:meet\s+at|pickup\s+at|collect\s+at)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:drop\s+off|delivery\s+point|pickup\s+point)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+)\b',
    ],
    'postal_code': [
        r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',  # UK postal codes
        r'\b\d{5}(?:-\d{4})?\b',  # US ZIP codes
        r'\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b',  # Canadian postal codes
        r'\b\d{4}\s?[A-Z]{2}\b',  # Dutch postal codes
        r'\b\d{5}\b',  # Generic 5-digit codes
    ],
    'city_state': [
        r'\b[A-Za-z\s]+\s*,\s*[A-Z]{2}\b',  # City, State format
        r'\b[A-Za-z\s]+\s*,\s*[A-Za-z\s]+\b',  # City, Country format
        r'\b[A-Za-z\s]+\s*,\s*\d{5}\b',  # City, ZIP format
    ],
    'coordinates': [
        r'\b\d+\.\d+,\s*\d+\.\d+\b',  # Decimal coordinates
        r'\b\d+°\s*\d+\'\s*\d+\.?\d*"[NS]\s*\d+°\s*\d+\'\s*\d+\.?\d*"[EW]\b',  # DMS coordinates
        r'\b(?:lat|latitude|lon|longitude)\s*[:\-]?\s*\d+\.\d+\b',  # Lat/Lon format
    ],
    'shipping_instructions': [
        r'\b(?:ship|deliver|send|mail|post)\s+(?:to|at|via)\s+([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:delivery|shipping|postal)\s+(?:address|location|point)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:meet|pickup|collect)\s+(?:at|in|near)\s+([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:drop|leave|place)\s+(?:at|in|near)\s+([A-Za-z0-9\s,\.\-]+)\b',
    ],
    'landmark_references': [
        r'\b(?:near|close\s+to|next\s+to|behind|in\s+front\s+of)\s+([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:landmark|reference|point)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:look\s+for|find|locate)\s+([A-Za-z0-9\s,\.\-]+)\b',
    ],
    'time_instructions': [
        r'\b(?:meet|pickup|deliver|drop)\s+(?:at|on|during)\s+([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:time|when|schedule)\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]+)\b',
        r'\b(?:available|open|ready)\s+(?:at|during|from)\s+([A-Za-z0-9\s,\.\-]+)\b',
    ]
}

# === Knowledge base for RAG ===
knowledge_texts = [
    "SHIPPING ADDRESSES: Dark web vendors often use hidden or coded addresses for physical delivery. Look for disguised postal addresses, drop locations, and meetup points.",
    "DROP LOCATIONS: Vendors may use landmarks, public places, or coded locations instead of direct addresses. Common drop points include parks, train stations, and shopping centers.",
    "DELIVERY INSTRUCTIONS: Vendors provide specific instructions for package pickup or delivery. Look for time-based instructions, landmark references, and safety protocols.",
    "PHYSICAL MEETUPS: Some vendors arrange face-to-face meetings for high-value items. Look for meeting points, time schedules, and identification methods.",
    "ADDRESS CODING: Vendors often use coded language to describe locations. Common patterns include 'near the old building', 'behind the station', or 'next to the red door'.",
    "SHIPPING METHODS: Vendors use various shipping methods including postal services, courier services, and hand delivery. Look for mentions of specific carriers or delivery methods.",
    "SAFETY PROTOCOLS: Vendors include safety instructions for package pickup. Look for phrases like 'discrete packaging', 'no signature required', or 'leave at door'.",
    "LANDMARK REFERENCES: Vendors often use landmarks instead of street addresses. Look for references to buildings, signs, trees, or other distinctive features.",
    "TIME-BASED DELIVERY: Vendors may specify exact times for pickup or delivery. Look for time windows, specific dates, or availability schedules.",
    "COORDINATES: Some vendors provide GPS coordinates instead of street addresses. Look for latitude/longitude pairs or coordinate references.",
    "POSTAL CODES: Vendors may provide only postal codes with additional instructions. Look for ZIP codes, postal codes, or area codes with location hints.",
    "PACKAGE INSTRUCTIONS: Vendors specify how packages should be handled. Look for instructions about packaging, labeling, or delivery preferences.",
    "MEETUP POINTS: Vendors arrange specific meeting points for hand delivery. Look for public places, landmarks, or coded locations.",
    "DELIVERY ZONES: Vendors may specify delivery areas or zones. Look for area names, district references, or zone descriptions.",
    "ALTERNATIVE ADDRESSES: Vendors provide backup addresses or alternative delivery points. Look for multiple address options or fallback locations."
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

def extract_shipping_addresses_with_regex(text):
    """Extract shipping addresses using regex patterns."""
    try:
        shipping_data = []
        
        for data_type, patterns in shipping_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Clean and validate the match
                    matched_text = match.group().strip()
                    if len(matched_text) > 5:  # Minimum length validation
                        shipping_data.append({
                            'type': data_type,
                            'content': matched_text,
                            'method': 'regex'
                        })
        
        return {"method": "regex", "results": shipping_data, "success": True}
    except Exception as e:
        return {"method": "regex", "results": [], "success": False, "error": str(e)}

def extract_shipping_addresses_with_ai(text):
    """Extract shipping addresses using Hugging Face AI model"""
    try:
        # Use StarPII for location entity detection
        result = hf_client.token_classification(text, model="bigcode/starpii")
        shipping_data = []
        
        for entity in result:
            if entity['entity_group'].lower() in ['loc', 'org', 'misc']:
                content = entity['word']
                # Check if it looks like a shipping address
                if re.search(r'\b(?:street|avenue|road|lane|drive|way|place|court|circle|terrace|st|ave|rd|ln|dr|pl|ct|cir|ter)\b', content, re.IGNORECASE):
                    shipping_data.append({
                        'type': 'postal_address',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.search(r'\b(?:drop|delivery|pickup|meet|location|address)\b', content, re.IGNORECASE):
                    shipping_data.append({
                        'type': 'drop_location',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.search(r'\b(?:ship|deliver|send|mail|post)\b', content, re.IGNORECASE):
                    shipping_data.append({
                        'type': 'shipping_instructions',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.match(r'^\d{5}(?:-\d{4})?$', content):
                    shipping_data.append({
                        'type': 'postal_code',
                        'content': content,
                        'method': 'ai'
                    })
        
        return {"method": "ai", "results": shipping_data, "success": True}
    except Exception as e:
        return {"method": "ai", "results": [], "success": False, "error": str(e)}

def extract_shipping_addresses_with_llm_rag(text):
    """Extract shipping addresses using LLM with RAG context"""
    try:
        retrieved_context = retrieve_context("shipping address delivery location drop", knowledge_texts)
        
        prompt = f"""
        You are an expert forensic analyst specializing in dark web shipping and delivery address extraction.
        
        KNOWLEDGE BASE:
        {retrieved_context}
        
        Extract shipping addresses, drop locations, and delivery instructions from the text.
        
        Look for:
        - Postal addresses (street names, numbers, cities)
        - Drop locations and meetup points
        - Delivery instructions and pickup locations
        - Landmark references and coded locations
        - Time-based delivery instructions
        - GPS coordinates
        - Postal codes with location hints
        - Safety protocols and packaging instructions
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of shipping-related items found.
        Format: type:content,type:content,type:content
        Examples: postal_address:123 Main Street,city_state:New York NY,drop_location:meet at the park
        """
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        shipping_data = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        shipping_data.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_rag'
                        })
        
        return {"method": "llm_rag", "results": shipping_data, "success": True}
        
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_shipping_addresses_with_llm_only(text):
    """Extract shipping addresses using LLM only."""
    try:
        prompt = f"""
        You are an expert forensic analyst. Extract shipping addresses and delivery locations from the text.
        
        Look for:
        - Postal addresses (street names, numbers, cities)
        - Drop locations and meetup points
        - Delivery instructions and pickup locations
        - Landmark references and coded locations
        - Time-based delivery instructions
        - GPS coordinates
        - Postal codes with location hints
        - Safety protocols and packaging instructions
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of shipping-related items found.
        Format: type:content,type:content,type:content
        Examples: postal_address:123 Main Street,city_state:New York NY,drop_location:meet at the park
        """
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        shipping_data = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        shipping_data.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_only'
                        })
        
        return {"method": "llm_only", "results": shipping_data, "success": True}
        
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def deduplicate_results(all_results):
    """Remove duplicate shipping address entries and organize by method."""
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

def clean_shipping_addresses(shipping_data, text_context=""):
    """Clean and validate shipping address data using dynamic validation."""
    # Use dynamic validator instead of static lists
    return dynamic_validator.validate_shipping_addresses(shipping_data, text_context)

def extract_shipping_addresses_from_html(file_path, use_llm=True, use_rag=True, use_ai=True, translate=True):
    """Extract shipping addresses using parallel processing and deduplication"""
    
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
            extraction_methods.append(("regex", lambda: extract_shipping_addresses_with_regex(text)))
            
            # Add AI methods if enabled
            if use_ai:
                extraction_methods.append(("ai", lambda: extract_shipping_addresses_with_ai(text)))
            
            # Add LLM methods if enabled
            if use_llm:
                if use_rag:
                    extraction_methods.append(("llm_rag", lambda: extract_shipping_addresses_with_llm_rag(text)))
                extraction_methods.append(("llm_only", lambda: extract_shipping_addresses_with_llm_only(text)))

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
                            print(f"✅ {method_name.upper()}: Found {len(result['results'])} shipping items")
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
            print(f"🎯 Total unique shipping items found: {final_results['total_found']}")
            
            # Show method comparison
            print("\n📊 Method Comparison:")
            for method, items in final_results["method_results"].items():
                print(f"  {method.upper()}: {len(items)} items")
            
            # Clean and validate results
            cleaned_results = clean_shipping_addresses(final_results["unique_results"], text)
            return cleaned_results

    except Exception as e:
        print(f"[ERROR] Failed to extract from {file_path}: {e}")
        return [] 