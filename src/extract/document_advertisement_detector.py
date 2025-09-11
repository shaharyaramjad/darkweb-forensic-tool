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
import urllib.parse
from urllib.parse import urlparse

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

# === Document advertisement patterns ===
document_patterns = {
    'malicious_file_downloads': [
        r'\b(?:download|get|install|run)\s+(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\b',
        r'\b(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\s+(?:download|install|run|execute)\b',
        r'\b(?:free|premium|exclusive)\s+(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\s+(?:download|install)\b',
        r'\b(?:undetected|stealth|bypass)\s+(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\b',
        r'\b(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\s+(?:builder|generator|creator)\b',
    ],
    'suspicious_document_links': [
        r'\b(?:download|get|access|view|open)\s+(?:document|file|pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|exe|msi)\b',
        r'\b(?:document|file|pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|exe|msi)\s+(?:download|link|url|access)\b',
        r'\b(?:click|click\s+here|download\s+here)\s+(?:for|to\s+get|to\s+access)\s+(?:document|file)\b',
        r'\b(?:free|premium|exclusive|confidential|secret)\s+(?:document|file|download)\b',
        r'\b(?:document|file)\s+(?:sharing|sharing\s+link|download\s+link)\b',
    ],
    'file_extensions': [
        r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|exe|msi|bat|cmd|ps1|vbs|js|jar|apk|dmg|pkg)$',
        r'\b(?:\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.ppt|\.pptx|\.zip|\.rar|\.exe|\.msi|\.bat|\.cmd|\.ps1|\.vbs|\.js|\.jar|\.apk|\.dmg|\.pkg)\b',
    ],
    'suspicious_urls': [
        r'https?://[^\s<>"\']*\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|exe|msi|bat|cmd|ps1|vbs|js|jar|apk|dmg|pkg)',
        r'https?://[^\s<>"\']*/(?:download|file|document|get|access)',
        r'https?://[^\s<>"\']*/(?:\.pdf|\.doc|\.docx|\.xls|\.xlsx|\.ppt|\.pptx|\.zip|\.rar|\.exe|\.msi)',
        r'https?://[^\s<>"\']*/(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)',
    ],
    'dark_web_document_indicators': [
        r'\b(?:fake|forged|counterfeit|stolen|leaked)\s+(?:document|id|passport|license|certificate)\b',
        r'\b(?:document|id|passport|license|certificate)\s+(?:service|provider|vendor|seller)\b',
        r'\b(?:high\s+quality|premium|authentic)\s+(?:fake|forged|counterfeit)\s+(?:document|id)\b',
        r'\b(?:document|id|passport|license|certificate)\s+(?:template|sample|example)\b',
        r'\b(?:custom|personalized|tailored)\s+(?:document|id|passport|license)\b',
    ],
    'malware_indicators': [
        r'\b(?:virus|malware|trojan|spyware|ransomware)\s+(?:document|file|download)\b',
        r'\b(?:infected|contaminated|compromised)\s+(?:document|file)\b',
        r'\b(?:payload|exploit|backdoor)\s+(?:document|file|download)\b',
        r'\b(?:stealer|keylogger|rat)\s+(?:document|file|download)\b',
        r'\b(?:crypto|miner|botnet)\s+(?:malware|virus|trojan)\b',
        r'\b(?:remote|access|control)\s+(?:tool|software|malware)\b',
    ],
    'suspicious_descriptions': [
        r'\b(?:urgent|immediate|limited\s+time|expires\s+soon)\s+(?:document|download)\b',
        r'\b(?:exclusive|premium|vip|private)\s+(?:document|file|download)\b',
        r'\b(?:confidential|secret|classified|restricted)\s+(?:document|file)\b',
        r'\b(?:no\s+antivirus|bypass|undetected|stealth)\s+(?:document|file)\b',
        r'\b(?:destroy|damage|corrupt|infect)\s+(?:computer|laptop|system)\b',
    ]
}

