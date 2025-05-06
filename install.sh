#!/bin/bash
#
# AirGhost - Cross-Platform WiFi Penetration Testing Platform Setup
# Auto-detects OS and installs appropriate dependencies
#

# Terminal colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
INSTALL_DIR=""
OS_TYPE=""
OS_VERSION=""
CURRENT_DIR=$(pwd)

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
    echo -e "${YELLOW}Cross-Platform WiFi Penetration Testing Platform${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
    echo ""
}

# Function to detect OS and hardware capabilities
detect_os() {
    echo -e "${BLUE}[*] Detecting operating system and hardware capabilities...${NC}"
    
    # Detect OS type
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        OS_VERSION=$(sw_vers -productVersion)
        OS_NAME="macOS $OS_VERSION"
        PACKAGE_MANAGER="brew"
        echo -e "${GREEN}[+] Detected macOS $OS_VERSION${NC}"
        
        # Check macOS version compatibility
        MACOS_MAJOR_VERSION=$(echo "$OS_VERSION" | cut -d. -f1)
        if [[ $MACOS_MAJOR_VERSION -lt 11 ]]; then
            echo -e "${YELLOW}[!] Warning: AirGhost works best with macOS Big Sur (11.0) or newer${NC}"
            echo -e "${YELLOW}[!] Some features may not work correctly on your version${NC}"
        fi
    elif [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS_TYPE=$(echo "$ID" | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$VERSION_ID
        OS_NAME="$NAME $VERSION"
        echo -e "${GREEN}[+] Detected $NAME $VERSION${NC}"
        
        # Determine package manager and compatibility
        if [[ "$OS_TYPE" == "kali" ]]; then
            echo -e "${GREEN}[+] Kali Linux detected - optimal for AirGhost${NC}"
            PACKAGE_MANAGER="apt"
            COMPATIBILITY="full"
        elif [[ "$OS_TYPE" == "ubuntu" || "$OS_TYPE" == "debian" || "$OS_TYPE" == "linuxmint" || "$OS_TYPE" == "pop" ]]; then
            echo -e "${GREEN}[+] Debian-based system detected${NC}"
            PACKAGE_MANAGER="apt"
            COMPATIBILITY="full"
        elif [[ "$OS_TYPE" == "arch" || "$OS_TYPE" == "manjaro" || "$OS_TYPE" == "endeavouros" ]]; then
            echo -e "${GREEN}[+] Arch-based system detected${NC}"
            PACKAGE_MANAGER="pacman"
            COMPATIBILITY="full"
        elif [[ "$OS_TYPE" == "fedora" ]]; then
            echo -e "${GREEN}[+] Fedora detected${NC}"
            PACKAGE_MANAGER="dnf"
            COMPATIBILITY="partial"
        elif [[ "$OS_TYPE" == "centos" || "$OS_TYPE" == "rhel" || "$OS_TYPE" == "rocky" || "$OS_TYPE" == "alma" ]]; then
            echo -e "${GREEN}[+] Red Hat-based system detected${NC}"
            PACKAGE_MANAGER="dnf"
            COMPATIBILITY="partial"
        elif [[ "$OS_TYPE" == "opensuse" || "$OS_TYPE" == "sles" ]]; then
            echo -e "${GREEN}[+] OpenSUSE-based system detected${NC}"
            PACKAGE_MANAGER="zypper"
            COMPATIBILITY="partial"
        else
            echo -e "${YELLOW}[!] Unsupported Linux distribution: $OS_TYPE${NC}"
            echo -e "${YELLOW}[!] The installation might not work correctly${NC}"
            PACKAGE_MANAGER="unknown"
            COMPATIBILITY="limited"
            read -p "Continue anyway? (y/n): " choice
            if [[ ! "$choice" =~ ^[Yy]$ ]]; then
                echo -e "${RED}Setup aborted.${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${RED}[ERROR] Unsupported operating system${NC}"
        exit 1
    fi
    
    # Detect CPU architecture
    ARCH=$(uname -m)
    echo -e "${GREEN}[+] Architecture: $ARCH${NC}"
    
    # Check for virtualization
    if [[ -f /proc/cpuinfo ]] && grep -q "hypervisor" /proc/cpuinfo; then
        echo -e "${YELLOW}[!] Running in a virtual machine - some WiFi features may be limited${NC}"
        IS_VM=true
    elif [[ "$OS_TYPE" == "macos" ]] && sysctl -n machdep.cpu.features | grep -q "VMM"; then
        echo -e "${YELLOW}[!] Running in a virtual machine - some WiFi features may be limited${NC}"
        IS_VM=true
    else
        IS_VM=false
    fi
    
    # Save OS information to config file
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_DIR/system_info.json" << EOF
{
    "os_type": "$OS_TYPE",
    "os_version": "$OS_VERSION",
    "os_name": "$OS_NAME",
    "architecture": "$ARCH",
    "package_manager": "$PACKAGE_MANAGER",
    "compatibility": "$COMPATIBILITY",
    "is_vm": $IS_VM,
    "install_date": "$(date +"%Y-%m-%d %H:%M:%S")"
}
EOF
}

# Function to check if the script is running as root (for Linux)
check_root() {
    # Skip root check on macOS, as homebrew shouldn't run as root
    if [[ "$OS_TYPE" == "macos" ]]; then
        if [ "$EUID" -eq 0 ]; then 
            echo -e "${RED}[ERROR] On macOS, this script should NOT be run as root${NC}"
            echo "Please run without sudo"
            exit 1
        fi
        return
    fi
    
    # For Linux systems, we need root
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}[ERROR] This script must be run as root on Linux systems${NC}"
        echo "Please run with: sudo $0"
        exit 1
    fi
}

# Function to check and create directories
setup_directories() {
    echo -e "${BLUE}[*] Setting up directory structure...${NC}"
    
    if [[ "$OS_TYPE" == "macos" ]]; then
        # macOS installation directory
        INSTALL_DIR="$HOME/Library/Application Support/AirGhost"
        mkdir -p "$INSTALL_DIR"
        mkdir -p "$INSTALL_DIR/web"
        mkdir -p "$INSTALL_DIR/templates"
        mkdir -p "$INSTALL_DIR/logs"
        mkdir -p "$INSTALL_DIR/config"
        mkdir -p "$INSTALL_DIR/scripts"
    else
        # Linux installation directory
        INSTALL_DIR="/opt/airghost"
        mkdir -p "$INSTALL_DIR"
        mkdir -p "$INSTALL_DIR/web"
        mkdir -p "$INSTALL_DIR/templates"
        mkdir -p "$INSTALL_DIR/logs"
        mkdir -p "$INSTALL_DIR/config"
        mkdir -p "$INSTALL_DIR/scripts"
    fi
    
    echo -e "${GREEN}[+] Directory structure created at $INSTALL_DIR${NC}"
}

# Function to install dependencies on macOS
install_macos_dependencies() {
    echo -e "${BLUE}[*] Installing dependencies for macOS...${NC}"
    
    # Create a log file for installation
    INSTALL_LOG="$INSTALL_DIR/logs/install_$(date +"%Y%m%d_%H%M%S").log"
    mkdir -p "$INSTALL_DIR/logs"
    touch "$INSTALL_LOG"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}[!] Homebrew not found. Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >> "$INSTALL_LOG" 2>&1
        
        # Add Homebrew to PATH
        if [[ -f /opt/homebrew/bin/brew ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zshrc"
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.bash_profile"
        elif [[ -f /usr/local/bin/brew ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$HOME/.zshrc"
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$HOME/.bash_profile"
        else
            echo -e "${RED}[ERROR] Failed to install Homebrew${NC}"
            echo -e "${YELLOW}[!] Please check the installation log: $INSTALL_LOG${NC}"
            exit 1
        fi
    fi
    
    # Install required packages
    echo -e "${BLUE}[*] Installing required packages...${NC}"
    brew update >> "$INSTALL_LOG" 2>&1
    
    # Install Python and pip
    echo -e "${BLUE}[*] Installing Python...${NC}"
    brew install python3 >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${RED}[ERROR] Failed to install Python${NC}"
        echo -e "${YELLOW}[!] Please check the installation log: $INSTALL_LOG${NC}"
    }
    
    # Install aircrack-ng and other wireless tools with progress indicators
    echo -e "${BLUE}[*] Installing wireless tools...${NC}"
    echo -e "${CYAN}    - Installing aircrack-ng...${NC}"
    brew install aircrack-ng >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install aircrack-ng${NC}"
        echo -e "${YELLOW}[!] Some WiFi penetration features will be limited${NC}"
        MISSING_DEPS="aircrack-ng"
    }
    
    echo -e "${CYAN}    - Installing wireshark...${NC}"
    brew install wireshark >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install wireshark${NC}"
        echo -e "${YELLOW}[!] Packet capture features will be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS wireshark"
    }
    
    # Install alternative tools for macOS compatibility
    echo -e "${CYAN}    - Installing airport utility...${NC}"
    # Create a symbolic link to the airport utility
    if [[ -f /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport ]]; then
        mkdir -p "$INSTALL_DIR/bin"
        ln -sf /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport "$INSTALL_DIR/bin/airport"
        echo -e "${GREEN}[+] Airport utility linked${NC}"
    else
        echo -e "${YELLOW}[!] Warning: Airport utility not found${NC}"
        echo -e "${YELLOW}[!] Some WiFi scanning features will be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS airport"
    fi
    
    # Install web server components
    echo -e "${BLUE}[*] Installing web server components...${NC}"
    echo -e "${CYAN}    - Installing Node.js...${NC}"
    brew install node >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${RED}[ERROR] Failed to install Node.js${NC}"
        echo -e "${YELLOW}[!] Please check the installation log: $INSTALL_LOG${NC}"
        MISSING_DEPS="$MISSING_DEPS nodejs"
    }
    
    echo -e "${CYAN}    - Installing npm...${NC}"
    brew install npm >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install npm${NC}"
        echo -e "${YELLOW}[!] Will use Node.js built-in npm${NC}"
    }
    
    # Install Python packages
    echo -e "${BLUE}[*] Installing Python packages...${NC}"
    pip3 install flask flask-socketio psutil netifaces >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${RED}[ERROR] Failed to install Python packages${NC}"
        echo -e "${YELLOW}[!] Please check the installation log: $INSTALL_LOG${NC}"
        MISSING_DEPS="$MISSING_DEPS python-packages"
    }
    
    # Check for missing dependencies
    if [[ -n "$MISSING_DEPS" ]]; then
        echo -e "${YELLOW}[!] Some dependencies could not be installed: $MISSING_DEPS${NC}"
        echo -e "${YELLOW}[!] AirGhost will run with limited functionality${NC}"
        # Save missing dependencies to config
        echo "$MISSING_DEPS" > "$CONFIG_DIR/missing_dependencies.txt"
    else
        echo -e "${GREEN}[+] All macOS dependencies installed successfully${NC}"
    fi
    
    # Create macOS-specific configuration
    create_macos_config
}

