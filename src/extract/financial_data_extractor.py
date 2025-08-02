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

# === Hugging Face client for AI model ===
hf_client = InferenceClient(
    provider="hf-inference",
    api_key="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",
)

# Financial data patterns
financial_patterns = {
    'credit_card': [
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',  # Major card networks
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Generic 16-digit pattern
        r'\b\d{4}[- ]?\d{6}[- ]?\d{5}\b',  # 15-digit pattern (Amex)
    ],
    'cvv': [
        r'\bCVV[:\s]*(\d{3,4})\b',
        r'\bCVC[:\s]*(\d{3,4})\b',
        r'\bCV2[:\s]*(\d{3,4})\b',
        r'\bCVV2[:\s]*(\d{3,4})\b',
        r'\b(\d{3,4})\s*(?:CVV|CVC|CV2|CVV2)\b',
    ],
    'expiry_date': [
        r'\b(?:0[1-9]|1[0-2])/(?:2[0-9]|3[0-9])\b',  # MM/YY format
        r'\b(?:0[1-9]|1[0-2])/(?:20[2-9][0-9])\b',   # MM/YYYY format
        r'\b(?:2[0-9]|3[0-9])/(?:0[1-9]|1[0-2])\b',  # YY/MM format
        r'\b(?:20[2-9][0-9])/(?:0[1-9]|1[0-2])\b',   # YYYY/MM format
        r'\bexp(?:iry)?[:\s]*(?:0[1-9]|1[0-2])/(?:2[0-9]|3[0-9])\b',
    ],
    'iban': [
        r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b',  # IBAN pattern
        r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}[A-Z0-9]{0,16}\b',  # Alternative IBAN
    ],
    'swift_code': [
        r'\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b',  # SWIFT/BIC code
        r'\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?\b',  # Alternative SWIFT
    ],
    'bank_account': [
        r'\b(?:account|acc|acct)[:\s]*(\d{8,17})\b',
        r'\b(?:routing|routing number|aba)[:\s]*(\d{9})\b',
        r'\b(?:sort code)[:\s]*(\d{2}-\d{2}-\d{2})\b',
    ]
}

