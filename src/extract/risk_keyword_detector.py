import os
import faiss
import numpy as np
from openai import OpenAI
from deep_translator import GoogleTranslator
from langdetect import detect
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
from src.extract.utils_visible_text import detect_suspicious_prompts

# === LLM Client (Together.ai) ===
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"
client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

# === Hugging Face Zero-Shot Classifier ===
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# === Knowledge base for RAG ===
knowledge_texts = [
    "DRUGS: meth, cocaine, heroin, LSD, MDMA, fentanyl, weed, marijuana, prescription, pharmacy, dealer, supplier, grams, ounces, kilos, pure, high quality, best price, bulk, wholesale, escrow, feedback, trusted vendor, verified, stealth shipping, decoy, vacuum sealed, tracking, express delivery, overnight, worldwide shipping, no customs, guaranteed delivery, money back, refund, reship, dispute, resolution, finalize, release, auto-finalize, FE, finalize early, multisig, 2FA, PGP, encryption, secure communication, protonmail, tutanota, onionmail, jabber, wickr, telegram, signal, encrypted messaging, darknet, deep web, hidden service, .onion, tor, vpn, proxy, anonymous, privacy, security, opsec, operational security, burner phone, disposable, temporary, fake identity, fake name, fake address, fake documents, fake ID, fake passport, fake driver license, fake social security, fake credit card, fake bank account, fake paypal, fake venmo, fake cashapp, fake zelle, fake western union, fake moneygram, fake bitcoin, fake ethereum, fake monero, fake litecoin, fake dash, fake zcash, fake ripple, fake cardano, fake polkadot, fake solana, fake avalanche, fake polygon, fake binance coin, fake tether, fake usdt, fake usdc, fake dai, fake busd, fake pax, fake tusd, fake gusd, fake husd, fake jusd, fake kusd, fake lusd, fake musd, fake nusd, fake ousd, fake pusd, fake qusd, fake rusd, fake susd, fake tusd, fake uusd, fake vusd, fake wusd, fake xusd, fake yusd, fake zusd",
    "WEAPONS: guns, firearms, weapons, ammo, ammunition, bullets, rounds, magazines, clips, silencers, suppressors, Glock, AK-47, AR-15, rifle, pistol, handgun, shotgun, sniper, scope, sights, laser, tactical, military, army, navy, air force, marines, special forces, delta force, seal team, ranger, green beret, commando, mercenary, private military, security contractor, bodyguard, protection, security, guard, bouncer, doorman, watchman, sentinel, lookout, scout, spy, informant, snitch, rat, traitor, betrayer, backstabber, double agent, mole, infiltrator, saboteur, terrorist, extremist, radical, fundamentalist, jihadist, militant, insurgent, rebel, revolutionary, freedom fighter, resistance, underground, clandestine, covert, secret, hidden, concealed, disguised, camouflaged, stealth, invisible, undetectable, untraceable, anonymous, nameless, faceless, unknown, unidentified, mysterious, enigmatic, cryptic, obscure, vague, ambiguous, unclear, uncertain, doubtful, suspicious, questionable, dubious, shady, sketchy, fishy, dodgy, suspicious, questionable, dubious, shady, sketchy, fishy, dodgy",
    "HACKING: exploit, vulnerability, zero-day, backdoor, rootkit, keylogger, trojan, virus, malware, ransomware, spyware, adware, botnet, DDoS, DoS, denial of service, distributed denial of service, SQL injection, XSS, cross-site scripting, CSRF, cross-site request forgery, LFI, local file inclusion, RFI, remote file inclusion, buffer overflow, stack overflow, heap overflow, integer overflow, format string, race condition, time of check to time of use, TOCTOU, use after free, double free, memory leak, null pointer dereference, segmentation fault, core dump, crash, hang, freeze, lockup, deadlock, livelock, starvation, priority inversion, convoy effect, thundering herd, stampede, avalanche, cascade, domino effect, butterfly effect, chaos theory, complexity theory, algorithmic complexity, computational complexity, time complexity, space complexity, big O notation, asymptotic analysis, worst case, best case, average case, expected case, amortized analysis, competitive analysis, online algorithms, offline algorithms, approximation algorithms, heuristic algorithms, greedy algorithms, dynamic programming, divide and conquer, recursion, iteration, loop, conditional, branching, jumping, calling, returning, pushing, popping, stacking, queuing, linking, chaining, hashing, sorting, searching, filtering, mapping, reducing, folding, unfolding, expanding, contracting, growing, shrinking, increasing, decreasing, ascending, descending, rising, falling, climbing, descending, going up, going down, moving up, moving down, traveling up, traveling down, journeying up, journeying down, ascending, descending, climbing, descending, going up, going down, moving up, moving down, traveling up, traveling down, journeying up, journeying down",
    "FRAUD: stolen, fake, counterfeit, forged, fraudulent, scam, phishing, vishing, smishing, pretexting, baiting, quid pro quo, tailgating, piggybacking, shoulder surfing, dumpster diving, social engineering, psychological manipulation, cognitive bias, confirmation bias, anchoring bias, availability bias, representativeness bias, hindsight bias, overconfidence bias, optimism bias, pessimism bias, negativity bias, positivity bias, selection bias, sampling bias, measurement bias, observer bias, experimenter bias, subject bias, participant bias, volunteer bias, self-selection bias, non-response bias, response bias, acquiescence bias, social desirability bias, demand characteristics, Hawthorne effect, placebo effect, nocebo effect, Pygmalion effect, Rosenthal effect, experimenter expectancy effect, observer expectancy effect, subject expectancy effect, participant expectancy effect, volunteer expectancy effect, self-selection expectancy effect, non-response expectancy effect, response expectancy effect, acquiescence expectancy effect, social desirability expectancy effect, demand characteristics expectancy effect, Hawthorne expectancy effect, placebo expectancy effect, nocebo expectancy effect, Pygmalion expectancy effect, Rosenthal expectancy effect",
    "IDENTITY THEFT: SSN, social security, driver license, passport, fullz, dox, personal information, PII, personally identifiable information, sensitive data, confidential data, private data, secret data, classified data, restricted data, proprietary data, trade secret, intellectual property, copyright, trademark, patent, license, permit, authorization, certification, accreditation, qualification, credential, diploma, degree, certificate, badge, token, key, password, PIN, passcode, access code, security code, verification code, authentication code, authorization code, confirmation code, validation code, approval code, acceptance code, agreement code, consent code, permission code, allowance code, authorization code, clearance code, approval code, acceptance code, agreement code, consent code, permission code, allowance code, authorization code, clearance code, approval code, acceptance code, agreement code, consent code, permission code, allowance code, authorization code, clearance code"
]