# Function to create macOS-specific configuration
create_macos_config() {
    echo -e "${BLUE}[*] Creating macOS-specific configuration...${NC}"
    
    # Create config directory if it doesn't exist
    mkdir -p "$CONFIG_DIR"
    
    # Create macOS compatibility configuration
    cat > "$CONFIG_DIR/macos_compat.json" << EOF
{
    "wifi_tools": {
        "airport": {
            "path": "$INSTALL_DIR/bin/airport",
            "available": $(if [[ -f "$INSTALL_DIR/bin/airport" ]]; then echo "true"; else echo "false"; fi)
        },
        "aircrack-ng": {
            "available": $(if command -v aircrack-ng &> /dev/null; then echo "true"; else echo "false"; fi)
        },
        "wireshark": {
            "available": $(if command -v wireshark &> /dev/null; then echo "true"; else echo "false"; fi)
        }
    },
    "monitor_mode": {
        "supported": $(if [[ -f "$INSTALL_DIR/bin/airport" ]]; then echo "true"; else echo "false"; fi),
        "instructions": "To enable monitor mode on macOS, use the airport utility with: $INSTALL_DIR/bin/airport <interface> sniff <channel>"
    },
    "packet_injection": {
        "supported": false,
        "instructions": "Packet injection is not natively supported on macOS. Consider using an external USB WiFi adapter with compatible drivers."
    },
    "external_adapters": {
        "instructions": "For full functionality on macOS, use an external WiFi adapter with the appropriate kext drivers installed."
    }
}
EOF
    
    echo -e "${GREEN}[+] macOS configuration created${NC}"
}

