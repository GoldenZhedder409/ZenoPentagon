ZENOPENTAGON - Ultimate Pentesting Suite for Termux 🚀

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.7+-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Termux-Optimized-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-red?style=for-the-badge" />
</p>

<p align="center">
  <b>🔥 5 Powerful Tools, 1 Ultimate Framework 🔥</b><br/>
  <i>The Complete Pentesting Arsenal for Android (No Root Required!)</i>
</p>

---

📋 TABLE OF CONTENTS

· Overview
· Tools Included
· Installation
· Quick Start Guide
· Tool 1: BurpMini Advanced
· Tool 2: ZHydra Suite
· Tool 3: ZNmap Scanner
· Tool 4: ZSQLmap
· Tool 5: ZENEGO (The Maltego Killer)
· Comparison Chart
· Use Cases
· Legal Disclaimer
· Contributing

---

🎯 OVERVIEW

ZenoPentagon is a comprehensive penetration testing framework built specifically for Termux on Android. Unlike traditional security tools that require root access or heavy dependencies, ZenoPentagon is:

✅ Lightweight - Runs smoothly on Android
✅ No Root Required - Works in standard Termux
✅ All-in-One - 5 complete tools in 1 framework
✅ AI-Powered - Smart pattern generation (no wordlists!)
✅ Professional Grade - Bug bounty ready

---

🔧 TOOLS INCLUDED

# Tool Function Lines of Code
1 BurpMini Advanced Bug Bounty Multi-Tool 850+
2 ZHydra Suite AI-Powered Brute Force 1300+
3 ZNmap Scanner Advanced Network Scanner 700+
4 ZSQLmap SQL Injection Toolkit 900+
5 ZENEGO OSINT / Maltego Clone 600+
 TOTAL Complete Framework ~4350+ lines

---

📦 INSTALLATION

```bash
# 1. Update Termux
pkg update && pkg upgrade

# 2. Install Python and dependencies
pkg install python git
pip install requests colorama pyyaml paramiko pymysql aiohttp dnspython python-whois

# 3. Install additional tools (for some features)
pkg install nmap sqlmap

# 4. Clone ZenoPentagon
git clone https://github.com/yourusername/zenopentagon
cd zenopentagon

# 5. Make scripts executable
chmod +x *.py

# 6. Run the main launcher
python zenopentagon.py
```

---

🚀 QUICK START GUIDE

```bash
# Launch interactive menu
python zenopentagon.py

# Or run individual tools directly
python burpmini.py --help
python zhydra.py --help
python znmap.py --help
python zsqlmap.py --help
python zenego.py --help
```

---

🔥 TOOL 1: BurpMini Advanced - Bug Bounty Multi-Tool

BurpSuite-like CLI tool for bug bounty testing

✨ Features

· IDOR Scanner - Test for Insecure Direct Object References
· SSRF Scanner - Server-Side Request Forgery testing
· SQLi Scanner - SQL Injection detection
· XSS Scanner - Cross-Site Scripting testing
· CORS Scanner - CORS misconfiguration detection
· JWT Tester - JWT vulnerability testing
· Endpoint Discovery - Find hidden endpoints

🎮 Example Usage

```bash
# IDOR Scan
python burpmini.py -u https://api.target.com/users/{id} --scan idor --user-ids 1,2,3,4,5

# Full Scan with auth token
python burpmini.py -u https://target.com/api --scan all --token YOUR_TOKEN

# SSRF Testing
python burpmini.py -u https://target.com/webhook --scan ssrf --param url
```

---

🔥 TOOL 2: ZHydra Suite - AI-Powered Brute Force

The ultimate brute force tool that needs NO WORDLISTS!

✨ Features

· Smart Pattern Generation - AI creates passwords on-the-fly
· Leet Speak Variations - 4dm1n, p4ssw0rd, etc.
· Context-Aware - Uses company names, dates, hints
· Multi-Protocol - SSH, FTP, HTTP, MySQL, Telnet, SMTP
· No Wordlist Required - Pure algorithmic generation
· Progress Tracking - Real-time stats and ETA

🎮 Example Usage

```bash
# Smart SSH attack
python zhydra.py --target 192.168.1.100 --port 22 --protocol ssh --max-attempts 5000

# With context hints
python zhydra.py --target company.com --protocol http --context "company:techcorp,year:2024"

# Network pivoting
python zhydra.py --pivot --local-port 8080 --target-host internal.corp.com --target-port 80
```

🧠 Smart Pattern Examples

```
Base: "admin"
Generated: admin123, admin!, Admin2024, 4dm1n, admin@123, admin#2024, ADMIN, adminadmin
```

---

🔥 TOOL 3: ZNmap Scanner - Advanced Network Scanner

Termux-optimized network scanner with professional features

✨ Features

