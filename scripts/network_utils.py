#!/usr/bin/env python3
#
# AirGhost Network Utilities
# Helper functions for network management and routing
#

import os
import subprocess
import logging
import netifaces
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/airghost/logs/network.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('network_utils')

def get_default_gateway():
    """Get the default gateway interface and IP"""
    try:
        gateways = netifaces.gateways()
        default_gateway = gateways['default'][netifaces.AF_INET]
        gateway_ip = default_gateway[0]
        gateway_interface = default_gateway[1]
        
        return gateway_interface, gateway_ip
    except Exception as e:
        logger.error(f"Error getting default gateway: {e}")
        return None, None

def get_internet_interfaces():
    """Get interfaces that have internet connectivity"""
    interfaces = []
    
    try:
        gateway_interface, _ = get_default_gateway()
        if gateway_interface:
            interfaces.append(gateway_interface)
    except Exception as e:
        logger.error(f"Error detecting internet interfaces: {e}")
    
    return interfaces

def setup_nat(input_interface, output_interface):
    """Set up NAT between interfaces for internet sharing"""
    try:
        # Enable IP forwarding
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
        
        # Flush existing rules
        subprocess.run(['iptables', '--flush'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '--table', 'nat', '--flush'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '--delete-chain'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '--table', 'nat', '--delete-chain'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Set up NAT
        subprocess.run(['iptables', '--table', 'nat', '--append', 'POSTROUTING', 
                        '--out-interface', output_interface, '-j', 'MASQUERADE'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        subprocess.run(['iptables', '--append', 'FORWARD', 
                        '--in-interface', input_interface, '-j', 'ACCEPT'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"NAT set up between {input_interface} and {output_interface}")
        return True
    except Exception as e:
        logger.error(f"Error setting up NAT: {e}")
        return False

def disable_nat():
    """Disable NAT and IP forwarding"""
    try:
        # Disable IP forwarding
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('0')
        
        # Flush iptables
        subprocess.run(['iptables', '--flush'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '--table', 'nat', '--flush'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info("NAT disabled")
        return True
    except Exception as e:
        logger.error(f"Error disabling NAT: {e}")
        return False

def setup_ap_routing(interface, ssid, channel=1, hostapd_conf=None, dnsmasq_conf=None):
    """Set up an access point with routing"""
    try:
        if not hostapd_conf:
            hostapd_conf = '/opt/airghost/config/hostapd.conf'
        
        if not dnsmasq_conf:
            dnsmasq_conf = '/opt/airghost/config/dnsmasq.conf'
        
        # Configure hostapd
        with open(hostapd_conf, 'w') as f:
            f.write(f"interface={interface}\n")
            f.write(f"driver=nl80211\n")
            f.write(f"ssid={ssid}\n")
            f.write(f"hw_mode=g\n")
            f.write(f"channel={channel}\n")
            f.write(f"macaddr_acl=0\n")
            f.write(f"ignore_broadcast_ssid=0\n")
        
        # Configure dnsmasq
        with open(dnsmasq_conf, 'w') as f:
            f.write(f"interface={interface}\n")
            f.write(f"dhcp-range=192.168.1.2,192.168.1.30,255.255.255.0,12h\n")
            f.write(f"dhcp-option=3,192.168.1.1\n")  # Default gateway
            f.write(f"dhcp-option=6,192.168.1.1\n")  # DNS server
            f.write(f"server=8.8.8.8\n")             # Upstream DNS
            f.write(f"log-queries\n")
            f.write(f"log-dhcp\n")
        
        # Configure interface
        subprocess.run(['ip', 'link', 'set', interface, 'down'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ip', 'addr', 'flush', 'dev', interface], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ip', 'addr', 'add', '192.168.1.1/24', 'dev', interface], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ip', 'link', 'set', interface, 'up'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Start hostapd
        hostapd_process = subprocess.Popen(['hostapd', hostapd_conf], 
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for hostapd to start
        time.sleep(2)
        if hostapd_process.poll() is not None:
            # hostapd failed
            stderr = hostapd_process.stderr.read().decode('utf-8')
            logger.error(f"hostapd failed to start: {stderr}")
            return False, hostapd_process, None
        
        # Start dnsmasq
        dnsmasq_process = subprocess.Popen(['dnsmasq', '-C', dnsmasq_conf], 
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for dnsmasq to start
        time.sleep(2)
        if dnsmasq_process.poll() is not None:
            # dnsmasq failed
            stderr = dnsmasq_process.stderr.read().decode('utf-8')
            logger.error(f"dnsmasq failed to start: {stderr}")
            # Clean up hostapd
            hostapd_process.terminate()
            return False, hostapd_process, dnsmasq_process
        
        logger.info(f"Access point '{ssid}' set up on {interface}")
        return True, hostapd_process, dnsmasq_process
    
    except Exception as e:
        logger.error(f"Error setting up access point: {e}")
        return False, None, None

def get_wireless_interfaces():
    """Get a list of wireless interfaces"""
    interfaces = []
    try:
        # Method 1: Using iw dev
        output = subprocess.check_output(['iw', 'dev'], universal_newlines=True)
        pattern = re.compile(r'Interface\s+(\w+)')
        interfaces = pattern.findall(output)
        
        # Method 2: Check for wireless extensions using iwconfig
        if not interfaces:
            output = subprocess.check_output(['iwconfig'], universal_newlines=True, stderr=subprocess.STDOUT)
            for line in output.split('\n'):
                if 'no wireless extensions' not in line and line.strip():
                    interface = line.split()[0]
                    if interface:
                        interfaces.append(interface)
    except Exception as e:
        logger.error(f"Error getting wireless interfaces: {e}")
    
    return interfaces

def put_interface_in_monitor_mode(interface):
    """Put a wireless interface in monitor mode"""
    try:
        # Kill processes that might interfere
        subprocess.run(['airmon-ng', 'check', 'kill'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Set interface down
        subprocess.run(['ip', 'link', 'set', interface, 'down'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Set monitor mode
        subprocess.run(['iw', interface, 'set', 'monitor', 'none'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Set interface up
        subprocess.run(['ip', 'link', 'set', interface, 'up'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"Interface {interface} put in monitor mode")
        return True
    except Exception as e:
        logger.error(f"Error putting interface in monitor mode: {e}")
        return False

def put_interface_in_managed_mode(interface):
    """Put a wireless interface in managed mode"""
    try:
        # Set interface down
        subprocess.run(['ip', 'link', 'set', interface, 'down'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Set managed mode
        subprocess.run(['iw', interface, 'set', 'type', 'managed'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Set interface up
        subprocess.run(['ip', 'link', 'set', interface, 'up'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"Interface {interface} put in managed mode")
        return True
    except Exception as e:
        logger.error(f"Error putting interface in managed mode: {e}")
        return False

def change_mac_address(interface, mac=None):
    """Change the MAC address of an interface"""
    try:
        # Set interface down
        subprocess.run(['ip', 'link', 'set', interface, 'down'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Change MAC
        if mac:
            subprocess.run(['macchanger', '--mac', mac, interface], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            # Random MAC
            subprocess.run(['macchanger', '--random', interface], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Set interface up
        subprocess.run(['ip', 'link', 'set', interface, 'up'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Get new MAC
        output = subprocess.check_output(['macchanger', '--show', interface], 
                                         universal_newlines=True)
        new_mac = re.search(r'Current MAC:\s+([0-9a-f:]+)', output, re.IGNORECASE)
        
        if new_mac:
            logger.info(f"MAC address of {interface} changed to {new_mac.group(1)}")
            return True, new_mac.group(1)
        else:
            logger.error(f"Failed to get new MAC address for {interface}")
            return False, None
    except Exception as e:
        logger.error(f"Error changing MAC address: {e}")
        return False, None

def setup_captive_portal_firewall(interface):
    """Set up firewall rules for captive portal"""
    try:
        # Flush existing rules
        subprocess.run(['iptables', '--flush'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '--table', 'nat', '--flush'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Allow established connections
        subprocess.run(['iptables', '-A', 'INPUT', '-m', 'conntrack', '--ctstate', 
                        'ESTABLISHED,RELATED', '-j', 'ACCEPT'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Allow localhost
        subprocess.run(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Allow DNS and DHCP
        subprocess.run(['iptables', '-A', 'INPUT', '-i', interface, '-p', 'udp', 
                        '--dport', '53', '-j', 'ACCEPT'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '-A', 'INPUT', '-i', interface, '-p', 'udp', 
                        '--dport', '67', '-j', 'ACCEPT'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Allow HTTP/HTTPS
        subprocess.run(['iptables', '-A', 'INPUT', '-i', interface, '-p', 'tcp', 
                        '--dport', '80', '-j', 'ACCEPT'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '-A', 'INPUT', '-i', interface, '-p', 'tcp', 
                        '--dport', '443', '-j', 'ACCEPT'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Redirect HTTP/HTTPS traffic to captive portal
        subprocess.run(['iptables', '-t', 'nat', '-A', 'PREROUTING', '-i', interface, 
                        '-p', 'tcp', '--dport', '80', '-j', 'REDIRECT', '--to-port', '8080'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['iptables', '-t', 'nat', '-A', 'PREROUTING', '-i', interface, 
                        '-p', 'tcp', '--dport', '443', '-j', 'REDIRECT', '--to-port', '8080'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"Captive portal firewall rules set up for {interface}")
        return True
    except Exception as e:
        logger.error(f"Error setting up captive portal firewall: {e}")
        return False

if __name__ == "__main__":
    # Test functions
    print("Wireless interfaces:", get_wireless_interfaces())
    print("Default gateway:", get_default_gateway())
    print("Internet interfaces:", get_internet_interfaces())
