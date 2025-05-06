#!/usr/bin/env python3
"""
Configuration utility for Music-Upload-Assistant trackers.
This script helps users easily configure and test tracker settings.
"""

import os
import sys
import json
import getpass
import argparse
import logging
from typing import Dict, Any, Optional

# Import the ConfigManager
from modules.utils.config_manager import ConfigManager

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tracker-config")

def setup_yus_tracker(config_manager: ConfigManager) -> Dict[str, Any]:
    """
    Set up YUS tracker configuration interactively.
    
    Args:
        config_manager: ConfigManager instance
        
    Returns:
        dict: Updated tracker configuration
    """
    print("\n=== YU-Scene (YUS) Tracker Configuration ===")
    
    # Get current configuration if exists
    tracker_config = config_manager.get('trackers.YUS', {})
    
    # Set defaults if not already configured
    if not tracker_config:
        tracker_config = {
            'enabled': True,
            'name': 'YU-Scene',
            'url': 'https://yu-scene.net',
            'announce_url': 'https://yu-scene.net/announce',
            'api_key': '',
            'upload_url': 'https://yu-scene.net/api/torrents/upload',
            'source_name': 'YuScene',
            'anon': False
        }
    
    # API Key
    current_api_key = tracker_config.get('api_key', '')
    print(f"\nAPI Key [{current_api_key[:4] + '****' if current_api_key else 'Not set'}]: ", end='')
    api_key = getpass.getpass('').strip()
    if api_key:
        tracker_config['api_key'] = api_key
    
    # Upload URL
    current_upload_url = tracker_config.get('upload_url', 'https://yu-scene.net/api/torrents/upload')
    print(f"Upload URL [{current_upload_url}]: ", end='')
    upload_url = input().strip()
    if upload_url:
        tracker_config['upload_url'] = upload_url
    
    # Announce URL
    current_announce_url = tracker_config.get('announce_url', 'https://yu-scene.net/announce')
    print(f"Announce URL [{current_announce_url}]: ", end='')
    announce_url = input().strip()
    if announce_url:
        tracker_config['announce_url'] = announce_url
    
    # Anonymous uploads?
    current_anon = tracker_config.get('anon', False)
    print(f"Anonymous uploads? (y/n) [{current_anon and 'y' or 'n'}]: ", end='')
    anon_input = input().strip().lower()
    if anon_input in ['y', 'yes']:
        tracker_config['anon'] = True
    elif anon_input in ['n', 'no']:
        tracker_config['anon'] = False
    
    # Make sure it's enabled
    tracker_config['enabled'] = True
    
    # Update config
    return tracker_config

def list_trackers(config_manager: ConfigManager):
    """
    List the currently configured trackers.
    
    Args:
        config_manager: ConfigManager instance
    """
    trackers = config_manager.get('trackers', {})
    
    if not trackers:
        print("\nNo trackers are currently configured.")
        return
    
    print("\n=== Configured Trackers ===")
    
    for tracker_id, tracker in trackers.items():
        enabled = tracker.get('enabled', False)
        status = "ENABLED" if enabled else "DISABLED"
        url = tracker.get('url', 'Unknown URL')
        has_api = bool(tracker.get('api_key', ''))
        api_status = "API KEY SET" if has_api else "NO API KEY"
        
        print(f"{tracker_id}: {tracker.get('name', tracker_id)} - {url} - {status} - {api_status}")

def test_tracker(config_manager: ConfigManager, tracker_id: str):
    """
    Test tracker configuration to verify it's set up correctly.
    
    Args:
        config_manager: ConfigManager instance
        tracker_id: Tracker identifier
    """
    # Get tracker config
    tracker_config = config_manager.get(f'trackers.{tracker_id}', {})
    
    if not tracker_config:
        print(f"\nTracker {tracker_id} is not configured.")
        return
    
    # Check if enabled
    if not tracker_config.get('enabled', False):
        print(f"\nTracker {tracker_id} is disabled.")
        return
    
    # Check for API key
    if not tracker_config.get('api_key', ''):
        print(f"\nTracker {tracker_id} does not have an API key set.")
        return
    
    print(f"\nTesting tracker {tracker_id}...")
    
    # Load the appropriate tracker module and perform a test
    try:
        if tracker_id == 'YUS':
            from modules.upload.trackers.yus_tracker import YUSTracker
            
            # Create a config dictionary for the tracker
            config_dict = {
                'trackers': {
                    'YUS': tracker_config
                }
            }
            
            # Create tracker instance
            tracker = YUSTracker(config_dict)
            
            # Check if configured
            if not tracker.is_configured():
                print("Tracker is not properly configured. Please check your settings.")
                return
            
            # Here you would normally make an API call to verify the connection,
            # but we'll just check if the required fields are present for now
            required_fields = ['api_key', 'upload_url', 'announce_url']
            missing_fields = [field for field in required_fields if not tracker_config.get(field)]
            
            if missing_fields:
                print(f"Missing required fields: {', '.join(missing_fields)}")
                return
            
            print("Tracker configuration looks valid!")
            print("For a full connection test, upload a test torrent or")
            print("run the main tool with the --debug flag.")
        else:
            print(f"Testing for tracker {tracker_id} is not implemented yet.")
    except ImportError as e:
        print(f"Error importing tracker module: {e}")
    except Exception as e:
        print(f"Error testing tracker: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Configure trackers for Music-Upload-Assistant'
    )
    
    parser.add_argument('--list', '-l', action='store_true',
                      help='List configured trackers')
    parser.add_argument('--add', '-a', choices=['YUS'],
                      help='Add or update a tracker')
    parser.add_argument('--test', '-t', 
                      help='Test a tracker configuration')
    parser.add_argument('--config', '-c',
                      help='Path to config file (default: data/config.json)')
    parser.add_argument('--uploader', '-u',
                      help='Set your uploader name for release naming')
    
    args = parser.parse_args()
    
    # Create a config manager
    config_path = args.config or None
    config_manager = ConfigManager(config_path)
    
    # Set uploader name if specified
    if args.uploader:
        config_manager.set('uploader_name', args.uploader)
        print(f"Uploader name set to: {args.uploader}")
    
    # Process commands
    if args.list:
        list_trackers(config_manager)
    
    elif args.add:
        if args.add == 'YUS':
            tracker_config = setup_yus_tracker(config_manager)
            config_manager.set('trackers.YUS', tracker_config)
            print("YUS tracker configuration updated.")
    
    elif args.test:
        test_tracker(config_manager, args.test)
    
    else:
        # If no command specified, show current config status
        uploader_name = config_manager.get('uploader_name', 'Not set')
        trackers = config_manager.get('trackers', {})
        
        print("\n=== Music-Upload-Assistant Configuration ===")
        print(f"Uploader name: {uploader_name}")
        print(f"Configured trackers: {len(trackers)}")
        
        if trackers:
            print("\nTrackers:")
            for tracker_id, config in trackers.items():
                enabled = config.get('enabled', False)
                status = "Enabled" if enabled else "Disabled"
                has_api = bool(config.get('api_key', ''))
                api_status = "API key set" if has_api else "No API key"
                print(f"  - {tracker_id}: {status}, {api_status}")
        
        print("\nUse --list to see more details about configured trackers")
        print("Use --add YUS to add or update YUS tracker configuration")
        print("Use --test TRACKER to test a tracker configuration")
    
    # Save the configuration
    if args.add or args.uploader:
        saved = config_manager.save()
        if saved:
            print("\nConfiguration saved successfully.")
        else:
            print("\nError saving configuration.")

if __name__ == "__main__":
    main()
