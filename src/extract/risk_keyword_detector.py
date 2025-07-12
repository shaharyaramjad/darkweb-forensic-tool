import os
import faiss
import numpy as np
from openai import OpenAI
from deep_translator import GoogleTranslator
from langdetect import detect
from transformers import pipeline
from sentence_transformers import SentenceTransformer

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

def retrieve_context(text, k=5):
    query_embedding = model.encode([text])
    distances, indices = index.search(np.array(query_embedding), k)
    retrieved_contexts = [knowledge_texts[i] for i in indices[0]]
    return "\n".join(retrieved_contexts)

def detect_risk_keywords_from_html(filepath, use_llm=True, use_rag=True, use_ai=True, translate=True):
    found_keywords = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            html_text = f.read()

            # === Language detection and translation ===
            if translate:
                try:
                    lang = detect(html_text)
                    if lang != "en":
                        html_text = GoogleTranslator(source='auto', target='en').translate(html_text)
                        print(f"🌐 Translated content from {lang} to English.")
                except Exception as e:
                    print(f"⚠️ Language detection/translation error: {e}")

            # === AI Zero-shot classification check ===
            if use_ai:
                try:
                    candidate_labels = [
                        "drugs", "weapons", "hacking", "fraud", "child abuse",
                        "fake documents", "exploit", "ransomware", "credit card dump",
                        "botnet", "hitman", "forged passport", "zero-day"
                    ]
                    result = zero_shot_classifier(html_text, candidate_labels=candidate_labels, multi_label=True)

                    for label, score in zip(result["labels"], result["scores"]):
                        if score > 0.5:
                            found_keywords.append(label)
                    
                    if found_keywords:
                        print(f"✅ AI zero-shot classification found {len(found_keywords)} category matches.")
                    else:
                        print("⚠️ No keywords found using AI zero-shot classification.")
                except Exception as e:
                    print(f"⚠️ AI classification failed: {e}")

            # === RAG + LLM enhancement ===
            if use_llm:
                print("🔍 Using LLM to enhance keyword detection..." + (" (with RAG context)" if use_rag else " (no RAG context)"))

                try:
                    if use_rag:
                        retrieved_context = retrieve_context(html_text)
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

EXAMPLES of what to look for:
- Drug terms: meth, cocaine, heroin, weed, etc.
- Weapon terms: guns, ammo, silencers, etc.
- Hacking terms: exploit, malware, botnet, etc.
- Fraud terms: stolen, fake, counterfeit, etc.

HTML CONTENT:
{html_text[:3000]}

Return ONLY a comma-separated list of keywords. NO explanations or extra text.
Format: keyword1,keyword2,keyword3,keyword4
"""
                    else:
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
{html_text[:3000]}

Return format: keyword1,keyword2,keyword3,keyword4
"""

                    response = client.chat.completions.create(
                        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=500
                    )
                    llm_output = response.choices[0].message.content.strip()

                    # Split by comma and clean
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

                    # Combine AI and LLM results
                    all_keywords = found_keywords + cleaned_keywords
                    found_keywords = list(set(all_keywords))  # Remove duplicates
                    
                    print(f"✅ Enhanced keyword detection completed. Found {len(found_keywords)} total keywords." + (" (with RAG context)" if use_rag else " (no RAG context)"))
                except Exception as e:
                    print(f"❌ LLM enhancement failed: {e}")

    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")

    return list(set(found_keywords))  # Remove duplicates
