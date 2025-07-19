import re
from bs4 import BeautifulSoup

def detect_suspicious_prompts(html_or_text):
    """
    Scan HTML or text for suspicious prompt injection attempts.
    Returns a list of suspicious phrases found.
    """
    # Combine HTML comments and text
    if '<' in html_or_text:
        soup = BeautifulSoup(html_or_text, 'html.parser')
        text = soup.get_text(separator=' ')
        comments = soup.find_all(string=lambda text: isinstance(text, type(soup.Comment)))
        all_text = text + ' ' + ' '.join(comments)
    else:
        all_text = html_or_text

    suspicious_phrases = [
        r'do not extract',
        r'don\'t extract',
        r'ignore all',
        r'ignore this',
        r'llm:',
        r'prompt:',
        r'ignore emails',
        r'ignore payment',
        r'ignore addresses',
        r'no extraction',
        r'please ignore',
        r'please do not',
        r'for ai only',
        r'for llm only',
        r'for model only',
        r'for prompt only',
        r'prompt injection',
        r'jailbreak',
        r'anti-extract',
        r'anti-detect',
        r'anti-forensic',
    ]
    found = []
    for phrase in suspicious_phrases:
        if re.search(phrase, all_text, re.IGNORECASE):
            found.append(phrase)
    return found 