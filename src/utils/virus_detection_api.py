import requests
import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VirusDetectionAPI:
    """
    Virus Detection API integration for suspicious documents and URLs
    Supports multiple virus detection services with fallback options
    """
    
    def __init__(self):
        # API configurations - these would be set by users
        self.virus_total_api_key = os.getenv("VIRUS_TOTAL_API_KEY")
        self.url_void_api_key = os.getenv("URL_VOID_API_KEY")
        self.hybrid_analysis_api_key = os.getenv("HYBRID_ANALYSIS_API_KEY")
        # Optional global toggle via .env (UI can still override)
        self.enable_live_checks_env = os.getenv("ENABLE_VIRUS_LIVE_CHECKS", "").lower() in ("1", "true", "yes", "on")
        
        # API endpoints
        self.virus_total_url = "https://www.virustotal.com/vtapi/v2"
        self.url_void_url = "https://api.urlvoid.com"
        self.hybrid_analysis_url = "https://www.hybrid-analysis.com/api/v2"
        
        # Rate limiting and timeouts
        self.request_timeout = 30
        self.max_retries = 3

    def has_any_api_key(self) -> bool:
        """Return True if at least one supported API key is configured via .env"""
        return any([
            bool(self.virus_total_api_key),
            bool(self.url_void_api_key),
            bool(self.hybrid_analysis_api_key),
        ])
        
    def check_url_with_virus_total(self, url: str) -> Dict:
        """Check URL with VirusTotal API"""
        try:
            if not self.virus_total_api_key:
                return {
                    'success': False,
                    'error': 'VirusTotal API key not configured',
                    'malicious': False,
                    'detection_ratio': 0,
                    'scan_date': None
                }
            
            params = {
                'apikey': self.virus_total_api_key,
                'url': url
            }
            
            response = requests.post(
                f"{self.virus_total_url}/url/report",
                data=params,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                positives = result.get('positives', 0)
                total = result.get('total', 0)
                
                return {
                    'success': True,
                    'malicious': positives > 0,
                    'detection_ratio': positives / total if total > 0 else 0,
                    'positives': positives,
                    'total': total,
                    'scan_date': result.get('scan_date'),
                    'permalink': result.get('permalink'),
                    'response_code': result.get('response_code')
                }
            else:
                return {
                    'success': False,
                    'error': f'VirusTotal API error: {response.status_code}',
                    'malicious': False,
                    'detection_ratio': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'VirusTotal API exception: {str(e)}',
                'malicious': False,
                'detection_ratio': 0
            }
    
    def check_url_with_url_void(self, url: str) -> Dict:
        """Check URL with URLVoid API"""
        try:
            if not self.url_void_api_key:
                return {
                    'success': False,
                    'error': 'URLVoid API key not configured',
                    'malicious': False,
                    'detection_ratio': 0
                }
            
            params = {
                'key': self.url_void_api_key,
                'url': url
            }
            
            response = requests.get(
                f"{self.url_void_url}/url/{url}",
                params=params,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                detection_ratio = result.get('detection_ratio', 0)
                
                return {
                    'success': True,
                    'malicious': detection_ratio > 0,
                    'detection_ratio': detection_ratio,
                    'scan_date': result.get('scan_date'),
                    'response_code': result.get('response_code')
                }
            else:
                return {
                    'success': False,
                    'error': f'URLVoid API error: {response.status_code}',
                    'malicious': False,
                    'detection_ratio': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'URLVoid API exception: {str(e)}',
                'malicious': False,
                'detection_ratio': 0
            }
    
    def check_file_with_hybrid_analysis(self, file_url: str) -> Dict:
        """Check file with Hybrid Analysis API"""
        try:
            if not self.hybrid_analysis_api_key:
                return {
                    'success': False,
                    'error': 'Hybrid Analysis API key not configured',
                    'malicious': False,
                    'threat_score': 0
                }
            
            headers = {
                'api-key': self.hybrid_analysis_api_key,
                'user-agent': 'DarkWebForensicTool/1.0'
            }
            
            # Note: This would require downloading the file first
            # For now, we'll return a placeholder response
            return {
                'success': True,
                'malicious': False,  # Would be determined by actual analysis
                'threat_score': 0,
                'note': 'File analysis requires downloading the file first'
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Hybrid Analysis API exception: {str(e)}',
                'malicious': False,
                'threat_score': 0
            }
    
    def check_suspicious_urls(self, suspicious_urls: List[Dict]) -> Dict:
        """Check multiple suspicious URLs with virus detection APIs"""
        results = {
            'total_checked': len(suspicious_urls),
            'malicious_found': 0,
            'high_risk_urls': [],
            'api_results': {},
            'live_checks_available': self.has_any_api_key(),
        }
        
        # If no API keys configured, skip remote checks and return placeholder info
        if not results['live_checks_available']:
            results['note'] = 'No API keys configured in .env; live URL checks skipped.'
            return results
        
        for url_data in suspicious_urls:
            url = url_data['url']
            risk_level = url_data['risk_level']
            
            print(f"🔍 Checking URL: {url} (Risk: {risk_level})")
            
            # Try VirusTotal first
            vt_result = self.check_url_with_virus_total(url)
            
            # Try URLVoid as backup
            uv_result = self.check_url_with_url_void(url)
            
            # Combine results
            combined_result = {
                'url': url,
                'original_risk': risk_level,
                'virus_total': vt_result,
                'url_void': uv_result,
                'overall_malicious': vt_result.get('malicious', False) or uv_result.get('malicious', False),
                'highest_detection_ratio': max(
                    vt_result.get('detection_ratio', 0),
                    uv_result.get('detection_ratio', 0)
                )
            }
            
            results['api_results'][url] = combined_result
            
            if combined_result['overall_malicious']:
                results['malicious_found'] += 1
                results['high_risk_urls'].append({
                    'url': url,
                    'detection_ratio': combined_result['highest_detection_ratio'],
                    'risk_level': 'high'
                })
        
        return results

    def check_actual_links_from_database(self, case_id: str = None, limit: int = 50) -> Dict:
        """Check actual links from the database with virus detection APIs"""
        try:
            import mysql.connector
            from dotenv import load_dotenv
            
            # Connect to database
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
            cursor = conn.cursor()

            # Build query to get actual links
            if case_id:
                query = """
                SELECT al.url, al.link_type, al.suspicious_level, c.case_id, c.investigator_name
                FROM actual_links al
                JOIN case_metadata c ON al.case_id = c.id
                WHERE c.case_id = %s
                ORDER BY al.created_at DESC
                LIMIT %s
                """
                cursor.execute(query, (case_id, limit))
            else:
                query = """
                SELECT al.url, al.link_type, al.suspicious_level, c.case_id, c.investigator_name
                FROM actual_links al
                JOIN case_metadata c ON al.case_id = c.id
                ORDER BY al.created_at DESC
                LIMIT %s
                """
                cursor.execute(query, (limit,))

            links = cursor.fetchall()
            cursor.close()
            conn.close()

            if not links:
                return {
                    'success': False,
                    'error': 'No actual links found in database',
                    'total_checked': 0,
                    'malicious_found': 0,
                    'high_risk_urls': [],
                    'api_results': {}
                }

            # Convert to suspicious_urls format for existing check function
            suspicious_urls = []
            for link in links:
                url, link_type, suspicious_level, case_id, investigator = link
                suspicious_urls.append({
                    'url': url,
                    'risk_level': suspicious_level,
                    'link_type': link_type,
                    'case_id': case_id,
                    'investigator': investigator
                })

            # Use existing check function
            return self.check_suspicious_urls(suspicious_urls)

        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}',
                'total_checked': 0,
                'malicious_found': 0,
                'high_risk_urls': [],
                'api_results': {}
            }

    def check_actual_links_by_type(self, link_type: str = None, limit: int = 50) -> Dict:
        """Check actual links filtered by type (e.g., 'javascript', 'event_handler')"""
        try:
            import mysql.connector
            
            # Connect to database
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
            cursor = conn.cursor()

            # Build query based on link type
            if link_type:
                query = """
                SELECT al.url, al.link_type, al.suspicious_level, c.case_id, c.investigator_name
                FROM actual_links al
                JOIN case_metadata c ON al.case_id = c.id
                WHERE al.link_type = %s
                ORDER BY al.created_at DESC
                LIMIT %s
                """
                cursor.execute(query, (link_type, limit))
            else:
                query = """
                SELECT al.url, al.link_type, al.suspicious_level, c.case_id, c.investigator_name
                FROM actual_links al
                JOIN case_metadata c ON al.case_id = c.id
                ORDER BY al.created_at DESC
                LIMIT %s
                """
                cursor.execute(query, (limit,))

            links = cursor.fetchall()
            cursor.close()
            conn.close()

            if not links:
                return {
                    'success': False,
                    'error': f'No links found for type: {link_type}' if link_type else 'No links found',
                    'total_checked': 0,
                    'malicious_found': 0,
                    'high_risk_urls': [],
                    'api_results': {}
                }

            # Convert to suspicious_urls format
            suspicious_urls = []
            for link in links:
                url, link_type, suspicious_level, case_id, investigator = link
                suspicious_urls.append({
                    'url': url,
                    'risk_level': suspicious_level,
                    'link_type': link_type,
                    'case_id': case_id,
                    'investigator': investigator
                })

            return self.check_suspicious_urls(suspicious_urls)

        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}',
                'total_checked': 0,
                'malicious_found': 0,
                'high_risk_urls': [],
                'api_results': {}
            }
    
    def prepare_api_request_data(self, virus_detection_data: Dict) -> Dict:
        """Prepare data for external virus detection API"""
        try:
            api_request = {
                'timestamp': None,  # Will be set by API
                'source': 'dark_web_forensic_tool',
                'document_advertisements': [],
                'suspicious_urls': [],
                'high_risk_items': [],
                'summary': {
                    'total_document_ads': 0,
                    'total_suspicious_urls': 0,
                    'high_risk_count': 0,
                    'api_ready': True
                }
            }
            
            # Process document advertisements
            for ad in virus_detection_data.get('document_advertisements', []):
                api_request['document_advertisements'].append({
                    'content': ad['content'],
                    'type': ad['type'],
                    'suspicious_level': ad['suspicious_level'],
                    'method': ad['method'],
                    'priority': 'high' if ad['suspicious_level'] == 'high' else 'medium'
                })
                api_request['summary']['total_document_ads'] += 1
            
            # Process suspicious URLs
            for url_data in virus_detection_data.get('suspicious_urls', []):
                api_request['suspicious_urls'].append({
                    'url': url_data['url'],
                    'domain': url_data['domain'],
                    'suspicious_reason': url_data['suspicious_reason'],
                    'risk_level': url_data['risk_level'],
                    'priority': 'high' if url_data['risk_level'] == 'high' else 'medium'
                })
                api_request['summary']['total_suspicious_urls'] += 1
            
            # Process high risk items
            for item in virus_detection_data.get('high_risk_items', []):
                api_request['high_risk_items'].append({
                    'type': item['type'],
                    'content': item.get('content', ''),
                    'url': item.get('url', ''),
                    'risk_level': item['risk_level'],
                    'priority': 'high'
                })
                api_request['summary']['high_risk_count'] += 1
            
            return api_request
            
        except Exception as e:
            return {
                'error': f'Failed to prepare API request data: {str(e)}',
                'api_ready': False
            }
    
    def send_to_virus_detection_api(self, virus_detection_data: Dict, api_endpoint: str = None) -> Dict:
        """Send data to external virus detection API"""
        try:
            # Prepare the data
            api_request_data = self.prepare_api_request_data(virus_detection_data)
            
            if not api_request_data.get('api_ready', False):
                return {
                    'success': False,
                    'error': api_request_data.get('error', 'Unknown error'),
                    'sent_data': None
                }
            
            # If no specific endpoint provided, return the prepared data
            if not api_endpoint:
                return {
                    'success': True,
                    'message': 'Data prepared for virus detection API',
                    'sent_data': api_request_data,
                    'api_endpoint_required': True
                }
            
            # Send to specified API endpoint
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'DarkWebForensicTool/1.0'
            }
            
            response = requests.post(
                api_endpoint,
                json=api_request_data,
                headers=headers,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Data sent to virus detection API successfully',
                    'response': response.json(),
                    'sent_data': api_request_data
                }
            else:
                return {
                    'success': False,
                    'error': f'API request failed: {response.status_code}',
                    'response_text': response.text,
                    'sent_data': api_request_data
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception sending to virus detection API: {str(e)}',
                'sent_data': None
            }
    
    def generate_virus_detection_report(self, virus_detection_data: Dict, api_results: Dict = None) -> Dict:
        """Generate a comprehensive virus detection report with manual investigation focus"""
        try:
            report = {
                'timestamp': None,  # Will be set by caller
                'summary': {
                    'total_document_advertisements': len(virus_detection_data.get('document_advertisements', [])),
                    'total_suspicious_urls': len(virus_detection_data.get('suspicious_urls', [])),
                    'high_risk_items': len(virus_detection_data.get('high_risk_items', [])),
                    'executable_files': len(virus_detection_data.get('executable_files', [])),
                    'malicious_file_downloads': len(virus_detection_data.get('malicious_file_downloads', [])),
                    'malicious_urls_found': 0,
                    'api_checks_performed': 0,
                    'critical_threats': 0,
                    'requires_manual_investigation': False
                },
                'document_advertisements': [],
                'suspicious_urls': [],
                'high_risk_items': [],
                'executable_files': [],
                'malicious_file_downloads': [],
                'api_results': api_results or {},
                'recommendations': [],
                'manual_investigation_checklist': []
            }
            
            # Process document advertisements
            for ad in virus_detection_data.get('document_advertisements', []):
                report['document_advertisements'].append({
                    'content': ad['content'],
                    'type': ad['type'],
                    'suspicious_level': ad['suspicious_level'],
                    'method': ad['method'],
                    'recommendation': 'Investigate immediately' if ad['suspicious_level'] == 'high' else 'Monitor closely'
                })
            
            # Process executable files (highest priority for manual investigation)
            for exe_file in virus_detection_data.get('executable_files', []):
                report['executable_files'].append({
                    'url': exe_file['url'],
                    'domain': exe_file['domain'],
                    'file_extension': exe_file['file_extension'],
                    'suspicious_reason': exe_file['suspicious_reason'],
                    'risk_level': 'CRITICAL',
                    'priority': 'IMMEDIATE',
                    'recommendation': 'BLOCK IMMEDIATELY - Potential malware installer',
                    'manual_investigation_required': True
                })
                report['summary']['critical_threats'] += 1
                report['summary']['requires_manual_investigation'] = True
            
            # Process malicious file download advertisements
            for mal_ad in virus_detection_data.get('malicious_file_downloads', []):
                report['malicious_file_downloads'].append({
                    'content': mal_ad['content'],
                    'type': mal_ad['type'],
                    'suspicious_level': mal_ad['suspicious_level'],
                    'method': mal_ad['method'],
                    'priority': 'HIGH',
                    'recommendation': 'INVESTIGATE FOR MALWARE - Malicious file advertisement',
                    'manual_investigation_required': True
                })
                report['summary']['critical_threats'] += 1
                report['summary']['requires_manual_investigation'] = True
            
            # Process suspicious URLs
            for url_data in virus_detection_data.get('suspicious_urls', []):
                is_malicious = False
                detection_ratio = 0
                
                # Check if we have API results for this URL
                if api_results and url_data['url'] in api_results.get('api_results', {}):
                    api_result = api_results['api_results'][url_data['url']]
                    is_malicious = api_result.get('overall_malicious', False)
                    detection_ratio = api_result.get('highest_detection_ratio', 0)
                    report['summary']['api_checks_performed'] += 1
                
                report['suspicious_urls'].append({
                    'url': url_data['url'],
                    'domain': url_data['domain'],
                    'path': url_data.get('path', ''),
                    'query': url_data.get('query', ''),
                    'suspicious_reason': url_data['suspicious_reason'],
                    'risk_level': url_data['risk_level'],
                    'file_extension': url_data.get('file_extension'),
                    'malicious_keywords_found': url_data.get('malicious_keywords_found', []),
                    'malicious': is_malicious,
                    'detection_ratio': detection_ratio,
                    'recommendation': 'Block immediately' if is_malicious else 'Monitor closely',
                    'manual_investigation_required': url_data['risk_level'] == 'high'
                })
                
                if is_malicious:
                    report['summary']['malicious_urls_found'] += 1
                
                if url_data['risk_level'] == 'high':
                    report['summary']['requires_manual_investigation'] = True
            
            # Process high risk items
            for item in virus_detection_data.get('high_risk_items', []):
                report['high_risk_items'].append({
                    'type': item['type'],
                    'content': item.get('content', ''),
                    'url': item.get('url', ''),
                    'risk_level': item['risk_level'],
                    'file_extension': item.get('file_extension'),
                    'priority': item.get('priority', 'HIGH'),
                    'recommendation': 'Immediate action required',
                    'manual_investigation_required': True
                })
            
            # Generate recommendations with manual investigation focus
            if report['summary']['executable_files'] > 0:
                report['recommendations'].append('🚨 CRITICAL: Executable files detected - BLOCK ALL DOWNLOADS IMMEDIATELY')
                report['recommendations'].append('🔍 MANUAL INVESTIGATION: Review each executable file for malware')
            
            if report['summary']['malicious_file_downloads'] > 0:
                report['recommendations'].append('⚠️ HIGH RISK: Malicious file advertisements detected - INVESTIGATE IMMEDIATELY')
                report['recommendations'].append('📋 DOCUMENTATION: Document all malicious file advertisements for forensic analysis')
            
            if report['summary']['malicious_urls_found'] > 0:
                report['recommendations'].append('🚨 CRITICAL: Malicious URLs detected - BLOCK IMMEDIATELY')
            
            if report['summary']['high_risk_items'] > 0:
                report['recommendations'].append('⚠️ HIGH RISK: High risk items require immediate investigation')
            
            if report['summary']['total_document_advertisements'] > 5:
                report['recommendations'].append('📊 MONITORING: High volume of document advertisements detected')
            
            if report['summary']['requires_manual_investigation']:
                report['recommendations'].append('🔍 MANUAL INVESTIGATION REQUIRED: Use virus detection APIs to scan suspicious URLs')
                report['recommendations'].append('📋 FORENSIC DOCUMENTATION: Create detailed report for legal/forensic purposes')
            
            if not report['recommendations']:
                report['recommendations'].append('✅ No immediate threats detected, continue monitoring')
            
            # Generate manual investigation checklist
            if report['summary']['executable_files'] > 0:
                report['manual_investigation_checklist'].append({
                    'task': 'Review all executable files',
                    'priority': 'CRITICAL',
                    'description': 'Manually verify each executable file URL for malware',
                    'count': report['summary']['executable_files']
                })
            
            if report['summary']['malicious_file_downloads'] > 0:
                report['manual_investigation_checklist'].append({
                    'task': 'Investigate malicious file advertisements',
                    'priority': 'HIGH',
                    'description': 'Analyze content of malicious file download advertisements',
                    'count': report['summary']['malicious_file_downloads']
                })
            
            if report['summary']['total_suspicious_urls'] > 0:
                report['manual_investigation_checklist'].append({
                    'task': 'Virus scan suspicious URLs',
                    'priority': 'HIGH',
                    'description': 'Use virus detection APIs to scan suspicious URLs',
                    'count': report['summary']['total_suspicious_urls']
                })
            
            report['manual_investigation_checklist'].append({
                'task': 'Document findings',
                'priority': 'MEDIUM',
                'description': 'Create detailed report of all findings for legal/forensic purposes',
                'count': 1
            })
            
            return report
            
        except Exception as e:
            return {
                'error': f'Failed to generate virus detection report: {str(e)}',
                'summary': {'error': True}
            }

