from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import textwrap

def generate_pdf_report(
    filename, hash_value, btc_list, email_list, keywords, score,
    level, case_id, investigator, notes, llm_summary="", suspicious_prompts=None
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