# Function to install dependencies on Debian-based systems (Ubuntu, Kali)
install_debian_dependencies() {
    echo -e "${BLUE}[*] Installing dependencies for Debian-based system...${NC}"
    
    # Create a log file for installation
    INSTALL_LOG="$INSTALL_DIR/logs/install_$(date +"%Y%m%d_%H%M%S").log"
    mkdir -p "$INSTALL_DIR/logs"
    touch "$INSTALL_LOG"
    
    # Update package lists with progress indicator
    echo -e "${BLUE}[*] Updating package lists...${NC}"
    apt update >> "$INSTALL_LOG" 2>&1
    
    # Install packages with progress indicators
    echo -e "${BLUE}[*] Installing required packages...${NC}"
    
    # Define package groups for better error handling
    PYTHON_PKGS="python3 python3-pip python3-flask python3-flask-socketio python3-dev"
    NETWORK_PKGS="hostapd dnsmasq isc-dhcp-server"
    WIFI_PKGS="aircrack-ng mdk4 mdk3 rfkill iw wireless-tools macchanger"
    WEB_PKGS="apache2 php php-cgi libapache2-mod-php"
    UTIL_PKGS="build-essential libssl-dev libffi-dev git curl wget unzip net-tools iptables nftables"
    NODE_PKGS="nodejs npm"
    
    # Install Python packages
    echo -e "${CYAN}    - Installing Python packages...${NC}"
    apt install -y $PYTHON_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${RED}[ERROR] Failed to install Python packages${NC}"
        echo -e "${YELLOW}[!] Please check the installation log: $INSTALL_LOG${NC}"
        MISSING_DEPS="python-packages"
    }
    
    # Install networking packages
    echo -e "${CYAN}    - Installing networking packages...${NC}"
    apt install -y $NETWORK_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some networking packages${NC}"
        echo -e "${YELLOW}[!] AP functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS networking-packages"
    }
    
    # Install WiFi packages
    echo -e "${CYAN}    - Installing WiFi tools...${NC}"
    apt install -y $WIFI_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some WiFi tools${NC}"
        echo -e "${YELLOW}[!] WiFi penetration testing features may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS wifi-tools"
    }
    
    # Install web server packages
    echo -e "${CYAN}    - Installing web server components...${NC}"
    apt install -y $WEB_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install web server components${NC}"
        echo -e "${YELLOW}[!] Captive portal functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS web-server"
    }
    
    # Install utility packages
    echo -e "${CYAN}    - Installing utility packages...${NC}"
    apt install -y $UTIL_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some utility packages${NC}"
        MISSING_DEPS="$MISSING_DEPS utilities"
    }
    
    # Install Node.js packages
    echo -e "${CYAN}    - Installing Node.js...${NC}"
    apt install -y $NODE_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install Node.js${NC}"
        echo -e "${YELLOW}[!] Web interface functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS nodejs"
    }
    
    # Install Python packages via pip
    echo -e "${CYAN}    - Installing Python modules...${NC}"
    pip3 install psutil netifaces >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install Python modules${NC}"
        MISSING_DEPS="$MISSING_DEPS python-modules"
    }
    
    # Check for missing dependencies
    if [[ -n "$MISSING_DEPS" ]]; then
        echo -e "${YELLOW}[!] Some dependencies could not be installed: $MISSING_DEPS${NC}"
        echo -e "${YELLOW}[!] AirGhost will run with limited functionality${NC}"
        # Save missing dependencies to config
        echo "$MISSING_DEPS" > "$CONFIG_DIR/missing_dependencies.txt"
    else
        echo -e "${GREEN}[+] All Debian-based dependencies installed successfully${NC}"
    fi
    
    # Create Linux-specific configuration
    create_linux_config
}

