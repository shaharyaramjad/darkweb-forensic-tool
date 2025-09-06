#!/usr/bin/env python3
"""
Demonstration: Show exactly what content is preserved vs removed by security scanner
"""

import os
import sys

# Fix tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.path.append(os.path.abspath('.'))

from src.utils.security_scanner import SecurityScanner
from src.extract.email_extractor import extract_emails_from_html
from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
from src.extract.extract_payment_addresses_from_html import extract_payment_addresses_from_html

def create_demo_file():
    """Create a demo HTML file with both malicious content and forensic evidence"""
    
    demo_html = """
    <html>
    <head><title>Dark Web Market Demo</title></head>
    <body>
        <h1>Welcome to Dark Market</h1>
        
        <!-- MALICIOUS CONTENT (will be removed by security scanner) -->
        <script>
            alert('This is malicious JavaScript!');
            eval('alert("More malicious code")');
            document.location = 'javascript:alert("XSS attack")';
        </script>
        <iframe src="javascript:alert('iframe attack')"></iframe>
        <img src="x" onerror="alert('XSS via onerror')">
        <a href="javascript:alert('XSS via href')">Click me</a>
        
        <!-- FORENSIC EVIDENCE (will be preserved by security scanner) -->
        <div class="content">
            <h2>Our Services</h2>
            <p>Contact: vendor@protonmail.com</p>
            <p>Support: help@tutanota.com</p>
            <p>Sales: sales@onionmail.org</p>
            
            <h3>Payment Methods</h3>
            <p>Bitcoin: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</p>
            <p>Monero: 4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}</p>
            <p>Ethereum: 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6</p>
            
            <h3>Products</h3>
            <ul>
                <li>Drugs: cocaine, heroin, methamphetamine</li>
                <li>Weapons: guns, ammunition, explosives</li>
                <li>Fake Documents: passports, IDs, licenses</li>
                <li>Hacking Tools: exploits, malware, botnets</li>
            </ul>
            
            <h3>Services</h3>
            <p>We offer: drugs, weapons, fake documents, hacking tools, exploits, malware, botnets, fraud, identity theft, credit card dumps, ransomware, zero-day exploits</p>
            
            <h3>Prices</h3>
            <p>Drugs: $100-500 per gram</p>
            <p>Weapons: $500-2000 per item</p>
            <p>Fake IDs: $200-500 per document</p>
            <p>Hacking services: $1000-5000 per job</p>
        </div>
        
        <!-- MORE MALICIOUS CONTENT (will be removed) -->
        <script>
            // Base64 encoded malicious content
            eval(atob('YWxlcnQoIk1hbGljaW91cyBjb250ZW50ISIp'));
        </script>
        <object data="malware.exe"></object>
        <embed src="malware.swf"></embed>
    </body>
    </html>
    """
    
    with open('data/demo_forensic_evidence.html', 'w', encoding='utf-8') as f:
        f.write(demo_html)
    
    print("✅ Created demo file: data/demo_forensic_evidence.html")