· Multiple Scan Profiles - Quick, Basic, Stealth, Full, Vuln
· Network Discovery - Find all devices on network
· Service Detection - Identify running services
· OS Fingerprinting - Detect operating systems
· Vulnerability Scanning - Basic vuln detection
· Export Formats - JSON, CSV, TXT
· Android-Specific - Scans for ADB, mobile ports

🎮 Example Usage

```bash
# Quick scan (100 common ports)
python znmap.py --target 192.168.1.1 --profile quick

# Network discovery
python znmap.py --discover

# Vulnerability scan
python znmap.py --target example.com --profile vuln

# Mobile device scan
python znmap.py --target 192.168.1.10 --profile mobile
```

📊 Scan Profiles

Profile Command Use Case
quick -T4 -F --open Fast reconnaissance
basic -T4 -sV --open General purpose
stealth -T2 -sS --open Avoid detection
full -T4 -A -p- Comprehensive
vuln -T4 --script vuln Vulnerability check
mobile -T4 -p 22,80,443,5555,5037 Android devices

---

🔥 TOOL 4: ZSQLmap - SQL Injection Toolkit

Advanced SQL injection framework with request bridge

✨ Features

· Request Bridge - Capture & replay HTTP requests
· Audit Database - SQLite logging of all scans
· Multiple Attack Modes - Basic to Advanced
· Bug Bounty Workflow - Step-by-step methodology
· Data Extraction - Dump databases, tables, columns
· Report Generation - Professional PDF/HTML reports
· Integration - Works with saved .req files

🎮 Example Usage

```bash
# Interactive mode
python zsqlmap.py

# Quick URL test
python zsqlmap.py --url "http://testphp.vulnweb.com/artists.php?artist=1" --mode basic

# Test captured request
python zsqlmap.py --request captured_requests/request_20250101_120000.req --mode full

# Database enumeration
python zsqlmap.py --url TARGET --dbs --tables
```

📈 Bug Bounty Workflow

```
1. Reconnaissance → 2. Target Selection → 3. Automated Scan → 4. Manual Testing → 5. Report
```

---

🔥 TOOL 5: ZENEGO - Zeno Maltego (OSINT Powerhouse)

⚡ THE MALTEGO KILLER FOR TERMUX! ⚡

Finally - a lightweight Maltego alternative that runs on Android!

🎯 Why ZENEGO is a GAME CHANGER:

Feature Maltego ZENEGO
Needs Java ❌ YES (1GB+) ✅ NO
Runs on Termux ❌ ✅ YES
Memory Usage 2GB+ ✅ <50MB
Price $1000+/year ✅ FREE
Async API ❌ ✅ YES
Database Proprietary ✅ SQLite
Export Formats Limited ✅ JSON, CSV, GraphML
Learning Curve Steep ✅ Simple CLI

✨ ZENEGO Features:

🔍 Entities Supported

```
• IP Addresses     • Domains
• Ports            • MX Records
• Registrars       • SSL Certificates
• Email Addresses  • Social Media
• Companies        • Technologies
```

🔄 Transforms Available

```python
1. shodan  - One API call returns IPs + Ports + Services + OS + Location
2. dns     - A records, MX records, CNAME, TXT
3. whois   - Registrar, creation date, name servers
4. expand  - Find all connections to an entity
5. social  - Social media presence (coming soon)
```

💾 Smart Database

```sql
-- All entities and relationships saved
-- Build your OSINT graph over time
-- Query, search, export anytime
```

📊 Visualization Ready

```
Export to GraphML → Open in Gephi → See your OSINT graph!
```

🎮 ZENEGO Quick Start

```bash
# Interactive mode (recommended)
python zenego.py -i

# Command line transforms
python zenego.py transform shodan 8.8.8.8
python zenego.py transform dns google.com
python zenego.py transform whois example.org

# Search database
python zenego.py search "google"

# Export for visualization
python zenego.py export graphml --output osint_graph.graphml
```

🔥 ZENEGO Power Examples

```bash
# 1. Shodan transform - ONE CALL GETS ALL!
python zenego.py transform shodan 8.8.8.8
# Returns: IP, open ports, services, OS, location, ISP

# 2. Build relationship graph
python zenego.py transform dns google.com
python zenego.py transform whois google.com
python zenego.py transform expand google.com

# 3. Export and visualize
python zenego.py export graphml --output google_graph.graphml
# Open in Gephi → Apply Force Atlas 2 → See connections!
```

🎯 Real OSINT Workflow with ZENEGO

```bash
# Step 1: Start with a domain
python zenego.py transform dns target.com

# Step 2: Enrich with WHOIS
python zenego.py transform whois target.com

# Step 3: Find connected IPs
python zenego.py transform expand target.com

# Step 4: Scan IPs with Shodan
python zenego.py transform shodan 192.168.1.1

# Step 5: See the full picture
python zenego.py export graphml --output full_graph.graphml
# Open in Gephi → See all connections visually!
```

