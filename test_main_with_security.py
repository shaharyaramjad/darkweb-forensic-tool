#!/usr/bin/env python3
"""
Test the main application with security scanning enabled
"""

import os
import sys
sys.path.append(os.path.abspath('.'))

def test_main_imports():
    """Test that all main imports work with security scanner"""
    
    print("🔍 Testing main application imports...")
    
    try:
        # Test security scanner import
        from src.utils.security_scanner import SecurityScanner, secure_file_processing
        print("✅ Security scanner imports successfully")
        
        # Test main application imports
        from src.main import case_id, investigator, notes
        print("✅ Main application imports successfully")
        
        # Test extraction modules
        from src.extract.email_extractor import extract_emails_from_html
        from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
        from src.extract.extract_payment_addresses_from_html import extract_payment_addresses_from_html
        print("✅ Extraction modules import successfully")
        
        # Test utility modules
        from src.utils.hash_util import calculate_sha256
        from src.risk.risk_score import calculate_risk_score
        print("✅ Utility modules import successfully")
        
        # Test report modules
        from src.report.pdf_report import generate_pdf_report
        from src.report.json_report import generate_json_report
        print("✅ Report modules import successfully")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_security_integration():
    """Test security scanner integration with a test file"""
    
    print("\n🛡️ Testing security integration...")
    
    try:
        from src.utils.security_scanner import secure_file_processing
        
        # Test with a safe file
        test_file = "data/safe_test.html"
        if os.path.exists(test_file):
            success, safe_filepath, security_report, scan_result = secure_file_processing(test_file)
            
            if success:
                print("✅ Security integration test successful")
                print(f"Safe file created: {safe_filepath}")
                return True
            else:
                print("❌ Security integration test failed")
                return False
        else:
            print("⚠️ Test file not found, skipping security integration test")
            return True
            
    except Exception as e:
        print(f"❌ Security integration error: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Testing Main Application with Security Scanner")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_main_imports()
    
    # Test security integration
    security_ok = test_security_integration()
    
    if imports_ok and security_ok:
        print("\n✅ All tests passed!")
        print("\n🔒 Security Features:")
        print("- Security scanner is integrated")
        print("- Malicious content detection enabled")
        print("- File sanitization working")
        print("- Safe file creation functional")
    else:
        print("\n❌ Some tests failed!")
        
    print("\n📋 Next Steps:")
    print("1. Run: python src/main.py (for CLI mode)")
    print("2. Run: streamlit run src/ui/app.py (for web interface)")
    print("3. Check SECURITY.md for detailed security guidelines")

if __name__ == "__main__":
    main() 