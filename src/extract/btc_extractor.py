import re
from bs4 import BeautifulSoup

# Regular expression for BTC addresses
btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'

def extract_btc_from_html(file_path):
    btc_addresses = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()

            btc_addresses = re.findall(btc_pattern, text)

    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}: {e}")

    return btc_addresses
