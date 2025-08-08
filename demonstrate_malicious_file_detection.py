#!/usr/bin/env python3
"""
Demonstration script for malicious file detection workflow
Shows complete integration from detection to virus API to database storage
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.extract.document_advertisement_detector import extract_document_advertisements_from_html
from src.utils.virus_detection_api import VirusDetectionAPI, process_document_advertisements_for_virus_detection
from src.utils.db_insert import insert_into_db

def create_realistic_darkweb_content():
    """Create realistic dark web content with malicious file advertisements"""
    content = """
    <html>
    <head><title>Dark Web Marketplace - Premium Services</title></head>
    <body>
        <div class="header">
            <h1>🕸️ Dark Web Premium Services</h1>
            <p>Exclusive access to premium tools and services</p>
        </div>
        
        <div class="malware-section">
            <h2>🔥 Premium Malware Downloads</h2>
            <p>Latest undetected malware for professional use:</p>
            <ul>
                <li><a href="https://malware-distribution.net/download/trojan-stealer.exe">Download Trojan Stealer - Undetected</a></li>
                <li><a href="https://evil-tools.com/files/keylogger-pro.msi">Keylogger Pro - Stealth Mode</a></li>
                <li><a href="https://darkweb.org/malware/remote-access.bat">Remote Access Tool - Full Control</a></li>
                <li><a href="https://malicious-tools.net/spyware.ps1">PowerShell Spyware - Bypass Antivirus</a></li>
                <li><a href="https://crypto-miner.org/download/miner.exe">Crypto Miner - Destroy Performance</a></li>
            </ul>
        </div>
        
        <div class="fake-documents">
            <h2>🆔 Fake Document Services</h2>
            <p>High quality fake identification documents:</p>
            <ul>
                <li>Premium fake passport service - undetectable quality</li>
                <li>Counterfeit driver license generator - realistic holograms</li>
                <li>Forged certificate templates - professional grade</li>
                <li>Custom ID creation - personalized documents</li>
            </ul>
        </div>
        
        <div class="malware-tools">
            <h2>🛠️ Malware Development Tools</h2>
            <p>Professional malware development services:</p>
            <ul>
                <li>Virus builder - create custom malware payloads</li>
                <li>Spyware generator - undetected by all antivirus</li>
                <li>Backdoor creator - stealth mode operation</li>
                <li>RAT builder - remote access and control</li>
                <li>Botnet creator - mass infection tools</li>
            </ul>
        </div>
        
        <div class="suspicious-downloads">
            <h2>📁 Confidential Downloads</h2>
            <p>Access to sensitive documents and files:</p>
            <ul>
                <li><a href="https://suspicious-site.com/files/confidential.pdf">Confidential Document - Premium Access</a></li>
                <li><a href="https://download.net/archive.zip">Compressed Archive - Multiple Files</a></li>
                <li><a href="https://malware-installer.com/setup.exe">Software Installer - Professional Tools</a></li>
                <li><a href="https://darkweb.org/files/backdoor.scr">Screen Saver - Hidden Backdoor</a></li>
            </ul>
        </div>
        
        <div class="contact">
            <h2>📞 Contact Information</h2>
            <p>For premium services and custom malware development:</p>
            <ul>
                <li>Email: malware@darkweb.org</li>
                <li>Telegram: @malware_services</li>
                <li>Wickr: malware_provider</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return content

