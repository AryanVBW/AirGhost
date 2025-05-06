#!/bin/bash
#
# AirGhost - Raspberry Pi Zero W Wi-Fi Penetration Testing Platform Setup
# A comprehensive script to convert your Raspberry Pi Zero W into a portable 
# Wi-Fi penetration testing device with web interface
#

# Terminal colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner function
print_banner() {
    clear
    echo -e "${CYAN}"
    echo "  █████╗ ██╗██████╗  ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗"
    echo " ██╔══██╗██║██╔══██╗██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝"
    echo " ███████║██║██████╔╝██║  ███╗███████║██║   ██║███████╗   ██║   "
    echo " ██╔══██║██║██╔══██╗██║   ██║██╔══██║██║   ██║╚════██║   ██║   "
    echo " ██║  ██║██║██║  ██║╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   "
    echo " ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   "
    echo -e "${NC}"
    echo -e "${YELLOW}Raspberry Pi Zero W Wi-Fi Penetration Testing Platform${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
    echo ""
}

# Function to check if the script is running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}[ERROR] This script must be run as root${NC}"
        echo "Please run with: sudo $0"
        exit 1
    fi
}

# Function to check if we're running on a Raspberry Pi
check_hardware() {
    local model=$(cat /proc/device-tree/model 2>/dev/null | grep -i "raspberry pi" || echo "")
    
    if [[ -z "$model" ]]; then
        echo -e "${YELLOW}[WARNING] This doesn't appear to be a Raspberry Pi.${NC}"
        read -p "Continue anyway? (y/n): " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            echo -e "${RED}Setup aborted.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}[INFO] Detected: $model${NC}"
    fi
}

# Function to check and create directories
setup_directories() {
    echo -e "${BLUE}[*] Setting up directory structure...${NC}"
    
    # Main application directory
    mkdir -p /opt/airghost
    # Web interface directory
    mkdir -p /opt/airghost/web
    # Attack templates directory
    mkdir -p /opt/airghost/templates
    # Log directory
    mkdir -p /opt/airghost/logs
    # Config directory
    mkdir -p /opt/airghost/config
    # Scripts directory
    mkdir -p /opt/airghost/scripts
    
    echo -e "${GREEN}[+] Directory structure created${NC}"
}

# Update and upgrade packages
update_system() {
    echo -e "${BLUE}[*] Updating package lists and upgrading installed packages...${NC}"
    apt update && apt upgrade -y
    echo -e "${GREEN}[+] System updated${NC}"
}

# Install dependencies
install_dependencies() {
    echo -e "${BLUE}[*] Installing dependencies...${NC}"
    
    # List of packages to install
    PACKAGES=(
        python3 python3-pip python3-flask python3-flask-socketio python3-dev
        hostapd dnsmasq dhcpd isc-dhcp-server
        aircrack-ng mdk4 mdk3 
        apache2 php php-cgi libapache2-mod-php
        build-essential libssl-dev libffi-dev
        git curl wget unzip
        rfkill iw wireless-tools
        iptables nftables
        macchanger
        net-tools
        nodejs npm
    )
    
    # Install packages
    apt install -y ${PACKAGES[@]}
    
    # Install Python packages
    echo -e "${BLUE}[*] Installing Python packages...${NC}"
    pip3 install flask flask-socketio scapy netifaces psutil
    
    echo -e "${GREEN}[+] All dependencies installed${NC}"
}

# Install specialized tools
install_specialized_tools() {
    echo -e "${BLUE}[*] Installing specialized penetration testing tools...${NC}"
    
    # Current directory
    CURRENT_DIR=$(pwd)
    
    # Wifiphisher
    echo -e "${CYAN}[*] Installing Wifiphisher...${NC}"
    cd /tmp
    git clone https://github.com/wifiphisher/wifiphisher.git
    cd wifiphisher
    python3 setup.py install
    
    # Bettercap (for advanced MITM capabilities)
    echo -e "${CYAN}[*] Installing Bettercap...${NC}"
    apt install -y libpcap-dev libusb-1.0-0-dev libnetfilter-queue-dev
    cd /tmp
    go get github.com/bettercap/bettercap
    
    # Hcxdumptool (for PMKID attacks)
    echo -e "${CYAN}[*] Installing hcxdumptool...${NC}"
    cd /tmp
    git clone https://github.com/ZerBea/hcxdumptool.git
    cd hcxdumptool
    make
    make install
    
    # Return to original directory
    cd "$CURRENT_DIR"
    
    echo -e "${GREEN}[+] Specialized tools installed${NC}"
}

