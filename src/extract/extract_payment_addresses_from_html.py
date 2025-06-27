import re
from bs4 import BeautifulSoup

# Combined regex for multiple crypto/payment formats
payment_pattern = r"""
\b(
    [13][a-km-zA-HJ-NP-Z1-9]{25,34} |             # Bitcoin Legacy
    bc1[a-zA-HJ-NP-Z0-9]{11,71} |                 # Bitcoin Bech32
    0x[a-fA-F0-9]{40} |                           # Ethereum / ERC-20
    T[a-zA-Z0-9]{33} |                            # USDT TRC-20
    4[0-9AB][1-9A-HJ-NP-Za-km-z]{93} |            # Monero
    ltc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59} |# Litecoin Bech32
    L[a-km-zA-HJ-NP-Z1-9]{26,33} |                # Litecoin Legacy
    M[a-km-zA-HJ-NP-Z1-9]{26,33} |                # Litecoin M-type
    X[1-9A-HJ-NP-Za-km-z]{33} |                   # Dash
    t1[0-9A-Za-z]{33} |                           # Zcash Transparent
    U[0-9]{6,10}                                  # Perfect Money
)\b
"""

def extract_payment_addresses_from_html(file_path):
    matches = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()

            pattern = re.compile(payment_pattern, re.VERBOSE | re.IGNORECASE)
            matches = pattern.findall(text)

    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}: {e}")

    return matches
