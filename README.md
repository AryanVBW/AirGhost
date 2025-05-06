# AirGhost - WiFi Penetration Testing Platform

![AirGhost Logo](https://img.shields.io/badge/AirGhost-WiFi%20Pen%20Testing-red)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-blue)
![Raspberry Pi](https://img.shields.io/badge/Device-Raspberry%20Pi%20Zero%20W-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0.0-orange)

## Overview

AirGhost is a comprehensive WiFi penetration testing platform designed specifically for the Raspberry Pi Zero W running Kali Linux. It provides a full-featured web interface to manage and execute various wireless attacks, making WiFi security testing more accessible and efficient.

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

Run the automated setup script to install AirGhost:

```bash
git clone https://github.com/AryanVBW/AirGhost.git
cd AirGhost
chmod +x setup.sh
sudo ./setup.sh
```

The setup script will:
1. Install all required dependencies
2. Configure the necessary services
3. Set up the web interface
4. Create system services for auto-start

## Requirements

- Raspberry Pi Zero W (or any Raspberry Pi model)
- Kali Linux (or other compatible Linux distribution)
- At least one wireless adapter (built-in or external)
- Internet connection (for initial setup)

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

## Troubleshooting

Common issues and solutions:

- **Wireless interface not detected**: Ensure your wireless adapter is compatible with monitor mode
- **Service fails to start**: Check logs with `journalctl -u airghost.service`
- **Web interface inaccessible**: Verify the service is running with `systemctl status airghost.service`

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

## Acknowledgments

- The Kali Linux team
- Aircrack-ng developers
- The wider security research community