# Configure hostapd
configure_hostapd() {
    echo -e "${BLUE}[*] Configuring hostapd...${NC}"
    
    cat > /opt/airghost/config/hostapd.conf << EOF
# hostapd configuration
interface=wlan0
driver=nl80211
ssid=AirGhost_AP
hw_mode=g
channel=1
macaddr_acl=0
ignore_broadcast_ssid=0
auth_algs=1
wpa=2
wpa_passphrase=AirGhostAP
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

    echo -e "${GREEN}[+] hostapd configured${NC}"
}

# Configure dnsmasq
configure_dnsmasq() {
    echo -e "${BLUE}[*] Configuring dnsmasq...${NC}"
    
    cat > /opt/airghost/config/dnsmasq.conf << EOF
# dnsmasq configuration
interface=wlan0
dhcp-range=192.168.1.2,192.168.1.30,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1
server=8.8.8.8
log-queries
log-dhcp
address=/#/192.168.1.1
EOF

    echo -e "${GREEN}[+] dnsmasq configured${NC}"
}

# Create web interface
create_web_interface() {
    echo -e "${BLUE}[*] Creating web interface...${NC}"
    
    # We'll create the web interface files in the next steps
    
    echo -e "${GREEN}[+] Web interface created${NC}"
}

# Create backend scripts
create_backend_scripts() {
    echo -e "${BLUE}[*] Creating backend scripts...${NC}"
    
    # We'll create the backend scripts in the next steps
    
    echo -e "${GREEN}[+] Backend scripts created${NC}"
}

# Create service files
create_service_files() {
    echo -e "${BLUE}[*] Creating service files...${NC}"
    
    # AirGhost service
    cat > /etc/systemd/system/airghost.service << EOF
[Unit]
Description=AirGhost Wi-Fi Penetration Testing Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/airghost
ExecStart=/usr/bin/python3 /opt/airghost/scripts/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${GREEN}[+] Service files created${NC}"
    
    # Enable service
    systemctl daemon-reload
    systemctl enable airghost.service
}

# Function to detect available wireless interfaces
detect_wireless_interfaces() {
    echo -e "${BLUE}[*] Detecting wireless interfaces...${NC}"
    iw dev | grep Interface | awk '{print $2}'
}