---

📊 COMPARISON CHART

Feature BurpSuite Hydra Nmap SQLmap Maltego ZenoPentagon
Free ❌ ✅ ✅ ✅ ❌ ✅
No Wordlists ❌ ❌ N/A N/A N/A ✅
Termux Ready ❌ ⚠️ ✅ ✅ ❌ ✅
No Root ❌ ✅ ✅ ✅ ❌ ✅
Async ❌ ❌ ❌ ❌ ❌ ✅
AI-Powered ❌ ❌ ❌ ❌ ❌ ✅
All-in-One ❌ ❌ ❌ ❌ ❌ ✅

---

🎯 USE CASES

🔹 Bug Bounty Hunters

```bash
# Full workflow
1. ZENEGO - OSINT on target domain
2. ZNmap - Scan for open ports
3. BurpMini - Test web vulnerabilities
4. ZSQLmap - Deep SQL injection testing
5. ZHydra - Brute force if needed
```

🔹 Penetration Testers

```bash
# Internal network test
1. ZNmap discovery → Find live hosts
2. ZHydra → Test credentials
3. BurpMini → Web app testing
4. ZENEGO → Build target graph
```

🔹 Security Researchers

```bash
# Research workflow
1. ZENEGO → Gather OSINT data
2. Export to GraphML → Visualize in Gephi
3. Identify patterns and connections
4. Document findings
```

🔹 CTF Players

```bash
# CTF workflow
1. ZNmap → Find open ports
2. BurpMini → Web challenges
3. ZSQLmap → SQL injection challenges
4. ZHydra → Password cracking challenges
5. ZENEGO → OSINT challenges
```

---

⚖️ LEGAL DISCLAIMER

```
⚠️  IMPORTANT - READ BEFORE USING ⚠️

ZenoPentagon is designed for:
✅ Authorized penetration testing
✅ Security research on your own systems
✅ CTF competitions and labs
✅ Bug bounty hunting with permission

ZenoPentagon is NOT for:
❌ Unauthorized access to systems
❌ Hacking without permission
❌ Illegal activities of any kind

YOU are 100% responsible for your actions.
Always obtain WRITTEN PERMISSION before testing.
```

---

🤝 CONTRIBUTING

Want to make ZenoPentagon even better?

1. Fork the repository
2. Create your feature branch
3. Add your awesome feature
4. Submit a pull request

Ideas for contributions:

· Add more transforms to ZENEGO
· Add new protocols to ZHydra
· Improve scanning algorithms
· Add GUI interface
· Create Docker container

---

📞 SUPPORT

· Discord: On my description 
· Email: mailto:Zhedder409

---

⭐ SHOW YOUR SUPPORT

If ZenoPentagon helps you in your work:

· ⭐ Star the repository
· 🐦 Share on Twitter
· 💬 Tell your friends
· 🤝 Contribute code

---

🏆 ACKNOWLEDGMENTS

Built with ❤️ for the security community
Special thanks to all bug bounty hunters and pentesters

---

<p align="center">
  <b>🚀 ZenoPentagon - The Ultimate Termux Security Suite 🚀</b><br/>
  <i>One Framework to Rule Them All</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Runs%20on-Termux-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Power-Unlimited-red?style=for-the-badge" />
</p>

---

🎬 FINAL WORD - THE MALTEGO KILLER

Let's be real for a second:

Maltego is powerful but...

· Needs Java (1GB+ RAM)
· Costs $1000+/year
· Won't run on your phone
· Overkill for quick OSINT

ZENEGO is the solution:

· Runs on Termux (your phone!)
· Completely FREE
· <50MB memory
· Async = FAST
· GraphML export (use Gephi for viz)
· SQLite database (persistent storage)

One ZENEGO transform = 10 Maltego transforms

```bash
# Compare:
# Maltego: 
   Run "To IP" → then "To Ports" → then "To Services" → then "To Location"

# ZENEGO:
   python zenego.py transform shodan 8.8.8.8
   # Returns: IP + Ports + Services + Location + OS + ISP ALL AT ONCE!
```

This isn't just a tool - it's a MOVEMENT.
Making professional OSINT accessible to everyone, anywhere, on any device.

GASS BABY! 🔥🔥🔥

---

<p align="center">
  <b>⬇️ START YOUR JOURNEY ⬇️</b><br/>
  <code>git clone https://github.com/yourname/zenopentagon</code><br/>
  <code>cd zenopentagon</code><br/>
  <code>python zenopentagon.py</code>
</p>

<p align="center">
  <i>Remember: With great power comes great responsibility.</i><br/>
  <b>Stay Ethical. Stay Legal. Stay Awesome.</b>
</p>