# Function to create Linux-specific configuration
create_linux_config() {
    echo -e "${BLUE}[*] Creating Linux-specific configuration...${NC}"
    
    # Create config directory if it doesn't exist
    mkdir -p "$CONFIG_DIR"
    
    # Detect available wireless interfaces
    WIRELESS_INTERFACES=($(ls -1 /sys/class/net | grep -E "^(wlan|wlp|wlx)"))
    WIRELESS_INFO=
    for iface in "${WIRELESS_INTERFACES[@]}"; do
        # Get driver information
        DRIVER=$(readlink /sys/class/net/$iface/device/driver 2>/dev/null | awk -F'/' '{print $NF}')
        # Check if monitor mode is supported
        MONITOR_SUPPORTED="false"
        if command -v iw &> /dev/null; then
            if iw list | grep -q "monitor"; then
                MONITOR_SUPPORTED="true"
            fi
        fi
        # Add to wireless info JSON
        if [[ -n "$WIRELESS_INFO" ]]; then
            WIRELESS_INFO="$WIRELESS_INFO,"
        fi
        WIRELESS_INFO="$WIRELESS_INFO
        \"$iface\": {
            \"driver\": \"$DRIVER\",
            \"monitor_supported\": $MONITOR_SUPPORTED
        }"
    done
    
    # Check for airmon-ng
    AIRMON_AVAILABLE="false"
    if command -v airmon-ng &> /dev/null; then
        AIRMON_AVAILABLE="true"
    fi
    
    # Check for packet injection support
    PACKET_INJECTION="false"
    if command -v aireplay-ng &> /dev/null; then
        PACKET_INJECTION="true"
    fi
    
    # Create Linux compatibility configuration
    cat > "$CONFIG_DIR/linux_compat.json" << EOF
{
    "wifi_interfaces": {$WIRELESS_INFO
    },
    "wifi_tools": {
        "airmon-ng": {
            "available": $AIRMON_AVAILABLE
        },
        "aircrack-ng": {
            "available": $(if command -v aircrack-ng &> /dev/null; then echo "true"; else echo "false"; fi)
        },
        "wireshark": {
            "available": $(if command -v wireshark &> /dev/null; then echo "true"; else echo "false"; fi)
        }
    },
    "monitor_mode": {
        "supported": $(if [[ "$AIRMON_AVAILABLE" == "true" ]]; then echo "true"; else echo "false"; fi),
        "instructions": "To enable monitor mode, use: airmon-ng start <interface>"
    },
    "packet_injection": {
        "supported": $PACKET_INJECTION,
        "instructions": "To test packet injection: aireplay-ng --test <interface>"
    }
}
EOF
    
    echo -e "${GREEN}[+] Linux configuration created${NC}"
}