# Example usage function
def process_document_advertisements_for_virus_detection(
    document_ads_data: Dict,
    enable_live_checks: bool = True,
    api_endpoint: Optional[str] = None,
) -> Dict:
    """Main function to process document advertisements and prepare for virus detection.

    When enable_live_checks is False, no external API lookups are performed. The function
    still prepares an API-ready payload and generates a report focused on manual investigation.
    """
    try:
        virus_api = VirusDetectionAPI()

        # Decide whether to perform live checks (UI flag AND keys available OR env override)
        effective_live_checks = (
            enable_live_checks or virus_api.enable_live_checks_env
        ) and virus_api.has_any_api_key()

        # Check suspicious URLs with virus detection APIs only if enabled/effective
        suspicious_urls = document_ads_data.get('suspicious_urls', [])
        if effective_live_checks:
            api_results = virus_api.check_suspicious_urls(suspicious_urls)
        else:
            api_results = {
                'total_checked': len(suspicious_urls),
                'malicious_found': 0,
                'high_risk_urls': [],
                'api_results': {},
                'live_checks_available': virus_api.has_any_api_key(),
                'note': 'Live checks disabled or no API keys present; prepared manual investigation data only.'
            }

        # Prepare data for external API (only sends if api_endpoint provided)
        virus_detection_data = document_ads_data.get('virus_detection_data', {})
        if effective_live_checks and api_endpoint:
            api_request_result = virus_api.send_to_virus_detection_api(virus_detection_data, api_endpoint=api_endpoint)
        else:
            # Default: just prepare the payload without sending
            api_request_result = virus_api.send_to_virus_detection_api(virus_detection_data)

        # Generate comprehensive report
        report = virus_api.generate_virus_detection_report(virus_detection_data, api_results)

        return {
            'success': True,
            'api_results': api_results,
            'api_request_result': api_request_result,
            'report': report,
            'recommendations': report.get('recommendations', []),
            'live_checks_effective': effective_live_checks,
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to process document advertisements for virus detection: {str(e)}'
        }

