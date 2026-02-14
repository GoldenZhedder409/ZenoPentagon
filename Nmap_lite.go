#!/usr/bin/env python3                                                                  """
ZNmap - Advanced Network Scanner for Termux                                             Kompatibel dengan Termux & Android
"""
import os
import sys
import subprocess
import json
import csv
from datetime import datetime
from pathlib import Path
import ipaddress                                                                        import re
import socket
import concurrent.futures
import time

# ========== CONFIGURATION ==========
class Config:
    # Default scan options untuk Termux (optimized)
    NMAP_PATH = "nmap"
    DEFAULT_TIMEOUT = 30
    MAX_PARALLEL_SCANS = 3
    OUTPUT_DIR = "scan_results"

    # Scan profiles untuk berbagai kebutuhan
    SCAN_PROFILES = {
        "quick": "-T4 -F --open",  # Cepat, 100 port umum
        "basic": "-T4 -sV --open",  # Dasar + service detection
        "stealth": "-T2 -sS --open",  # Stealth SYN scan
        "full": "-T4 -A -p-",  # Full scan (lambat!)
        "vuln": "-T4 --script vuln",  # Vulnerability scan
        "os": "-T4 -O",  # OS detection
        "udp": "-T4 -sU",  # UDP scan
        "web": "-T4 -p 80,443,8080,8443 --script http*",  # Web scan
        "mobile": "-T4 -p 22,80,443,8080,8443,5555,5037",  # Port umum mobile
        "termux": "-T4 -p 1-1000 --open"  # Optimized untuk Termux
    }

# ========== UTILITIES ==========
class ScannerUtils:
    @staticmethod
    def clear_screen():
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def check_nmap_installed():
        """Cek apakah nmap terinstall di Termux"""
        try:
            result = subprocess.run(
                ["which", "nmap"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True
        except:
            pass

        # Coba install nmap
        print("\033[93m[!] Nmap tidak terdeteksi. Mencoba install...\033[0m")
        try:
            subprocess.run(
                ["pkg", "install", "nmap", "-y"],
                check=True,
                capture_output=True
            )
            print("\033[92m[✓] Nmap berhasil diinstall!\033[0m")
            return True
        except:
            print("\033[91m[✗] Gagal install nmap. Install manual: pkg install nmap\033[0m")
            return False

    @staticmethod
    def validate_target(target):
        """Validasi target IP/Domain"""
        # Cek jika IP address valid
        try:
            ipaddress.ip_address(target)
            return True, "ip"
        except ValueError:
            pass

        # Cek jika domain valid (sederhana)
        if re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', target):
            try:
                socket.gethostbyname(target)
                return True, "domain"
            except socket.gaierror:
                return False, "invalid"

        return False, "invalid"

    @staticmethod
    def get_local_ip():
        """Dapatkan IP lokal device"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

    @staticmethod
    def get_network_range():
        """Dapatkan network range lokal"""
        local_ip = ScannerUtils.get_local_ip()
        if local_ip == "127.0.0.1":
            return "192.168.1.0/24"  # Default fallback

        # Simple network range detection
        ip_parts = local_ip.split('.')
        return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"

    @staticmethod
    def format_duration(seconds):
        """Format durasi ke readable string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

# ========== SCANNER ENGINE ==========
class NmapScanner:
    def __init__(self, config=None):
        self.config = config or Config()
        self.utils = ScannerUtils()
        self.results = {}
        self.scan_history = []

        # Buat output directory
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)

    def run_scan(self, target, profile="quick", ports=None, options=""):
        """Jalankan scan dengan nmap"""
        scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n\033[94m[→] Scan ID: {scan_id}\033[0m")
        print(f"\033[94m[→] Target: {target}\033[0m")
        print(f"\033[94m[→] Profile: {profile}\033[0m")

        # Validasi target
        is_valid, target_type = self.utils.validate_target(target)
        if not is_valid:
            print("\033[91m[✗] Target tidak valid!\033[0m")
            return None

        # Pilih profile
        base_options = self.config.SCAN_PROFILES.get(profile, self.config.SCAN_PROFILES["quick"])

        # Tambah custom ports jika ada
        if ports:
            base_options = base_options.replace("-F", f"-p {ports}")

        # Gabungkan options
        full_options = f"{base_options} {options}".strip()

        # Bangun command nmap
        cmd = f"{self.config.NMAP_PATH} {full_options} {target}"

        print(f"\033[94m[→] Command: nmap {full_options}\033[0m")
        print("\033[93m[*] Memulai scan... (mungkin perlu beberapa saat)\033[0m\n")

        start_time = time.time()

        try:
            # Jalankan nmap dengan timeout
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.DEFAULT_TIMEOUT * 3  # 3x timeout untuk long scans
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                print(f"\033[92m[✓] Scan selesai dalam {self.utils.format_duration(duration)}\033[0m")
                return self.parse_results(result.stdout, target, profile, scan_id)
            else:
                print(f"\033[91m[✗] Scan gagal! Error: {result.stderr}\033[0m")
                return None

        except subprocess.TimeoutExpired:
            print(f"\033[91m[✗] Scan timeout setelah {self.config.DEFAULT_TIMEOUT} detik!\033[0m")
            return None

        except Exception as e:
            print(f"\033[91m[✗] Error: {str(e)}\033[0m")
            return None

    def parse_results(self, nmap_output, target, profile, scan_id):
        """Parse hasil nmap menjadi structured data"""
        results = {
            "scan_id": scan_id,
            "target": target,
            "profile": profile,
            "timestamp": datetime.now().isoformat(),
            "open_ports": [],
            "services": {},
            "host_info": {},
            "raw_output": nmap_output
        }

        lines = nmap_output.split('\n')
        current_ip = None

        for i, line in enumerate(lines):
            line = line.strip()

            # Extract host IP
            if "Nmap scan report for" in line:
                current_ip = line.split("for")[-1].strip()
                results["host_info"]["ip"] = current_ip

            # Extract host status
            elif "Host is up" in line:
                results["host_info"]["status"] = "up"
                # Extract latency
                latency_match = re.search(r'([\d.]+)s latency', line)
                if latency_match:
                    results["host_info"]["latency"] = float(latency_match.group(1))

            # Extract open ports
            elif "/tcp" in line or "/udp" in line:
                port_info = self.parse_port_line(line)
                if port_info:
                    results["open_ports"].append(port_info)

                    # Extract service info
                    if "service" in port_info:
                        results["services"][port_info["port"]] = port_info["service"]

            # Extract OS info
            elif "OS details:" in line or "Running:" in line:
                results["host_info"]["os"] = line.split(":", 1)[-1].strip()

            # Extract device type
            elif "Device type:" in line:
                results["host_info"]["device_type"] = line.split(":", 1)[-1].strip()

        # Simpan ke history
        self.scan_history.append(results)

        # Simpan ke file
        self.save_results(results)

        return results

    def parse_port_line(self, line):
        """Parse satu baris port info dari nmap"""
        # Contoh: "22/tcp   open  ssh"
        parts = line.split()
        if len(parts) >= 3:
            port_proto = parts[0].split('/')
            if len(port_proto) == 2:
                return {
                    "port": int(port_proto[0]),
                    "protocol": port_proto[1],
                    "state": parts[1],
                    "service": parts[2] if len(parts) > 2 else "unknown"
                }
        return None

    def save_results(self, results):
        """Simpan hasil scan ke berbagai format"""
        scan_id = results["scan_id"]

        # Save raw output
        raw_file = f"{self.config.OUTPUT_DIR}/{scan_id}_raw.txt"
        with open(raw_file, 'w') as f:
            f.write(results["raw_output"])

        # Save JSON
        json_file = f"{self.config.OUTPUT_DIR}/{scan_id}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Save CSV
        csv_file = f"{self.config.OUTPUT_DIR}/{scan_id}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Port", "Protocol", "State", "Service"])
            for port in results["open_ports"]:
                writer.writerow([
                    port["port"],
                    port["protocol"],
                    port["state"],
                    port.get("service", "")
                ])

        print("\033[92m[✓] Results saved to:\033[0m")
        print(f"    • \033[96m{raw_file}\033[0m")
        print(f"    • \033[96m{json_file}\033[0m")
        print(f"    • \033[96m{csv_file}\033[0m")

    def display_results(self, results):
        """Tampilkan hasil scan dengan format menarik"""
        if not results:
            print("\033[93m[!] Tidak ada hasil untuk ditampilkan\033[0m")
            return

        print("\n" + "="*60)
        print("\033[91m📡 ZNmap SCAN RESULTS\033[0m")
        print("="*60)

        # Host info
        host = results["host_info"]
        print(f"\n\033[93m🎯 Target: {results['target']}\033[0m")
        print(f"\033[93m📅 Scan Time: {results['timestamp']}\033[0m")
        print(f"\033[93m🔧 Profile: {results['profile']}\033[0m")

        if "ip" in host:
            print(f"\033[96m📍 IP Address: {host['ip']}\033[0m")
        if "status" in host:
            print(f"\033[92m✅ Status: {host['status'].upper()}\033[0m")
        if "latency" in host:
            print(f"\033[96m⏱️  Latency: {host['latency']}s\033[0m")
        if "os" in host:
            print(f"\033[96m💻 OS: {host['os']}\033[0m")

        # Open ports
        print(f"\n\033[93m🚪 OPEN PORTS ({len(results['open_ports'])} found):\033[0m")
        print("\033[90m" + "-"*60 + "\033[0m")
        print("\033[97m PORT     PROTOCOL  STATE    SERVICE\033[0m")
        print("\033[90m" + "-"*60 + "\033[0m")

        for port in results["open_ports"]:
            port_num = port["port"]
            proto = port["protocol"].upper()
            state = port["state"]
            service = port.get("service", "unknown")

            # Warna berdasarkan port
            if port_num in [80, 443, 8080, 8443]:
                port_display = f"\033[92m{port_num:5d}\033[0m"  # Hijau untuk web
            elif port_num in [21, 22, 23, 25, 110, 143]:
                port_display = f"\033[93m{port_num:5d}\033[0m"  # Kuning untuk common
            elif port_num < 1024:
                port_display = f"\033[96m{port_num:5d}\033[0m"  # Cyan untuk well-known
            else:
                port_display = f"\033[97m{port_num:5d}\033[0m"

            state_color = "\033[92m" if state == "open" else "\033[93m"

            print(f" {port_display}/\033[97m{proto:<4}\033[0m  {state_color}{state:<8}\033[0m \033[97m{service}\033[0m")

        print("\033[90m" + "-"*60 + "\033[0m")

        # Security recommendations
        self.display_recommendations(results)

    def display_recommendations(self, results):
        """Tampilkan rekomendasi keamanan berdasarkan hasil scan"""
        print("\n\033[91m🔒 SECURITY RECOMMENDATIONS:\033[0m")
        print("\033[90m" + "-"*60 + "\033[0m")

        recommendations = []
        open_ports = [p["port"] for p in results["open_ports"]]

        # Check common vulnerable ports
        vulnerable_ports = {
            21: "FTP - Consider using SFTP/FTPS instead",
            23: "Telnet - Highly insecure, use SSH",
            445: "SMB - Check for EternalBlue vulnerability",
            3389: "RDP - Ensure strong passwords",
            5900: "VNC - Consider SSH tunneling",
            873: "Rsync - Ensure proper authentication"
        }

        for port, recommendation in vulnerable_ports.items():
            if port in open_ports:
                recommendations.append(f"\033[91m⚠️  Port {port}: {recommendation}\033[0m")

        # Check web ports without HTTPS
        if 80 in open_ports and 443 not in open_ports:
            recommendations.append("\033[93m🌐 Port 80: HTTP only - Consider enabling HTTPS\033[0m")

        # Check SSH
        if 22 in open_ports:
            recommendations.append("\033[93m🔑 Port 22: SSH open - Use key-based auth, disable root login\033[0m")

        # Check database ports
        db_ports = [3306, 5432, 27017, 6379]
        for port in db_ports:
            if port in open_ports:
                recommendations.append(f"\033[93m🗄️  Port {port}: Database exposed - Restrict to localhost\033[0m")

        if recommendations:
            for rec in recommendations:
                print(f"  • {rec}")
        else:
            print("  \033[92m✅ No critical vulnerabilities detected\033[0m")

        print("\033[90m" + "-"*60 + "\033[0m")

    def batch_scan(self, targets_file):
        """Scan multiple targets dari file"""
        if not os.path.exists(targets_file):
            print(f"\033[91m[✗] File {targets_file} tidak ditemukan!\033[0m")
            return

        with open(targets_file) as f:
            targets = [line.strip() for line in f if line.strip()]

        print(f"\033[94m[*] Found {len(targets)} targets in file\033[0m")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.MAX_PARALLEL_SCANS) as executor:
            futures = []
            for target in targets:
                future = executor.submit(self.run_scan, target, "quick")
                futures.append((target, future))

            for target, future in futures:
                try:
                    results = future.result(timeout=self.config.DEFAULT_TIMEOUT)
                    if results:
                        print(f"\n\033[92m[✓] Scan completed for {target}\033[0m")
                except concurrent.futures.TimeoutError:
                    print(f"\n\033[91m[✗] Scan timeout for {target}\033[0m")

    def network_discovery(self, network_range=None):
        """Network discovery scan"""
        if not network_range:
            network_range = self.utils.get_network_range()

        print(f"\n\033[94m[→] Discovering devices in {network_range}...\033[0m")

        # Quick ping scan untuk menemukan live hosts
        cmd = f"{self.config.NMAP_PATH} -sn {network_range}"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Parse hasil discovery
                lines = result.stdout.split('\n')
                devices = []

                current_device = {}
                for line in lines:
                    line = line.strip()

                    if "Nmap scan report for" in line:
                        if current_device:
                            devices.append(current_device)
                        current_device = {"hostname": line.split("for")[-1].strip()}

                    elif "Host is up" in line:
                        current_device["status"] = "up"

                    elif "MAC Address:" in line:
                        mac_match = re.search(r'([0-9A-F:]{17})', line)
                        if mac_match:
                            current_device["mac"] = mac_match.group(1)

                        vendor_match = re.search(r'\((.*?)\)', line)
                        if vendor_match:
                            current_device["vendor"] = vendor_match.group(1)

                if current_device:
                    devices.append(current_device)

                # Tampilkan hasil
                print(f"\n\033[92m[✓] Found {len(devices)} devices:\033[0m")
                print("\033[90m" + "-"*50 + "\033[0m")
                for i, device in enumerate(devices, 1):
                    print(f"\033[97m{i:2d}. {device.get('hostname', 'Unknown')}\033[0m")
                    if "mac" in device:
                        print(f"    \033[96mMAC: {device['mac']}\033[0m")
                    if "vendor" in device:
                        print(f"    \033[96mVendor: {device['vendor']}\033[0m")
                    print()

                return devices
            else:
                print("\033[91m[✗] Discovery failed!\033[0m")
                return []

        except Exception as e:
            print(f"\033[91m[✗] Error: {str(e)}\033[0m")
            return []

    def show_history(self):
        """Tampilkan scan history"""
        if not self.scan_history:
            print("\033[93m[!] No scan history found\033[0m")
            return

        print("\n\033[91m📜 SCAN HISTORY:\033[0m")
        print("="*60)

        for i, scan in enumerate(reversed(self.scan_history[-10:]), 1):
            print(f"\033[97m{i:2d}. [{scan['scan_id']}]\033[0m")
            print(f"    \033[96mTarget: {scan['target']}\033[0m")
            print(f"    \033[96mProfile: {scan['profile']}\033[0m")
            print(f"    \033[96mPorts: {len(scan['open_ports'])} open\033[0m")
            print(f"    \033[96mTime: {scan['timestamp']}\033[0m")
            print()

# ========== COMMAND LINE INTERFACE ==========
class ZNmapCLI:
    def __init__(self):
        self.scanner = NmapScanner()
        self.running = True
        self.utils = ScannerUtils()
    def print_banner(self):
        """Print ZNmap banner dengan warna merah cyber"""
        banner = """