# Function to install dependencies on Arch-based systems
install_arch_dependencies() {
    echo -e "${BLUE}[*] Installing dependencies for Arch-based system...${NC}"
    
    # Create a log file for installation
    INSTALL_LOG="$INSTALL_DIR/logs/install_$(date +"%Y%m%d_%H%M%S").log"
    mkdir -p "$INSTALL_DIR/logs"
    touch "$INSTALL_LOG"
    
    # Update package database with progress indicator
    echo -e "${BLUE}[*] Updating package database...${NC}"
    pacman -Sy >> "$INSTALL_LOG" 2>&1
    
    # Define package groups for better error handling
    PYTHON_PKGS="python python-pip python-flask python-flask-socketio"
    NETWORK_PKGS="hostapd dnsmasq dhcp"
    WIFI_PKGS="aircrack-ng iw wireless_tools macchanger"
    WEB_PKGS="apache php php-apache"
    UTIL_PKGS="base-devel openssl git curl wget unzip net-tools iptables nftables"
    NODE_PKGS="nodejs npm"
    
    # Install packages with progress indicators
    echo -e "${BLUE}[*] Installing required packages...${NC}"
    
    # Install Python packages
    echo -e "${CYAN}    - Installing Python packages...${NC}"
    pacman -S --noconfirm $PYTHON_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${RED}[ERROR] Failed to install Python packages${NC}"
        echo -e "${YELLOW}[!] Please check the installation log: $INSTALL_LOG${NC}"
        MISSING_DEPS="python-packages"
    }
    
    # Install networking packages
    echo -e "${CYAN}    - Installing networking packages...${NC}"
    pacman -S --noconfirm $NETWORK_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some networking packages${NC}"
        echo -e "${YELLOW}[!] AP functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS networking-packages"
    }
    
    # Install WiFi packages
    echo -e "${CYAN}    - Installing WiFi tools...${NC}"
    pacman -S --noconfirm $WIFI_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some WiFi tools${NC}"
        echo -e "${YELLOW}[!] WiFi penetration testing features may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS wifi-tools"
    }
    
    # Install web server packages
    echo -e "${CYAN}    - Installing web server components...${NC}"
    pacman -S --noconfirm $WEB_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install web server components${NC}"
        echo -e "${YELLOW}[!] Captive portal functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS web-server"
    }
    
    # Install utility packages
    echo -e "${CYAN}    - Installing utility packages...${NC}"
    pacman -S --noconfirm $UTIL_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some utility packages${NC}"
        MISSING_DEPS="$MISSING_DEPS utilities"
    }
    
    # Install Node.js packages
    echo -e "${CYAN}    - Installing Node.js...${NC}"
    pacman -S --noconfirm $NODE_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install Node.js${NC}"
        echo -e "${YELLOW}[!] Web interface functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS nodejs"
    }
    
    # Install Python packages via pip
    echo -e "${CYAN}    - Installing Python modules...${NC}"
    pip install psutil netifaces >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install Python modules${NC}"
        MISSING_DEPS="$MISSING_DEPS python-modules"
    }
    
    # Check for missing dependencies
    if [[ -n "$MISSING_DEPS" ]]; then
        echo -e "${YELLOW}[!] Some dependencies could not be installed: $MISSING_DEPS${NC}"
        echo -e "${YELLOW}[!] AirGhost will run with limited functionality${NC}"
        # Save missing dependencies to config
        echo "$MISSING_DEPS" > "$CONFIG_DIR/missing_dependencies.txt"
    else
        echo -e "${GREEN}[+] All Arch-based dependencies installed successfully${NC}"
    fi
    
    # Create Linux-specific configuration
    create_linux_config
}

