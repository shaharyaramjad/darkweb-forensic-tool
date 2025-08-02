#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.extract.shipping_address_extractor import extract_shipping_addresses_from_html

def test_shipping_extractor():
    """Test the shipping address extractor with a sample file."""
    
    print("🧪 Testing Shipping Address Extractor")
    print("=" * 50)
    
    # Test file path
    test_file = "data/test_shipping.html"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Testing with file: {test_file}")
    print()
    
    # Test with all methods enabled
    print("🔍 Testing with all methods enabled...")
    results = extract_shipping_addresses_from_html(
        test_file,
        use_llm=True,
        use_rag=True,
        use_ai=True,
        translate=True
    )
    
    print("\n📊 Results Summary:")
    print(f"Total shipping items found: {len(results)}")
    
    if results:
        print("\n📍 Shipping Items Found:")
        for i, item in enumerate(results, 1):
            print(f"{i}. Type: {item['type'].upper()}")
            print(f"   Content: {item['content']}")
            print(f"   Method: {item['method']}")
            print()
    else:
        print("❌ No shipping items found")
    
    # Test with only regex
    print("\n🔍 Testing with regex only...")
    results_regex = extract_shipping_addresses_from_html(
        test_file,
        use_llm=False,
        use_rag=False,
        use_ai=False,
        translate=True
    )
    
    print(f"Regex found: {len(results_regex)} items")
    
    # Test with AI only
    print("\n🔍 Testing with AI only...")
    results_ai = extract_shipping_addresses_from_html(
        test_file,
        use_llm=False,
        use_rag=False,
        use_ai=True,
        translate=True
    )
    
    print(f"AI found: {len(results_ai)} items")
    
    print("\n✅ Shipping address extractor test completed!")

if __name__ == "__main__":
    test_shipping_extractor() 