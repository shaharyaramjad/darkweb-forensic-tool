import re
import os
import hashlib
import json
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup
import html
import base64
import urllib.parse

class SecurityScanner:
    """
    Security scanner for dark web HTML files to detect and neutralize malicious content
    """
    
    def __init__(self):
        # Malicious patterns to detect
        self.malicious_patterns = {
            'javascript_execution': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=\s*["\'][^"\']*["\']',
                r'eval\s*\(',
                r'exec\s*\(',
                r'system\s*\(',
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>',
                r'<applet[^>]*>'
            ],
            'suspicious_urls': [
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                r'data:text/html',
                r'data:application/javascript',
                r'vbscript:',
                r'file://',
                r'ftp://'
            ],
            'encoded_content': [
                r'base64[^>]*>',
                r'%[0-9a-fA-F]{2}',
                r'\\x[0-9a-fA-F]{2}',
                r'\\u[0-9a-fA-F]{4}'
            ],
            'suspicious_attributes': [
                r'onload\s*=',
                r'onerror\s*=',
                r'onclick\s*=',
                r'onmouseover\s*=',
                r'onfocus\s*=',
                r'onblur\s*=',
                r'onchange\s*=',
                r'onsubmit\s*='
            ]
        }
        
        # Known malicious domains/IPs (example list)
        self.malicious_domains = [
            'malware.example.com',
            'evil.com',
            'hack.com',
            'stealer.com'
        ]
        
        # File size limits
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
    def scan_file_safety(self, filepath: str) -> Dict:
        """
        Comprehensive security scan of HTML file
        Returns: {'safe': bool, 'threats': List, 'sanitized_content': str}
        """
        threats = []
        sanitized_content = ""
        
        try:
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > self.max_file_size:
                threats.append(f"File too large: {file_size} bytes (max: {self.max_file_size})")
                return {'safe': False, 'threats': threats, 'sanitized_content': ""}
            
            # Read file content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Scan for malicious patterns
            for category, patterns in self.malicious_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        threats.append(f"{category}: {len(matches)} matches found")
            
            # Check for suspicious URLs
            url_matches = re.findall(r'https?://[^\s<>"\']+', content)
            for url in url_matches:
                if any(domain in url.lower() for domain in self.malicious_domains):
                    threats.append(f"Suspicious URL: {url}")
            
            # Check for encoded content
            encoded_patterns = [
                r'base64[^>]*>([A-Za-z0-9+/=]+)',
                r'%[0-9a-fA-F]{2,}',
                r'\\x[0-9a-fA-F]{2,}'
            ]
            
            for pattern in encoded_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    threats.append(f"Encoded content detected: {len(matches)} instances")
            
            # Sanitize content if threats found
            if threats:
                sanitized_content = self.sanitize_html(content)
            else:
                sanitized_content = content
                
            return {
                'safe': len(threats) == 0,
                'threats': threats,
                'sanitized_content': sanitized_content,
                'original_size': len(content),
                'sanitized_size': len(sanitized_content)
            }
            
        except Exception as e:
            threats.append(f"Error scanning file: {str(e)}")
            return {'safe': False, 'threats': threats, 'sanitized_content': ""}
    
    def sanitize_html(self, content: str) -> str:
        """
        Remove malicious content from HTML
        """
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove all script tags
        for script in soup.find_all('script'):
            script.decompose()
        
        # Remove all iframe tags
        for iframe in soup.find_all('iframe'):
            iframe.decompose()
        
        # Remove all object tags
        for obj in soup.find_all('object'):
            obj.decompose()
        
        # Remove all embed tags
        for embed in soup.find_all('embed'):
            embed.decompose()
        
        # Remove all applet tags
        for applet in soup.find_all('applet'):
            applet.decompose()
        
        # Remove suspicious event handlers
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr.lower().startswith('on'):
                    del tag[attr]
                elif attr.lower() == 'href' and tag[attr].lower().startswith('javascript:'):
                    del tag[attr]
        
        # Remove encoded content
        text = soup.get_text()
        # Remove base64 encoded content
        text = re.sub(r'base64[^>]*>[A-Za-z0-9+/=]+', '', text)
        # Remove URL encoded content
        text = re.sub(r'%[0-9a-fA-F]{2,}', '', text)
        
        return text
    
    def create_safe_copy(self, original_filepath: str, safe_filepath: str) -> bool:
        """
        Create a sanitized copy of the file
        """
        try:
            scan_result = self.scan_file_safety(original_filepath)
            
            if scan_result['safe']:
                # File is safe, just copy it
                with open(original_filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # Use sanitized content
                content = scan_result['sanitized_content']
            
            # Write safe content to new file
            with open(safe_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error creating safe copy: {e}")
            return False
    
    def generate_security_report(self, scan_result: Dict, filename: str) -> str:
        """
        Generate a security report
        """
        report = f"""
🔒 SECURITY SCAN REPORT
File: {filename}
Safe: {'✅ YES' if scan_result['safe'] else '❌ NO'}

Threats Detected: {len(scan_result['threats'])}
"""
        
        if scan_result['threats']:
            report += "\n🚨 THREATS FOUND:\n"
            for i, threat in enumerate(scan_result['threats'], 1):
                report += f"{i}. {threat}\n"
        else:
            report += "\n✅ No threats detected\n"
        
        report += f"""
📊 STATISTICS:
Original size: {scan_result.get('original_size', 0)} characters
Sanitized size: {scan_result.get('sanitized_size', 0)} characters
Size reduction: {scan_result.get('original_size', 0) - scan_result.get('sanitized_size', 0)} characters
"""
        
        return report

def secure_file_processing(filepath: str, output_dir: str = "data/safe_files") -> Tuple[bool, str, str]:
    """
    Secure wrapper for file processing
    Returns: (success, safe_filepath, security_report)
    """
    scanner = SecurityScanner()
    
    # Create safe files directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate safe file path
    filename = os.path.basename(filepath)
    safe_filename = f"safe_{filename}"
    safe_filepath = os.path.join(output_dir, safe_filename)
    
    # Scan the file
    scan_result = scanner.scan_file_safety(filepath)
    security_report = scanner.generate_security_report(scan_result, filename)
    
    # Create safe copy
    success = scanner.create_safe_copy(filepath, safe_filepath)
    
    return success, safe_filepath, security_report 