def demonstrate_complete_workflow():
    """Demonstrate the complete malicious file detection workflow"""
    print("🕸️ Dark Web Malicious File Detection Workflow")
    print("=" * 70)
    
    # Step 1: Create test content
    print("\n📋 Step 1: Creating realistic dark web content...")
    test_file = "darkweb_malicious_content.html"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(create_realistic_darkweb_content())
    
    try:
        # Step 2: Document advertisement detection
        print("🔍 Step 2: Running enhanced document advertisement detection...")
        detection_results = extract_document_advertisements_from_html(
            test_file,
            use_llm=False,  # Disable LLM for demo (API issues)
            use_rag=False,
            use_ai=True,
            translate=False
        )
        
        print(f"✅ Detection completed! Found {detection_results['total_found']} items")
        
        # Step 3: Virus detection API processing
        print("\n🦠 Step 3: Processing with virus detection API...")
        virus_api = VirusDetectionAPI()
        
        # Process document advertisements for virus detection
        virus_results = process_document_advertisements_for_virus_detection(detection_results)
        
        if virus_results['success']:
            print("✅ Virus detection processing completed successfully")
        else:
            print(f"❌ Virus detection processing failed: {virus_results.get('error')}")
        
        # Step 4: Generate comprehensive reports
        print("\n📄 Step 4: Generating comprehensive reports...")
        
        # Investigation report
        if 'investigation_report' in detection_results:
            inv_report = detection_results['investigation_report']
            print(f"📊 Investigation Report Summary:")
            print(f"  Critical Threats: {inv_report['summary']['critical_threats']}")
            print(f"  Executable Files: {inv_report['summary']['executable_files']}")
            print(f"  Malicious Downloads: {inv_report['summary']['malicious_file_downloads']}")
            print(f"  Requires Action: {inv_report['summary']['requires_immediate_action']}")
        
        # Virus detection report
        if virus_results['success'] and 'report' in virus_results:
            virus_report = virus_results['report']
            print(f"\n🦠 Virus Detection Report Summary:")
            print(f"  Executable Files: {virus_report['summary']['executable_files']}")
            print(f"  Malicious Downloads: {virus_report['summary']['malicious_file_downloads']}")
            print(f"  Critical Threats: {virus_report['summary']['critical_threats']}")
            print(f"  Manual Investigation Required: {virus_report['summary']['requires_manual_investigation']}")
        
        # Step 5: Prepare database insertion data
        print("\n💾 Step 5: Preparing data for database storage...")
        
        # Extract data for database
        document_ads = detection_results['document_advertisements']
        suspicious_urls = detection_results['suspicious_urls']
        virus_data = detection_results['virus_detection_data']
        
        # Prepare data for database insertion
        case_id = f"darkweb_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        investigator = "Automated Forensic Tool"
        notes = f"Dark web malicious file detection analysis. Found {len(document_ads)} document advertisements and {len(suspicious_urls)} suspicious URLs."
        
        # Extract emails, payment addresses, etc. (empty for this demo)
        emails = []
        payment_addresses = []
        keywords = [ad['content'] for ad in document_ads if ad['suspicious_level'] == 'high']
        pgp_content = []
        financial_data = []
        shipping_addresses = []
        usernames = []
        
        # Calculate risk score
        high_risk_count = len([ad for ad in document_ads if ad['suspicious_level'] == 'high'])
        executable_count = len(virus_data.get('executable_files', []))
        malicious_downloads = len(virus_data.get('malicious_file_downloads', []))
        
        risk_score = (high_risk_count * 10) + (executable_count * 20) + (malicious_downloads * 15)
        
        # Determine severity
        if risk_score >= 50:
            severity = "CRITICAL"
        elif risk_score >= 30:
            severity = "HIGH"
        elif risk_score >= 15:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        # Generate LLM summary
        llm_summary = f"Analysis detected {len(document_ads)} document advertisements including {malicious_downloads} malicious file downloads. "
        llm_summary += f"Found {executable_count} executable files and {len(suspicious_urls)} suspicious URLs. "
        llm_summary += f"Risk score: {risk_score} ({severity} severity). Manual investigation required."
        
        # File hash (simulated)
        file_hash = "sha256:demo_hash_for_darkweb_content_analysis"
        
        # Prepare document advertisements data for database
        document_ads_data = {
            'document_advertisements': document_ads,
            'suspicious_urls': suspicious_urls
        }
        
        print(f"📊 Prepared data for database:")
        print(f"  Case ID: {case_id}")
        print(f"  Risk Score: {risk_score}")
        print(f"  Severity: {severity}")
        print(f"  Document Ads: {len(document_ads)}")
        print(f"  Suspicious URLs: {len(suspicious_urls)}")
        print(f"  Executable Files: {executable_count}")
        print(f"  Malicious Downloads: {malicious_downloads}")
        
        # Step 6: Database insertion (simulated)
        print("\n💾 Step 6: Simulating database insertion...")
        print("📋 Data prepared for database storage:")
        print(f"  - Case metadata with risk score {risk_score}")
        print(f"  - {len(document_ads)} document advertisements")
        print(f"  - {len(suspicious_urls)} suspicious URLs")
        print(f"  - {len(keywords)} high-risk keywords")
        print(f"  - Comprehensive virus detection data")
        
        # Step 7: Generate final report
        print("\n📋 Step 7: Generating final forensic report...")
        
        final_report = {
            'case_id': case_id,
            'timestamp': datetime.now().isoformat(),
            'investigator': investigator,
            'risk_score': risk_score,
            'severity': severity,
            'summary': {
                'document_advertisements': len(document_ads),
                'suspicious_urls': len(suspicious_urls),
                'executable_files': executable_count,
                'malicious_downloads': malicious_downloads,
                'high_risk_items': high_risk_count
            },
            'critical_findings': [],
            'recommendations': [],
            'manual_investigation_required': []
        }
        
        # Add critical findings
        if executable_count > 0:
            final_report['critical_findings'].append({
                'type': 'EXECUTABLE_FILES',
                'severity': 'CRITICAL',
                'description': f'Found {executable_count} executable files that could install malware',
                'action': 'BLOCK ALL EXECUTABLE DOWNLOADS IMMEDIATELY'
            })
        
        if malicious_downloads > 0:
            final_report['critical_findings'].append({
                'type': 'MALICIOUS_DOWNLOADS',
                'severity': 'HIGH',
                'description': f'Found {malicious_downloads} advertisements for malicious file downloads',
                'action': 'INVESTIGATE ALL MALICIOUS FILE ADVERTISEMENTS'
            })
        
        # Add recommendations
        if risk_score >= 30:
            final_report['recommendations'].append('🚨 IMMEDIATE ACTION REQUIRED: Block all suspicious downloads')
            final_report['recommendations'].append('🔍 MANUAL INVESTIGATION: Review all URLs for malware')
            final_report['recommendations'].append('📋 FORENSIC DOCUMENTATION: Document findings for legal purposes')
        else:
            final_report['recommendations'].append('✅ Continue monitoring - no critical threats detected')
        
        # Add manual investigation tasks
        if executable_count > 0:
            final_report['manual_investigation_required'].append({
                'task': 'Review executable files',
                'priority': 'CRITICAL',
                'count': executable_count
            })
        
        if malicious_downloads > 0:
            final_report['manual_investigation_required'].append({
                'task': 'Investigate malicious downloads',
                'priority': 'HIGH',
                'count': malicious_downloads
            })
        
        # Display final report
        print(f"\n📄 FINAL FORENSIC REPORT")
        print("=" * 70)
        print(f"Case ID: {final_report['case_id']}")
        print(f"Risk Score: {final_report['risk_score']} ({final_report['severity']})")
        print(f"Timestamp: {final_report['timestamp']}")
        
        print(f"\n📊 Summary:")
        for key, value in final_report['summary'].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        if final_report['critical_findings']:
            print(f"\n🚨 Critical Findings:")
            for finding in final_report['critical_findings']:
                print(f"  {finding['type']}: {finding['description']}")
                print(f"     Action: {finding['action']}")
        
        if final_report['recommendations']:
            print(f"\n📋 Recommendations:")
            for rec in final_report['recommendations']:
                print(f"  {rec}")
        
        if final_report['manual_investigation_required']:
            print(f"\n🔍 Manual Investigation Required:")
            for task in final_report['manual_investigation_required']:
                print(f"  {task['priority']}: {task['task']} ({task['count']} items)")
        
        print("\n" + "=" * 70)
        print("✅ Complete malicious file detection workflow demonstrated!")
        print("=" * 70)
        
        # Clean up
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ Workflow demonstration failed: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    demonstrate_complete_workflow() 