#!/data/data/com.termux/files/usr/bin/bash
# install_zenego.sh

echo "Installing Zenego (Zeno Maltego) for Termux..."

# Update Termux
pkg update -y && pkg upgrade -y

# Install Python and dependencies
pkg install -y python python-pip git clang

# Install Python packages (LIGHTWEIGHT ONLY!)
pip install --user aiohttp requests beautifulsoup4 lxml python-whois dnspython

# Clone Zenego
git clone https://github.com/yourusername/zenego.git
cd zenego

# Make executable
chmod +x zenego.py

# Create alias
echo 'alias zenego="python $(pwd)/zenego.py"' >> ~/.bashrc
echo 'alias zenego-i="python $(pwd)/zenego.py --interactive"' >> ~/.bashrc

# Create config file
cat > config.json << 'EOF'
{
  "SHODAN_API_KEY": "YOUR_API_KEY!!",
  "VIRUSTOTAL_API_KEY": "YOUR_API_KEY!!",
  "HIBP_API_KEY": "",
  "MAX_WORKERS": 3,
  "CACHE_TTL": 3600
}
EOF

echo ""
echo "╭────────────────────────────────────────╮"
echo "│      ZENEGO INSTALLATION COMPLETE!     │"
echo "╰────────────────────────────────────────╯"
echo ""
echo "Usage:"
echo "  zenego transform shodan 1.2.3.4"
echo "  zenego search google.com"
echo "  zenego --interactive"
echo ""
echo "First, edit config.json to add your API keys!"
echo "Config file: $(pwd)/config.json"
