#!/usr/bin/env python3
"""
Test script for PGP extractor functionality
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from src.extract.pgp_extractor import extract_pgp_from_html

def test_pgp_extractor():
    """Test the PGP extractor with a sample file"""
    
    print("🔐 Testing PGP Extractor")
    print("=" * 50)
    
    # Test file path
    test_file = "data/test_pgp.html"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Test with different configurations
        print("\n1️⃣ Testing with Regex only...")
        results_regex = extract_pgp_from_html(test_file, use_llm=False, use_rag=False, use_ai=False, translate=False)
        print(f"✅ Regex found {len(results_regex)} PGP items")
        
        print("\n2️⃣ Testing with LLM only...")
        results_llm = extract_pgp_from_html(test_file, use_llm=True, use_rag=False, use_ai=False, translate=False)
        print(f"✅ LLM found {len(results_llm)} PGP items")
        
        print("\n3️⃣ Testing with RAG+LLM...")
        results_rag = extract_pgp_from_html(test_file, use_llm=True, use_rag=True, use_ai=False, translate=False)
        print(f"✅ RAG+LLM found {len(results_rag)} PGP items")
        
        # Display results
        print("\n📊 Results Summary:")
        print(f"Regex: {len(results_regex)} items")
        print(f"LLM: {len(results_llm)} items")
        print(f"RAG+LLM: {len(results_rag)} items")
        
        # Show detailed results
        print("\n🔍 Detailed Results:")
        for i, result in enumerate(results_rag, 1):
            pgp_type = result.get('type', 'unknown')
            content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
            confidence = result.get('confidence', 'unknown')
            print(f"{i}. Type: {pgp_type.upper()}")
            print(f"   Content: {content}")
            print(f"   Confidence: {confidence}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_pgp_extractor()
    if success:
        print("✅ PGP extractor test completed successfully!")
    else:
        print("❌ PGP extractor test failed!") 