# Function to install dependencies on Red Hat-based systems
install_redhat_dependencies() {
    echo -e "${BLUE}[*] Installing dependencies for Red Hat-based system...${NC}"
    
    # Create a log file for installation
    INSTALL_LOG="$INSTALL_DIR/logs/install_$(date +"%Y%m%d_%H%M%S").log"
    mkdir -p "$INSTALL_DIR/logs"
    touch "$INSTALL_LOG"
    
    # Install EPEL repository if not already installed
    if [[ "$OS_TYPE" == "centos" || "$OS_TYPE" == "rhel" ]]; then
        echo -e "${BLUE}[*] Installing EPEL repository...${NC}"
        dnf install -y epel-release >> "$INSTALL_LOG" 2>&1 || {
            echo -e "${YELLOW}[!] Warning: Failed to install EPEL repository${NC}"
            echo -e "${YELLOW}[!] Some packages may not be available${NC}"
        }
    fi
    
    # Update package lists with progress indicator
    echo -e "${BLUE}[*] Updating package lists...${NC}"
    dnf check-update >> "$INSTALL_LOG" 2>&1
    
    # Define package groups for better error handling
    PYTHON_PKGS="python3 python3-pip python3-flask"
    NETWORK_PKGS="hostapd dnsmasq dhcp-server"
    WIFI_PKGS="aircrack-ng iw wireless-tools macchanger"
    WEB_PKGS="httpd php"
    UTIL_PKGS="openssl-devel git curl wget unzip net-tools iptables"
    NODE_PKGS="nodejs npm"
    
    # Install packages with progress indicators
    echo -e "${BLUE}[*] Installing required packages...${NC}"
    
    # Install Python packages
    echo -e "${CYAN}    - Installing Python packages...${NC}"
    dnf install -y $PYTHON_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${RED}[ERROR] Failed to install Python packages${NC}"
        echo -e "${YELLOW}[!] Please check the installation log: $INSTALL_LOG${NC}"
        MISSING_DEPS="python-packages"
    }
    
    # Install networking packages
    echo -e "${CYAN}    - Installing networking packages...${NC}"
    dnf install -y $NETWORK_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some networking packages${NC}"
        echo -e "${YELLOW}[!] AP functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS networking-packages"
    }
    
    # Install WiFi packages
    echo -e "${CYAN}    - Installing WiFi tools...${NC}"
    dnf install -y $WIFI_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some WiFi tools${NC}"
        echo -e "${YELLOW}[!] WiFi penetration testing features may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS wifi-tools"
    }
    
    # Install web server packages
    echo -e "${CYAN}    - Installing web server components...${NC}"
    dnf install -y $WEB_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install web server components${NC}"
        echo -e "${YELLOW}[!] Captive portal functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS web-server"
    }
    
    # Install utility packages
    echo -e "${CYAN}    - Installing utility packages...${NC}"
    dnf install -y $UTIL_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install some utility packages${NC}"
        MISSING_DEPS="$MISSING_DEPS utilities"
    }
    
    # Install Node.js packages
    echo -e "${CYAN}    - Installing Node.js...${NC}"
    dnf install -y $NODE_PKGS >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install Node.js${NC}"
        echo -e "${YELLOW}[!] Web interface functionality may be limited${NC}"
        MISSING_DEPS="$MISSING_DEPS nodejs"
    }
    
    # Install Python packages via pip
    echo -e "${CYAN}    - Installing Python modules...${NC}"
    pip3 install flask-socketio psutil netifaces >> "$INSTALL_LOG" 2>&1 || {
        echo -e "${YELLOW}[!] Warning: Failed to install Python modules${NC}"
        MISSING_DEPS="$MISSING_DEPS python-modules"
    }
    
    # Check for missing dependencies
    if [[ -n "$MISSING_DEPS" ]]; then
        echo -e "${YELLOW}[!] Some dependencies could not be installed: $MISSING_DEPS${NC}"
        echo -e "${YELLOW}[!] AirGhost will run with limited functionality${NC}"
        # Save missing dependencies to config
        echo "$MISSING_DEPS" > "$CONFIG_DIR/missing_dependencies.txt"
    else
        echo -e "${GREEN}[+] All Red Hat-based dependencies installed successfully${NC}"
    fi
    
    # Create Linux-specific configuration
    create_linux_config
}

