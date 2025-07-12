import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.extract.risk_keyword_detector import detect_risk_keywords_from_html
import glob
import time
from datetime import datetime

def test_keyword_detection(filepath, page_name):
    print(f"\n{'='*80}")
    print(f"🔍 Testing: {page_name}")
    print(f"{'='*80}")
    results = {
        'ai': [],
        'rag_llm': [],
        'llm_only': [],
        'times': {'ai': 0, 'rag_llm': 0, 'llm_only': 0}
    }

    # AI Zero-shot
    print("🤖 AI Zero-shot classification:")
    start = time.time()
    try:
        ai_keywords = detect_risk_keywords_from_html(filepath, use_ai=True, use_llm=False, use_rag=False)
        results['ai'] = ai_keywords
        print(f"   Found: {len(ai_keywords)} keywords")
        print(f"   {ai_keywords}")
    except Exception as e:
        print(f"   ❌ AI Zero-shot failed: {e}")
    results['times']['ai'] = time.time() - start

    # RAG+LLM
    print("\n🧠 RAG+LLM (Self-Adaptive):")
    start = time.time()
    try:
        rag_keywords = detect_risk_keywords_from_html(filepath, use_ai=True, use_llm=True, use_rag=True)
        results['rag_llm'] = rag_keywords
        print(f"   Found: {len(rag_keywords)} keywords")
        print(f"   {rag_keywords}")
    except Exception as e:
        print(f"   ❌ RAG+LLM failed: {e}")
    results['times']['rag_llm'] = time.time() - start

    # LLM-only
    print("\n🤖 LLM-only:")
    start = time.time()
    try:
        llm_keywords = detect_risk_keywords_from_html(filepath, use_ai=True, use_llm=True, use_rag=False)
        results['llm_only'] = llm_keywords
        print(f"   Found: {len(llm_keywords)} keywords")
        print(f"   {llm_keywords}")
    except Exception as e:
        print(f"   ❌ LLM-only failed: {e}")
    results['times']['llm_only'] = time.time() - start

    print(f"\n⏱️  Times (seconds): AI: {results['times']['ai']:.2f} | RAG+LLM: {results['times']['rag_llm']:.2f} | LLM-only: {results['times']['llm_only']:.2f}")
    return results

def run_keyword_tests():
    print("🚀 Starting Self-Adaptive Keyword Detection Testing")
    print("="*100)
    test_files = glob.glob("data/darkweb_test_pages/*.html")
    if not test_files:
        print("❌ No test files found in data/darkweb_test_pages/")
        return
    all_results = []
    for filepath in test_files:
        page_name = os.path.basename(filepath)
        result = test_keyword_detection(filepath, page_name)
        all_results.append({
            'page': page_name,
            'ai': result['ai'],
            'rag_llm': result['rag_llm'],
            'llm_only': result['llm_only'],
            'ai_time': result['times']['ai'],
            'rag_time': result['times']['rag_llm'],
            'llm_time': result['times']['llm_only']
        })
    print("\n\n📊 SUMMARY:")
    for res in all_results:
        print(f"{res['page']}: AI={len(res['ai'])}, RAG+LLM={len(res['rag_llm'])}, LLM-only={len(res['llm_only'])}")
    print("\nDone.")

if __name__ == "__main__":
    run_keyword_tests() 