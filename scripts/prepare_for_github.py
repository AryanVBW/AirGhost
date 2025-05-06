#!/usr/bin/env python3
"""
Script to prepare the AirGhost project for GitHub by removing unnecessary files
and ensuring all required files are present.
"""

import os
import shutil
import glob

# Base directory
BASE_DIR = '/Volumes/DATA_vivek/GITHUB/AirGhost'

# Files and directories to remove
REMOVE_PATTERNS = [
    '**/.DS_Store',
    '**/*.pyc',
    '**/__pycache__',
    '**/.idea',
    '**/.vscode',
    '**/node_modules',
    '**/tmp',
    '**/temp',
    '**/*.tmp',
    '**/*.bak',
    '**/*.swp',
    '**/*.log'
]

# Temporary script files that can be removed
TEMP_SCRIPTS = [
    'modify_templates.py',
    'move_templates.py',
    'rename_templates.py',
    'cleanup_templates.py',
    'fix_form_actions.py',
    'fix_remaining_templates.py',
    'fix_remaining_forms.py',
    'verify_templates.py',
    'fix_all_templates.py'
]

def remove_files_by_pattern():
    """Remove files matching the specified patterns"""
    print("Removing unnecessary files...")
    
    for pattern in REMOVE_PATTERNS:
        full_pattern = os.path.join(BASE_DIR, pattern)
        matches = glob.glob(full_pattern, recursive=True)
        
        for match in matches:
            try:
                if os.path.isdir(match):
                    shutil.rmtree(match)
                    print(f"  Removed directory: {os.path.relpath(match, BASE_DIR)}")
                else:
                    os.remove(match)
                    print(f"  Removed file: {os.path.relpath(match, BASE_DIR)}")
            except Exception as e:
                print(f"  Error removing {match}: {str(e)}")

def remove_temporary_scripts():
    """Remove temporary scripts used for template modification"""
    print("\nRemoving temporary scripts...")
    
    scripts_dir = os.path.join(BASE_DIR, 'scripts')
    
    for script in TEMP_SCRIPTS:
        script_path = os.path.join(scripts_dir, script)
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
                print(f"  Removed script: {script}")
            except Exception as e:
                print(f"  Error removing {script}: {str(e)}")

def ensure_required_files():
    """Ensure all required files are present"""
    print("\nChecking required files...")
    
    required_files = [
        '.gitignore',
        'README.md',
        'TEMPLATES.md',
        'LICENSE'
    ]
    
    for file in required_files:
        file_path = os.path.join(BASE_DIR, file)
        if os.path.exists(file_path):
            print(f"  ✓ {file} exists")
        else:
            print(f"  ✗ {file} is missing")

def main():
    """Main function"""
    print("Preparing AirGhost project for GitHub...\n")
    
    remove_files_by_pattern()
    remove_temporary_scripts()
    ensure_required_files()
    
    print("\nProject is ready for GitHub!")
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Initialize Git repository (if not already done)")
    print("3. Add files to Git")
    print("4. Commit changes")
    print("5. Push to GitHub")

if __name__ == "__main__":
    main()
