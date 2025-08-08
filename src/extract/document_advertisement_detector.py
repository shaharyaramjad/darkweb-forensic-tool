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
import requests
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
            model="meta-llama/Llama-3.1-8B-Instruct",
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
            model="meta-llama/Llama-3.1-8B-Instruct",
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
    """Extract URLs from text for virus detection with enhanced malicious file detection."""
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
                    'path': path,
                    'query': query,
                    'suspicious_reason': ' + '.join(suspicious_reason),
                    'risk_level': risk_level,
                    'file_extension': next((ext for ext in high_risk_extensions + medium_risk_extensions if ext in path), None),
                    'malicious_keywords_found': [kw for kw in malicious_keywords if kw in path or kw in query]
                })
        
        return suspicious_urls
    except Exception as e:
        print(f"Error extracting URLs: {e}")
        return []

def prepare_for_virus_detection(document_ads, suspicious_urls):
    """Prepare data for virus detection API with enhanced malicious file detection."""
    try:
        virus_detection_data = {
            'document_advertisements': [],
            'suspicious_urls': [],
            'high_risk_items': [],
            'malicious_file_downloads': [],
            'executable_files': [],
            'api_ready': True,
            'summary': {
                'total_document_ads': 0,
                'total_suspicious_urls': 0,
                'high_risk_urls': 0,
                'executable_files': 0,
                'malicious_keywords_found': 0
            }
        }
        
        # Process document advertisements
        for ad in document_ads:
            virus_detection_data['document_advertisements'].append({
                'content': ad['content'],
                'type': ad['type'],
                'suspicious_level': ad['suspicious_level'],
                'method': ad['method']
            })
            virus_detection_data['summary']['total_document_ads'] += 1
            
            # Check if it's a malicious file download advertisement
            if 'malicious_file_downloads' in ad['type'] or 'malware_indicators' in ad['type']:
                virus_detection_data['malicious_file_downloads'].append({
                    'content': ad['content'],
                    'type': ad['type'],
                    'suspicious_level': ad['suspicious_level'],
                    'method': ad['method'],
                    'priority': 'critical'
                })
            
            if ad['suspicious_level'] == 'high':
                virus_detection_data['high_risk_items'].append({
                    'type': 'document_advertisement',
                    'content': ad['content'],
                    'risk_level': 'high',
                    'priority': 'critical'
                })
        
        # Process suspicious URLs
        for url_data in suspicious_urls:
            virus_detection_data['suspicious_urls'].append({
                'url': url_data['url'],
                'domain': url_data['domain'],
                'path': url_data.get('path', ''),
                'query': url_data.get('query', ''),
                'suspicious_reason': url_data['suspicious_reason'],
                'risk_level': url_data['risk_level'],
                'file_extension': url_data.get('file_extension'),
                'malicious_keywords_found': url_data.get('malicious_keywords_found', [])
            })
            virus_detection_data['summary']['total_suspicious_urls'] += 1
            
            # Track executable files separately
            if url_data.get('file_extension') in ['.exe', '.msi', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.jar', '.apk', '.dmg', '.pkg', '.scr', '.com']:
                virus_detection_data['executable_files'].append({
                    'url': url_data['url'],
                    'domain': url_data['domain'],
                    'file_extension': url_data['file_extension'],
                    'risk_level': 'critical',
                    'suspicious_reason': url_data['suspicious_reason']
                })
                virus_detection_data['summary']['executable_files'] += 1
            
            if url_data['risk_level'] == 'high':
                virus_detection_data['summary']['high_risk_urls'] += 1
                virus_detection_data['high_risk_items'].append({
                    'type': 'suspicious_url',
                    'url': url_data['url'],
                    'risk_level': 'high',
                    'file_extension': url_data.get('file_extension'),
                    'priority': 'critical'
                })
            
            # Count malicious keywords
            if url_data.get('malicious_keywords_found'):
                virus_detection_data['summary']['malicious_keywords_found'] += len(url_data['malicious_keywords_found'])
        
        return virus_detection_data
        
    except Exception as e:
        print(f"Error preparing virus detection data: {e}")
        return {
            'document_advertisements': [],
            'suspicious_urls': [],
            'high_risk_items': [],
            'malicious_file_downloads': [],
            'executable_files': [],
            'api_ready': False,
            'error': str(e),
            'summary': {
                'total_document_ads': 0,
                'total_suspicious_urls': 0,
                'high_risk_urls': 0,
                'executable_files': 0,
                'malicious_keywords_found': 0
            }
        }

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

def generate_investigation_report(document_ads, suspicious_urls, virus_detection_data):
    """Generate a detailed report for manual investigation of malicious files."""
    try:
        report = {
            'timestamp': time.time(),
            'summary': {
                'total_document_advertisements': len(document_ads),
                'total_suspicious_urls': len(suspicious_urls),
                'high_risk_items': len(virus_detection_data.get('high_risk_items', [])),
                'executable_files': len(virus_detection_data.get('executable_files', [])),
                'malicious_file_downloads': len(virus_detection_data.get('malicious_file_downloads', [])),
                'critical_threats': 0,
                'requires_immediate_action': False
            },
            'critical_findings': [],
            'executable_files_detected': [],
            'malicious_file_advertisements': [],
            'suspicious_urls_for_investigation': [],
            'recommendations': [],
            'manual_investigation_required': []
        }
        
        # Analyze executable files (highest priority)
        for exe_file in virus_detection_data.get('executable_files', []):
            report['executable_files_detected'].append({
                'url': exe_file['url'],
                'domain': exe_file['domain'],
                'file_extension': exe_file['file_extension'],
                'suspicious_reason': exe_file['suspicious_reason'],
                'priority': 'CRITICAL',
                'action_required': 'IMMEDIATE BLOCKING REQUIRED',
                'investigation_notes': f"Executable file detected: {exe_file['file_extension']} from {exe_file['domain']}"
            })
            report['summary']['critical_threats'] += 1
            report['summary']['requires_immediate_action'] = True
        
        # Analyze malicious file download advertisements
        for mal_ad in virus_detection_data.get('malicious_file_downloads', []):
            report['malicious_file_advertisements'].append({
                'content': mal_ad['content'],
                'type': mal_ad['type'],
                'suspicious_level': mal_ad['suspicious_level'],
                'method': mal_ad['method'],
                'priority': 'HIGH',
                'action_required': 'INVESTIGATE FOR MALWARE',
                'investigation_notes': f"Malicious file advertisement detected via {mal_ad['method']}"
            })
            report['summary']['critical_threats'] += 1
        
        # Analyze suspicious URLs for manual investigation
        for url_data in suspicious_urls:
            if url_data['risk_level'] == 'high':
                report['suspicious_urls_for_investigation'].append({
                    'url': url_data['url'],
                    'domain': url_data['domain'],
                    'suspicious_reason': url_data['suspicious_reason'],
                    'file_extension': url_data.get('file_extension'),
                    'malicious_keywords': url_data.get('malicious_keywords_found', []),
                    'priority': 'HIGH',
                    'action_required': 'VIRUS SCAN REQUIRED',
                    'investigation_notes': f"High-risk URL with {url_data['suspicious_reason']}"
                })
                report['summary']['critical_threats'] += 1
            elif url_data['risk_level'] == 'medium':
                report['suspicious_urls_for_investigation'].append({
                    'url': url_data['url'],
                    'domain': url_data['domain'],
                    'suspicious_reason': url_data['suspicious_reason'],
                    'file_extension': url_data.get('file_extension'),
                    'malicious_keywords': url_data.get('malicious_keywords_found', []),
                    'priority': 'MEDIUM',
                    'action_required': 'MONITOR CLOSELY',
                    'investigation_notes': f"Medium-risk URL with {url_data['suspicious_reason']}"
                })
        
        # Generate critical findings
        if report['summary']['executable_files'] > 0:
            report['critical_findings'].append({
                'type': 'EXECUTABLE_FILES_DETECTED',
                'severity': 'CRITICAL',
                'description': f"Found {report['summary']['executable_files']} executable files that could install malware",
                'immediate_action': 'BLOCK ALL EXECUTABLE DOWNLOADS IMMEDIATELY'
            })
        
        if report['summary']['malicious_file_downloads'] > 0:
            report['critical_findings'].append({
                'type': 'MALICIOUS_FILE_ADVERTISEMENTS',
                'severity': 'HIGH',
                'description': f"Found {report['summary']['malicious_file_downloads']} advertisements for malicious file downloads",
                'immediate_action': 'INVESTIGATE ALL MALICIOUS FILE ADVERTISEMENTS'
            })
        
        if report['summary']['high_risk_items'] > 0:
            report['critical_findings'].append({
                'type': 'HIGH_RISK_ITEMS',
                'severity': 'HIGH',
                'description': f"Found {report['summary']['high_risk_items']} high-risk items requiring immediate attention",
                'immediate_action': 'PRIORITIZE INVESTIGATION OF HIGH-RISK ITEMS'
            })
        
        # Generate recommendations
        if report['summary']['requires_immediate_action']:
            report['recommendations'].append('🚨 IMMEDIATE ACTION REQUIRED: Block all executable file downloads')
            report['recommendations'].append('🔍 MANUAL INVESTIGATION: Review all suspicious URLs for malware')
            report['recommendations'].append('📋 DOCUMENTATION: Document all findings for forensic analysis')
        else:
            report['recommendations'].append('✅ No critical threats detected, continue monitoring')
        
        # Prepare manual investigation checklist
        report['manual_investigation_required'] = [
            {
                'task': 'Review all executable files',
                'priority': 'CRITICAL',
                'description': 'Manually verify each executable file URL for malware'
            },
            {
                'task': 'Investigate malicious file advertisements',
                'priority': 'HIGH',
                'description': 'Analyze content of malicious file download advertisements'
            },
            {
                'task': 'Virus scan suspicious URLs',
                'priority': 'HIGH',
                'description': 'Use virus detection APIs to scan suspicious URLs'
            },
            {
                'task': 'Document findings',
                'priority': 'MEDIUM',
                'description': 'Create detailed report of all findings for legal/forensic purposes'
            }
        ]
        
        return report
        
    except Exception as e:
        return {
            'error': f'Failed to generate investigation report: {str(e)}',
            'summary': {'error': True}
        }

def extract_document_advertisements_from_html(file_path, use_llm=True, use_rag=True, use_ai=True, translate=True):
    """Extract document advertisements using parallel processing and prepare for virus detection."""
    
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
                            print(f"✅ {method_name.upper()}: Found {len(result['results'])} document advertisements")
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
            print(f"🎯 Total unique document advertisements found: {final_results['total_found']}")
            
            # Show method comparison
            print("\n📊 Method Comparison:")
            for method, items in final_results["method_results"].items():
                print(f"  {method.upper()}: {len(items)} items")
            
            # Clean and validate results
            cleaned_results = clean_document_ads(final_results["unique_results"])
            
            # Extract suspicious URLs
            suspicious_urls = extract_urls_from_text(text)
            
            # Prepare for virus detection API
            virus_detection_data = prepare_for_virus_detection(cleaned_results, suspicious_urls)
            
                    # Generate detailed report for manual investigation
        investigation_report = generate_investigation_report(cleaned_results, suspicious_urls, virus_detection_data)
        
        return {
            'document_advertisements': cleaned_results,
            'suspicious_urls': suspicious_urls,
            'virus_detection_data': virus_detection_data,
            'investigation_report': investigation_report,
            'total_found': len(cleaned_results) + len(suspicious_urls)
        }

    except Exception as e:
        print(f"[ERROR] Failed to extract document advertisements from {file_path}: {e}")
        return {
            'document_advertisements': [],
            'suspicious_urls': [],
            'virus_detection_data': {
                'document_advertisements': [],
                'suspicious_urls': [],
                'high_risk_items': [],
                'malicious_file_downloads': [],
                'executable_files': [],
                'api_ready': False,
                'error': str(e),
                'summary': {
                    'total_document_ads': 0,
                    'total_suspicious_urls': 0,
                    'high_risk_urls': 0,
                    'executable_files': 0,
                    'malicious_keywords_found': 0
                }
            },
            'investigation_report': {
                'error': str(e),
                'summary': {'error': True}
            },
            'total_found': 0
        } 