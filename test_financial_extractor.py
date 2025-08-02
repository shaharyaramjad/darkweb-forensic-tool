#!/usr/bin/env python3
"""
Test script for financial data extractor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.extract.financial_data_extractor import extract_financial_data_from_html

def test_financial_extractor():
    """Test the financial data extractor with sample HTML."""
    
    # Test HTML with various financial data
    test_html = """
    <html>
    <body>
        <h1>Payment Information</h1>
        <p>Card Number: 4111111111111111</p>
        <p>CVV: 123</p>
        <p>Expiry Date: 12/25</p>
        <p>IBAN: DE89370400440532013000</p>
        <p>SWIFT Code: DEUTDEFF</p>
        <p>Account Number: 1234567890</p>
        <p>Routing Number: 021000021</p>
    </body>
    </html>
    """
    
    print("🔍 Testing Financial Data Extractor...")
    print("=" * 50)
    
    try:
        # Extract financial data
        financial_data = extract_financial_data_from_html(test_html)
        
        print(f"✅ Found {len(financial_data)} financial data items:")
        print()
        
        # Group by type
        by_type = {}
        for item in financial_data:
            data_type = item['type']
            if data_type not in by_type:
                by_type[data_type] = []
            by_type[data_type].append(item)
        
        # Display results
        for data_type, items in by_type.items():
            print(f"📊 {data_type.upper()} ({len(items)} items):")
            for item in items:
                print(f"   • {item['content']} (via {item['method']})")
            print()
        
        # Summary
        print("=" * 50)
        print(f"🎯 Total unique financial data items: {len(financial_data)}")
        
        # Test with actual file
        test_file = "data/test_financial.html"
        if os.path.exists(test_file):
            print(f"\n📁 Testing with file: {test_file}")
            with open(test_file, 'r', encoding='utf-8') as f:
                file_html = f.read()
            
            file_results = extract_financial_data_from_html(file_html)
            print(f"✅ Found {len(file_results)} financial data items from file")
            
            # Show file results
            by_type_file = {}
            for item in file_results:
                data_type = item['type']
                if data_type not in by_type_file:
                    by_type_file[data_type] = []
                by_type_file[data_type].append(item)
            
            for data_type, items in by_type_file.items():
                print(f"📊 {data_type.upper()} ({len(items)} items):")
                for item in items:
                    print(f"   • {item['content']} (via {item['method']})")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing financial extractor: {e}")
        return False

if __name__ == "__main__":
    success = test_financial_extractor()
    if success:
        print("✅ Financial data extractor test completed successfully!")
    else:
        print("❌ Financial data extractor test failed!")
        sys.exit(1) 