# === Knowledge base for RAG ===
knowledge_texts = [
    "DOCUMENT ADVERTISEMENTS: Dark web vendors often advertise fake documents, IDs, passports, and licenses. Look for suspicious document download links and file sharing services.",
    "MALWARE DOCUMENTS: Malicious actors embed malware in seemingly legitimate documents. Look for suspicious file extensions like .exe, .msi, .bat, .ps1, .vbs.",
    "FAKE DOCUMENT SERVICES: Vendors offer fake ID services, forged passports, counterfeit licenses, and fake certificates. Look for terms like 'high quality fake', 'authentic fake', 'premium document'.",
    "SUSPICIOUS DOWNLOADS: Dark web users share malicious documents through file sharing services. Look for download links, file sharing URLs, and suspicious document descriptions.",
    "DOCUMENT MALWARE: Attackers use documents to deliver malware payloads. Look for infected documents, compromised files, and malicious downloads.",
    "FAKE ID SERVICES: Vendors advertise fake identification documents including driver licenses, passports, social security cards, and birth certificates.",
    "COUNTERFEIT DOCUMENTS: Dark web markets sell counterfeit documents like diplomas, certificates, licenses, and official papers.",
    "MALICIOUS ATTACHMENTS: Documents may contain embedded malware, macros, or malicious scripts. Look for suspicious file types and descriptions.",
    "DOCUMENT SHARING: Users share sensitive or malicious documents through file hosting services. Look for sharing links and download URLs.",
    "STEALTH DOCUMENTS: Malicious documents designed to bypass antivirus detection. Look for terms like 'undetected', 'stealth', 'bypass'.",
    "URGENT DOCUMENTS: Scammers create urgency around document downloads. Look for terms like 'urgent', 'limited time', 'expires soon'.",
    "PREMIUM DOCUMENTS: Vendors offer premium or exclusive document services. Look for terms like 'exclusive', 'premium', 'vip', 'private'.",
    "CONFIDENTIAL DOCUMENTS: Dark web users share confidential or classified documents. Look for terms like 'confidential', 'secret', 'classified', 'restricted'.",
    "DOCUMENT TEMPLATES: Vendors sell document templates for creating fake IDs and certificates. Look for terms like 'template', 'sample', 'example'.",
    "CUSTOM DOCUMENTS: Personalized document services for fake IDs and certificates. Look for terms like 'custom', 'personalized', 'tailored'."
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

def extract_document_ads_with_regex(text):
    """Extract document advertisements using regex patterns."""
    try:
        document_ads = []
        
        for category, patterns in document_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Clean and validate the match
                    matched_text = match.group().strip()
                    if len(matched_text) > 3:  # Minimum length validation
                        document_ads.append({
                            'type': category,
                            'content': matched_text,
                            'method': 'regex',
                            'suspicious_level': 'high' if 'malware' in category or 'dark_web' in category else 'medium'
                        })
        
        return {"method": "regex", "results": document_ads, "success": True}
    except Exception as e:
        return {"method": "regex", "results": [], "success": False, "error": str(e)}

def extract_document_ads_with_ai(text):
    """Extract document advertisements using Hugging Face AI model"""
    try:
        # Use StarPII for entity detection
        result = hf_client.token_classification(text, model="bigcode/starpii")
        document_ads = []
        
        for entity in result:
            if entity['entity_group'].lower() in ['misc', 'org', 'person']:
                content = entity['word']
                # Check if it looks like a document advertisement
                if re.search(r'\b(?:document|file|download|pdf|doc|exe|zip)\b', content, re.IGNORECASE):
                    # Determine type based on context
                    if re.search(r'\b(?:fake|forged|counterfeit)\b', text[max(0, entity['start']-20):entity['start']], re.IGNORECASE):
                        ad_type = 'dark_web_document_indicators'
                    elif re.search(r'\b(?:virus|malware|trojan)\b', text[max(0, entity['start']-20):entity['start']], re.IGNORECASE):
                        ad_type = 'malware_indicators'
                    elif re.search(r'\b(?:download|link|url)\b', text[max(0, entity['start']-20):entity['start']], re.IGNORECASE):
                        ad_type = 'suspicious_document_links'
                    else:
                        ad_type = 'suspicious_descriptions'
                    
                    document_ads.append({
                        'type': ad_type,
                        'content': content,
                        'method': 'ai',
                        'suspicious_level': 'high' if 'malware' in ad_type or 'dark_web' in ad_type else 'medium'
                    })
        
        return {"method": "ai", "results": document_ads, "success": True}
    except Exception as e:
        return {"method": "ai", "results": [], "success": False, "error": str(e)}

def extract_document_ads_with_llm_rag(text):
    """Extract document advertisements using LLM with RAG."""
    try:
        # Retrieve relevant context
        retrieved_context = retrieve_context("document advertisement fake id malware download", knowledge_texts)
        
        prompt = f"""
        You are an expert forensic analyst specializing in dark web document advertisement detection.
        
        KNOWLEDGE BASE:
        {retrieved_context}
        
        Extract ONLY document advertisements, suspicious downloads, and malicious file links from the text.
        
        Look for:
        - Fake document services (IDs, passports, licenses)
        - Malware-infected documents
        - Suspicious download links
        - File sharing advertisements
        - Malicious document descriptions
        - Dark web document vendors
        
        DO NOT include:
        - General text that isn't about documents
        - Normal file references
        - Legitimate document mentions
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of document advertisements found.
        Format: type:content,suspicious_level:level
        Examples: dark_web_document_indicators:fake passport service,high,suspicious_document_links:download malware.exe,high
        """
        
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        document_ads = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        suspicious_level = 'high' if 'malware' in content.lower() or 'fake' in content.lower() else 'medium'
                        document_ads.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_rag',
                            'suspicious_level': suspicious_level
                        })
        
        return {"method": "llm_rag", "results": document_ads, "success": True}
        
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_document_ads_with_llm_only(text):
    """Extract document advertisements using LLM only."""
    try:
        prompt = f"""
        You are an expert forensic analyst. Extract document advertisements and suspicious downloads from the text.
        
        Look for:
        - Fake document services (IDs, passports, licenses)
        - Malware-infected documents
        - Suspicious download links
        - File sharing advertisements
        - Malicious document descriptions
        - Dark web document vendors
        
        HTML CONTENT:
        {text[:3000]}
        
        Return ONLY a comma-separated list of document advertisements found.
        Format: type:content,suspicious_level:level
        Examples: dark_web_document_indicators:fake passport service,high,suspicious_document_links:download malware.exe,high
        """
        
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        document_ads = []
        if result and ',' in result:
            items = result.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        data_type, content = parts
                        suspicious_level = 'high' if 'malware' in content.lower() or 'fake' in content.lower() else 'medium'
                        document_ads.append({
                            'type': data_type.strip(),
                            'content': content.strip(),
                            'method': 'llm_only',
                            'suspicious_level': suspicious_level
                        })
        
        return {"method": "llm_only", "results": document_ads, "success": True}
        
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def extract_urls_from_text(text):
    """Extract URLs from text for analysis."""
    try:
        url_pattern = r'https?://[^\s<>"\']+'
        urls = re.findall(url_pattern, text)
        
        suspicious_urls = []
        for url in urls:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            query = parsed_url.query.lower()
            
            # Check for highly suspicious file extensions (executable files)
            high_risk_extensions = ['.exe', '.msi', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.jar', '.apk', '.dmg', '.pkg', '.scr', '.com']
            is_high_risk = any(ext in path for ext in high_risk_extensions)
            
            # Check for suspicious file extensions (documents that could contain macros)
            medium_risk_extensions = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.zip', '.rar', '.7z']
            is_medium_risk = any(ext in path for ext in medium_risk_extensions)
            
            # Check for malicious keywords in URL path and query
            malicious_keywords = [
                'malware', 'virus', 'trojan', 'spyware', 'keylogger', 'stealer', 'rat', 'backdoor',
                'crypto', 'miner', 'botnet', 'payload', 'exploit', 'undetected', 'stealth', 'bypass'
            ]
            has_malicious_keywords = any(keyword in path or keyword in query for keyword in malicious_keywords)
            
            # Check for suspicious download keywords
            download_keywords = ['download', 'file', 'document', 'get', 'access', 'install', 'run', 'execute']
            has_download_keywords = any(keyword in path or keyword in query for keyword in download_keywords)
            
            # Determine risk level and reason
            risk_level = 'low'
            suspicious_reason = []
            
            if is_high_risk:
                risk_level = 'high'
                suspicious_reason.append('executable_file')
            
            if has_malicious_keywords:
                risk_level = 'high'
                suspicious_reason.append('malicious_keywords')
            
            if is_medium_risk and has_download_keywords:
                risk_level = 'medium'
                suspicious_reason.append('suspicious_document_download')
            
            if has_download_keywords and not is_medium_risk and not is_high_risk:
                risk_level = 'medium'
                suspicious_reason.append('download_keywords')
            
            # Only add URLs that meet our criteria
            if risk_level in ['high', 'medium']:
                suspicious_urls.append({
                    'url': url,
                    'domain': parsed_url.netloc,
                    'suspicious_reason': ' + '.join(suspicious_reason),
                    'risk_level': risk_level,
                    'file_extension': next((ext for ext in high_risk_extensions + medium_risk_extensions if ext in path), None)
                })
        
        return suspicious_urls
    except Exception as e:
        print(f"Error extracting URLs: {e}")
        return []

def deduplicate_results(all_results):
    """Remove duplicate document advertisements and organize by method."""
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

def clean_document_ads(document_ads):
    """Clean and validate document advertisements."""
    cleaned_data = []
    
    for item in document_ads:
        content = item['content']
        data_type = item['type']
        
        # Basic validation
        if content and len(content.strip()) > 3:
            # Remove common false positives
            false_positives = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            if content.lower() not in false_positives:
                cleaned_data.append(item)
    
    return cleaned_data

def extract_actual_links_from_html(html_content):
    """Extract actual links and URLs from HTML content exactly as they appear."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_links = []
        
        # Extract all <a> tags with href attributes
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            link_text = link.get_text(strip=True)
            
            if href and href.startswith(('http://', 'https://')):
                extracted_links.append({
                    'type': 'hyperlink',
                    'url': href,
                    'link_text': link_text,
                    'method': 'html_parser',
                    'suspicious_level': 'medium'
                })
        
        # Extract all URLs from text content (including those not in <a> tags)
        url_pattern = r'https?://[^\s<>"\']+'
        text_urls = re.findall(url_pattern, html_content)
        
        for url in text_urls:
            # Check if this URL wasn't already extracted as a hyperlink
            if not any(link['url'] == url for link in extracted_links):
                extracted_links.append({
                    'type': 'text_url',
                    'url': url,
                    'link_text': url,
                    'method': 'regex',
                    'suspicious_level': 'medium'
                })
        
        # Extract links from src attributes (images, scripts, etc.)
        for tag in soup.find_all(['img', 'script', 'iframe', 'embed'], src=True):
            src = tag.get('src', '').strip()
            if src and src.startswith(('http://', 'https://')):
                extracted_links.append({
                    'type': 'resource_link',
                    'url': src,
                    'link_text': f"{tag.name} source",
                    'method': 'html_parser',
                    'suspicious_level': 'medium'
                })
        
        # Extract links from data attributes
        for tag in soup.find_all(attrs={'data-url': True}):
            data_url = tag.get('data-url', '').strip()
            if data_url and data_url.startswith(('http://', 'https://')):
                extracted_links.append({
                    'type': 'data_attribute',
                    'url': data_url,
                    'link_text': f"data-url from {tag.name}",
                    'method': 'html_parser',
                    'suspicious_level': 'medium'
                })
        
        # Extract links from onclick and other event handlers
        for tag in soup.find_all(attrs={'onclick': True}):
            onclick = tag.get('onclick', '')
            urls_in_onclick = re.findall(url_pattern, onclick)
            for url in urls_in_onclick:
                extracted_links.append({
                    'type': 'event_handler',
                    'url': url,
                    'link_text': f"onclick from {tag.name}",
                    'method': 'html_parser',
                    'suspicious_level': 'high'
                })
        
        # Extract links from JavaScript code
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                urls_in_script = re.findall(url_pattern, script.string)
                for url in urls_in_script:
                    extracted_links.append({
                        'type': 'javascript',
                        'url': url,
                        'link_text': f"JavaScript code",
                        'method': 'html_parser',
                        'suspicious_level': 'high'
                    })
        
        # Extract links from CSS (style attributes and <style> tags)
        for tag in soup.find_all(attrs={'style': True}):
            style_content = tag.get('style', '')
            urls_in_style = re.findall(url_pattern, style_content)
            for url in urls_in_style:
                extracted_links.append({
                    'type': 'css_inline',
                    'url': url,
                    'link_text': f"CSS from {tag.name}",
                    'method': 'html_parser',
                    'suspicious_level': 'medium'
                })
        
        style_tags = soup.find_all('style')
        for style in style_tags:
            if style.string:
                urls_in_style = re.findall(url_pattern, style.string)
                for url in urls_in_style:
                    extracted_links.append({
                        'type': 'css_tag',
                        'url': url,
                        'link_text': f"CSS tag",
                        'method': 'html_parser',
                        'suspicious_level': 'medium'
                    })
        
        # Remove duplicates while preserving order
        seen_urls = set()
        unique_links = []
        for link in extracted_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        return unique_links
        
    except Exception as e:
        print(f"Error extracting actual links: {e}")
        return []

def extract_document_advertisements_from_html(file_path, use_llm=True, use_rag=True, use_ai=True, translate=True):
    """Extract actual links and URLs from HTML pages exactly as they appear."""
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()

            # Detect suspicious prompt injection attempts
            suspicious = detect_suspicious_prompts(html_content)
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

            # Extract actual links from HTML
            print("🔗 Extracting actual links from HTML...")
            actual_links = extract_actual_links_from_html(html_content)
            
            # Also run the original pattern-based detection for comparison
            if use_ai or use_llm:
                print("🔍 Running pattern-based detection...")
                # Define extraction methods to run
                extraction_methods = []
                
                # Always run regex (fastest and most reliable)
                extraction_methods.append(("regex", lambda: extract_document_ads_with_regex(text)))
                
                # Add AI methods if enabled
                if use_ai:
                    extraction_methods.append(("ai", lambda: extract_document_ads_with_ai(text)))
                
                # Add LLM methods if enabled
                if use_llm:
                    if use_rag:
                        extraction_methods.append(("llm_rag", lambda: extract_document_ads_with_llm_rag(text)))
                    extraction_methods.append(("llm_only", lambda: extract_document_ads_with_llm_only(text)))

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
                                print(f"✅ {method_name.upper()}: Found {len(result['results'])} patterns")
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

                # Deduplicate pattern results
                final_results = deduplicate_results(all_results)
                pattern_based_ads = clean_document_ads(final_results["unique_results"])
                
                processing_time = time.time() - start_time
                print(f"⏱️ Pattern detection completed in {processing_time:.2f} seconds")
                print(f"🎯 Pattern-based items found: {final_results['total_found']}")
            else:
                pattern_based_ads = []

            # Extract suspicious URLs using the existing function
            suspicious_urls = extract_urls_from_text(text)
            
            print(f"🔗 Actual links extracted: {len(actual_links)}")
            print(f"⚠️ Suspicious URLs detected: {len(suspicious_urls)}")
            
            # Return comprehensive structure with actual links
            return {
                'actual_links': actual_links,
                'document_advertisements': pattern_based_ads,
                'suspicious_urls': suspicious_urls,
                'total_found': len(actual_links) + len(pattern_based_ads) + len(suspicious_urls),
                'link_summary': {
                    'total_links': len(actual_links),
                    'hyperlink_links': len([l for l in actual_links if l['type'] == 'hyperlink']),
                    'text_urls': len([l for l in actual_links if l['type'] == 'text_url']),
                    'resource_links': len([l for l in actual_links if l['type'] == 'resource_link']),
                    'javascript_links': len([l for l in actual_links if l['type'] == 'javascript']),
                    'event_handler_links': len([l for l in actual_links if l['type'] == 'event_handler'])
                }
            }

    except Exception as e:
        print(f"[ERROR] Failed to extract links from {file_path}: {e}")
        return {
            'actual_links': [],
            'document_advertisements': [],
            'suspicious_urls': [],
            'total_found': 0,
            'link_summary': {}
        } 