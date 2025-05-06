#!/usr/bin/env python3
"""
Minimal setup script for Music-Upload-Assistant.
This script creates the necessary directories and checks if the tool can run with minimal dependencies.
"""

import os
import sys
import importlib
import subprocess

def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        except Exception as e:
            print(f"Could not create directory {directory}: {e}")
    else:
        print(f"Directory already exists: {directory}")

def check_module(module_name):
    """Check if a Python module is installed."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def main():
    """Main function to set up minimal environment."""
    print("Music-Upload-Assistant Minimal Setup")
    print("====================================")
    
    # Essential directories
    essential_dirs = [
        "temp",
        "output",
        "data/templates"
    ]
    
    # Create essential directories
    print("\nCreating essential directories...")
    for directory in essential_dirs:
        create_directory(directory)
    
    # Check minimal required modules
    print("\nChecking essential modules...")
    required_modules = {
        "requests": "For HTTP requests",
        "mutagen": "For audio metadata",
        "PIL": "For image processing (installed as pillow)"
    }
    
    missing_modules = []
    for module, description in required_modules.items():
        if check_module(module):
            print(f"✓ {module} - {description}")
        else:
            print(f"✗ {module} - {description} - MISSING")
            missing_modules.append(module)
    
    # Print summary
    print("\nSetup Summary:")
    if missing_modules:
        print(f"- {len(missing_modules)} missing modules: {', '.join(missing_modules)}")
        print("  Install them with: pip install " + " ".join(missing_modules))
    else:
        print("- All essential modules are installed!")
    
    print("\nTo run the tool with minimal functionality:")
    print("python test_script.py /path/to/your/music.flac")

if __name__ == "__main__":
    main()
