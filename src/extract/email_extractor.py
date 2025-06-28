import re
import os
from bs4 import BeautifulSoup
from huggingface_hub import InferenceClient

# Initialize StarPII client
client = InferenceClient(
    provider="hf-inference",
    api_key="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",
)

# Regex patterns
generic_email_re = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
obfuscated_email_re = re.compile(
    r'\b([a-zA-Z0-9._%+-]+)\s*(?:@|\[\s*at\s*\]|\s+at\s+)\s*([a-zA-Z0-9.-]+)\s*(?:\.|\[\s*dot\s*\]|\s+dot\s+)\s*([a-zA-Z]{2,})\b',
    re.IGNORECASE
)

def extract_emails_with_starpii(text):
    result = client.token_classification(text, model="bigcode/starpii")
    emails = []
    for entity in result:
        if entity['entity_group'].lower() == 'email':
            emails.append(entity['word'])
    return emails

def extract_emails(text):
    normal = generic_email_re.findall(text)
    obfuscated = [f"{m[0]}@{m[1]}.{m[2]}" for m in obfuscated_email_re.findall(text)]
    starpii_emails = extract_emails_with_starpii(text)
    return sorted(set(normal + obfuscated + starpii_emails))

def extract_emails_from_html(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    # Optional: extract clean text using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ')
    return extract_emails(text)