# Embedding model for knowledge base
model = SentenceTransformer("all-MiniLM-L6-v2")
knowledge_embeddings = model.encode(knowledge_texts)
dimension = knowledge_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(knowledge_embeddings))

def retrieve_context_self_adaptive(text, top_k=10, final_k=5, rationale=False, focus=None):
    # Step 1: Retrieve top_k entries
    query_text = text
    if focus:
        query_text += f"\n\nFocus: {focus}"
    query_embedding = model.encode([query_text])
    distances, indices = index.search(np.array(query_embedding), top_k)
    candidate_contexts = [knowledge_texts[i] for i in indices[0]]
    # Step 2: Use LLM to select the most relevant final_k entries, with rationale
    selection_prompt = f"""
Given the following knowledge base entries and the HTML/text content, select the {final_k} most relevant entries for keyword extraction. For each, return the number and a short rationale. Format: 1:reason,3:reason,5:reason

Knowledge base entries:
"""
    for idx, entry in enumerate(candidate_contexts):
        selection_prompt += f"{idx+1}. {entry}\n"
    selection_prompt += f"\nHTML/TEXT Content:\n{text[:1000]}\n\nReturn format: 1:reason,3:reason,5:reason"
    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": selection_prompt}],
            temperature=0.1,
            max_tokens=100
        )
        llm_output = response.choices[0].message.content.strip()
        # Parse output: e.g., "1:mentions drugs,3:mentions hacking,5:mentions fraud"
        selected = []
        rationales = []
        for part in llm_output.split(","):
            if ":" in part:
                idx_str, reason = part.split(":", 1)
                if idx_str.strip().isdigit():
                    idx = int(idx_str.strip()) - 1
                    if 0 <= idx < len(candidate_contexts):
                        selected.append(idx)
                        rationales.append((idx, reason.strip()))
        selected_contexts = [candidate_contexts[i] for i in selected][:final_k]
        if not selected_contexts:
            selected_contexts = candidate_contexts[:final_k]
        if rationale:
            rationale_text = "\n".join([f"{i+1}: {candidate_contexts[i]}\n  Reason: {r}" for i, r in rationales])
            return "\n".join(selected_contexts), rationale_text
        return "\n".join(selected_contexts)
    except Exception as e:
        print(f"[Self-Adaptive RAG] LLM selection failed: {e}")
        if rationale:
            return "\n".join(candidate_contexts[:final_k]), "[LLM selection failed]"
        return "\n".join(candidate_contexts[:final_k])

