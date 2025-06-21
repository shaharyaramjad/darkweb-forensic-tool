from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_pdf_report(filename, hash_value, btc_list, email_list, keywords, score, level):
    report_filename = f"report_{filename.replace('.html', '')}.pdf"
    c = canvas.Canvas(f"reports/{report_filename}", pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "🕵️ DarkWeb Forensic Report")
    
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    y -= 30
    c.drawString(50, y, f"📄 File: {filename}")

    y -= 20
    c.drawString(50, y, f"🔐 SHA-256: {hash_value}")

    y -= 30
    c.drawString(50, y, "✅ BTC Addresses:")
    for btc in btc_list or ["None"]:
        y -= 20
        c.drawString(70, y, f"- {btc}")

    y -= 30
    c.drawString(50, y, "📧 Emails:")
    for email in email_list or ["None"]:
        y -= 20
        c.drawString(70, y, f"- {email}")

    y -= 30
    c.drawString(50, y, "⚠️ Risky Keywords:")
    for keyword in keywords or ["None"]:
        y -= 20
        c.drawString(70, y, f"- {keyword}")

    y -= 30
    c.drawString(50, y, f"🔥 Risk Score: {score}")
    y -= 20
    c.drawString(50, y, f"🔒 Severity Level: {level.upper()}")

    c.save()
    print(f"📄 PDF report generated: {report_filename}")