def scan_actual_links_from_database(
    case_id: str = None,
    link_type: str = None,
    limit: int = 50,
    enable_live_checks: bool = True,
    api_endpoint: Optional[str] = None,
) -> Dict:
    """Main function to scan actual links from database with virus detection APIs.
    
    Args:
        case_id: Specific case ID to scan (optional)
        link_type: Filter by link type (e.g., 'javascript', 'event_handler') (optional)
        limit: Maximum number of links to scan (default: 50)
        enable_live_checks: Whether to perform live API checks
        api_endpoint: External API endpoint to send results to (optional)
    
    Returns:
        Dict with scan results and recommendations
    """
    try:
        virus_api = VirusDetectionAPI()
        
        # Decide whether to perform live checks
        effective_live_checks = (
            enable_live_checks or virus_api.enable_live_checks_env
        ) and virus_api.has_any_api_key()
        
        # Get links from database
        if link_type:
            api_results = virus_api.check_actual_links_by_type(link_type, limit)
        else:
            api_results = virus_api.check_actual_links_from_database(case_id, limit)
        
        if not api_results.get('success', True):
            return {
                'success': False,
                'error': api_results.get('error', 'Unknown error'),
                'api_results': api_results
            }
        
        # Generate report for actual links
        report = {
            'timestamp': None,  # Will be set by caller
            'scan_type': 'actual_links_database',
            'case_id': case_id,
            'link_type_filter': link_type,
            'limit_applied': limit,
            'summary': {
                'total_links_checked': api_results.get('total_checked', 0),
                'malicious_links_found': api_results.get('malicious_found', 0),
                'high_risk_links': len(api_results.get('high_risk_urls', [])),
                'api_checks_performed': api_results.get('live_checks_available', False),
                'live_checks_effective': effective_live_checks
            },
            'api_results': api_results,
            'recommendations': [],
            'high_risk_links': api_results.get('high_risk_urls', []),
            'all_checked_urls': list(api_results.get('api_results', {}).keys())
        }
        
        # Generate recommendations based on results
        if api_results.get('malicious_found', 0) > 0:
            report['recommendations'].append(f"🚨 CRITICAL: {api_results['malicious_found']} malicious URLs detected - BLOCK IMMEDIATELY")
            report['recommendations'].append("🔍 MANUAL INVESTIGATION: Review each malicious URL for threat analysis")
        
        if len(api_results.get('high_risk_urls', [])) > 0:
            report['recommendations'].append(f"⚠️ HIGH RISK: {len(api_results['high_risk_urls'])} high-risk URLs require immediate attention")
        
        if link_type in ['javascript', 'event_handler']:
            report['recommendations'].append("🔒 SECURITY: JavaScript and event handler links are high-risk - investigate thoroughly")
        
        if api_results.get('total_checked', 0) > 20:
            report['recommendations'].append("📊 MONITORING: Large number of links scanned - consider automated monitoring")
        
        if not effective_live_checks:
            report['recommendations'].append("🔑 CONFIGURATION: No API keys configured - enable live checks for real-time threat detection")
        
        if not report['recommendations']:
            report['recommendations'].append("✅ No immediate threats detected in scanned links")
        
        # Send to external API if endpoint provided
        api_request_result = None
        if effective_live_checks and api_endpoint:
            api_request_result = virus_api.send_to_virus_detection_api({
                'actual_links_scan': report
            }, api_endpoint=api_endpoint)
        
        return {
            'success': True,
            'report': report,
            'api_results': api_results,
            'api_request_result': api_request_result,
            'recommendations': report['recommendations'],
            'live_checks_effective': effective_live_checks,
            'total_links_scanned': api_results.get('total_checked', 0),
            'malicious_found': api_results.get('malicious_found', 0)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to scan actual links from database: {str(e)}',
            'api_results': {},
            'recommendations': ['❌ Error occurred during virus scan']
        }