def extract_keywords_with_ai(text):
    """Extract keywords using AI zero-shot classification"""
    try:
        candidate_labels = [
            "drugs", "weapons", "hacking", "fraud", "child abuse",
            "fake documents", "exploit", "ransomware", "credit card dump",
            "botnet", "hitman", "forged passport", "zero-day"
        ]
        result = zero_shot_classifier(text, candidate_labels=candidate_labels, multi_label=True)
        
        keywords = []
        for label, score in zip(result["labels"], result["scores"]):
            if score > 0.5:
                keywords.append(label)
        
        return {"method": "ai_zero_shot", "results": keywords, "success": True}
    except Exception as e:
        return {"method": "ai_zero_shot", "results": [], "success": False, "error": str(e)}

def extract_keywords_with_llm_rag(text):
    """Extract keywords using LLM with RAG context"""
    try:
        retrieved_context, rationale_text = retrieve_context_self_adaptive(text, top_k=10, final_k=5, rationale=True)
        
        prompt = f"""
You are an expert dark web forensic analyst. Extract ALL risky keywords from the HTML content.

KNOWLEDGE BASE (use these as examples to find similar terms):
{retrieved_context}

TASK: Find ALL risky keywords in the HTML content, including:
1. Exact matches from the knowledge base
2. Synonyms and related terms
3. Abbreviations and code words
4. Misspellings and variations
5. Industry-specific terminology
6. Hidden or obfuscated references

HTML CONTENT:
{text[:3000]}

Return ONLY a comma-separated list of keywords. NO explanations or extra text.
Format: keyword1,keyword2,keyword3,keyword4
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        llm_output = response.choices[0].message.content.strip()
        raw_keywords = [kw.strip().lower() for kw in llm_output.split(",") if kw.strip()]
        
        # Enhanced cleanup: Remove sentences, keep only valid keywords
        cleaned_keywords = []
        for kw in raw_keywords:
            # Remove common sentence starters
            if kw.startswith(('the ', 'a ', 'an ', 'and ', 'or ', 'but ', 'in ', 'on ', 'at ', 'to ', 'for ', 'of ', 'with ', 'by ')):
                continue
            # Keep only single words or short phrases
            if len(kw) < 50 and not kw.endswith('.') and not kw.endswith('!') and not kw.endswith('?'):
                cleaned_keywords.append(kw)
        
        return {"method": "llm_rag", "results": cleaned_keywords, "success": True}
    except Exception as e:
        return {"method": "llm_rag", "results": [], "success": False, "error": str(e)}

def extract_keywords_with_llm_only(text):
    """Extract keywords using LLM without RAG context"""
    try:
        prompt = f"""
You are an expert dark web forensic analyst. Extract ALL risky keywords from the HTML content.

Look for keywords related to:
- Illegal drugs and substances
- Weapons and firearms
- Hacking and cybercrime
- Fraud and identity theft
- Illegal services

INSTRUCTIONS:
1. Extract ALL risky keywords you can find
2. Include both obvious and subtle references
3. Look for misspellings, abbreviations, and code words
4. Return ONLY a comma-separated list of keywords
5. NO explanations, sentences, or extra text

HTML CONTENT:
{text[:3000]}

