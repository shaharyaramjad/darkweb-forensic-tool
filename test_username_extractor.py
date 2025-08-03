#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.extract.username_extractor import extract_usernames_from_html

def test_username_extractor():
    """Test the username extractor with a sample file."""
    
    print("🧪 Testing Username Extractor")
    print("=" * 50)
    
    # Test file path
    test_file = "data/test_usernames.html"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Testing with file: {test_file}")
    print()
    
    # Test with all methods enabled
    print("🔍 Testing with all methods enabled...")
    results = extract_usernames_from_html(
        test_file,
        use_llm=True,
        use_rag=True,
        use_ai=True,
        translate=True
    )
    
    print("\n📊 Results Summary:")
    print(f"Total usernames found: {len(results)}")
    
    if results:
        print("\n👤 Usernames Found:")
        for i, item in enumerate(results, 1):
            print(f"{i}. Type: {item['type'].upper()}")
            print(f"   Username: {item['content']}")
            print(f"   Method: {item['method']}")
            print()
    else:
        print("❌ No usernames found")
    
    # Test with only regex
    print("\n🔍 Testing with regex only...")
    results_regex = extract_usernames_from_html(
        test_file,
        use_llm=False,
        use_rag=False,
        use_ai=False,
        translate=True
    )
    
    print(f"Regex found: {len(results_regex)} usernames")
    
    # Test with AI only
    print("\n🔍 Testing with AI only...")
    results_ai = extract_usernames_from_html(
        test_file,
        use_llm=False,
        use_rag=False,
        use_ai=True,
        translate=True
    )
    
    print(f"AI found: {len(results_ai)} usernames")
    
    print("\n✅ Username extractor test completed!")

if __name__ == "__main__":
    test_username_extractor() 