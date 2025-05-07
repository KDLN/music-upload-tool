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

def setup_generic_tracker(config_manager: ConfigManager, tracker_id: str) -> Dict[str, Any]:
    """
    Set up a generic tracker configuration interactively.
    
    Args:
        config_manager: ConfigManager instance
        tracker_id: Tracker identifier (e.g., 'SP', 'RED', etc.)
        
    Returns:
        dict: Updated tracker configuration
    """
    print(f"\n=== {tracker_id} Tracker Configuration ===")
    
    # Get current configuration if exists
    tracker_config = config_manager.get(f'trackers.{tracker_id}', {})
    
    # Get tracker name
    tracker_name = tracker_config.get('name', '')
    if not tracker_name:
        print(f"Enter the full name of the tracker (e.g., SeedPeer, Redacted): ", end='')
        tracker_name = input().strip()
        if not tracker_name:
            tracker_name = tracker_id
    
    # Set defaults if not already configured
    if not tracker_config:
        base_url = input(f"Enter the base URL for {tracker_id} (e.g., https://tracker.example.com): ").strip()
        
        if not base_url:
            print("Base URL is required. Configuration cancelled.")
            return None
            
        # Try to create default URLs based on the base URL
        if not base_url.endswith('/'):
            base_url += '/'
            
        tracker_config = {
            'enabled': True,
            'name': tracker_name,
            'url': base_url.rstrip('/'),
            'announce_url': f"{base_url}announce",
            'api_key': '',
            'upload_url': f"{base_url}api/torrents/upload",
            'source_name': tracker_id,
            'anon': False
        }
    
    print(f"\nConfiguring {tracker_name} ({tracker_id})...")
    
    # Tracker URL
    current_url = tracker_config.get('url', '')
    print(f"Tracker URL [{current_url}]: ", end='')
    url = input().strip()
    if url:
        tracker_config['url'] = url
    
    # API Key
    current_api_key = tracker_config.get('api_key', '')
    print(f"API Key [{current_api_key[:4] + '****' if current_api_key else 'Not set'}]: ", end='')
    api_key = getpass.getpass('').strip()
    if api_key:
        tracker_config['api_key'] = api_key
    
    # Upload URL
    current_upload_url = tracker_config.get('upload_url', '')
    print(f"Upload URL [{current_upload_url}]: ", end='')
    upload_url = input().strip()
    if upload_url:
        tracker_config['upload_url'] = upload_url
    
    # Announce URL
    current_announce_url = tracker_config.get('announce_url', '')
    print(f"Announce URL [{current_announce_url}]: ", end='')
    announce_url = input().strip()
    if announce_url:
        tracker_config['announce_url'] = announce_url
    
    # Source name for torrents
    current_source = tracker_config.get('source_name', tracker_id)
    print(f"Source name for torrents [{current_source}]: ", end='')
    source_name = input().strip()
    if source_name:
        tracker_config['source_name'] = source_name
    
    # Anonymous uploads?
    current_anon = tracker_config.get('anon', False)
    print(f"Anonymous uploads? (y/n) [{current_anon and 'y' or 'n'}]: ", end='')
    anon_input = input().strip().lower()
    if anon_input in ['y', 'yes']:
        tracker_config['anon'] = True
    elif anon_input in ['n', 'no']:
        tracker_config['anon'] = False
    
    # Category IDs (optional)
    print("\nWould you like to configure category IDs? (y/n): ", end='')
    if input().strip().lower() in ['y', 'yes']:
        category_ids = tracker_config.get('category_ids', {})
        print("Enter category IDs (press enter to skip):")
        
        categories = ['ALBUM', 'SINGLE', 'EP', 'COMPILATION', 'SOUNDTRACK', 'LIVE']
        for category in categories:
            current_id = category_ids.get(category, '')
            print(f"  {category} ID [{current_id}]: ", end='')
            cat_id = input().strip()
            if cat_id:
                category_ids[category] = cat_id
        
        tracker_config['category_ids'] = category_ids
    
    # Format IDs (optional)
    print("\nWould you like to configure format IDs? (y/n): ", end='')
    if input().strip().lower() in ['y', 'yes']:
        format_ids = tracker_config.get('format_ids', {})
        print("Enter format IDs (press enter to skip):")
        
        formats = ['FLAC', 'MP3', 'AAC', 'ALAC', 'OGG', 'WAV']
        for format_type in formats:
            current_id = format_ids.get(format_type, '')
            print(f"  {format_type} ID [{current_id}]: ", end='')
            fmt_id = input().strip()
            if fmt_id:
                format_ids[format_type] = fmt_id
        
        tracker_config['format_ids'] = format_ids
    
    # Make sure it's enabled
    tracker_config['enabled'] = True
    
    # Update config
    return tracker_config

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
    tracker_id = tracker_id.upper()
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
    
    # Create config dictionary for the tracker
    config_dict = {
        'trackers': {
            tracker_id: tracker_config
        }
    }
    
    # Check required fields
    required_fields = ['api_key', 'upload_url', 'announce_url']
    missing_fields = [field for field in required_fields if not tracker_config.get(field)]
    
    if missing_fields:
        print(f"Missing required fields: {', '.join(missing_fields)}")
        return
    
    # Load the appropriate tracker module and perform a test
    try:
        # Try to import specific tracker module
        try:
            # Dynamic import based on tracker ID
            tracker_module_name = f"modules.upload.trackers.{tracker_id.lower()}_tracker"
            tracker_class_name = f"{tracker_id.capitalize()}Tracker"
            
            # Try to import the specific module
            module = __import__(tracker_module_name, fromlist=[tracker_class_name])
            tracker_class = getattr(module, tracker_class_name)
            
            print(f"Found dedicated module for {tracker_id}.")
        except (ImportError, AttributeError) as e:
            # If specific module not found, try to use the generic tracker
            try:
                from modules.upload.trackers.generic_tracker import GenericTracker
                tracker_class = GenericTracker
                print(f"No dedicated module for {tracker_id}, using GenericTracker.")
            except ImportError:
                print(f"Error: GenericTracker module not found. Please ensure it exists.")
                return
        
        # Create tracker instance
        try:
            tracker = tracker_class(config_dict)
        except Exception as e:
            print(f"Error creating tracker instance: {e}")
            return
        
        # Check if configured
        if hasattr(tracker, 'is_configured'):
            if not tracker.is_configured():
                print("Tracker is not properly configured. Please check your settings.")
                return
        
        print(f"Tracker configuration for {tracker_id} looks valid!")
        print("For a full connection test, upload a test torrent or")
        print("run the main tool with the --debug flag.")
        
    except Exception as e:
        print(f"Error testing tracker: {e}")
        print("Make sure you have the necessary tracker modules installed.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Configure trackers for Music-Upload-Assistant'
    )
    
    parser.add_argument('--list', '-l', action='store_true',
                      help='List configured trackers')
    parser.add_argument('--add', '-a', 
                      help='Add or update a tracker (e.g., YUS, SP, RED, etc.)')
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
        tracker_id = args.add.upper()
        
        # Handle specific trackers with dedicated setup functions
        if tracker_id == 'YUS':
            tracker_config = setup_yus_tracker(config_manager)
        else:
            # For any other tracker, use the generic setup function
            tracker_config = setup_generic_tracker(config_manager, tracker_id)
        
        if tracker_config:
            config_manager.set(f'trackers.{tracker_id}', tracker_config)
            print(f"{tracker_id} tracker configuration updated.")
    
    elif args.test:
        test_tracker(config_manager, args.test.upper())
    
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
        print("Use --add TRACKER_ID to add or update a tracker configuration")
        print("Use --test TRACKER_ID to test a tracker configuration")
    
    # Save the configuration
    if args.add or args.uploader:
        saved = config_manager.save()
        if saved:
            print("\nConfiguration saved successfully.")
        else:
            print("\nError saving configuration.")

if __name__ == "__main__":
    main()
