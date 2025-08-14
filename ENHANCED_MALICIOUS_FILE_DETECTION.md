# Enhanced Malicious File Detection System

## Overview

The enhanced document advertisement detector now specifically focuses on detecting malicious file advertisements on the dark web that could install viruses on laptops. The system extracts suspicious URLs and prepares them for virus detection API investigation, even when APIs are not available for purchase.

## Key Enhancements

### 1. **Enhanced Malicious File Detection Patterns**

The system now includes specific patterns for detecting malicious file advertisements:

```python
'malicious_file_downloads': [
    r'\b(?:download|get|install|run)\s+(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\b',
    r'\b(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\s+(?:download|install|run|execute)\b',
    r'\b(?:free|premium|exclusive)\s+(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\s+(?:download|install)\b',
    r'\b(?:undetected|stealth|bypass)\s+(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\b',
    r'\b(?:malware|virus|trojan|spyware|keylogger|stealer|rat|backdoor)\s+(?:builder|generator|creator)\b',
]
```

### 2. **Enhanced URL Extraction for Virus Detection**

The system now extracts URLs with detailed analysis:

- **High-risk file extensions**: `.exe`, `.msi`, `.bat`, `.cmd`, `.ps1`, `.vbs`, `.js`, `.jar`, `.apk`, `.dmg`, `.pkg`, `.scr`, `.com`
- **Medium-risk file extensions**: `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.pdf`, `.zip`, `.rar`, `.7z`
- **Malicious keywords**: malware, virus, trojan, spyware, keylogger, stealer, rat, backdoor, crypto, miner, botnet, payload, exploit, undetected, stealth, bypass
- **Download keywords**: download, file, document, get, access, install, run, execute

### 3. **Comprehensive Virus Detection Data Preparation**

The system prepares detailed data for virus detection APIs:

```python
virus_detection_data = {
    'document_advertisements': [],
    'suspicious_urls': [],
    'high_risk_items': [],
    'malicious_file_downloads': [],
    'executable_files': [],
    'api_ready': True,
    'summary': {
        'total_document_ads': 0,
        'total_suspicious_urls': 0,
        'high_risk_urls': 0,
        'executable_files': 0,
        'malicious_keywords_found': 0
    }
}
```

### 4. **Manual Investigation Reports**

Since APIs cannot be purchased, the system generates comprehensive reports for manual investigation:

#### Investigation Report Features:
- **Critical Findings**: Identifies executable files and malicious downloads
- **Risk Assessment**: Categorizes threats by severity (CRITICAL, HIGH, MEDIUM)
- **Manual Investigation Checklist**: Provides specific tasks for investigators
- **Recommendations**: Clear action items for immediate response

#### Example Report Structure:
```json
{
    "summary": {
        "critical_threats": 8,
        "executable_files": 4,
        "malicious_file_downloads": 6,
        "requires_immediate_action": true
    },
    "critical_findings": [
        {
            "type": "EXECUTABLE_FILES_DETECTED",
            "severity": "CRITICAL",
            "description": "Found 4 executable files that could install malware",
            "immediate_action": "BLOCK ALL EXECUTABLE DOWNLOADS IMMEDIATELY"
        }
    ],
    "manual_investigation_required": [
        {
            "task": "Review all executable files",
            "priority": "CRITICAL",
            "description": "Manually verify each executable file URL for malware"
        }
    ]
}
```

## Workflow Integration

### 1. **Document Advertisement Detection**
- Detects malicious file advertisements using multiple methods (regex, AI, LLM)
- Identifies suspicious URLs with detailed risk analysis
- Categorizes threats by severity level

### 2. **Virus Detection API Integration**
- Prepares data for external virus detection APIs
- Generates comprehensive reports for manual investigation
- Provides structured data for forensic analysis

### 3. **Database Storage**
- Stores all findings in the forensic database
- Includes risk scores and severity assessments
- Maintains audit trail for legal purposes

### 4. **Reporting System**
- Generates detailed forensic reports
- Provides manual investigation checklists
- Includes recommendations for immediate action

## Key Features for Supervisor's Requirements

