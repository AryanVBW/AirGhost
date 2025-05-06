#!/bin/bash
# AirGhost Development Environment Setup Script
# This script sets up the development environment for AirGhost on Kali Linux

# Text colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored status messages
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_good() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root"
    echo "Usage: sudo ./dev_setup.sh"
    exit 1
fi

# Check if running on Kali Linux
if [ ! -f /etc/os-release ] || ! grep -q 'Kali' /etc/os-release; then
    print_warning "This script is designed for Kali Linux"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_status "Starting AirGhost development environment setup..."

# Update package lists
print_status "Updating package lists..."
apt-get update

# Install system dependencies
print_status "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    aircrack-ng \
    hostapd \
    dnsmasq \
    iptables \
    macchanger \
    net-tools \
    wireless-tools \
    iw \
    rfkill \
    git \
    nodejs \
    npm

if [ $? -ne 0 ]; then
    print_error "Failed to install system dependencies"
    exit 1
fi
print_good "System dependencies installed successfully"

# Create Python virtual environment
print_status "Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    print_good "Virtual environment created successfully"
fi

# Activate virtual environment and install Python dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null

# If requirements.txt doesn't exist, create it and install common dependencies
if [ $? -ne 0 ]; then
    print_warning "requirements.txt not found. Creating default requirements file."
    cat > requirements.txt << EOF
Flask==2.0.1
Flask-SocketIO==5.1.1
scapy==2.4.5
netifaces==0.11.0
psutil==5.8.0
requests==2.26.0
python-dotenv==0.19.0
pyOpenSSL==20.0.1
EOF
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "Failed to install Python dependencies"
        exit 1
    fi
fi
print_good "Python dependencies installed successfully"

# Install frontend dependencies
if [ -f "package.json" ]; then
    print_status "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        print_error "Failed to install frontend dependencies"
        exit 1
    fi
    print_good "Frontend dependencies installed successfully"
else
    print_warning "No package.json found. Skipping frontend dependencies."
fi

# Create necessary directories if they don't exist
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p config

# Create default configuration files if they don't exist
print_status "Creating default configuration files..."

# hostapd.conf
if [ ! -f "config/hostapd.conf" ]; then
    cat > config/hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=Free-WiFi
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
EOF
    print_good "Created default hostapd.conf"
fi

# dnsmasq.conf
if [ ! -f "config/dnsmasq.conf" ]; then
    cat > config/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=192.168.1.2,192.168.1.30,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1
server=8.8.8.8
log-queries
log-dhcp
listen-address=127.0.0.1
address=/#/192.168.1.1
EOF
    print_good "Created default dnsmasq.conf"
fi

# Create development environment file
if [ ! -f ".env" ]; then
    cat > .env << EOF
# AirGhost Development Environment Variables
DEBUG=True
HOST=0.0.0.0
PORT=8080
SECRET_KEY=$(openssl rand -hex 32)
EOF
    print_good "Created .env file with development settings"
fi

# Set up Git hooks for development
print_status "Setting up Git hooks..."
if [ -d ".git" ]; then
    # Create pre-commit hook
    cat > .git/hooks/pre-commit << EOF
#!/bin/bash
# Pre-commit hook for AirGhost

# Run linting
echo "Running Python linting..."
source venv/bin/activate
pip install pylint 2>/dev/null
pylint --disable=C0111,C0103,C0303,W0312,W0611,R0903,C0301 --ignore=venv *.py scripts/*.py

if [ \$? -ne 0 ]; then
    echo "Linting failed. Please fix the issues before committing."
    exit 1
fi

exit 0
EOF
    chmod +x .git/hooks/pre-commit
    print_good "Git hooks set up successfully"
else
    print_warning "Not a Git repository. Skipping Git hooks setup."
fi

# Create a development startup script
cat > dev_start.sh << EOF
#!/bin/bash
# AirGhost Development Startup Script

# Activate virtual environment
source venv/bin/activate

# Export environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start the development server
python scripts/server.py
EOF
chmod +x dev_start.sh
print_good "Created development startup script (dev_start.sh)"

print_status "Development environment setup complete!"
print_status "To start the development server, run: ./dev_start.sh"
print_status "To activate the virtual environment manually, run: source venv/bin/activate"

# Provide additional information
cat << EOF

${BLUE}=== AirGhost Development Environment ====${NC}

${GREEN}Directories:${NC}
- templates/: Phishing templates
- scripts/: Python scripts for various functions
- config/: Configuration files
- logs/: Log files
- data/: Data storage

${GREEN}Development Commands:${NC}
- Start development server: ./dev_start.sh
- Activate virtual environment: source venv/bin/activate
- Deactivate virtual environment: deactivate
- Install new Python dependency: pip install <package> && pip freeze > requirements.txt

${YELLOW}Note:${NC} This is a development environment. For production use, please use the standard installation method described in the README.

EOF

exit 0
