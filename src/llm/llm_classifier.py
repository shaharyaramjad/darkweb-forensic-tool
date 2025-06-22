import os
from openai import OpenAI

# 🧪 For testing: Enter your Together.ai API key as a string
TOGETHER_API_KEY = "1198a6fc34e0f74feb1a65172609d1401d30de7344f7ef6fb4833d5c12e3cad2"

client = OpenAI(
    base_url="https://api.together.ai/",
    api_key=TOGETHER_API_KEY,
)

def classify_with_llm(html_text):
    if not TOGETHER_API_KEY:
        return "⚠️ No API Key found."

    prompt = f"""
You are an AI forensic assistant helping to analyze HTML content extracted from dark web sources.

Please identify and summarize **any potentially illegal, suspicious, unethical, or harmful activity** mentioned in the following HTML. Focus on identifying categories such as:

- Illicit marketplaces
- Violence or extremist content
- Illegal services or offers
- Fraud, financial scams, or stolen data
- Weapons, drugs, counterfeit documents
- Abuse material or exploitation
- Hacking tools or guides

Only return the **relevant category labels** or short descriptions. If no suspicious content is detected, return "None".

HTML CONTENT:
{html_text[:2000]}
"""

    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error from LLM API: {str(e)}"