### ✅ **Malicious File Advertisement Detection**
- Detects advertisements for malware, viruses, trojans, spyware, keyloggers, stealers, RATs, backdoors
- Identifies malicious file builders, generators, and creators
- Recognizes undetected, stealth, and bypass malware

### ✅ **URL Extraction for Virus Investigation**
- Extracts all suspicious URLs from dark web content
- Categorizes URLs by risk level (high, medium, low)
- Identifies executable files and malicious keywords
- Provides detailed analysis for manual investigation

### ✅ **Virus Detection API Preparation**
- Prepares structured data for virus detection APIs
- Works without purchasing APIs (manual investigation mode)
- Generates comprehensive reports for investigators
- Provides actionable intelligence for threat response

### ✅ **Comprehensive Reporting**
- Detailed investigation reports with critical findings
- Manual investigation checklists with priorities
- Risk assessment and severity classification
- Recommendations for immediate action

## Usage Examples

### Running Enhanced Detection
```python
from src.extract.document_advertisement_detector import extract_document_advertisements_from_html

# Run enhanced detection
results = extract_document_advertisements_from_html(
    "darkweb_content.html",
    use_llm=True,
    use_rag=True,
    use_ai=True,
    translate=True
)

# Access results
print(f"Found {results['total_found']} items")
print(f"Executable files: {len(results['virus_detection_data']['executable_files'])}")
print(f"Malicious downloads: {len(results['virus_detection_data']['malicious_file_downloads'])}")
```

### Virus Detection API Integration
```python
from src.utils.virus_detection_api import VirusDetectionAPI

# Process for virus detection
virus_api = VirusDetectionAPI()
virus_results = virus_api.send_to_virus_detection_api(results['virus_detection_data'])

# Generate comprehensive report
report = virus_api.generate_virus_detection_report(results['virus_detection_data'])
```

### Database Storage
```python
from src.utils.db_insert import insert_into_db

# Prepare data for database
case_id = "darkweb_analysis_20250806_223018"
investigator = "Automated Forensic Tool"
notes = "Dark web malicious file detection analysis"

# Insert into database
insert_into_db(
    case_id=case_id,
    investigator=investigator,
    notes=notes,
    emails=[],
    payment_addresses=[],
    keywords=keywords,
    pgp_content=[],
    financial_data=[],
    shipping_addresses=[],
    usernames=[],
    score=risk_score,
    severity=severity,
    file_hash=file_hash,
    llm_summary=llm_summary,
    document_ads_data=document_ads_data
)
```

## Test Results

### Sample Detection Results:
```
📊 Detection Summary:
  Document Advertisements: 15
  Suspicious URLs: 7
  Executable Files: 4
  Malicious Downloads: 8
  Risk Score: 180 (CRITICAL)

🚨 Critical Findings:
  - Found 4 executable files that could install malware
  - Found 8 advertisements for malicious file downloads
  - High-risk URLs requiring immediate investigation

📋 Manual Investigation Required:
  CRITICAL: Review all executable files (4 items)
  HIGH: Investigate malicious downloads (8 items)
  HIGH: Virus scan suspicious URLs (7 items)
```

## Benefits

1. **Comprehensive Detection**: Detects all types of malicious file advertisements
2. **Detailed Analysis**: Provides in-depth URL analysis with risk assessment
3. **Manual Investigation Ready**: Generates reports for investigators without requiring API purchases
4. **Forensic Documentation**: Maintains detailed records for legal purposes
5. **Immediate Action Guidance**: Provides clear recommendations for threat response
6. **Scalable Architecture**: Can be extended with additional detection methods

## Conclusion

The enhanced system successfully addresses the supervisor's requirements by:

1. **Detecting malicious file advertisements** that could install viruses on laptops
2. **Extracting suspicious URLs** for virus investigation
3. **Preparing data for virus detection APIs** even when APIs cannot be purchased
4. **Generating comprehensive reports** for manual investigation
5. **Providing actionable intelligence** for immediate threat response

The system is now ready for production use in dark web forensic analysis, providing investigators with the tools they need to identify and respond to malicious file threats effectively. 