Return format: keyword1,keyword2,keyword3,keyword4
"""
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        llm_output = response.choices[0].message.content.strip()
        raw_keywords = [kw.strip().lower() for kw in llm_output.split(",") if kw.strip()]
        
        # Enhanced cleanup: Remove sentences, keep only valid keywords
        cleaned_keywords = []
        for kw in raw_keywords:
            # Remove common sentence starters
            if kw.startswith(('the ', 'a ', 'an ', 'and ', 'or ', 'but ', 'in ', 'on ', 'at ', 'to ', 'for ', 'of ', 'with ', 'by ')):
                continue
            # Keep only single words or short phrases
            if len(kw) < 50 and not kw.endswith('.') and not kw.endswith('!') and not kw.endswith('?'):
                cleaned_keywords.append(kw)
        
        return {"method": "llm_only", "results": cleaned_keywords, "success": True}
    except Exception as e:
        return {"method": "llm_only", "results": [], "success": False, "error": str(e)}

def deduplicate_results(all_results):
    """Deduplicate results from multiple methods"""
    all_keywords = []
    method_results = {}
    
    for result in all_results:
        method = result["method"]
        keywords = result["results"]
        method_results[method] = keywords
        all_keywords.extend(keywords)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in all_keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return {
        "unique_results": unique_keywords,
        "method_results": method_results,
        "total_found": len(unique_keywords)
    }

def clean_keywords(keyword_list):
    """Clean and filter keywords to remove irrelevant content"""
    cleaned = []
    
    # Patterns to exclude
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    obfuscated_email_pattern = re.compile(r'.*[\[\(]at[\]\)].*[\[\(]dot[\]\)].*')
    payment_pattern = re.compile(r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,}$')
    domain_pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    for keyword in keyword_list:
        # Skip if it's an email address
        if email_pattern.match(keyword) or obfuscated_email_pattern.match(keyword):
            continue
            
        # Skip if it's a payment address
        if payment_pattern.match(keyword):
            continue
            
        # Skip if it's a domain name
        if domain_pattern.match(keyword):
            continue
            
        # Skip if it's too short (likely not meaningful)
        if len(keyword) < 3:
            continue
            
        # Skip if it's too long (likely a sentence or explanation)
        if len(keyword) > 50:
            continue
            
        # Skip if it contains spaces (likely a phrase or sentence)
        if ' ' in keyword:
            continue
            
        # Skip common irrelevant terms
        if keyword.lower() in ['btc', 'usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf', 'cny', 'inr', 'brl', 'mxn', 'krw', 'sgd', 'hkd', 'nzd', 'sek', 'nok', 'dkk', 'pln', 'czk', 'huf', 'ron', 'hrk', 'bgm', 'bgn', 'all', 'amd', 'azn', 'bam', 'byn', 'gel', 'kzt', 'kgs', 'mdl', 'mkd', 'rsd', 'tjs', 'tmt', 'uah', 'uzs', 'xcd', 'xof', 'xpf', 'yer', 'zmw', 'zwl']:
            continue
            
        # Skip if it's just a number or currency code
        if keyword.isdigit() or (len(keyword) <= 3 and keyword.isupper()):
            continue
            
        # Skip if it's a common file extension or technical term
        if keyword.lower() in ['.onion', '.org', '.com', '.net', '.io', '.co', '.me', '.tv', '.cc', '.ws', '.biz', '.info', '.name', '.pro', '.aero', '.coop', '.museum', '.jobs', '.mobi', '.travel', '.cat', '.asia', '.tel', '.xxx', '.post', '.int', '.edu', '.gov', '.mil']:
            continue
            
        cleaned.append(keyword)
    
    return cleaned

def detect_risk_keywords_from_html(filepath, use_llm=True, use_rag=True, use_ai=True, translate=True, min_keywords=5, max_loops=2):
    """Extract risk keywords using parallel processing and deduplication"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html_text = f.read()

            # Detect suspicious prompt injection attempts
            suspicious = detect_suspicious_prompts(html_text)
            if suspicious:
                print(f"⚠️ Suspicious prompt injection detected in {filepath}: {suspicious}")
                # Optionally, you could log or return this for reporting

            # === Language detection and translation ===
            if translate:
                try:
                    lang = detect(html_text)
                    if lang != "en":
                        html_text = GoogleTranslator(source='auto', target='en').translate(html_text)
                        print(f"🌐 Translated content from {lang} to English.")
                except Exception as e:
                    print(f"⚠️ Language detection/translation error: {e}")

            # Define extraction methods to run
            extraction_methods = []
            
            # Add AI methods if enabled
            if use_ai:
                extraction_methods.append(("ai_zero_shot", lambda: extract_keywords_with_ai(html_text)))
            
            # Add LLM methods if enabled
            if use_llm:
                if use_rag:
                    extraction_methods.append(("llm_rag", lambda: extract_keywords_with_llm_rag(html_text)))
                extraction_methods.append(("llm_only", lambda: extract_keywords_with_llm_only(html_text)))

            # Run methods in parallel
            all_results = []
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=len(extraction_methods)) as executor:
                # Submit all tasks
                future_to_method = {
                    executor.submit(method_func): method_name 
                    for method_name, method_func in extraction_methods
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_method):
                    method_name = future_to_method[future]
                    try:
                        result = future.result()
                        all_results.append(result)
                        
                        if result["success"]:
                            print(f"✅ {method_name.upper()}: Found {len(result['results'])} keywords")
                        else:
                            print(f"❌ {method_name.upper()}: Failed - {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        print(f"❌ {method_name.upper()}: Exception - {str(e)}")
                        all_results.append({
                            "method": method_name,
                            "results": [],
                            "success": False,
                            "error": str(e)
                        })

            # Deduplicate results
            final_results = deduplicate_results(all_results)
            
            processing_time = time.time() - start_time
            print(f"⏱️ Parallel processing completed in {processing_time:.2f} seconds")
            print(f"🎯 Total unique keywords found: {final_results['total_found']}")
            
            # Show method comparison
            print("\n📊 Method Comparison:")
            for method, keywords in final_results["method_results"].items():
                print(f"  {method.upper()}: {len(keywords)} keywords")
            
            # Clean keywords before returning
            cleaned_keywords = clean_keywords(final_results["unique_results"])
            return cleaned_keywords

    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return [] 