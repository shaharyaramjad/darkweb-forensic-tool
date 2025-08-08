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
        draw_line("📄 Document Advertisements:", font="Helvetica-Bold", size=13, gap=20)
        draw_line(f"Total Items Found: {document_ads_result['total_found']}", indent=70)
        
        # Document advertisements
        if document_ads_result.get('document_advertisements'):
            draw_line("Document Ads:", font="Helvetica-Bold", size=12, gap=15)
            for ad in document_ads_result['document_advertisements']:
                risk_icon = "🔴" if ad['suspicious_level'] == 'high' else "🟡"
                content = ad['content'][:80] + "..." if len(ad['content']) > 80 else ad['content']
                draw_line(f"{risk_icon} {ad['type']}: {content}", indent=70, gap=15)
        
        # Suspicious URLs
        if document_ads_result.get('suspicious_urls'):
            draw_line("Suspicious URLs:", font="Helvetica-Bold", size=12, gap=15)
            for url_data in document_ads_result['suspicious_urls']:
                risk_icon = "🔴" if url_data['risk_level'] == 'high' else "🟡"
                url = url_data['url'][:60] + "..." if len(url_data['url']) > 60 else url_data['url']
                draw_line(f"{risk_icon} {url}", indent=70, gap=15)
                draw_line(f"   Reason: {url_data['suspicious_reason']}", indent=90, gap=12)
                if url_data.get('file_extension'):
                    draw_line(f"   File: {url_data['file_extension']}", indent=90, gap=12)
    else:
        draw_line("📄 Document Advertisements: None found", gap=20)

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
