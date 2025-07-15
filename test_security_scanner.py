#!/usr/bin/env python3
"""
Test script for the security scanner
Demonstrates how the security scanner protects against malicious HTML content
"""

import os
import sys
sys.path.append(os.path.abspath('.'))

from src.utils.security_scanner import SecurityScanner, secure_file_processing

def create_test_files():
    """Create test HTML files with various malicious content"""
    
    # Test 1: Safe HTML file
    safe_html = """
    <html>
    <head><title>Safe Page</title></head>
    <body>
        <h1>Welcome</h1>
        <p>This is a safe HTML page with no malicious content.</p>
        <p>Contact: user@example.com</p>
        <p>Bitcoin: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</p>
    </body>
    </html>
    """
    
    # Test 2: Malicious HTML with JavaScript
    malicious_html = """
    <html>
    <head><title>Malicious Page</title></head>
    <body>
        <h1>Welcome</h1>
        <script>
            alert('This is malicious JavaScript!');
            eval('alert("More malicious code")');
            document.location = 'javascript:alert("XSS")';
        </script>
        <iframe src="javascript:alert('iframe attack')"></iframe>
        <img src="x" onerror="alert('XSS via onerror')">
        <a href="javascript:alert('XSS via href')">Click me</a>
        <p>Contact: user@example.com</p>
    </body>
    </html>
    """
    
    # Test 3: HTML with encoded malicious content
    encoded_html = """
    <html>
    <head><title>Encoded Malicious Page</title></head>
    <body>
        <h1>Welcome</h1>
        <script>
            // Base64 encoded malicious content
            eval(atob('YWxlcnQoIk1hbGljaW91cyBjb250ZW50ISIp'));
        </script>
        <p>URL encoded: %3Cscript%3Ealert('XSS')%3C/script%3E</p>
        <p>Hex encoded: \x3Cscript\x3Ealert('XSS')\x3C/script\x3E</p>
        <p>Contact: user@example.com</p>
    </body>
    </html>
    """
    
    # Create test files
    test_files = {
        'safe_test.html': safe_html,
        'malicious_test.html': malicious_html,
        'encoded_test.html': encoded_html
    }
    
    for filename, content in test_files.items():
        with open(f'data/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created test file: {filename}")

def test_security_scanner():
    """Test the security scanner with various files"""
    
    print("🔒 Testing Security Scanner")
    print("=" * 50)
    
    scanner = SecurityScanner()
    
    test_files = [
        'data/safe_test.html',
        'data/malicious_test.html', 
        'data/encoded_test.html'
    ]
    
    for filepath in test_files:
        if os.path.exists(filepath):
            print(f"\n📄 Testing: {os.path.basename(filepath)}")
            print("-" * 30)
            
            # Scan the file
            scan_result = scanner.scan_file_safety(filepath)
            
            # Display results
            print(f"Safe: {'✅ YES' if scan_result['safe'] else '❌ NO'}")
            print(f"Threats: {len(scan_result['threats'])}")
            
            if scan_result['threats']:
                print("🚨 Threats found:")
                for i, threat in enumerate(scan_result['threats'], 1):
                    print(f"  {i}. {threat}")
            
            print(f"Original size: {scan_result.get('original_size', 0)} chars")
            print(f"Sanitized size: {scan_result.get('sanitized_size', 0)} chars")
            
            # Generate security report
            report = scanner.generate_security_report(scan_result, os.path.basename(filepath))
            print("\n📋 Security Report:")
            print(report)

def test_secure_processing():
    """Test the secure file processing wrapper"""
    
    print("\n🛡️ Testing Secure File Processing")
    print("=" * 50)
    
    test_files = [
        'data/safe_test.html',
        'data/malicious_test.html',
        'data/encoded_test.html'
    ]
    
    for filepath in test_files:
        if os.path.exists(filepath):
            print(f"\n📄 Processing: {os.path.basename(filepath)}")
            print("-" * 30)
            
            success, safe_filepath, security_report, scan_result = secure_file_processing(filepath)
            
            if success:
                print(f"✅ Processing successful")
                print(f"Safe file: {safe_filepath}")
                print(f"Security report generated")
            else:
                print(f"❌ Processing failed")
            
            print("\nSecurity Report:")
            print(security_report)

def main():
    """Main test function"""
    
    print("🚀 Security Scanner Test Suite")
    print("=" * 60)
    
    # Create test files
    print("📝 Creating test files...")
    create_test_files()
    
    # Test security scanner
    test_security_scanner()
    
    # Test secure processing
    test_secure_processing()
    
    print("\n✅ Security scanner tests completed!")
    print("\n📁 Check the 'data/safe_files/' directory for sanitized versions")

if __name__ == "__main__":
    main() 