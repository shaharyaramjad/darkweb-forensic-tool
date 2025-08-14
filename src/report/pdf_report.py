from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import textwrap

def generate_pdf_report(
    filename, hash_value, btc_list, email_list, keywords, pgp_content, financial_data, shipping_addresses, usernames, score,
    level, case_id, investigator, notes, llm_summary="", suspicious_prompts=None, document_ads_result=None, virus_detection_result=None
):
    os.makedirs("reports", exist_ok=True)
    report_filename = f"report_{filename.replace('.html', '')}.pdf"
    report_path = os.path.join("reports", report_filename)
    c = canvas.Canvas(report_path, pagesize=A4)
    width, height = A4
    y = height - 50

    def draw_line(text, indent=50, font="Helvetica", size=12, gap=20):
        nonlocal y
        c.setFont(font, size)
        c.drawString(indent, y, text)
        y -= gap
        if y < 50:
            c.showPage()
            y = height - 50

    # ─── Header ───────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 16)
    draw_line("🕵️ DarkWeb Forensic Report", gap=30)

    draw_line(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    draw_line(f"🔎 Case ID: {case_id or 'N/A'}")
    draw_line(f"👮 Investigator: {investigator or 'N/A'}")
    draw_line(f"📝 Description: {notes or 'N/A'}")

    draw_line(f"📄 File: {filename}", gap=25)
    draw_line(f"🔐 SHA-256: {hash_value}", gap=25)

    # ─── Suspicious Prompts ──────────────────────────────────
    if suspicious_prompts:
        draw_line("⚠️ Suspicious Prompts Detected:", font="Helvetica-Bold", size=13, gap=20)
        for prompt in suspicious_prompts:
            draw_line(f"- {prompt}", indent=70, font="Helvetica", size=12, gap=18)
        draw_line("", gap=10)

    # ─── Hybrid Detection Results ─────────────────────────────
    draw_line("💰 Payment Addresses:")
    for addr in btc_list or ["None"]:
        draw_line(f"- {addr}", indent=70)

    draw_line("📧 Emails:")
    for email in email_list or ["None"]:
        draw_line(f"- {email}", indent=70)

    draw_line("⚠️ Risky Keywords:")
    for keyword in keywords or ["None"]:
        draw_line(f"- {keyword}", indent=70)

    draw_line("🔐 PGP Content:")
    if pgp_content:
        for pgp_item in pgp_content:
            pgp_type = pgp_item.get('type', 'unknown')
            content = pgp_item.get('content', '')[:50] + "..." if len(pgp_item.get('content', '')) > 50 else pgp_item.get('content', '')
            draw_line(f"- {pgp_type.upper()}: {content}", indent=70)
    else:
        draw_line("- None", indent=70)

    draw_line("💳 Financial Data:")
    if financial_data:
        for financial_item in financial_data:
            data_type = financial_item.get('type', 'unknown')
            content = financial_item.get('content', '')[:50] + "..." if len(financial_item.get('content', '')) > 50 else financial_item.get('content', '')
            draw_line(f"- {data_type.upper()}: {content}", indent=70)
    else:
        draw_line("- None", indent=70)

    draw_line("📦 Shipping Addresses:")
    if shipping_addresses:
        for shipping_item in shipping_addresses:
            data_type = shipping_item.get('type', 'unknown')
            content = shipping_item.get('content', '')[:50] + "..." if len(shipping_item.get('content', '')) > 50 else shipping_item.get('content', '')
            draw_line(f"- {data_type.upper()}: {content}", indent=70)
    else:
        draw_line("- None", indent=70)

    draw_line("👤 Usernames/Aliases:")
    if usernames:
        for username_item in usernames:
            data_type = username_item.get('type', 'unknown')
            content = username_item.get('content', '')[:50] + "..." if len(username_item.get('content', '')) > 50 else username_item.get('content', '')
            draw_line(f"- {data_type.upper()}: {content}", indent=70)
    else:
        draw_line("- None", indent=70)

    # ─── Document Advertisement Detection Results ──────────────
    if document_ads_result and document_ads_result.get('total_found', 0) > 0:
        draw_line("🔗 LINK EXTRACTION RESULTS:", font="Helvetica-Bold", size=16, gap=30)
        
        # Show comprehensive link summary
        if document_ads_result.get('link_summary'):
            link_summary = document_ads_result['link_summary']
            draw_line("📊 EXTRACTION SUMMARY:", font="Helvetica-Bold", size=13, gap=20)
            
            # Create a better summary layout
            total_links = link_summary.get('total_links', 0)
            draw_line(f"🔗 Total Links Extracted: {total_links}", font="Helvetica-Bold", size=12, gap=15)
            
            # Show breakdown in columns
            col1_items = [
                f"🔗 Hyperlinks: {link_summary.get('hyperlink_links', 0)}",
                f"📝 Text URLs: {link_summary.get('text_urls', 0)}",
                f"📁 Resources: {link_summary.get('resource_links', 0)}"
            ]
            
            col2_items = [
                f"💻 JavaScript: {link_summary.get('javascript_links', 0)}",
                f"⚡ Event Handlers: {link_summary.get('event_handler_links', 0)}",
                f"📊 Data Attributes: {link_summary.get('data_attribute_links', 0)}"
            ]
            
            # Display in two columns
            for i in range(max(len(col1_items), len(col2_items))):
                col1_text = col1_items[i] if i < len(col1_items) else ""
                col2_text = col2_items[i] if i < len(col2_items) else ""
                
                if col1_text and col2_text:
                    draw_line(f"{col1_text:<25} {col2_text}", indent=70, gap=12)
                elif col1_text:
                    draw_line(col1_text, indent=70, gap=12)
                elif col2_text:
                    draw_line(col2_text, indent=70, gap=12)
            
            draw_line("", gap=15)
        
        # Show actual links by category (improved formatting)
        if document_ads_result.get('actual_links'):
            draw_line("🔗 EXTRACTED LINKS SUMMARY:", font="Helvetica-Bold", size=14, gap=25)
            
            # Group links by type
            link_types = {}
            for link in document_ads_result['actual_links']:
                link_type = link['type']
                if link_type not in link_types:
                    link_types[link_type] = []
                link_types[link_type].append(link)
            
            # Display links by type with better formatting
            for link_type, links in link_types.items():
                type_icon = {
                    'hyperlink': '🔗',
                    'text_url': '📝',
                    'resource_link': '📁',
                    'javascript': '💻',
                    'event_handler': '⚡',
                    'data_attribute': '📊',
                    'css_inline': '🎨',
                    'css_tag': '🎨'
                }.get(link_type, '🔗')
                
                # Show type header with count
                draw_line(f"{type_icon} {link_type.upper()} LINKS ({len(links)} found):", font="Helvetica-Bold", size=12, gap=18)
                
                # Show only first 5 links of each type to avoid clutter
                max_links_per_type = 5
                for i, link in enumerate(links[:max_links_per_type], 1):
                    url = link['url']
                    link_text = link.get('link_text', '')
                    
                    # Truncate URL for display if too long
                    display_url = url[:50] + "..." if len(url) > 50 else url
                    display_text = link_text[:35] + "..." if len(link_text) > 35 else link_text
                    
                    # Show link with better formatting
                    if link_text and link_text != url and link_text.strip():
                        draw_line(f"  {i}. {display_text}", indent=70, gap=12)
                        draw_line(f"     → {display_url}", indent=85, gap=10, font="Helvetica", size=10)
                    else:
                        draw_line(f"  {i}. {display_url}", indent=70, gap=12)
                    
                    # Make it clickable with better positioning
                    try:
                        url_x = 85 if (link_text and link_text != url and link_text.strip()) else 70
                        url_y = y + 10
                        url_width = c.stringWidth(display_url, "Helvetica", 10 if (link_text and link_text != url and link_text.strip()) else 12)
                        
                        # Add link annotation
                        c.linkURL(url, (url_x, url_y, url_x + url_width, url_y + 12), relative=0)
                        
                        # Add blue underline to indicate it's clickable
                        c.setStrokeColorRGB(0, 0, 1)  # Blue color
                        c.line(url_x, url_y - 2, url_x + url_width, url_y - 2)
                        c.setStrokeColorRGB(0, 0, 0)  # Reset to black
                    except Exception as e:
                        # Fallback if link creation fails
                        pass
                    
                    # Add metadata in smaller font
                    metadata = f"Method: {link['method']} | Risk: {link['suspicious_level']}"
                    draw_line(f"     {metadata}", indent=85, gap=8, font="Helvetica", size=9)
                    
                    # Add spacing between links
                    draw_line("", gap=3)
                
                # Show count if more links exist
                if len(links) > max_links_per_type:
                    remaining = len(links) - max_links_per_type
                    draw_line(f"     ... and {remaining} more {link_type} links", indent=85, gap=10, font="Helvetica", size=9)
                
                # Add spacing between link types
                draw_line("", gap=8)
        
        # Show pattern-based document advertisements (concise)
        if document_ads_result.get('document_advertisements'):
            draw_line("🔍 PATTERN-BASED DETECTIONS:", font="Helvetica-Bold", size=13, gap=20)
            pattern_count = len(document_ads_result['document_advertisements'])
            draw_line(f"Pattern Items Found: {pattern_count}", indent=70, gap=15)
            
            # Show only first 3 pattern-based ads to save space
            for i, ad in enumerate(document_ads_result['document_advertisements'][:3], 1):
                risk_icon = "🔴" if ad['suspicious_level'] == 'high' else "🟡"
                content = ad['content'][:50] + "..." if len(ad['content']) > 50 else ad['content']
                draw_line(f"{risk_icon} {i}. {ad['type']}: {content}", indent=70, gap=12)
                draw_line(f"   Method: {ad['method']} | Risk: {ad['suspicious_level']}", indent=90, gap=8)
            
            if pattern_count > 3:
                draw_line(f"... and {pattern_count - 3} more pattern items", indent=70, gap=15)
            
            draw_line("", gap=10)
        
        # Show suspicious URLs (concise)
        if document_ads_result.get('suspicious_urls'):
            draw_line("⚠️ SUSPICIOUS URLS DETECTED:", font="Helvetica-Bold", size=13, gap=20)
            suspicious_count = len(document_ads_result['suspicious_urls'])
            draw_line(f"Suspicious URLs: {suspicious_count}", indent=70, gap=15)
            
            # Show only first 3 suspicious URLs to save space
            for i, url_data in enumerate(document_ads_result['suspicious_urls'][:3], 1):
                risk_icon = "🔴" if url_data['risk_level'] == 'high' else "🟡"
                url = url_data['url']
                display_url = url[:45] + "..." if len(url) > 45 else url
                draw_line(f"{risk_icon} {i}. {display_url}", indent=70, gap=12)
                
                # Make it clickable
                try:
                    url_x = 70
                    url_y = y + 10
                    url_width = c.stringWidth(display_url, "Helvetica", 12)
                    c.linkURL(url, (url_x, url_y, url_x + url_width, url_y + 12), relative=0)
                    c.setStrokeColorRGB(1, 0, 0) if url_data['risk_level'] == 'high' else c.setStrokeColorRGB(1, 0.5, 0)
                    c.line(url_x, url_y - 2, url_x + url_width, url_y - 2)
                    c.setStrokeColorRGB(0, 0, 0)
                except:
                    pass
                
                draw_line(f"   Risk: {url_data['risk_level']} | Reason: {url_data['suspicious_reason']}", indent=90, gap=8)
                if url_data.get('file_extension'):
                    draw_line(f"   File Type: {url_data['file_extension']}", indent=90, gap=8)
            
            if suspicious_count > 3:
                draw_line(f"... and {suspicious_count - 3} more suspicious URLs", indent=70, gap=15)
            
            draw_line("", gap=10)
    else:
        draw_line("🔗 No links or document advertisements found", gap=20)

    # ─── Virus Detection Results ──────────────────────────────
    if virus_detection_result and virus_detection_result.get('success'):
        draw_line("🦠 Virus Detection Results:", font="Helvetica-Bold", size=13, gap=20)
        
        api_results = virus_detection_result.get('api_results', {})
        draw_line(f"URLs Checked: {api_results.get('total_checked', 0)}", indent=70)
        draw_line(f"Malicious URLs: {api_results.get('malicious_found', 0)}", indent=70)
        draw_line(f"High Risk URLs: {len(api_results.get('high_risk_urls', []))}", indent=70)
        
        # Virus detection report
        if virus_detection_result.get('report'):
            report = virus_detection_result['report']
            draw_line("Summary:", font="Helvetica-Bold", size=12, gap=15)
            draw_line(f"Executable Files: {report['summary'].get('executable_files', 0)}", indent=70)
            draw_line(f"Malicious Downloads: {report['summary'].get('malicious_file_downloads', 0)}", indent=70)
            draw_line(f"Critical Threats: {report['summary'].get('critical_threats', 0)}", indent=70)
            
            # Recommendations
            if report.get('recommendations'):
                draw_line("Recommendations:", font="Helvetica-Bold", size=12, gap=15)
                for rec in report['recommendations']:
                    draw_line(f"• {rec}", indent=70, gap=15)
    else:
        draw_line("🦠 Virus Detection Results: Not available", gap=20)

    draw_line(f"🔥 Risk Score: {score}")
    draw_line(f"🔒 Severity Level: {level.upper()}", gap=30)

    # ─── LLM Summary ──────────────────────────────────────────
    draw_line("🤖 LLM Summary:")
    wrapped = textwrap.wrap(llm_summary or "None", width=100)
    for line in wrapped:
        draw_line(line, indent=70)

    c.save()
    print(f"📄 PDF report generated: {report_filename}")
    return report_path