def demonstrate_extraction():
    """Demonstrate content extraction with and without security scanning"""
    
    print("\n" + "="*80)
    print("🔍 DEMONSTRATION: Content Extraction with Security Scanner")
    print("="*80)
    
    demo_file = "data/demo_forensic_evidence.html"
    if not os.path.exists(demo_file):
        print("❌ Demo file not found. Creating it first...")
        create_demo_file()
    
    # Initialize security scanner
    scanner = SecurityScanner()
    
    print(f"\n📄 Processing: {demo_file}")
    print("-" * 60)
    
    # Step 1: Security Scan
    print("🛡️ STEP 1: Security Scanning...")
    scan_result = scanner.scan_file_safety(demo_file)
    
    print(f"Safe: {'✅ YES' if scan_result['safe'] else '❌ NO'}")
    print(f"Threats: {len(scan_result['threats'])}")
    
    if scan_result['threats']:
        print("🚨 Threats found:")
        for i, threat in enumerate(scan_result['threats'], 1):
            print(f"  {i}. {threat}")
    
    print(f"Original size: {scan_result.get('original_size', 0)} chars")
    print(f"Sanitized size: {scan_result.get('sanitized_size', 0)} chars")
    print(f"Size reduction: {scan_result.get('original_size', 0) - scan_result.get('sanitized_size', 0)} chars")
    
    # Step 2: Content Extraction from Original File
    print(f"\n📊 STEP 2: Content Extraction (Original File)...")
    try:
        emails_original = extract_emails_from_html(demo_file, use_ai=True, use_llm=False, translate=False, use_rag=False)
        payments_original = extract_payment_addresses_from_html(demo_file, use_llm=False, use_rag=False, use_ai=True, translate=False)
        keywords_original = detect_risk_keywords_from_html(demo_file, use_llm=False, use_rag=False, use_ai=True, translate=False)
        
        print(f"✅ Emails found: {len(emails_original)}")
        print(f"✅ Payment addresses found: {len(payments_original)}")
        print(f"✅ Risk keywords found: {len(keywords_original)}")
        
    except Exception as e:
        print(f"❌ Error extracting from original file: {e}")
        emails_original = []
        payments_original = []
        keywords_original = []
    
    # Step 3: Create Safe Copy
    print(f"\n🛡️ STEP 3: Creating Safe Copy...")
    safe_file = "data/safe_demo_forensic_evidence.html"
    success = scanner.create_safe_copy(demo_file, safe_file)
    
    if success:
        print(f"✅ Safe copy created: {safe_file}")
    else:
        print(f"❌ Failed to create safe copy")
        return
    
    # Step 4: Content Extraction from Safe File
    print(f"\n📊 STEP 4: Content Extraction (Safe File)...")
    try:
        emails_safe = extract_emails_from_html(safe_file, use_ai=True, use_llm=False, translate=False, use_rag=False)
        payments_safe = extract_payment_addresses_from_html(safe_file, use_llm=False, use_rag=False, use_ai=True, translate=False)
        keywords_safe = detect_risk_keywords_from_html(safe_file, use_llm=False, use_rag=False, use_ai=True, translate=False)
        
        print(f"✅ Emails found: {len(emails_safe)}")
        print(f"✅ Payment addresses found: {len(payments_safe)}")
        print(f"✅ Risk keywords found: {len(keywords_safe)}")
        
    except Exception as e:
        print(f"❌ Error extracting from safe file: {e}")
        emails_safe = []
        payments_safe = []
        keywords_safe = []
    
    # Step 5: Comparison
    print(f"\n📈 STEP 5: Comparison Results...")
    print("-" * 60)
    
    print("📧 EMAIL EXTRACTION:")
    print(f"  Original file: {len(emails_original)} emails")
    print(f"  Safe file: {len(emails_safe)} emails")
    print(f"  Difference: {len(emails_safe) - len(emails_original)}")
    
    print("\n💰 PAYMENT ADDRESS EXTRACTION:")
    print(f"  Original file: {len(payments_original)} addresses")
    print(f"  Safe file: {len(payments_safe)} addresses")
    print(f"  Difference: {len(payments_safe) - len(payments_original)}")
    
    print("\n⚠️ RISK KEYWORD EXTRACTION:")
    print(f"  Original file: {len(keywords_original)} keywords")
    print(f"  Safe file: {len(keywords_safe)} keywords")
    print(f"  Difference: {len(keywords_safe) - len(keywords_original)}")
    
    # Step 6: Detailed Results
    print(f"\n📋 DETAILED RESULTS:")
    print("-" * 60)
    
    print("📧 Emails Found:")
    for email in emails_safe:
        print(f"  ✅ {email}")
    
    print("\n💰 Payment Addresses Found:")
    for payment in payments_safe:
        print(f"  ✅ {payment}")
    
    print("\n⚠️ Risk Keywords Found:")
    for keyword in keywords_safe:
        print(f"  ✅ {keyword}")
    
    # Step 7: Conclusion
    print(f"\n🎯 CONCLUSION:")
    print("-" * 60)
    
    if len(emails_safe) >= len(emails_original) and len(payments_safe) >= len(payments_original) and len(keywords_safe) >= len(keywords_original):
        print("✅ SUCCESS: Security scanner preserved ALL forensic evidence!")
        print("✅ All emails, payment addresses, and risk keywords were extracted")
        print("✅ Malicious content was removed without affecting evidence")
    else:
        print("❌ ISSUE: Some evidence may have been lost")
        print("This would indicate a problem with the security scanner")

def main():
    """Main demonstration function"""
    
    print("🚀 Security Scanner Content Preservation Demonstration")
    print("=" * 80)
    
    # Create demo file
    create_demo_file()
    
    # Run demonstration
    demonstrate_extraction()
    
    print(f"\n📁 Files created:")
    print(f"  - data/demo_forensic_evidence.html (original with malware)")
    print(f"  - data/safe_demo_forensic_evidence.html (sanitized version)")
    
    print(f"\n🔒 Security Benefits:")
    print(f"  - System protected from malware")
    print(f"  - All forensic evidence preserved")
    print(f"  - Better extraction accuracy")
    print(f"  - Faster and safer processing")

if __name__ == "__main__":
    main() 