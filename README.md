# AirGhost - WiFi Penetration Testing Platform

![AirGhost Logo](https://img.shields.io/badge/AirGhost-WiFi%20Pen%20Testing-red)
![Platform](https://img.shields.io/badge/Platform-Cross%20Platform-blue)
![Raspberry Pi](https://img.shields.io/badge/Device-Raspberry%20Pi%20%7C%20ESP32%20%7C%20PC-brightgreen)
![Version](https://img.shields.io/badge/Version-2.0.0-orange)

## Overview

AirGhost is a comprehensive WiFi penetration testing platform that runs on multiple platforms including Raspberry Pi, ESP32, macOS, and various Linux distributions. It provides a full-featured web interface to manage and execute various wireless attacks, making WiFi security testing more accessible and efficient.

**Warning**: This tool is intended for legitimate security testing only. Always obtain proper authorization before testing any network. Unauthorized network penetration testing is illegal and unethical.

## Features

- **Intuitive Web Interface**: Control everything from a modern, responsive web UI
- **Multiple Attack Vectors**:
  - Evil Twin Access Point creation
  - Captive Portal phishing attacks
  - WiFi Deauthentication (DoS) attacks
- **Real-time Monitoring**: View attack status, connected clients, and captured credentials
- **Customizable Templates**: Easily create and use custom captive portal templates
- **External Adapter Support**: Compatible with various external wireless adapters
- **Optimized for Low Power**: Designed to run efficiently on the Raspberry Pi Zero W

## Installation

### 1-Click Installation (All Platforms)

Install AirGhost with a single command:

```bash
curl -sSL https://raw.githubusercontent.com/AryanVBW/AirGhost/main/install.sh | bash
```

This command will automatically:
1. Detect your operating system (macOS, Kali, Ubuntu, Arch, etc.)
2. Install all required dependencies
3. Configure the necessary services
4. Set up the web interface
5. Create system services for auto-start

### Manual Installation

Alternatively, you can manually install AirGhost:

```bash
git clone https://github.com/AryanVBW/AirGhost.git
cd AirGhost
chmod +x install.sh
./install.sh
```

> **Note for macOS users**: Do NOT use sudo when running the installation script on macOS.

### Development Setup

For developers who want to modify or contribute to AirGhost, use the development setup script:

```bash
git clone https://github.com/AryanVBW/AirGhost.git
cd AirGhost
chmod +x dev_setup.sh
sudo ./dev_setup.sh
```

This will create a development environment with:
- Python virtual environment
- All necessary dependencies
- Development configuration files
- Git hooks for code quality

For more information, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Requirements

### For Raspberry Pi / PC Installation
- Raspberry Pi (any model) or PC/laptop
- Kali Linux, Ubuntu, Debian, Arch Linux, Fedora, macOS, or other compatible OS
- At least one wireless adapter (built-in or external)
- Internet connection (for initial setup)

### For ESP32 Installation
- ESP32 development board (ESP32-WROOM, ESP32-WROVER, etc.)
- Arduino IDE with ESP32 support
- Required libraries (see ESP32 section below)

## Dependencies

AirGhost relies on the following tools and libraries:
- aircrack-ng suite
- hostapd
- dnsmasq
- Python Flask
- NodeJS/npm (for web interface)
- Various system utilities (iptables, macchanger, etc.)

All dependencies will be automatically installed by the setup script.

## Usage

After installation, you can access the AirGhost web interface at:

```
http://<raspberry-pi-ip>:8080
```

From there, you can:

1. Select the wireless interface to use
2. Choose an attack type (Evil Twin, Captive Portal, Deauth)
3. Configure attack parameters
4. Start/stop attacks and view results

## Advanced Configuration

Advanced users can modify the configuration files in `/opt/airghost/config/`:

- `hostapd.conf`: Access Point settings
- `dnsmasq.conf`: DHCP and DNS settings
- Interface configurations and more

## Captive Portal Templates

AirGhost comes with 40+ pre-configured phishing templates for popular websites. Each template has been modified to work with the captive portal system.

Custom captive portal templates can be added to `/opt/airghost/templates/`. Each template should include:

- `index.html`: The main portal page
- `config.json`: Template configuration and metadata
- Additional assets (CSS, JavaScript, images)

### Template Structure

Each template follows a standard structure:

1. **index.html**: Contains the login form with action set to `/captive/login`
2. **config.json**: Defines the credential fields and redirect URL
3. **JavaScript**: Handles form submission via fetch API to the captive portal

### Available Templates

AirGhost includes templates for popular services like:
- Facebook, Instagram, Twitter, LinkedIn
- Google, Microsoft, Yahoo
- Netflix, Spotify, Steam, PlayStation
- And many more!

## ESP32 Implementation

AirGhost now includes support for ESP32 devices, allowing you to create an ultra-portable WiFi penetration testing platform.

### ESP32 Features

- **Standalone Operation**: Run AirGhost directly on ESP32 without a Raspberry Pi or PC
- **Web Interface**: Control via any browser-enabled device
- **WiFi Attacks**: Perform Evil Twin, Captive Portal, and Deauth attacks
- **Credential Harvesting**: Capture and view credentials from the captive portal

### ESP32 Installation

1. Install the Arduino IDE and ESP32 board support
2. Install required libraries:
   - ESPAsyncWebServer
   - AsyncTCP
   - ArduinoJson
3. Open `/esp32/AirGhost_ESP32.ino` in Arduino IDE
4. Upload the SPIFFS data (web interface files) to your ESP32
5. Upload the sketch to your ESP32

Detailed instructions are available in the [ESP32 README](/esp32/README.md).

## Troubleshooting

Common issues and solutions:

### For Linux/macOS Installation
- **Wireless interface not detected**: Ensure your wireless adapter is compatible with monitor mode
- **Service fails to start**: Check logs with `journalctl -u airghost.service` (Linux) or `cat ~/Library/Application\ Support/AirGhost/logs/error.log` (macOS)
- **Web interface inaccessible**: Verify the service is running with `systemctl status airghost.service` (Linux) or `launchctl list | grep airghost` (macOS)

### For ESP32 Installation
- **Compilation errors**: Make sure all required libraries are installed
- **WiFi scanning not working**: Some ESP32 boards have different WiFi capabilities
- **Deauth attacks not working**: Some countries have firmware that blocks sending deauth frames

## Security Considerations

- Change the default web interface password immediately after setup
- Regularly update your Kali Linux system and AirGhost
- Be aware of legal implications before conducting any penetration tests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

AirGhost is provided for educational and ethical penetration testing purposes only. Users are responsible for complying with applicable laws and regulations. The authors are not responsible for any misuse or damage caused by this tool.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

If you're interested in contributing to AirGhost, please check out our [Development Guide](DEVELOPMENT.md) for information on setting up a development environment and our contribution workflow.

## Acknowledgments

- The Kali Linux team
- Aircrack-ng developers
- The wider security research community
