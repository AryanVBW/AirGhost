#!/usr/bin/env python3
#
# AirGhost Platform Utilities
# Handles OS detection, hardware capabilities, and platform-specific features
#

import os
import sys
import json
import platform
import subprocess
import re
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('airghost.platform')

# Constants
CONFIG_DIR = os.path.join('/opt/airghost/config' if os.name != 'posix' or os.geteuid() == 0 
                         else os.path.expanduser('~/Library/Application Support/AirGhost/config'))


class PlatformManager:
    """Manages platform-specific detection and compatibility"""
    
    def __init__(self):
        """Initialize the platform manager"""
        self.os_info = self._detect_os()
        self.wifi_interfaces = []
        self.wifi_tools = {}
        self.missing_dependencies = []
        
        # Create config directory if it doesn't exist
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # Load system info from config if available
        system_info_path = os.path.join(CONFIG_DIR, 'system_info.json')
        if os.path.exists(system_info_path):
            try:
                with open(system_info_path, 'r') as f:
                    self.os_info = json.load(f)
                logger.info(f"Loaded system info from {system_info_path}")
            except Exception as e:
                logger.error(f"Error loading system info: {e}")
        
        # Detect WiFi interfaces
        self.detect_wifi_interfaces()
        
        # Detect WiFi tools
        self.detect_wifi_tools()
        
        # Load missing dependencies if available
        missing_deps_path = os.path.join(CONFIG_DIR, 'missing_dependencies.txt')
        if os.path.exists(missing_deps_path):
            try:
                with open(missing_deps_path, 'r') as f:
                    self.missing_dependencies = [line.strip() for line in f.readlines() if line.strip()]
                logger.info(f"Loaded missing dependencies: {self.missing_dependencies}")
            except Exception as e:
                logger.error(f"Error loading missing dependencies: {e}")
    
    def _detect_os(self):
        """Detect the operating system and its capabilities"""
        os_info = {
            'os_type': '',
            'os_version': '',
            'os_name': '',
            'architecture': platform.machine(),
            'package_manager': '',
            'compatibility': 'unknown',
            'is_vm': False
        }
        
        # Detect OS type and version
        system = platform.system()
        if system == 'Darwin':
            os_info['os_type'] = 'macos'
            os_info['os_version'] = platform.mac_ver()[0]
            os_info['os_name'] = f"macOS {os_info['os_version']}"
            os_info['package_manager'] = 'brew'
            
            # Check macOS version for compatibility
            major_version = int(os_info['os_version'].split('.')[0])
            if major_version >= 11:
                os_info['compatibility'] = 'partial'
            else:
                os_info['compatibility'] = 'limited'
                
            # Check if running in a VM
            try:
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.features'], 
                                       capture_output=True, text=True)
                if 'VMM' in result.stdout:
                    os_info['is_vm'] = True
            except Exception:
                pass
                
        elif system == 'Linux':
            # Try to get more detailed Linux distribution info
            try:
                # Check for /etc/os-release file
                if os.path.exists('/etc/os-release'):
                    with open('/etc/os-release', 'r') as f:
                        os_release = {}
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                os_release[key] = value.strip('"\'')
                    
                    if 'ID' in os_release:
                        os_info['os_type'] = os_release['ID'].lower()
                    if 'VERSION_ID' in os_release:
                        os_info['os_version'] = os_release['VERSION_ID']
                    if 'PRETTY_NAME' in os_release:
                        os_info['os_name'] = os_release['PRETTY_NAME']
                    else:
                        os_info['os_name'] = f"{os_release.get('NAME', 'Linux')} {os_release.get('VERSION', '')}"
                else:
                    # Fallback to generic Linux detection
                    os_info['os_type'] = 'linux'
                    os_info['os_version'] = platform.release()
                    os_info['os_name'] = f"Linux {os_info['os_version']}"
            except Exception as e:
                logger.error(f"Error detecting Linux distribution: {e}")
                os_info['os_type'] = 'linux'
                os_info['os_version'] = platform.release()
                os_info['os_name'] = f"Linux {os_info['os_version']}"
            
            # Determine package manager
            if os_info['os_type'] in ['debian', 'ubuntu', 'kali', 'raspbian', 'linuxmint', 'pop']:
                os_info['package_manager'] = 'apt'
                os_info['compatibility'] = 'full'
            elif os_info['os_type'] in ['fedora', 'rhel', 'centos', 'rocky', 'alma']:
                os_info['package_manager'] = 'dnf'
                os_info['compatibility'] = 'partial'
            elif os_info['os_type'] in ['arch', 'manjaro', 'endeavouros']:
                os_info['package_manager'] = 'pacman'
                os_info['compatibility'] = 'full'
            elif os_info['os_type'] in ['opensuse', 'sles']:
                os_info['package_manager'] = 'zypper'
                os_info['compatibility'] = 'partial'
            else:
                os_info['package_manager'] = 'unknown'
                os_info['compatibility'] = 'limited'
            
            # Check if running in a VM
            try:
                if os.path.exists('/proc/cpuinfo'):
                    with open('/proc/cpuinfo', 'r') as f:
                        if 'hypervisor' in f.read():
                            os_info['is_vm'] = True
            except Exception:
                pass
                
        elif system == 'Windows':
            os_info['os_type'] = 'windows'
            os_info['os_version'] = platform.version()
            os_info['os_name'] = f"Windows {platform.release()}"
            os_info['package_manager'] = 'unknown'
            os_info['compatibility'] = 'limited'
        else:
            os_info['os_type'] = system.lower()
            os_info['os_version'] = platform.version()
            os_info['os_name'] = f"{system} {platform.version()}"
            os_info['compatibility'] = 'unknown'
        
        # Save OS info to config
        try:
            with open(os.path.join(CONFIG_DIR, 'system_info.json'), 'w') as f:
                json.dump(os_info, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving system info: {e}")
        
        return os_info
    
    def detect_wifi_interfaces(self):
        """Detect available WiFi interfaces"""
        self.wifi_interfaces = []
        
        if self.os_info['os_type'] == 'macos':
            # macOS WiFi interface detection
            try:
                # Use networksetup to list hardware ports
                result = subprocess.run(['networksetup', '-listallhardwareports'], 
                                       capture_output=True, text=True)
                
                # Parse the output to find WiFi interfaces
                current_interface = None
                for line in result.stdout.splitlines():
                    if 'Hardware Port: Wi-Fi' in line:
                        current_interface = {'type': 'wifi'}
                    elif current_interface and 'Device:' in line:
                        current_interface['name'] = line.split('Device:')[1].strip()
                    elif current_interface and 'Ethernet Address:' in line:
                        current_interface['mac'] = line.split('Ethernet Address:')[1].strip()
                        
                        # Get additional info using airport utility
                        airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
                        if os.path.exists(airport_path):
                            try:
                                airport_result = subprocess.run([airport_path, current_interface['name'], '-I'], 
                                                              capture_output=True, text=True)
                                
                                # Parse airport output
                                for airport_line in airport_result.stdout.splitlines():
                                    if ':' in airport_line:
                                        key, value = airport_line.split(':', 1)
                                        key = key.strip()
                                        value = value.strip()
                                        
                                        if key == 'channel':
                                            current_interface['channel'] = value
                            except Exception as e:
                                logger.error(f"Error getting airport info: {e}")
                        
                        # Add driver info
                        current_interface['driver'] = 'Apple Wireless Driver'
                        
                        # Add monitor mode support info (limited on macOS)
                        current_interface['monitor_supported'] = True
                        
                        # Add the interface to the list
                        self.wifi_interfaces.append(current_interface)
                        current_interface = None
                        
            except Exception as e:
                logger.error(f"Error detecting macOS WiFi interfaces: {e}")
                
        elif self.os_info['os_type'] in ['linux', 'debian', 'ubuntu', 'kali', 'fedora', 'arch', 'manjaro']:
            # Linux WiFi interface detection
            try:
                # Check /sys/class/net for wireless interfaces
                if os.path.exists('/sys/class/net'):
                    for iface in os.listdir('/sys/class/net'):
                        # Check if it's a wireless interface
                        if os.path.exists(f'/sys/class/net/{iface}/wireless') or \
                           iface.startswith(('wlan', 'wlp', 'wlx')):
                            
                            interface = {'name': iface, 'type': 'wifi'}
                            
                            # Get MAC address
                            try:
                                with open(f'/sys/class/net/{iface}/address', 'r') as f:
                                    interface['mac'] = f.read().strip()
                            except Exception:
                                pass
                            
                            # Get driver information
                            try:
                                driver_path = os.path.realpath(f'/sys/class/net/{iface}/device/driver')
                                if driver_path:
                                    interface['driver'] = os.path.basename(driver_path)
                            except Exception:
                                pass
                            
                            # Check monitor mode support using iw
                            interface['monitor_supported'] = False
                            try:
                                result = subprocess.run(['iw', 'list'], capture_output=True, text=True)
                                if 'monitor' in result.stdout:
                                    interface['monitor_supported'] = True
                            except Exception:
                                pass
                            
                            # Add the interface to the list
                            self.wifi_interfaces.append(interface)
            except Exception as e:
                logger.error(f"Error detecting Linux WiFi interfaces: {e}")
        
        # Save WiFi interfaces to config
        try:
            with open(os.path.join(CONFIG_DIR, 'wifi_interfaces.json'), 'w') as f:
                json.dump(self.wifi_interfaces, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving WiFi interfaces: {e}")
        
        return self.wifi_interfaces
    
    def detect_wifi_tools(self):
        """Detect available WiFi tools"""
        self.wifi_tools = {}
        
        # Check for aircrack-ng suite
        self.wifi_tools['aircrack-ng'] = self._check_tool('aircrack-ng')
        self.wifi_tools['airmon-ng'] = self._check_tool('airmon-ng')
        self.wifi_tools['aireplay-ng'] = self._check_tool('aireplay-ng')
        self.wifi_tools['airodump-ng'] = self._check_tool('airodump-ng')
        
        # Check for other WiFi tools
        self.wifi_tools['iwconfig'] = self._check_tool('iwconfig')
        self.wifi_tools['iw'] = self._check_tool('iw')
        self.wifi_tools['hostapd'] = self._check_tool('hostapd')
        self.wifi_tools['dnsmasq'] = self._check_tool('dnsmasq')
        self.wifi_tools['macchanger'] = self._check_tool('macchanger')
        
        # macOS specific tools
        if self.os_info['os_type'] == 'macos':
            airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
            self.wifi_tools['airport'] = {
                'available': os.path.exists(airport_path),
                'path': airport_path if os.path.exists(airport_path) else None
            }
        
        # Save WiFi tools to config
        try:
            with open(os.path.join(CONFIG_DIR, 'wifi_tools.json'), 'w') as f:
                json.dump(self.wifi_tools, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving WiFi tools: {e}")
        
        return self.wifi_tools
    
    def _check_tool(self, tool_name):
        """Check if a tool is available in the system"""
        result = {
            'available': False,
            'path': None,
            'version': None
        }
        
        try:
            path = shutil.which(tool_name)
            if path:
                result['available'] = True
                result['path'] = path
                
                # Try to get version
                try:
                    version_result = subprocess.run([tool_name, '--version'], 
                                                  capture_output=True, text=True)
                    result['version'] = version_result.stdout.strip()
                except Exception:
                    pass
        except Exception:
            pass
        
        return result
    
    def get_compatibility_info(self):
        """Get platform compatibility information"""
        compatibility = {}
        
        if self.os_info['os_type'] == 'macos':
            # macOS compatibility info
            compatibility = {
                'wifi_tools': self.wifi_tools,
                'monitor_mode': {
                    'supported': self.wifi_tools.get('airport', {}).get('available', False),
                    'instructions': 'To enable monitor mode on macOS, use the airport utility with: '
                                   '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport '
                                   '<interface> sniff <channel>'
                },
                'packet_injection': {
                    'supported': False,
                    'instructions': 'Packet injection is not natively supported on macOS. '
                                   'Consider using an external USB WiFi adapter with compatible drivers.'
                },
                'external_adapters': {
                    'instructions': 'For full functionality on macOS, use an external WiFi adapter '
                                   'with the appropriate kext drivers installed.'
                }
            }
        else:
            # Linux compatibility info
            airmon_available = self.wifi_tools.get('airmon-ng', {}).get('available', False)
            aireplay_available = self.wifi_tools.get('aireplay-ng', {}).get('available', False)
            
            compatibility = {
                'wifi_tools': self.wifi_tools,
                'wifi_interfaces': self.wifi_interfaces,
                'monitor_mode': {
                    'supported': airmon_available,
                    'instructions': 'To enable monitor mode, use: airmon-ng start <interface>'
                },
                'packet_injection': {
                    'supported': aireplay_available,
                    'instructions': 'To test packet injection: aireplay-ng --test <interface>'
                }
            }
        
        # Save compatibility info to config
        try:
            with open(os.path.join(CONFIG_DIR, 'compatibility.json'), 'w') as f:
                json.dump(compatibility, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving compatibility info: {e}")
        
        return compatibility
    
    def get_system_info(self):
        """Get system information"""
        return self.os_info
    
    def get_wifi_interfaces(self):
        """Get WiFi interfaces"""
        return self.wifi_interfaces
    
    def get_missing_dependencies(self):
        """Get missing dependencies"""
        return self.missing_dependencies
    
    def install_missing_dependencies(self):
        """Install missing dependencies"""
        if not self.missing_dependencies:
            return {'success': True, 'message': 'No missing dependencies to install'}
        
        results = {'success': False, 'installed': [], 'failed': []}
        
        # Install dependencies based on package manager
        if self.os_info['package_manager'] == 'brew':
            # macOS with Homebrew
            for dep in self.missing_dependencies:
                try:
                    logger.info(f"Installing {dep} with Homebrew")
                    result = subprocess.run(['brew', 'install', dep], 
                                           capture_output=True, text=True)
                    if result.returncode == 0:
                        results['installed'].append(dep)
                    else:
                        results['failed'].append(dep)
                        logger.error(f"Failed to install {dep}: {result.stderr}")
                except Exception as e:
                    results['failed'].append(dep)
                    logger.error(f"Error installing {dep}: {e}")
        
        elif self.os_info['package_manager'] == 'apt':
            # Debian-based systems
            try:
                # Update package lists
                subprocess.run(['apt', 'update'], capture_output=True)
                
                # Install each dependency
                for dep in self.missing_dependencies:
                    try:
                        logger.info(f"Installing {dep} with apt")
                        result = subprocess.run(['apt', 'install', '-y', dep], 
                                               capture_output=True, text=True)
                        if result.returncode == 0:
                            results['installed'].append(dep)
                        else:
                            results['failed'].append(dep)
                            logger.error(f"Failed to install {dep}: {result.stderr}")
                    except Exception as e:
                        results['failed'].append(dep)
                        logger.error(f"Error installing {dep}: {e}")
            except Exception as e:
                logger.error(f"Error updating apt: {e}")
        
        elif self.os_info['package_manager'] == 'pacman':
            # Arch-based systems
            for dep in self.missing_dependencies:
                try:
                    logger.info(f"Installing {dep} with pacman")
                    result = subprocess.run(['pacman', '-S', '--noconfirm', dep], 
                                           capture_output=True, text=True)
                    if result.returncode == 0:
                        results['installed'].append(dep)
                    else:
                        results['failed'].append(dep)
                        logger.error(f"Failed to install {dep}: {result.stderr}")
                except Exception as e:
                    results['failed'].append(dep)
                    logger.error(f"Error installing {dep}: {e}")
        
        elif self.os_info['package_manager'] == 'dnf':
            # Red Hat-based systems
            for dep in self.missing_dependencies:
                try:
                    logger.info(f"Installing {dep} with dnf")
                    result = subprocess.run(['dnf', 'install', '-y', dep], 
                                           capture_output=True, text=True)
                    if result.returncode == 0:
                        results['installed'].append(dep)
                    else:
                        results['failed'].append(dep)
                        logger.error(f"Failed to install {dep}: {result.stderr}")
                except Exception as e:
                    results['failed'].append(dep)
                    logger.error(f"Error installing {dep}: {e}")
        
        # Update missing dependencies list
        if results['installed']:
            self.missing_dependencies = [dep for dep in self.missing_dependencies 
                                        if dep not in results['installed']]
            
            # Save updated missing dependencies to config
            try:
                with open(os.path.join(CONFIG_DIR, 'missing_dependencies.txt'), 'w') as f:
                    for dep in self.missing_dependencies:
                        f.write(f"{dep}\n")
            except Exception as e:
                logger.error(f"Error saving missing dependencies: {e}")
        
        results['success'] = len(results['failed']) == 0
        results['message'] = f"Installed {len(results['installed'])} dependencies, {len(results['failed'])} failed"
        
        return results
    
    def select_interface(self, interface_name):
        """Select a WiFi interface for operations"""
        # Find the interface in the list
        selected_interface = None
        for iface in self.wifi_interfaces:
            if iface['name'] == interface_name:
                selected_interface = iface
                break
        
        if not selected_interface:
            return {'success': False, 'message': f"Interface {interface_name} not found"}
        
        # Save selected interface to config
        try:
            with open(os.path.join(CONFIG_DIR, 'selected_interface.json'), 'w') as f:
                json.dump(selected_interface, f, indent=4)
            
            return {'success': True, 'message': f"Interface {interface_name} selected", 
                    'interface': selected_interface}
        except Exception as e:
            logger.error(f"Error saving selected interface: {e}")
            return {'success': False, 'message': f"Error selecting interface: {e}"}


# Initialize platform manager when module is imported
platform_manager = PlatformManager()


# API functions for server integration
def get_system_info():
    """API function to get system information"""
    return platform_manager.get_system_info()

def get_compatibility_info():
    """API function to get compatibility information"""
    return platform_manager.get_compatibility_info()

def get_wifi_interfaces():
    """API function to get WiFi interfaces"""
    return platform_manager.get_wifi_interfaces()

def get_missing_dependencies():
    """API function to get missing dependencies"""
    return platform_manager.get_missing_dependencies()

def install_missing_dependencies():
    """API function to install missing dependencies"""
    return platform_manager.install_missing_dependencies()

def select_interface(interface_name):
    """API function to select a WiFi interface"""
    return platform_manager.select_interface(interface_name)


# Main function for testing
if __name__ == "__main__":
    print("AirGhost Platform Utilities")
    print("--------------------------")
    
    # Get system info
    system_info = platform_manager.get_system_info()
    print(f"OS: {system_info['os_name']} ({system_info['os_type']} {system_info['os_version']})")
    print(f"Architecture: {system_info['architecture']}")
    print(f"Package Manager: {system_info['package_manager']}")
    print(f"Compatibility: {system_info['compatibility']}")
    print(f"VM: {'Yes' if system_info['is_vm'] else 'No'}")
    print()
    
    # Get WiFi interfaces
    wifi_interfaces = platform_manager.get_wifi_interfaces()
    print(f"WiFi Interfaces: {len(wifi_interfaces)}")
    for iface in wifi_interfaces:
        print(f"  - {iface['name']}")
        if 'driver' in iface:
            print(f"    Driver: {iface['driver']}")
        if 'monitor_supported' in iface:
            print(f"    Monitor Mode: {'Supported' if iface['monitor_supported'] else 'Not Supported'}")
    print()
    
    # Get WiFi tools
    wifi_tools = platform_manager.wifi_tools
    print("WiFi Tools:")
    for tool, info in wifi_tools.items():
        status = "Available" if info.get('available', False) else "Not Available"
        print(f"  - {tool}: {status}")
    print()
    
    # Get missing dependencies
    missing_deps = platform_manager.get_missing_dependencies()
    if missing_deps:
        print("Missing Dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
    else:
        print("No missing dependencies")
