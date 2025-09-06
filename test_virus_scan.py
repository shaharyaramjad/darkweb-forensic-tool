#!/usr/bin/env python3
"""
Test script to demonstrate virus detection for actual links from database.
"""

import os
import sys

# Fix tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.path.append('src')

from src.utils.virus_detection_api import scan_actual_links_from_database, VirusDetectionAPI

def test_virus_scan():
    """Test virus detection for actual links from database."""
    
    print("🦠 Testing Virus Detection for Actual Links from Database")
    print("=" * 60)
    
    # Test 1: Check if API keys are configured
    virus_api = VirusDetectionAPI()
    has_keys = virus_api.has_any_api_key()
    print(f"🔑 API Keys Configured: {has_keys}")
    
    if not has_keys:
        print("⚠️ No API keys found. Add to .env file:")
        print("   VIRUS_TOTAL_API_KEY=your_key_here")
        print("   URL_VOID_API_KEY=your_key_here")
        print("   HYBRID_ANALYSIS_API_KEY=your_key_here")
        print()
    
    # Test 2: Scan recent actual links (without live checks)
    print("🔍 Test 1: Scanning recent actual links (simulation mode)")
    result1 = scan_actual_links_from_database(
        limit=10,
        enable_live_checks=False  # Simulate without API keys
    )
    
    if result1['success']:
        print(f"✅ Scan completed successfully!")
        print(f"📊 Total links scanned: {result1['total_links_scanned']}")
        print(f"🚨 Malicious found: {result1['malicious_found']}")
        print(f"📋 Recommendations:")
        for rec in result1['recommendations']:
            print(f"   - {rec}")
    else:
        print(f"❌ Scan failed: {result1.get('error', 'Unknown error')}")
    
    print()
    
    # Test 3: Scan JavaScript links specifically
    print("🔍 Test 2: Scanning JavaScript links (simulation mode)")
    result2 = scan_actual_links_from_database(
        link_type='javascript',
        limit=5,
        enable_live_checks=False
    )
    
    if result2['success']:
        print(f"✅ JavaScript links scan completed!")
        print(f"📊 Total JavaScript links scanned: {result2['total_links_scanned']}")
        print(f"🚨 Malicious found: {result2['malicious_found']}")
    else:
        print(f"❌ JavaScript scan failed: {result2.get('error', 'Unknown error')}")
    
    print()
    
    # Test 4: Scan event handler links
    print("🔍 Test 3: Scanning event handler links (simulation mode)")
    result3 = scan_actual_links_from_database(
        link_type='event_handler',
        limit=5,
        enable_live_checks=False
    )
    
    if result3['success']:
        print(f"✅ Event handler links scan completed!")
        print(f"📊 Total event handler links scanned: {result3['total_links_scanned']}")
        print(f"🚨 Malicious found: {result3['malicious_found']}")
    else:
        print(f"❌ Event handler scan failed: {result3.get('error', 'Unknown error')}")
    
    print()
    
    # Test 5: Show how to use with live checks (if API keys available)
    if has_keys:
        print("🔍 Test 4: Live virus scan (with API keys)")
        print("⚠️ This will make actual API calls to virus detection services")
        
        # Uncomment the following lines to test live scanning
        # result4 = scan_actual_links_from_database(
        #     limit=3,
        #     enable_live_checks=True
        # )
        # 
        # if result4['success']:
        #     print(f"✅ Live scan completed!")
        #     print(f"📊 Total links scanned: {result4['total_links_scanned']}")
        #     print(f"🚨 Malicious found: {result4['malicious_found']}")
        # else:
        #     print(f"❌ Live scan failed: {result4.get('error', 'Unknown error')}")
    else:
        print("🔍 Test 4: Live virus scan (skipped - no API keys)")
        print("💡 Configure API keys in .env file to test live scanning")
    
    print()
    print("✅ Virus detection test completed!")
    print()
    print("📋 Usage in app.py:")
    print("""
    # Import the function
    from src.utils.virus_detection_api import scan_actual_links_from_database
    
    # Scan all recent links
    result = scan_actual_links_from_database(limit=50)
    
    # Scan specific case
    result = scan_actual_links_from_database(case_id="your_case_id")
    
    # Scan specific link type
    result = scan_actual_links_from_database(link_type="javascript")
    
    # Scan with live checks (requires API keys)
    result = scan_actual_links_from_database(enable_live_checks=True)
    """)

if __name__ == "__main__":
    test_virus_scan()