# Function to install dependencies based on detected OS
install_dependencies() {
    case "$OS_TYPE" in
        "macos")
            install_macos_dependencies
            ;;
        "kali"|"ubuntu"|"debian")
            install_debian_dependencies
            ;;
        "arch"|"manjaro")
            install_arch_dependencies
            ;;
        "fedora"|"centos"|"rhel")
            install_redhat_dependencies
            ;;
        *)
            echo -e "${YELLOW}[!] Unsupported OS for automatic dependency installation${NC}"
            echo -e "${YELLOW}[!] Please install the required dependencies manually${NC}"
            ;;
    esac
}

# Function to copy source files to installation directory
copy_source_files() {
    echo -e "${BLUE}[*] Copying source files to installation directory...${NC}"
    
    # Create necessary directories
    mkdir -p "$INSTALL_DIR/scripts"
    mkdir -p "$INSTALL_DIR/web"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/config"
    
    # Copy files
    cp -r "$CURRENT_DIR/scripts"/* "$INSTALL_DIR/scripts/"
    cp -r "$CURRENT_DIR/web"/* "$INSTALL_DIR/web/"
    
    # Set permissions
    chmod +x "$INSTALL_DIR/scripts"/*.py
    
    # Install Python dependencies
    echo -e "${BLUE}[*] Installing Python dependencies...${NC}"
    if [[ "$OS_TYPE" == "macos" ]]; then
        pip3 install -r "$CURRENT_DIR/requirements.txt"
    else
        pip3 install -r "$CURRENT_DIR/requirements.txt"
    fi
    
    echo -e "${GREEN}[+] Source files copied and dependencies installed${NC}"
}

# Function to create service files (for Linux)
create_service_files() {
    # Skip for macOS
    if [[ "$OS_TYPE" == "macos" ]]; then
        return
    fi
    
    echo -e "${BLUE}[*] Creating service files...${NC}"
    
    # Create main service file
    cat > /etc/systemd/system/airghost.service << EOF
[Unit]
Description=AirGhost WiFi Penetration Testing Platform
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/scripts/server.py
WorkingDirectory=$INSTALL_DIR
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

    # Create API service file
    cat > /etc/systemd/system/airghost-api.service << EOF
[Unit]
Description=AirGhost API Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/scripts/api_server.py
WorkingDirectory=$INSTALL_DIR
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable the services to start on boot
    systemctl enable airghost.service
    systemctl enable airghost-api.service
    
    echo -e "${GREEN}[+] Service files created${NC}"
}

# Function to create macOS launch agent
create_macos_launch_agent() {
    echo -e "${BLUE}[*] Creating macOS launch agent...${NC}"
    
    # Create LaunchAgent directory if it doesn't exist
    mkdir -p "$HOME/Library/LaunchAgents"
    
    # Create plist file for main server
    cat > "$HOME/Library/LaunchAgents/com.airghost.server.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.airghost.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$INSTALL_DIR/scripts/server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/logs/error.log</string>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/logs/output.log</string>
</dict>
</plist>
EOF
    
    # Create plist file for API server
    cat > "$HOME/Library/LaunchAgents/com.airghost.api.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.airghost.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$INSTALL_DIR/scripts/api_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/logs/api_error.log</string>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/logs/api_output.log</string>
</dict>
</plist>
EOF
    
    # Load the launch agents
    launchctl load "$HOME/Library/LaunchAgents/com.airghost.server.plist"
    launchctl load "$HOME/Library/LaunchAgents/com.airghost.api.plist"
    
    echo -e "${GREEN}[+] macOS launch agents created${NC}"
}

# Function to create a desktop shortcut (for Linux)
create_desktop_shortcut() {
    # Skip for macOS
    if [[ "$OS_TYPE" == "macos" ]]; then
        return
    fi
    
    echo -e "${BLUE}[*] Creating desktop shortcut...${NC}"
    
    # Create desktop file
    cat > /usr/share/applications/airghost.desktop << EOF
[Desktop Entry]
Name=AirGhost
Comment=WiFi Penetration Testing Platform
Exec=xdg-open http://localhost:8080
Icon=$INSTALL_DIR/web/static/img/icon.png
Terminal=false
Type=Application
Categories=Security;Network;
EOF
    
    echo -e "${GREEN}[+] Desktop shortcut created${NC}"
}

# Function to finalize the setup
finalize_setup() {
    echo -e "${BLUE}[*] Finalizing setup...${NC}"
    
    # Generate platform compatibility information
    echo -e "${BLUE}[*] Generating platform compatibility information...${NC}"
    python3 "$INSTALL_DIR/scripts/platform_utils.py"
    
    # Start the service on Linux
    if [[ "$OS_TYPE" != "macos" ]]; then
        systemctl start airghost.service
    fi
    
    # Get IP address
    if [[ "$OS_TYPE" == "macos" ]]; then
        IP_ADDRESS=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
    else
        IP_ADDRESS=$(hostname -I | awk '{print $1}')
    fi
    
    echo -e "${GREEN}[+] AirGhost setup completed!${NC}"
    echo -e "${YELLOW}[i] You can access the web interface at:${NC}"
    echo -e "${CYAN}    http://$IP_ADDRESS:8080${NC}"
    echo -e "${YELLOW}[i] To check platform compatibility:${NC}"
    echo -e "${CYAN}    http://$IP_ADDRESS:8080/platform.html${NC}"
    echo ""
    
    if [[ "$OS_TYPE" != "macos" ]]; then
        echo -e "${YELLOW}[i] To start/stop the AirGhost service:${NC}"
        echo -e "${CYAN}    sudo systemctl start airghost.service${NC}"
        echo -e "${CYAN}    sudo systemctl stop airghost.service${NC}"
        echo -e "${YELLOW}[i] To run the API server manually:${NC}"
        echo -e "${CYAN}    sudo python3 $INSTALL_DIR/scripts/api_server.py${NC}"
    else
        echo -e "${YELLOW}[i] To start/stop the AirGhost service:${NC}"
        echo -e "${CYAN}    launchctl load ~/Library/LaunchAgents/com.airghost.server.plist${NC}"
        echo -e "${CYAN}    launchctl unload ~/Library/LaunchAgents/com.airghost.server.plist${NC}"
        echo -e "${YELLOW}[i] To run the API server manually:${NC}"
        echo -e "${CYAN}    python3 $INSTALL_DIR/scripts/api_server.py${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}[i] Platform compatibility:${NC}"
    if [[ "$OS_TYPE" == "macos" ]]; then
        echo -e "${CYAN}    - macOS: Partial compatibility${NC}"
        echo -e "${CYAN}    - Monitor mode: Limited support via airport utility${NC}"
        echo -e "${CYAN}    - Packet injection: Requires external WiFi adapter${NC}"
    elif [[ "$OS_TYPE" == "kali" || "$OS_TYPE" == "ubuntu" || "$OS_TYPE" == "debian" ]]; then
        echo -e "${CYAN}    - Linux: Full compatibility${NC}"
        echo -e "${CYAN}    - Monitor mode: Supported with compatible WiFi adapters${NC}"
        echo -e "${CYAN}    - Packet injection: Supported with compatible WiFi adapters${NC}"
    elif [[ "$OS_TYPE" == "arch" || "$OS_TYPE" == "manjaro" ]]; then
        echo -e "${CYAN}    - Arch Linux: Full compatibility${NC}"
        echo -e "${CYAN}    - Monitor mode: Supported with compatible WiFi adapters${NC}"
        echo -e "${CYAN}    - Packet injection: Supported with compatible WiFi adapters${NC}"
    else
        echo -e "${CYAN}    - Limited compatibility, some features may not work${NC}"
    fi
    
    echo ""
    echo -e "${RED}[!] IMPORTANT: This tool should only be used for legitimate security testing!${NC}"
    echo ""
}

# Main execution function
main() {
    print_banner
    detect_os
    check_root
    setup_directories
    install_dependencies
    copy_source_files
    configure_hostapd
    configure_dnsmasq
    
    if [[ "$OS_TYPE" == "macos" ]]; then
        create_macos_launch_agent
    else
        create_service_files
        create_desktop_shortcut
    fi
    
    finalize_setup
}

# Execute main function
main
