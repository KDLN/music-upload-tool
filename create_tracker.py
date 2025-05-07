#!/usr/bin/env python3
"""
Tracker Generator for Music-Upload-Assistant.
This script creates a new tracker module based on the template.
"""

import os
import sys
import argparse
import shutil
from string import Template

def get_tracker_class_name(tracker_id):
    """Convert tracker ID to class name format, e.g. SP -> SPTracker"""
    return f"{tracker_id.capitalize()}Tracker"

def create_tracker_module(tracker_id, output_dir=None, force=False):
    """
    Create a new tracker module based on the template.
    
    Args:
        tracker_id: Tracker identifier
        output_dir: Output directory (default: modules/upload/trackers)
        force: Whether to overwrite existing files
        
    Returns:
        bool: Success status
    """
    # Validate tracker ID
    if not tracker_id.isalpha():
        print(f"Error: Tracker ID must contain only letters (got: {tracker_id})")
        return False
    
    # Normalize tracker ID
    tracker_id = tracker_id.upper()
    
    # Determine output directory
    if not output_dir:
        output_dir = os.path.join('modules', 'upload', 'trackers')
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if file already exists
    output_file = os.path.join(output_dir, f"{tracker_id.lower()}_tracker.py")
    if os.path.exists(output_file) and not force:
        print(f"Error: File already exists: {output_file}")
        print("Use --force to overwrite.")
        return False
    
    # Check if template exists
    template_file = os.path.join(output_dir, 'template_tracker.py')
    if not os.path.exists(template_file):
        print(f"Error: Template file not found: {template_file}")
        return False
    
    # Read template
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Replace template strings
    tracker_class_name = get_tracker_class_name(tracker_id)
    
    # Replace the template tracker class name with the new one
    content = template_content.replace('TemplateTracker', tracker_class_name)
    
    # Replace the tracker ID in the initialization
    content = content.replace('tracker_id = "TEMPLATE"', f'tracker_id = "{tracker_id}"')
    
    # Replace the module docstring
    content = content.replace(
        'Template tracker module for Music-Upload-Assistant.',
        f'{tracker_id} tracker module for Music-Upload-Assistant.\nHandles uploading to the {tracker_id} tracker.'
    )
    
    # Replace class docstring
    content = content.replace(
        '"""Template tracker implementation.',
        f'"""{tracker_id} tracker implementation.'
    )
    
    # Write the new file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created tracker module: {output_file}")
    
    # Create a simple test script to validate the new tracker
    test_file = os.path.join(output_dir, f"test_{tracker_id.lower()}_tracker.py")
    
    test_content = f'''#!/usr/bin/env python3
"""
Test script for {tracker_id} tracker.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from modules.upload.trackers.{tracker_id.lower()}_tracker import {tracker_class_name}

def test_tracker():
    """Basic test for {tracker_id} tracker."""
    # Sample config
    config = {{
        'trackers': {{
            '{tracker_id}': {{
                'enabled': True,
                'name': '{tracker_id} Tracker',
                'url': 'https://example.com',
                'api_key': 'test_key',
                'upload_url': 'https://example.com/api/upload',
                'announce_url': 'https://example.com/announce',
                'source_name': '{tracker_id}',
                'anon': False,
                'api_auth_type': 'bearer'
            }}
        }},
        'debug': True
    }}
    
    # Create tracker
    tracker = {tracker_class_name}(config)
    
    # Check if configured
    if tracker.is_configured():
        print("Tracker configuration is valid.")
    else:
        print("Tracker configuration is invalid.")
    
    # Print details
    print(f"Tracker ID: {{tracker.tracker_id}}")
    print(f"Upload URL: {{tracker.upload_url}}")
    print(f"API auth type: {{tracker.api_auth_type}}")
    
    # Test building form data
    metadata = {{
        'album': 'Test Album',
        'album_artists': ['Test Artist'],
        'format': 'FLAC',
        'year': '2023'
    }}
    
    form_data = tracker._build_form_data(metadata, "Test description")
    print("\\nForm data:")
    for key, value in form_data.items():
        print(f"  {{key}}: {{value}}")
    
    print("\\nTest completed successfully!")

if __name__ == "__main__":
    test_tracker()
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"Created test script: {test_file}")
    
    # Print next steps
    print("\nNext steps:")
    print(f"1. Configure the {tracker_id} tracker:")
    print(f"   python configure_tracker.py --add {tracker_id}")
    print("2. Customize the tracker module if needed:")
    print(f"   edit {output_file}")
    print("3. Test the tracker:")
    print(f"   python {test_file}")
    print("4. Use the tracker with the main tool:")
    print(f"   python music_upload_assistant.py /path/to/album --tracker {tracker_id} --debug")
    
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create a new tracker module for Music-Upload-Assistant'
    )
    
    parser.add_argument('tracker_id', help='Tracker identifier (e.g., SP, RED)')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--force', '-f', action='store_true', 
                      help='Overwrite existing files')
    
    args = parser.parse_args()
    
    success = create_tracker_module(args.tracker_id, args.output, args.force)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
