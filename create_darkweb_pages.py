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
            
            <!-- Additional test data for extraction methods -->
            <p>For secure communication: secure(at)darkweb(dot)org</p>
            <p>Payment address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</p>
            <p>Keywords: drugs, weapons, hacking, fraud, money laundering</p>
        </div>
        
        <!-- Hidden contact info for testing -->
        <div class="hidden">
            Contact: vendor[at]protonmail[dot]com
            Backup: support(at)onionmail(dot)org
            Escrow: escrow(at)darkmarket(dot)onion
            Support: help(at)securemarket(dot)org
        </div>
        
        <!-- Obfuscated info -->
        <div class="obfuscated">
            For deals: ghost [at] tutanota [dot] com
            Secure: admin [ a t ] darkweb [ d o t ] market
            Bitcoin: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
            Monero: 4A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2W3x4Y5z6
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
            
            <!-- Additional test data for extraction methods -->
            <p>Contact: {market_data.get('Vendor Username', 'vendor')}(at)secure(dot)market</p>
            <p>Payment: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy</p>
            <p>Keywords: illegal, contraband, restricted, dangerous, prohibited</p>
        </div>
        
        <div class="feedback">
            <h4>Customer Feedback:</h4>
            {market_data.get('Feedback', 'No feedback available')}
        </div>
        
        <!-- Hidden contact info for testing -->
        <div class="hidden">
            Contact: {market_data.get('Vendor Username', 'vendor')}[at]protonmail[dot]com
            Support: help(at)darkmarket(dot)org
            Escrow: escrow(at)securemarket(dot)onion
            Backup: backup(at)darkweb(dot)org
        </div>
        
        <!-- Obfuscated contact -->
        <div class="obfuscated">
            For orders: {market_data.get('Vendor Username', 'vendor')} [at] secure [dot] market
            Escrow: escrow [ a t ] {market_data.get('Market', 'market')} [dot] onion
            Bitcoin: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
            Monero: 4A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2W3x4Y5z6
            Ethereum: 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6
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
        # Filter for posts with meaningful content and select 3 diverse samples
        forum_df = forum_df[forum_df['Post Content'].notnull()]
        forum_df = forum_df[forum_df['Post Content'].str.len() > 50]  # Posts with substantial content
        
        # Select 3 diverse samples: first, middle, and last
        selected_forum = []
        if len(forum_df) >= 3:
            selected_forum = [
                forum_df.iloc[0],  # First post
                forum_df.iloc[len(forum_df)//2],  # Middle post
                forum_df.iloc[-1]  # Last post
            ]
        else:
            selected_forum = forum_df.head(3).to_dict('records')
        
        for i, row in enumerate(selected_forum):
            html_content = create_darkweb_forum_page(row, i+1)
            filename = f"forum_page_{i+1}.html"
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Created {filename} with content length: {len(str(row.get('Post Content', '')))} chars")
    except Exception as e:
        print(f"⚠️ Error processing forum data: {e}")
    
    # Process marketplace data
    print("\n🛒 Creating marketplace pages...")
    try:
        market_df = pd.read_csv('dataset/market_data_obfuscated.csv')
        # Filter for listings with meaningful descriptions and select 3 diverse samples
        market_df = market_df[market_df['Item Description'].notnull()]
        market_df = market_df[market_df['Item Description'].str.len() > 30]  # Listings with substantial descriptions
        
        # Select 3 diverse samples: first, middle, and last
        selected_market = []
        if len(market_df) >= 3:
            selected_market = [
                market_df.iloc[0],  # First listing
                market_df.iloc[len(market_df)//2],  # Middle listing
                market_df.iloc[-1]  # Last listing
            ]
        else:
            selected_market = market_df.head(3).to_dict('records')
        
        for i, row in enumerate(selected_market):
            html_content = create_darkweb_marketplace_page(row, i+1)
            filename = f"marketplace_page_{i+1}.html"
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Created {filename} with description length: {len(str(row.get('Item Description', '')))} chars")
    except Exception as e:
        print(f"⚠️ Error processing marketplace data: {e}")
    
    total_pages = len(os.listdir(output_dir))
    print(f"\n🎉 Created {total_pages} test pages in {output_dir}/")
    print(f"📊 Summary:")
    print(f"   • Forum pages: 3 (with diverse content for testing)")
    print(f"   • Marketplace pages: 3 (with diverse listings for testing)")
    print(f"   • Total pages: {total_pages}")
    print(f"   • Each page contains test data for email, payment, and keyword extraction")
    return output_dir

if __name__ == "__main__":
    create_test_pages() 