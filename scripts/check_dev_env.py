#!/usr/bin/env python3
"""
Script to check if the AirGhost development environment is properly set up
and to help developers troubleshoot any issues.
"""

import os
import sys
import subprocess
import platform
import shutil
import json

# ANSI color codes
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def print_status(message):
    """Print a status message"""
    print(f"{BLUE}[*]{NC} {message}")

def print_good(message):
    """Print a success message"""
    print(f"{GREEN}[+]{NC} {message}")

def print_error(message):
    """Print an error message"""
    print(f"{RED}[-]{NC} {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"{YELLOW}[!]{NC} {message}")

def check_os():
    """Check if running on Linux"""
    print_status("Checking operating system...")
    
    if platform.system() != "Linux":
        print_warning(f"Not running on Linux. Detected: {platform.system()}")
        return False
    
    # Check if running on Kali Linux
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r") as f:
            if "Kali" in f.read():
                print_good("Running on Kali Linux")
                return True
    
    print_warning("Not running on Kali Linux. Some features may not work correctly.")
    return True

def check_dependencies():
    """Check if required system dependencies are installed"""
    print_status("Checking system dependencies...")
    
    dependencies = [
        "aircrack-ng",
        "hostapd",
        "dnsmasq",
        "python3",
        "pip3",
        "nodejs",
        "npm"
    ]
    
    missing = []
    
    for dep in dependencies:
        if shutil.which(dep) is None:
            missing.append(dep)
            print_error(f"Missing dependency: {dep}")
        else:
            print_good(f"Found dependency: {dep}")
    
    if missing:
        print_warning(f"Missing {len(missing)} dependencies. Run dev_setup.sh to install them.")
        return False
    
    return True

def check_python_env():
    """Check if Python virtual environment is set up"""
    print_status("Checking Python virtual environment...")
    
    # Check if venv directory exists
    if not os.path.isdir("venv"):
        print_error("Virtual environment not found. Run dev_setup.sh to create it.")
        return False
    
    # Check if requirements.txt exists
    if not os.path.isfile("requirements.txt"):
        print_warning("requirements.txt not found. Dependencies may not be properly tracked.")
    
    # Check if we're running in the virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_warning("Not running in virtual environment. Activate it with: source venv/bin/activate")
    else:
        print_good("Running in virtual environment")
    
    return True

def check_config_files():
    """Check if configuration files exist"""
    print_status("Checking configuration files...")
    
    config_files = [
        "config/hostapd.conf",
        "config/dnsmasq.conf",
        ".env"
    ]
    
    all_exist = True
    
    for config in config_files:
        if os.path.isfile(config):
            print_good(f"Found config file: {config}")
        else:
            print_warning(f"Missing config file: {config}")
            all_exist = False
    
    return all_exist

def check_templates():
    """Check if phishing templates are properly configured"""
    print_status("Checking phishing templates...")
    
    if not os.path.isdir("templates"):
        print_error("Templates directory not found")
        return False
    
    template_dirs = [d for d in os.listdir("templates") if os.path.isdir(os.path.join("templates", d))]
    
    if not template_dirs:
        print_error("No templates found")
        return False
    
    print_good(f"Found {len(template_dirs)} templates")
    
    # Check a few templates for proper configuration
    sample_size = min(5, len(template_dirs))
    samples = template_dirs[:sample_size]
    
    issues = 0
    
    for template in samples:
        template_path = os.path.join("templates", template)
        
        # Check for index.html
        if not os.path.isfile(os.path.join(template_path, "index.html")):
            print_error(f"Template {template} is missing index.html")
            issues += 1
        
        # Check for config.json
        config_path = os.path.join(template_path, "config.json")
        if not os.path.isfile(config_path):
            print_error(f"Template {template} is missing config.json")
            issues += 1
        else:
            # Validate config.json
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if "credentials" not in config or "redirect" not in config:
                    print_error(f"Template {template} has invalid config.json")
                    issues += 1
            except json.JSONDecodeError:
                print_error(f"Template {template} has invalid JSON in config.json")
                issues += 1
    
    if issues:
        print_warning(f"Found {issues} issues in template configuration")
        return False
    
    print_good("All sampled templates are properly configured")
    return True

def check_git_setup():
    """Check if Git is properly set up"""
    print_status("Checking Git setup...")
    
    if not os.path.isdir(".git"):
        print_warning("Not a Git repository. Initialize with: git init")
        return False
    
    # Check if Git hooks are set up
    if not os.path.isfile(".git/hooks/pre-commit"):
        print_warning("Git pre-commit hook not found. Run dev_setup.sh to set it up.")
        return False
    
    print_good("Git repository and hooks are properly set up")
    return True

def check_network_interfaces():
    """Check available network interfaces"""
    print_status("Checking network interfaces...")
    
    try:
        # Run ip link to get network interfaces
        result = subprocess.run(["ip", "link"], capture_output=True, text=True)
        
        if result.returncode != 0:
            print_error("Failed to get network interfaces")
            return False
        
        # Parse output to get interface names
        interfaces = []
        for line in result.stdout.splitlines():
            if ": " in line:
                iface = line.split(": ")[1].split(":")[0]
                interfaces.append(iface)
        
        if not interfaces:
            print_error("No network interfaces found")
            return False
        
        print_good(f"Found {len(interfaces)} network interfaces: {', '.join(interfaces)}")
        
        # Check for wireless interfaces
        wireless_interfaces = []
        for iface in interfaces:
            # Skip loopback and virtual interfaces
            if iface == "lo" or "vir" in iface or "docker" in iface or "br-" in iface:
                continue
            
            # Check if it's a wireless interface
            try:
                result = subprocess.run(["iwconfig", iface], capture_output=True, text=True)
                if "no wireless extensions" not in result.stdout and "no wireless extensions" not in result.stderr:
                    wireless_interfaces.append(iface)
            except:
                pass
        
        if not wireless_interfaces:
            print_warning("No wireless interfaces found. AirGhost requires at least one wireless interface.")
            return False
        
        print_good(f"Found {len(wireless_interfaces)} wireless interfaces: {', '.join(wireless_interfaces)}")
        return True
    
    except Exception as e:
        print_error(f"Error checking network interfaces: {str(e)}")
        return False

def main():
    """Main function"""
    print(f"\n{BLUE}=== AirGhost Development Environment Check ==={NC}\n")
    
    checks = [
        ("Operating System", check_os),
        ("System Dependencies", check_dependencies),
        ("Python Environment", check_python_env),
        ("Configuration Files", check_config_files),
        ("Phishing Templates", check_templates),
        ("Git Setup", check_git_setup),
        ("Network Interfaces", check_network_interfaces)
    ]
    
    results = {}
    
    for name, check_func in checks:
        print(f"\n{BLUE}Checking {name}...{NC}")
        results[name] = check_func()
        print()
    
    # Print summary
    print(f"\n{BLUE}=== Summary ==={NC}\n")
    
    all_passed = True
    for name, result in results.items():
        if result:
            print(f"{GREEN}✓{NC} {name}: OK")
        else:
            print(f"{RED}✗{NC} {name}: Issues detected")
            all_passed = False
    
    if all_passed:
        print(f"\n{GREEN}All checks passed! Your development environment is ready.{NC}")
    else:
        print(f"\n{YELLOW}Some checks failed. Please fix the issues before continuing development.{NC}")
        print(f"{YELLOW}Run dev_setup.sh to automatically set up the development environment.{NC}")

if __name__ == "__main__":
    main()