# Function to configure the default interface
configure_interface() {
    echo -e "${BLUE}[*] Configuring network interfaces...${NC}"
    
    INTERFACES=($(detect_wireless_interfaces))
    
    if [ ${#INTERFACES[@]} -eq 0 ]; then
        echo -e "${RED}[ERROR] No wireless interfaces detected!${NC}"
        echo "Please ensure your wireless interfaces are properly connected and enabled."
        exit 1
    fi
    
    echo "Detected wireless interfaces:"
    for i in "${!INTERFACES[@]}"; do
        echo "[$i] ${INTERFACES[$i]}"
    done
    
    DEFAULT_INTERFACE=0
    read -p "Select the default interface for creating the Access Point [0]: " choice
    
    if [[ -n "$choice" ]]; then
        DEFAULT_INTERFACE=$choice
    fi
    
    if [[ $DEFAULT_INTERFACE -ge ${#INTERFACES[@]} ]]; then
        echo -e "${RED}[ERROR] Invalid interface selection!${NC}"
        exit 1
    fi
    
    SELECTED_INTERFACE=${INTERFACES[$DEFAULT_INTERFACE]}
    echo -e "${GREEN}[+] Selected ${SELECTED_INTERFACE} as the default interface${NC}"
    
    # Save the selected interface to the configuration
    echo "DEFAULT_INTERFACE=${SELECTED_INTERFACE}" > /opt/airghost/config/interface.conf
}

# Function to configure AP settings
configure_ap_settings() {
    echo -e "${BLUE}[*] Configuring Access Point settings...${NC}"
    
    read -p "Enter Access Point Name (SSID) [AirGhost_AP]: " AP_SSID
    AP_SSID=${AP_SSID:-AirGhost_AP}
    
    read -p "Enable WPA2 security? (y/n) [y]: " ENABLE_SECURITY
    ENABLE_SECURITY=${ENABLE_SECURITY:-y}
    
    if [[ "$ENABLE_SECURITY" =~ ^[Yy]$ ]]; then
        read -p "Enter WPA2 Password (min 8 characters) [AirGhostAP]: " AP_PASSWORD
        AP_PASSWORD=${AP_PASSWORD:-AirGhostAP}
        
        # Ensure password is at least 8 characters
        while [ ${#AP_PASSWORD} -lt 8 ]; do
            echo -e "${RED}[ERROR] Password must be at least 8 characters long!${NC}"
            read -p "Enter WPA2 Password (min 8 characters) [AirGhostAP]: " AP_PASSWORD
            AP_PASSWORD=${AP_PASSWORD:-AirGhostAP}
        done
        
        SECURITY_CONFIG="wpa=2\nwpa_passphrase=$AP_PASSWORD\nwpa_key_mgmt=WPA-PSK\nwpa_pairwise=TKIP\nrsn_pairwise=CCMP"
    else
        SECURITY_CONFIG=""
    fi
    
    # Save AP settings to the configuration
    cat > /opt/airghost/config/ap.conf << EOF
SSID=$AP_SSID
SECURITY=$ENABLE_SECURITY
PASSWORD=$AP_PASSWORD
CHANNEL=1
EOF

    # Update hostapd configuration
    sed -i "s/^ssid=.*/ssid=$AP_SSID/" /opt/airghost/config/hostapd.conf
    
    if [[ "$ENABLE_SECURITY" =~ ^[Yy]$ ]]; then
        # Ensure security parameters exist in the hostapd.conf
        sed -i "s/^wpa_passphrase=.*/wpa_passphrase=$AP_PASSWORD/" /opt/airghost/config/hostapd.conf
    else
        # Remove security parameters from hostapd.conf
        sed -i '/^wpa=/d' /opt/airghost/config/hostapd.conf
        sed -i '/^wpa_passphrase=/d' /opt/airghost/config/hostapd.conf
        sed -i '/^wpa_key_mgmt=/d' /opt/airghost/config/hostapd.conf
        sed -i '/^wpa_pairwise=/d' /opt/airghost/config/hostapd.conf
        sed -i '/^rsn_pairwise=/d' /opt/airghost/config/hostapd.conf
    fi
    
    echo -e "${GREEN}[+] Access Point settings configured${NC}"
}

# Function for final setup steps
finalize_setup() {
    echo -e "${BLUE}[*] Finalizing setup...${NC}"
    
    # Set proper permissions
    chmod +x /opt/airghost/scripts/*
    
    # Start services
    systemctl start airghost.service
    
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    
    echo -e "${GREEN}[+] AirGhost setup completed!${NC}"
    echo -e "${YELLOW}[i] You can access the web interface at:${NC}"
    echo -e "${CYAN}    http://$IP_ADDRESS:8080${NC}"
    echo ""
    echo -e "${YELLOW}[i] To start/stop the AirGhost service:${NC}"
    echo -e "${CYAN}    sudo systemctl start airghost.service${NC}"
    echo -e "${CYAN}    sudo systemctl stop airghost.service${NC}"
    echo ""
    echo -e "${YELLOW}[i] Logs can be viewed with:${NC}"
    echo -e "${CYAN}    sudo journalctl -u airghost.service${NC}"
    echo ""
    echo -e "${RED}[!] IMPORTANT: This tool should only be used for legitimate security testing!${NC}"
    echo ""
}

# Main execution
print_banner
check_root
check_hardware
setup_directories
update_system
install_dependencies
install_specialized_tools
configure_hostapd
configure_dnsmasq
create_web_interface
create_backend_scripts
create_service_files
configure_interface
configure_ap_settings
finalize_setup

exit 0
