#!/usr/bin/env python3
#
# AirGhost API Server
# Provides REST API endpoints for the web interface
#

import os
import sys
import json
import logging
import platform
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import platform_utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("airghost_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('airghost.api')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web')
STATIC_DIR = os.path.join(WEB_DIR, 'static')
CONFIG_DIR = os.path.join('/opt/airghost/config' if os.name != 'posix' or os.geteuid() == 0 
                         else os.path.expanduser('~/Library/Application Support/AirGhost/config'))

# Create config directory if it doesn't exist
os.makedirs(CONFIG_DIR, exist_ok=True)


# API Routes
@app.route('/')
def index():
    """Serve the main index.html file"""
    return send_from_directory(WEB_DIR, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(STATIC_DIR, path)

@app.route('/api/system-info', methods=['GET'])
def api_system_info():
    """Get system information"""
    try:
        system_info = platform_utils.get_system_info()
        return jsonify({"success": True, "data": system_info})
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/compatibility', methods=['GET'])
def api_compatibility():
    """Get compatibility information"""
    try:
        compatibility = platform_utils.get_compatibility_info()
        return jsonify({"success": True, "data": compatibility})
    except Exception as e:
        logger.error(f"Error getting compatibility info: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wifi-interfaces', methods=['GET'])
def api_wifi_interfaces():
    """Get WiFi interfaces"""
    try:
        # Force refresh if requested
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        if refresh:
            platform_utils.platform_manager.detect_wifi_interfaces()
        
        interfaces = platform_utils.get_wifi_interfaces()
        return jsonify({"success": True, "data": interfaces})
    except Exception as e:
        logger.error(f"Error getting WiFi interfaces: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wifi-tools', methods=['GET'])
def api_wifi_tools():
    """Get WiFi tools"""
    try:
        # Force refresh if requested
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        if refresh:
            platform_utils.platform_manager.detect_wifi_tools()
        
        tools = platform_utils.platform_manager.wifi_tools
        return jsonify({"success": True, "data": tools})
    except Exception as e:
        logger.error(f"Error getting WiFi tools: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/missing-dependencies', methods=['GET'])
def api_missing_dependencies():
    """Get missing dependencies"""
    try:
        dependencies = platform_utils.get_missing_dependencies()
        return jsonify({"success": True, "data": dependencies})
    except Exception as e:
        logger.error(f"Error getting missing dependencies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/install-dependencies', methods=['POST'])
def api_install_dependencies():
    """Install missing dependencies"""
    try:
        result = platform_utils.install_missing_dependencies()
        return jsonify({"success": result['success'], "data": result})
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/select-interface', methods=['POST'])
def api_select_interface():
    """Select a WiFi interface"""
    try:
        data = request.get_json()
        if not data or 'interface' not in data:
            return jsonify({"success": False, "error": "Missing interface parameter"}), 400
        
        result = platform_utils.select_interface(data['interface'])
        return jsonify({"success": result['success'], "data": result})
    except Exception as e:
        logger.error(f"Error selecting interface: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scan-networks', methods=['POST'])
def api_scan_networks():
    """Scan for WiFi networks"""
    try:
        data = request.get_json()
        if not data or 'interface' not in data:
            return jsonify({"success": False, "error": "Missing interface parameter"}), 400
        
        interface = data['interface']
        system_info = platform_utils.get_system_info()
        
        # Different scanning methods based on OS
        networks = []
        
        if system_info['os_type'] == 'macos':
            # macOS scanning using airport utility
            airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
            if os.path.exists(airport_path):
                import subprocess
                try:
                    result = subprocess.run([airport_path, interface, '-s'], 
                                          capture_output=True, text=True)
                    
                    # Parse airport scan output
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:  # Skip header line
                        for line in lines[1:]:
                            parts = line.split()
                            if len(parts) >= 5:
                                network = {
                                    'ssid': parts[0],
                                    'bssid': parts[1],
                                    'rssi': parts[2],
                                    'channel': parts[3],
                                    'security': ' '.join(parts[4:])
                                }
                                networks.append(network)
                except Exception as e:
                    logger.error(f"Error scanning with airport: {e}")
                    return jsonify({"success": False, "error": f"Error scanning with airport: {e}"}), 500
            else:
                return jsonify({"success": False, "error": "Airport utility not found"}), 500
        
        elif system_info['os_type'] in ['linux', 'debian', 'ubuntu', 'kali', 'fedora', 'arch', 'manjaro']:
            # Linux scanning using iw
            import subprocess
            try:
                result = subprocess.run(['iw', 'dev', interface, 'scan'], 
                                      capture_output=True, text=True)
                
                # Parse iw scan output
                current_network = None
                for line in result.stdout.splitlines():
                    line = line.strip()
                    
                    if line.startswith('BSS '):
                        if current_network:
                            networks.append(current_network)
                        
                        # Extract BSSID
                        bssid = line.split('BSS ')[1].split('(')[0].strip()
                        current_network = {'bssid': bssid}
                    
                    elif current_network:
                        if 'SSID: ' in line:
                            current_network['ssid'] = line.split('SSID: ')[1]
                        elif 'signal: ' in line:
                            current_network['rssi'] = line.split('signal: ')[1]
                        elif 'freq: ' in line:
                            current_network['frequency'] = line.split('freq: ')[1]
                        elif 'capability: ' in line:
                            current_network['capability'] = line.split('capability: ')[1]
                
                # Add the last network
                if current_network:
                    networks.append(current_network)
                    
            except Exception as e:
                logger.error(f"Error scanning with iw: {e}")
                return jsonify({"success": False, "error": f"Error scanning with iw: {e}"}), 500
        
        else:
            return jsonify({"success": False, "error": "Scanning not supported on this platform"}), 500
        
        return jsonify({"success": True, "data": networks})
    except Exception as e:
        logger.error(f"Error scanning networks: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "version": "1.0.0"})


# Main function
if __name__ == "__main__":
    # Get port from arguments or use default
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    
    print(f"AirGhost API Server starting on port {port}")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Web Directory: {WEB_DIR}")
    print(f"Config Directory: {CONFIG_DIR}")
    print("API Endpoints:")
    print("  - /api/system-info")
    print("  - /api/compatibility")
    print("  - /api/wifi-interfaces")
    print("  - /api/wifi-tools")
    print("  - /api/missing-dependencies")
    print("  - /api/install-dependencies")
    print("  - /api/select-interface")
    print("  - /api/scan-networks")
    print("  - /api/health")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)