\033[91m
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           Advanced Network Scanner for Termux            ║
║               Znmap Cyber Security Edition               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
\033[0m
"""
        print(banner)

    def print_menu(self):
        """Print main menu"""
        print("\n" + "\033[90m" + "="*50 + "\033[0m")
        print("\033[97m[1]\033[0m \033[96mQuick Scan (100 common ports)\033[0m")
        print("\033[97m[2]\033[0m \033[96mCustom Scan\033[0m")
        print("\033[97m[3]\033[0m \033[96mNetwork Discovery\033[0m")
        print("\033[97m[4]\033[0m \033[96mBatch Scan from File\033[0m")
        print("\033[97m[5]\033[0m \033[96mVulnerability Scan\033[0m")
        print("\033[97m[6]\033[0m \033[96mWeb Server Scan\033[0m")
        print("\033[97m[7]\033[0m \033[96mMobile/Android Scan\033[0m")
        print("\033[97m[8]\033[0m \033[96mView Scan History\033[0m")
        print("\033[97m[9]\033[0m \033[96mScan Profiles Help\033[0m")
        print("\033[97m[0]\033[0m \033[91mExit\033[0m")
        print("\033[90m" + "="*50 + "\033[0m")

    def get_scan_profile(self):
        """Pilih scan profile"""
        print("\n\033[91m📊 SCAN PROFILES:\033[0m")
        profiles = Config.SCAN_PROFILES

        for i, (name, options) in enumerate(profiles.items(), 1):
            print(f"  \033[97m{i:2d}. \033[96m{name:10}\033[0m - \033[90m{options}\033[0m")

        try:
            choice = int(input("\n\033[93mSelect profile (1-10): \033[0m").strip())
            profile_names = list(profiles.keys())

            if 1 <= choice <= len(profile_names):
                return profile_names[choice - 1]
            else:
                print("\033[93m[!] Invalid choice, using 'quick'\033[0m")
                return "quick"
        except:
            return "quick"

    def run_quick_scan(self):
        """Quick scan dengan defaults"""
        target = input("\n\033[93m[?] Enter target (IP/Domain): \033[0m").strip()

        if not target:
            print("\033[91m[!] Target required!\033[0m")
            return

        # Auto-detect local scan
        if target.lower() in ["local", "lan", "network"]:
            target = self.scanner.utils.get_network_range()
            print(f"\033[94m[*] Using network range: {target}\033[0m")

        results = self.scanner.run_scan(target, "termux")
        if results:
            self.scanner.display_results(results)

    def run_custom_scan(self):
        """Custom scan dengan options"""
        target = input("\n\033[93m[?] Enter target: \033[0m").strip()

        if not target:
            print("\033[91m[!] Target required!\033[0m")
            return

        profile = self.get_scan_profile()

        custom_ports = input("\033[93m[?] Custom ports (e.g., 22,80,443 or 1-1000): \033[0m").strip()
        custom_options = input("\033[93m[?] Additional nmap options: \033[0m").strip()

        results = self.scanner.run_scan(
            target,
            profile,
            ports=custom_ports if custom_ports else None,
            options=custom_options
        )

        if results:
            self.scanner.display_results(results)

    def run_vulnerability_scan(self):
        """Vulnerability scan khusus"""
        target = input("\n\033[93m[?] Enter target: \033[0m").strip()

        if not target:
            print("\033[91m[!] Target required!\033[0m")
            return

        print("\033[93m[*] Running vulnerability scan...\033[0m")
        print("\033[93m[!] This may take several minutes\033[0m")

        results = self.scanner.run_scan(target, "vuln")
        if results:
            self.scanner.display_results(results)

    def run_web_scan(self):
        """Web server scan"""
        target = input("\n\033[93m[?] Enter web server (IP/Domain): \033[0m").strip()

        if not target:
            print("\033[91m[!] Target required!\033[0m")
            return

        results = self.scanner.run_scan(target, "web")
        if results:
            self.scanner.display_results(results)

            # Additional web info
            open_ports = [p["port"] for p in results["open_ports"]]

            if 80 in open_ports:
                print("\n\033[96m🌐 HTTP Server detected:\033[0m")
                print("  \033[90mTry: curl -I http://" + target + "\033[0m")

            if 443 in open_ports:
                print("\n\033[92m🔒 HTTPS Server detected:\033[0m")
                print("  \033[90mTry: curl -I https://" + target + "\033[0m")
                print("  \033[90mCheck SSL: openssl s_client -connect " + target + ":443\033[0m")

    def run_mobile_scan(self):
        """Mobile/Android device scan"""
        target = input("\n\033[93m[?] Enter Android device IP: \033[0m").strip()

        if not target:
            print("\033[91m[!] Target required!\033[0m")
            return

        print("\033[93m[*] Scanning common Android ports...\033[0m")

        results = self.scanner.run_scan(target, "mobile")
        if results:
            self.scanner.display_results(results)

            # Android specific recommendations
            print("\n\033[91m📱 ANDROID SPECIFIC:\033[0m")
            open_ports = [p["port"] for p in results["open_ports"]]

            if 5555 in open_ports:
                print("\033[91m⚠️  Port 5555: ADB debugging enabled!\033[0m")
                print("\033[93m   This allows remote shell access\033[0m")
                print("\033[93m   Consider disabling Developer Options\033[0m")

            if 5037 in open_ports:
                print("\033[91m⚠️  Port 5037: ADB server running!\033[0m")
                print("\033[93m   Device may be rooted/unlocked\033[0m")

    def run_batch_scan(self):
        """Batch scan dari file"""
        filename = input("\n\033[93m[?] Enter targets file path: \033[0m").strip()

        if not os.path.exists(filename):
            print(f"\033[91m[!] File {filename} not found!\033[0m")
            return

        self.scanner.batch_scan(filename)

    def show_profiles_help(self):
        """Tampilkan bantuan scan profiles"""
        print("\n\033[91m📖 SCAN PROFILES HELP:\033[0m")
        print("\033[90m" + "="*60 + "\033[0m")

        profiles = Config.SCAN_PROFILES

        for name, options in profiles.items():
            print(f"\n\033[96m🔹 {name.upper()}:\033[0m")
            print(f"\033[90m   Command: nmap {options}\033[0m")
            print(f"\033[97m   Use case: \033[0m", end="")

            if name == "quick":
                print("\033[93mFast reconnaissance\033[0m")
            elif name == "basic":
                print("\033[93mGeneral purpose scan\033[0m")
            elif name == "stealth":
                print("\033[93mAvoid detection\033[0m")
            elif name == "full":
                print("\033[93mComprehensive scan (slow)\033[0m")
            elif name == "vuln":
                print("\033[91mVulnerability detection\033[0m")
            elif name == "os":
                print("\033[93mOS fingerprinting\033[0m")
            elif name == "udp":
                print("\033[93mUDP services scan\033[0m")
            elif name == "web":
                print("\033[93mWeb server assessment\033[0m")
            elif name == "mobile":
                print("\033[93mAndroid/iOS devices\033[0m")
            elif name == "termux":
                print("\033[92mOptimized for Termux\033[0m")

        print("\n\033[96m💡 Tips:\033[0m")
        print("  \033[97m• Use 'termux' profile for best performance on Android\033[0m")
        print("  \033[97m• Use 'quick' for fast results\033[0m")
        print("  \033[97m• Use 'stealth' to avoid firewalls\033[0m")
        print("  \033[97m• Root may be needed for some scans\033[0m")
        print("\033[90m" + "="*60 + "\033[0m")

    def run(self):
        """Main CLI loop"""
        # Cek nmap terinstall
        if not ScannerUtils.check_nmap_installed():
            print("\033[91m[✗] Nmap is required but not installed!\033[0m")
            print("\033[93m[*] Install with: pkg install nmap\033[0m")
            return

        while self.running:
            self.utils.clear_screen()
            self.print_banner()
            self.print_menu()

            try:
                choice = input("\n\033[93mSelect option: \033[0m").strip()

                if choice == "1":
                    self.run_quick_scan()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "2":
                    self.run_custom_scan()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "3":
                    devices = self.scanner.network_discovery()
                    if devices and input("\n\033[93mScan discovered devices? (y/N): \033[0m").lower() == 'y':
                        for device in devices:
                            if "hostname" in device:
                                self.scanner.run_scan(device["hostname"], "quick")
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "4":
                    self.run_batch_scan()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "5":
                    self.run_vulnerability_scan()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "6":
                    self.run_web_scan()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "7":
                    self.run_mobile_scan()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "8":
                    self.scanner.show_history()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "9":
                    self.show_profiles_help()
                    input("\n\033[90mPress Enter to continue...\033[0m")

                elif choice == "0":
                    print("\n\033[92mGoodbye! 👋\033[0m")
                    self.running = False

                else:
                    print("\033[91m[!] Invalid choice!\033[0m")
                    time.sleep(1)

            except KeyboardInterrupt:
                print("\n\n\033[93mExiting...\033[0m")
                self.running = False

            except Exception as e:
                print(f"\033[91m[!] Error: {str(e)}\033[0m")
                time.sleep(2)

# ========== MAIN ==========
if __name__ == "__main__":
    try:
        cli = ZNmapCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n\033[93mProgram interrupted. Exiting...\033[0m")
    except Exception as e:
        print(f"\n\033[91m[✗] Fatal error: {str(e)}\033[0m")
