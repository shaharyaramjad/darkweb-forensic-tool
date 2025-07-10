import pandas as pd
import os
import random
from datetime import datetime

def create_darkweb_forum_page(post_data, page_num):
    """Create a realistic dark web forum page"""
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dark Web Forum - Thread {page_num}</title>
    <style>
        body {{ 
            background: #0a0a0a; 
            color: #e0e0e0; 
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            background: #1a1a1a;
            padding: 15px;
            border-bottom: 2px solid #333;
            margin-bottom: 20px;
        }}
        .forum-post {{
            background: #1a1a1a;
            border: 1px solid #333;
            margin: 10px 0;
            padding: 15px;
        }}
        .username {{
            color: #00ff00;
            font-weight: bold;
        }}
        .timestamp {{
            color: #888;
            font-size: 0.8em;
        }}
        .content {{
            margin-top: 10px;
            line-height: 1.4;
        }}
        .hidden {{
            display: none;
        }}
        .obfuscated {{
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕵️ Dark Web Forum</h1>
        <p>Thread: {post_data.get('Thread Title', 'General Discussion')}</p>
    </div>
    
    <div class="forum-post">
        <div class="username">{post_data.get('Username', 'Anonymous')}</div>
        <div class="timestamp">{post_data.get('Date', 'Unknown')} {post_data.get('Time', '')}</div>
        <div class="content">
            {post_data.get('Post Content', 'No content available')}
        </div>
        
        <!-- Hidden contact info for testing -->
        <div class="hidden">
            Contact: vendor[at]protonmail[dot]com
            Backup: support(at)onionmail(dot)org
        </div>
        
        <!-- Obfuscated info -->
        <div class="obfuscated">
            For deals: ghost [at] tutanota [dot] com
            Secure: admin [ a t ] darkweb [ d o t ] market
        </div>
    </div>
</body>
</html>
"""
    return html

def create_darkweb_marketplace_page(market_data, page_num):
    """Create a realistic dark web marketplace page"""
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dark Web Marketplace - Listing {page_num}</title>
    <style>
        body {{ 
            background: #0a0a0a; 
            color: #e0e0e0; 
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            background: #1a1a1a;
            padding: 15px;
            border-bottom: 2px solid #333;
            margin-bottom: 20px;
        }}
        .listing {{
            background: #1a1a1a;
            border: 1px solid #333;
            margin: 10px 0;
            padding: 20px;
        }}
        .vendor {{
            color: #00ff00;
            font-weight: bold;
            font-size: 1.2em;
        }}
        .price {{
            color: #ffaa00;
            font-size: 1.1em;
        }}
        .category {{
            color: #888;
            font-style: italic;
        }}
        .description {{
            margin: 15px 0;
            line-height: 1.4;
        }}
        .feedback {{
            background: #2a2a2a;
            padding: 10px;
            margin: 10px 0;
            border-left: 3px solid #00ff00;
        }}
        .hidden {{
            display: none;
        }}
        .obfuscated {{
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 Dark Web Marketplace</h1>
        <p>Secure • Anonymous • Reliable</p>
    </div>
    
    <div class="listing">
        <div class="vendor">Vendor: {market_data.get('Vendor Username', 'Anonymous')}</div>
        <div class="price">Price: ${market_data.get('USD Price (median)', '0.00')}</div>
        <div class="category">Category: {market_data.get('Product Category', 'General')}</div>
        
        <div class="description">
            <h3>Product Description:</h3>
            {market_data.get('Item Description', 'No description available')}
        </div>
        
        <div class="feedback">
            <h4>Customer Feedback:</h4>
            {market_data.get('Feedback', 'No feedback available')}
        </div>
        
        <!-- Hidden contact info for testing -->
        <div class="hidden">
            Contact: {market_data.get('Vendor Username', 'vendor')}[at]protonmail[dot]com
            Support: help(at)darkmarket(dot)org
        </div>
        
        <!-- Obfuscated contact -->
        <div class="obfuscated">
            For orders: {market_data.get('Vendor Username', 'vendor')} [at] secure [dot] market
            Escrow: escrow [ a t ] {market_data.get('Market', 'market')} [dot] onion
        </div>
    </div>
</body>
</html>
"""
    return html

def create_test_pages():
    """Create realistic dark web HTML pages from dataset"""
    
    # Create output directory
    output_dir = "data/darkweb_test_pages"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process forum data
    print("📄 Creating forum pages...")
    try:
        forum_df = pd.read_csv('dataset/forum_data_part1.csv')
        forum_df = forum_df[forum_df['Post Content'].notnull()].head(10)  # First 10 posts
        
        for i, row in forum_df.iterrows():
            html_content = create_darkweb_forum_page(row, i+1)
            filename = f"forum_page_{i+1}.html"
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Created {filename}")
    except Exception as e:
        print(f"⚠️ Error processing forum data: {e}")
    
    # Process marketplace data
    print("\n🛒 Creating marketplace pages...")
    try:
        market_df = pd.read_csv('dataset/market_data_obfuscated.csv')
        market_df = market_df[market_df['Item Description'].notnull()].head(10)  # First 10 listings
        
        for i, row in market_df.iterrows():
            html_content = create_darkweb_marketplace_page(row, i+1)
            filename = f"marketplace_page_{i+1}.html"
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Created {filename}")
    except Exception as e:
        print(f"⚠️ Error processing marketplace data: {e}")
    
    print(f"\n🎉 Created {len(os.listdir(output_dir))} test pages in {output_dir}/")
    return output_dir

if __name__ == "__main__":
    create_test_pages() 