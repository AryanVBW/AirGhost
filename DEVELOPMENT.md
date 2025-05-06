# AirGhost Development Guide

This document provides guidelines and information for developers who want to contribute to or modify the AirGhost project.

## Development Environment Setup

AirGhost includes a development setup script that configures all necessary dependencies and creates a suitable environment for development on Kali Linux.

### Prerequisites

- Kali Linux (recommended) or any Debian-based Linux distribution
- Root privileges
- Internet connection for downloading dependencies

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/AryanVBW/AirGhost.git
   cd AirGhost
   ```

2. Run the development setup script:
   ```bash
   sudo ./dev_setup.sh
   ```

   This script will:
   - Install system dependencies (aircrack-ng, hostapd, dnsmasq, etc.)
   - Create a Python virtual environment
   - Install Python dependencies
   - Set up development configurations
   - Create necessary directories and default config files
   - Configure Git hooks for development

3. Start the development server:
   ```bash
   ./dev_start.sh
   ```

## Project Structure

```
AirGhost/
├── app.py                  # Main application entry point
├── config/                 # Configuration files
│   ├── dnsmasq.conf        # DNS and DHCP configuration
│   └── hostapd.conf        # Access point configuration
├── data/                   # Data storage directory
├── logs/                   # Log files
├── scripts/                # Python scripts for various functions
│   ├── network_utils.py    # Network utility functions
│   ├── attack.py           # Attack implementations
│   └── server.py           # Web server implementation
├── templates/              # Phishing templates
│   ├── default/            # Default template
│   ├── facebook/           # Facebook template
│   └── ...                 # Other templates
├── web/                    # Web interface files
│   ├── static/             # Static assets (CSS, JS, images)
│   └── templates/          # Web interface HTML templates
├── requirements.txt        # Python dependencies
├── setup.sh                # Production setup script
└── dev_setup.sh            # Development setup script
```

## Development Workflow

1. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Make your changes** to the codebase.

3. **Test your changes**:
   - For backend changes: Run the development server with `./dev_start.sh`
   - For template changes: Test with the captive portal functionality

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```
   The pre-commit hook will run linting checks before allowing the commit.

5. **Push your changes** to your fork or branch.

## Adding New Templates

To add a new phishing template:

1. Create a new directory in the `templates/` folder with your template name.

2. Add the following files:
   - `index.html`: The main portal page with the login form
   - `config.json`: Configuration file with credential fields and redirect URL

3. Ensure the form in `index.html` has:
   - Action attribute set to `/captive/login`
   - JavaScript to handle form submission via fetch API

4. The `config.json` should follow this format:
   ```json
   {
     "credentials": [
       {"name": "username", "type": "text"},
       {"name": "password", "type": "password"}
     ],
     "redirect": "https://www.google.com/"
   }
   ```

5. Test your template with the development server.

## Modifying the Web Interface

The web interface files are located in the `web/` directory:

- `web/templates/`: HTML templates for the web interface
- `web/static/`: Static assets (CSS, JavaScript, images)

After making changes to the web interface, restart the development server to see the changes.

## Debugging

- Check the logs in the `logs/` directory for error messages.
- Use the Flask debug mode (enabled by default in development) for detailed error messages.
- For network-related issues, use tools like `tcpdump` or Wireshark to analyze traffic.

## Common Issues and Solutions

### Wireless Interface Not Detected

- Ensure your wireless adapter supports monitor mode.
- Check if the interface is blocked by rfkill: `rfkill list`
- Unblock the interface if needed: `rfkill unblock all`

### Service Fails to Start

- Check logs: `journalctl -u airghost.service`
- Verify that all dependencies are installed.
- Check if another service is using the same port.

### Web Interface Inaccessible

- Verify the service is running: `systemctl status airghost.service`
- Check if the correct IP and port are being used.
- Check firewall settings: `iptables -L`

## Contributing Guidelines

1. Follow the coding style of the existing codebase.
2. Write clear, concise commit messages.
3. Document your changes in the code and update relevant documentation.
4. Test your changes thoroughly before submitting a pull request.
5. For major changes, open an issue first to discuss the proposed changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
