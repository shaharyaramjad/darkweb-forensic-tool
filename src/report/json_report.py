import json
import os
from datetime import datetime

def generate_json_report(
    filename, hash_value, btc_list, email_list, keywords, pgp_content, financial_data, shipping_addresses, usernames, score,
    level, case_id, investigator, notes, llm_summary="", suspicious_prompts=None, document_ads_result=None, virus_detection_result=None
):
    os.makedirs("reports", exist_ok=True)
    report_filename = f"report_{filename.replace('.html', '')}.json"
    report_path = os.path.join("reports", report_filename)
    
    # Process document advertisements for better JSON structure
    processed_document_ads = {}
    if document_ads_result:
        # Count by risk level
        high_risk_urls = [url for url in document_ads_result.get('suspicious_urls', []) if url['risk_level'] == 'high']
        medium_risk_urls = [url for url in document_ads_result.get('suspicious_urls', []) if url['risk_level'] == 'medium']
        
        high_risk_ads = [ad for ad in document_ads_result.get('document_advertisements', []) if ad['suspicious_level'] == 'high']
        medium_risk_ads = [ad for ad in document_ads_result.get('document_advertisements', []) if ad['suspicious_level'] == 'medium']
        
        # Process actual links by type
        actual_links = document_ads_result.get('actual_links', [])
        links_by_type = {}
        for link in actual_links:
            link_type = link['type']
            if link_type not in links_by_type:
                links_by_type[link_type] = []
            links_by_type[link_type].append(link)
        
        processed_document_ads = {
            "summary": {
                "total_found": document_ads_result.get('total_found', 0),
                "actual_links_count": len(actual_links),
                "document_advertisements_count": len(document_ads_result.get('document_advertisements', [])),
                "suspicious_urls_count": len(document_ads_result.get('suspicious_urls', [])),
                "high_risk_urls": len(high_risk_urls),
                "medium_risk_urls": len(medium_risk_urls),
                "high_risk_ads": len(high_risk_ads),
                "medium_risk_ads": len(medium_risk_ads)
            },
            "link_summary": document_ads_result.get('link_summary', {}),
            "actual_links": actual_links,
            "links_by_type": links_by_type,
            "document_advertisements": document_ads_result.get('document_advertisements', []),
            "suspicious_urls": document_ads_result.get('suspicious_urls', []),
            "high_risk_urls": high_risk_urls,
            "medium_risk_urls": medium_risk_urls,
            "high_risk_ads": high_risk_ads,
            "medium_risk_ads": medium_risk_ads
        }
    
    report_data = {
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "case_id": case_id,
        "investigator": investigator,
        "description": notes,
        "file": filename,
        "sha256": hash_value,
        "suspicious_prompts": suspicious_prompts or [],
        "payment_addresses": btc_list or [],
        "emails": email_list or [],
        "risky_keywords": keywords or [],
        "pgp_content": pgp_content or [],
        "financial_data": financial_data or [],
        "shipping_addresses": shipping_addresses or [],
        "usernames": usernames or [],
        "risk_score": score,
        "severity": level,
        "llm_summary": llm_summary or "None",
        "document_advertisements": processed_document_ads,
        "virus_detection_results": virus_detection_result or {}
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"📄 JSON report generated: {report_filename}")
    return report_path
