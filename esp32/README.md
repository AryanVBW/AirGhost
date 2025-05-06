# AirGhost ESP32

A port of the AirGhost WiFi Penetration Testing Platform for ESP32 devices.

## Overview

AirGhost ESP32 brings the powerful WiFi penetration testing capabilities of AirGhost to the ESP32 platform. This allows for an extremely portable and low-cost solution for WiFi security testing.

**Warning**: This tool is intended for legitimate security testing only. Always obtain proper authorization before testing any network. Unauthorized network penetration testing is illegal and unethical.

## Features

- **Web Interface**: Control everything from a responsive web UI
- **Multiple Attack Vectors**:
  - Evil Twin Access Point creation
  - Captive Portal phishing attacks
  - WiFi Deauthentication (DoS) attacks
- **Real-time Monitoring**: View attack status and connected clients
- **Credential Capture**: Capture and view credentials from the captive portal

## Requirements

- ESP32 development board (ESP32-WROOM, ESP32-WROVER, etc.)
- Arduino IDE or PlatformIO
- Required libraries:
  - ESPAsyncWebServer
  - AsyncTCP
  - ArduinoJson (v6.x)
  - SPIFFS file system

## Installation

### 1. Install Required Libraries

In Arduino IDE:
1. Go to Sketch > Include Library > Manage Libraries
2. Search for and install:
   - ESPAsyncWebServer
   - AsyncTCP
   - ArduinoJson

### 2. Install ESP32 Board Support

1. Go to File > Preferences
2. Add this URL to the "Additional Boards Manager URLs" field:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Go to Tools > Board > Boards Manager
4. Search for "esp32" and install "ESP32 by Espressif Systems"

### 3. Upload the SPIFFS Data

1. Install the ESP32 Filesystem Uploader in Arduino IDE
   - Download from: https://github.com/me-no-dev/arduino-esp32fs-plugin
   - Follow installation instructions in the repository
2. Select your ESP32 board and port in Arduino IDE
3. Go to Tools > ESP32 Sketch Data Upload
   - This will upload all files in the "data" folder to the ESP32's SPIFFS

### 4. Upload the Sketch

1. Open `AirGhost_ESP32.ino` in Arduino IDE
2. Select your ESP32 board and port
3. Click Upload

## Usage

1. After uploading the code, the ESP32 will create a WiFi access point named "Free-WiFi"
2. Connect to this network with your device
3. Open a web browser and navigate to `http://192.168.4.1`
4. Use the web interface to:
   - Scan for nearby WiFi networks
   - Create Evil Twin access points
   - Set up captive portals
   - Launch deauthentication attacks
   - View captured credentials

## Troubleshooting

- **ESP32 crashes during attacks**: Ensure you're using a stable power supply
- **Web interface not accessible**: Check that you're connected to the ESP32's WiFi network
- **Deauth attacks not working**: Some countries have firmware that blocks sending deauth frames

## Customization

You can customize the web interface by modifying the files in the `data` folder:
- `index.html`: Main web interface
- `success.html`: Page shown after credentials are captured

## Legal Disclaimer

AirGhost ESP32 is provided for educational and ethical penetration testing purposes only. Users are responsible for complying with applicable laws and regulations. The authors are not responsible for any misuse or damage caused by this tool.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