# Knowledge base for financial data detection
knowledge_texts = [
    "FINANCIAL DATA: credit card, debit card, visa, mastercard, american express, discover, jcb, diners club, card number, cardholder name, billing address, cvv, cvc, cvv2, security code, expiry date, expiration, valid thru, valid through, issue date, card type, card brand, card issuer, bank name, account number, routing number, aba number, sort code, iban, swift code, bic code, bank identifier, financial institution, payment method, payment details, billing information, card verification, card validation, card authentication, card security, card protection, card fraud, card theft, card cloning, card skimming, card phishing, card scam",
    "PAYMENT METHODS: credit card payment, debit card payment, online payment, digital payment, electronic payment, card payment, bank transfer, wire transfer, swift transfer, iban transfer, direct debit, standing order, recurring payment, subscription payment, membership payment, service payment, product payment, order payment, purchase payment, transaction payment, financial transaction, monetary transaction, payment processing, payment gateway, payment processor, payment service, payment platform, payment system, payment solution, payment method, payment option, payment choice, payment preference, payment selection, payment decision, payment agreement, payment terms, payment conditions, payment requirements, payment specifications, payment details, payment information, payment data, payment records, payment history, payment log, payment trail, payment audit, payment verification, payment validation, payment confirmation, payment receipt, payment proof, payment evidence, payment documentation, payment paperwork, payment forms, payment applications, payment requests, payment orders, payment instructions, payment directions, payment guidelines, payment rules, payment regulations, payment laws, payment policies, payment procedures, payment protocols, payment standards, payment practices, payment customs, payment traditions, payment conventions, payment norms, payment expectations, payment requirements, payment demands, payment needs, payment wants, payment desires, payment preferences, payment choices, payment decisions, payment agreements, payment contracts, payment deals, payment arrangements, payment setups, payment configurations, payment settings, payment options, payment alternatives, payment substitutes, payment replacements, payment backups, payment reserves, payment spares, payment extras, payment additions, payment supplements, payment complements, payment enhancements, payment improvements, payment upgrades, payment modifications, payment changes, payment adjustments, payment alterations, payment variations, payment differences, payment distinctions, payment contrasts, payment comparisons, payment evaluations, payment assessments, payment reviews, payment examinations, payment inspections, payment checks, payment verifications, payment validations, payment confirmations, payment approvals, payment authorizations, payment permissions, payment consents, payment agreements, payment acceptances, payment acknowledgments, payment recognitions, payment understandings, payment comprehensions, payment grasps, payment holds, payment grips, payment clutches, payment grasps, payment seizes, payment captures, payment catches, payment traps, payment snares, payment nets, payment webs, payment meshes, payment grids, payment networks, payment systems, payment structures, payment frameworks, payment foundations, payment bases, payment grounds, payment roots, payment sources, payment origins, payment beginnings, payment starts, payment initiations, payment launches, payment commencements, payment openings, payment introductions, payment presentations, payment displays, payment shows, payment exhibits, payment demonstrations, payment illustrations, payment examples, payment instances, payment cases, payment situations, payment circumstances, payment conditions, payment states, payment statuses, payment positions, payment locations, payment places, payment sites, payment venues, payment arenas, payment stages, payment platforms, payment bases, payment foundations, payment grounds, payment roots, payment sources, payment origins, payment beginnings, payment starts, payment initiations, payment launches, payment commencements, payment openings, payment introductions, payment presentations, payment displays, payment shows, payment exhibits, payment demonstrations, payment illustrations, payment examples, payment instances, payment cases, payment situations, payment circumstances, payment conditions, payment states, payment statuses, payment positions, payment locations, payment places, payment sites, payment venues, payment arenas, payment stages, payment platforms"
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

def extract_financial_data_with_regex(text):
    """Extract financial data using regex patterns."""
    try:
        financial_data = []
        
        for data_type, patterns in financial_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Clean and validate the match
                    matched_text = match.group().strip()
                    if len(matched_text) > 3:  # Minimum length validation
                        financial_data.append({
                            'type': data_type,
                            'content': matched_text,
                            'method': 'regex'
                        })
        
        return {"method": "regex", "results": financial_data, "success": True}
    except Exception as e:
        return {"method": "regex", "results": [], "success": False, "error": str(e)}

def extract_financial_data_with_llm_rag(text):
    """Extract financial data using LLM with RAG."""
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url="https://api.together.xyz/v1"
        )
        
        # Retrieve relevant context
        retrieved_context = retrieve_context("financial data credit card payment", knowledge_texts)
        
        prompt = f"""
        You are an expert financial forensic analyst. Extract ONLY financial data patterns from the text.
        
        KNOWLEDGE BASE (use these as examples to find similar financial terms):
        {retrieved_context}
        
        FOCUS ONLY on:
        - Credit card numbers (16 digits, 15 digits for Amex)
        - CVV/CVC codes (3-4 digits)
        - Expiry dates (MM/YY, MM/YYYY formats)
        - IBAN codes (international bank account numbers)
        - SWIFT/BIC codes (bank identifier codes)
        - Bank account numbers
        - Routing numbers
        
        DO NOT include:
        - General numbers that aren't financial
        - Phone numbers
        - Addresses
        - General text
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of financial data found.
        Format: type:content,type:content,type:content
        Examples: credit_card:4111111111111111,cvv:123,expiry:12/25
        """
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        financial_data = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        financial_data.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_rag'
                        })
        
        return {"method": "llm_rag", "results": financial_data, "success": True}
        
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_financial_data_with_llm_only(text):
    """Extract financial data using LLM only."""
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url="https://api.together.xyz/v1"
        )
        
        prompt = f"""
        You are an expert financial forensic analyst. Extract financial data patterns from the text.
        
        Look for:
        - Credit card numbers (16 digits, 15 digits for Amex)
        - CVV/CVC codes (3-4 digits)
        - Expiry dates (MM/YY, MM/YYYY formats)
        - IBAN codes (international bank account numbers)
        - SWIFT/BIC codes (bank identifier codes)
        - Bank account numbers
        - Routing numbers
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of financial data found.
        Format: type:content,type:content,type:content
        Examples: credit_card:4111111111111111,cvv:123,expiry:12/25
        """
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        financial_data = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        financial_data.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_only'
                        })
        
        return {"method": "llm_only", "results": financial_data, "success": True}
        
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def extract_financial_data_with_ai(text):
    """Extract financial data using Hugging Face AI model"""
    try:
        # Use a financial NER model or zero-shot classification
        result = hf_client.token_classification(text, model="bigcode/starpii")
        financial_data = []
        
        for entity in result:
            if entity['entity_group'].lower() in ['cardinal', 'money', 'org']:
                # Check if it looks like financial data
                content = entity['word']
                if re.match(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', content):  # Credit card
                    financial_data.append({
                        'type': 'credit_card',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.match(r'\b\d{3,4}\b', content) and len(content) in [3, 4]:  # CVV
                    financial_data.append({
                        'type': 'cvv',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.match(r'\b(?:0[1-9]|1[0-2])/(?:2[0-9]|3[0-9])\b', content):  # Expiry
                    financial_data.append({
                        'type': 'expiry_date',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.match(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b', content):  # IBAN
                    financial_data.append({
                        'type': 'iban',
                        'content': content,
                        'method': 'ai'
                    })
                elif re.match(r'\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b', content):  # SWIFT
                    financial_data.append({
                        'type': 'swift_code',
                        'content': content,
                        'method': 'ai'
                    })
        
        return {"method": "ai", "results": financial_data, "success": True}
    except Exception as e:
        return {"method": "ai", "results": [], "success": False, "error": str(e)}

def deduplicate_results(all_results):
    """Remove duplicate financial data entries and organize by method."""
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

def clean_financial_data(financial_data):
    """Clean and validate financial data."""
    cleaned_data = []
    
    for item in financial_data:
        content = item['content']
        data_type = item['type']
        
        # Basic validation based on type
        if data_type == 'credit_card':
            # Remove spaces and dashes, validate length
            cleaned = re.sub(r'[^\d]', '', content)
            if len(cleaned) in [13, 15, 16] and cleaned.isdigit():
                item['content'] = cleaned
                cleaned_data.append(item)
        
        elif data_type == 'cvv':
            # Validate CVV length
            cleaned = re.sub(r'[^\d]', '', content)
            if len(cleaned) in [3, 4] and cleaned.isdigit():
                item['content'] = cleaned
                cleaned_data.append(item)
        
        elif data_type == 'expiry_date':
            # Validate date format
            if re.match(r'^(0[1-9]|1[0-2])/(2[0-9]|3[0-9]|20[2-9][0-9])$', content):
                cleaned_data.append(item)
        
        elif data_type in ['iban', 'swift_code']:
            # Validate format
            if len(content) >= 8:
                cleaned_data.append(item)
        
        else:
            # For other types, just add if not empty
            if content.strip():
                cleaned_data.append(item)
    
    return cleaned_data

def extract_financial_data_from_html(file_path, use_llm=True, use_rag=True, use_ai=True, translate=True):
    """Extract financial data using parallel processing and deduplication"""
    
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
            extraction_methods.append(("regex", lambda: extract_financial_data_with_regex(text)))
            
            # Add AI methods if enabled
            if use_ai:
                extraction_methods.append(("ai", lambda: extract_financial_data_with_ai(text)))
            
            # Add LLM methods if enabled
            if use_llm:
                if use_rag:
                    extraction_methods.append(("llm_rag", lambda: extract_financial_data_with_llm_rag(text)))
                extraction_methods.append(("llm_only", lambda: extract_financial_data_with_llm_only(text)))

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
                            print(f"✅ {method_name.upper()}: Found {len(result['results'])} financial items")
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
            print(f"🎯 Total unique financial items found: {final_results['total_found']}")
            
            # Show method comparison
            print("\n📊 Method Comparison:")
            for method, items in final_results["method_results"].items():
                print(f"  {method.upper()}: {len(items)} items")
            
            # Clean and validate results
            cleaned_results = clean_financial_data(final_results["unique_results"])
            return cleaned_results

    except Exception as e:
        print(f"[ERROR] Failed to extract from {file_path}: {e}")
        return [] 