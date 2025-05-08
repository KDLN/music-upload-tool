#!/usr/bin/env python3
"""
Configuration utility for Music-Upload-Tool.
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
logger = logging.getLogger("music-upload-tool-config")

def setup_tracker(config_manager: ConfigManager, tracker_id: str) -> Dict[str, Any]:
    """
    Set up tracker configuration interactively.
    
    Args:
        config_manager: ConfigManager instance
        tracker_id: Tracker identifier (e.g., 'YUS')
        
    Returns:
        dict: Updated tracker configuration
    """
    print(f"\n=== {tracker_id} Tracker Configuration ===")
    
    # Get current configuration if exists
    tracker_config = config_manager.get(f'trackers.{tracker_id}', {})
    
    # Get tracker name
    tracker_name = tracker_config.get('name', '')
    if not tracker_name:
        print(f"Enter the full name of the tracker (e.g., YU-Scene): ", end='')
        tracker_name = input().strip()
        if not tracker_name:
            tracker_name = tracker_id
    
    # Set defaults if not already configured
    if not tracker_config:
        base_url = input(f"Enter the base URL for {tracker_id} (e.g., https://yu-scene.net): ").strip()
        
        if not base_url:
            if tracker_id == 'YUS':
                base_url = "https://yu-scene.net"
            else:
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
    
    # API Key - FIXED: Ensure this properly asks for input and confirms when entered
    current_api_key = tracker_config.get('api_key', '')
    masked_key = "****" if current_api_key else "Not set"
    print(f"API Key [{masked_key}]: ", end='')
    api_key = input().strip()  # Changed from getpass to regular input for visibility
    if api_key:
        tracker_config['api_key'] = api_key
        print(f"API Key set to: {api_key[:4]}{'*' * (len(api_key) - 4) if len(api_key) > 4 else ''}")
    else:
        print(f"API Key unchanged: {masked_key}")
    
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
    
    # Would you like to configure category IDs?
    print("\nWould you like to configure category IDs? (y/n): ", end='')
    if input().strip().lower() in ['y', 'yes']:
        category_ids = tracker_config.get('category_ids', {})
        
        if tracker_id == 'YUS':
            # Default YUS category IDs
            print("Using default YUS category IDs")
            category_ids['ALBUM'] = '8'
            category_ids['SINGLE'] = '9'
            category_ids['EP'] = '9'
            category_ids['COMPILATION'] = '8'
            category_ids['SOUNDTRACK'] = '8'
            category_ids['LIVE'] = '8'
        elif tracker_id == 'SP':
            # Default SP category IDs from SP.py
            print("Using default SP category IDs")
            category_ids['MOVIE'] = '1'
            category_ids['TV'] = '2'
            category_ids['ANIME'] = '6'
            category_ids['SPORTS'] = '8'
            category_ids['BOXSET'] = '13'
            
            # Add music categories with default values
            # Since SP doesn't have specific music categories, we'll map to MOVIE (1)
            print("\nNote: SP doesn't have specific music categories. Using category 1 (MOVIE) for music.")
            category_ids['ALBUM'] = '1'
            category_ids['SINGLE'] = '1'
            category_ids['EP'] = '1'
            category_ids['COMPILATION'] = '1'
            category_ids['SOUNDTRACK'] = '1'
            category_ids['LIVE'] = '1'
            
            # Ask if they want to customize these
            print("\nWould you like to customize music category mappings? (y/n): ", end='')
            if input().strip().lower() in ['y', 'yes']:
                categories = ['ALBUM', 'SINGLE', 'EP', 'COMPILATION', 'SOUNDTRACK', 'LIVE']
                for category in categories:
                    current_id = category_ids.get(category, '1')
                    print(f"  {category} ID [{current_id}]: ", end='')
                    cat_id = input().strip()
                    if cat_id:
                        category_ids[category] = cat_id
                        print(f"    → Set {category} to category ID: {cat_id}")
                
                # Display a summary after all categories are configured
                print("\nMusic category mappings configured:")
                for category in categories:
                    print(f"  {category}: {category_ids.get(category, '1')}")
        else:
            print("Enter category IDs (press enter to skip):")
            
            categories = ['ALBUM', 'SINGLE', 'EP', 'COMPILATION', 'SOUNDTRACK', 'LIVE']
            for category in categories:
                current_id = category_ids.get(category, '')
                print(f"  {category} ID [{current_id}]: ", end='')
                cat_id = input().strip()
                if cat_id:
                    category_ids[category] = cat_id
        
        tracker_config['category_ids'] = category_ids
    
    # Would you like to configure format IDs?
    print("\nWould you like to configure format IDs? (y/n): ", end='')
    format_input = input().strip().lower()
    if format_input in ['y', 'yes']:
        format_ids = tracker_config.get('format_ids', {})
        
        if tracker_id == 'YUS':
            # Default YUS format IDs
            print("Using default YUS format IDs")
            format_ids['FLAC'] = '16'
            format_ids['MP3'] = '2'
            format_ids['AAC'] = '3'
            format_ids['OGG'] = '6'
            format_ids['WAV'] = '9'
        elif tracker_id == 'SP':
            # Default SP format IDs from SP.py
            print("Using default SP format IDs")
            format_ids['DISC'] = '1'
            format_ids['REMUX'] = '2'
            format_ids['ENCODE'] = '3'
            format_ids['WEBDL'] = '4'
            format_ids['WEBRIP'] = '5'
            format_ids['HDTV'] = '6'
            
            # Map music formats to video formats
            print("\nNote: SP doesn't have specific music format IDs. Mapping to video formats:")
            format_ids['FLAC'] = '1'  # Map to DISC
            format_ids['MP3'] = '3'   # Map to ENCODE
            format_ids['AAC'] = '3'   # Map to ENCODE
            format_ids['ALAC'] = '3'  # Map to ENCODE
            format_ids['OGG'] = '3'   # Map to ENCODE
            format_ids['WAV'] = '3'   # Map to ENCODE
            
            # Ask if they want to customize these
            print("\nWould you like to customize music format mappings? (y/n): ", end='')
            if input().strip().lower() in ['y', 'yes']:
                formats = ['FLAC', 'MP3', 'AAC', 'ALAC', 'OGG', 'WAV']
                print("Available SP format IDs: DISC=1, REMUX=2, ENCODE=3, WEBDL=4, WEBRIP=5, HDTV=6")
                for format_type in formats:
                    current_id = format_ids.get(format_type, '3')
                    print(f"  {format_type} ID [{current_id}]: ", end='')
                    fmt_id = input().strip()
                    if fmt_id:
                        format_ids[format_type] = fmt_id
            
            # Add resolution IDs for SP
            resolution_ids = tracker_config.get('resolution_ids', {})
            resolution_ids.update({
                '4320p': '1',
                '2160p': '2',
                '1080p': '3',
                '1080i': '4',
                '720p': '5',
                '576p': '6',
                '576i': '7',
                '480p': '8',
                '480i': '9',
                'OTHER': '10'
            })
            tracker_config['resolution_ids'] = resolution_ids
            
            # Add API configuration for SP
            if 'api_auth_type' not in tracker_config:
                tracker_config['api_auth_type'] = 'param'
            if 'api_format' not in tracker_config:
                tracker_config['api_format'] = 'form'
            
            print("\nSP API configuration:")
            print(f"  API Auth Type: {tracker_config['api_auth_type']}")
            print(f"  API Format: {tracker_config['api_format']}")
        else:
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
    
    # Configure cover art field name
    current_cover_field = tracker_config.get('cover_field_name', 'image')
    print(f"\nCover art field name [{current_cover_field}]: ", end='')
    if tracker_id == 'SP':
        print("torrent-cover (recommended for SP)")
    else:
        print("")
    
    cover_field = input().strip()
    if cover_field:
        tracker_config['cover_field_name'] = cover_field
        print(f"Cover art field name set to: {cover_field}")
    elif tracker_id == 'SP' and current_cover_field == 'image':
        # Set default recommended value for SP
        tracker_config['cover_field_name'] = 'torrent-cover'
        print(f"Cover art field name set to default for SP: torrent-cover")
    
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
    
    # Check required fields
    required_fields = ['api_key', 'upload_url', 'announce_url']
    missing_fields = [field for field in required_fields if not tracker_config.get(field)]
    
    if missing_fields:
        print(f"Missing required fields: {', '.join(missing_fields)}")
        return
    
    # Try to import the tracker module
    try:
        # Try to import specific tracker module
        tracker_name = f"{tracker_id.lower()}_tracker"
        import_path = f"modules.upload.trackers.{tracker_name}"  # Updated path to modules.upload.trackers
        
        try:
            module = __import__(import_path, fromlist=[''])
            print(f"Found tracker module: {import_path}")
            
            # Look for tracker class
            class_name = None
            if tracker_id == 'YUS':
                class_name = 'YusTracker'
            else:
                class_name = f"{tracker_id.capitalize()}Tracker"
            
            if hasattr(module, class_name):
                print(f"Found tracker class: {class_name}")
                
                # Try to instantiate the tracker
                tracker_class = getattr(module, class_name)
                tracker = tracker_class({'trackers': {tracker_id: tracker_config}})
                
                if tracker.is_configured():
                    print(f"Tracker {tracker_id} is properly configured.")
                else:
                    print(f"Tracker {tracker_id} is not properly configured.")
            else:
                print(f"Tracker class {class_name} not found in module {import_path}")
        except ImportError:
            print(f"Tracker module {import_path} not found.")
            print("You may need to create the tracker module first.")
        
    except Exception as e:
        print(f"Error testing tracker: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Configure Music-Upload-Tool'
    )
    
    parser.add_argument('--list', '-l', action='store_true',
                      help='List configured trackers')
    parser.add_argument('--add', '-a', 
                      help='Add or update a tracker (e.g., YUS)')
    parser.add_argument('--test', '-t', 
                      help='Test a tracker configuration')
    parser.add_argument('--config', '-c',
                      help='Path to config file (default: config.json)')
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
        tracker_config = setup_tracker(config_manager, tracker_id)
        
        if tracker_config:
            config_manager.set(f'trackers.{tracker_id}', tracker_config)
            print(f"{tracker_id} tracker configuration updated.")
    
    elif args.test:
        test_tracker(config_manager, args.test)
    
    else:
        # If no command specified, show current config status
        uploader_name = config_manager.get('uploader_name', 'Not set')
        trackers = config_manager.get('trackers', {})
        
        print("\n=== Music-Upload-Tool Configuration ===")
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
        
        print("\nCommands:")
        print("  --list (-l): List configured trackers")
        print("  --add (-a) TRACKER_ID: Add or update a tracker")
        print("  --test (-t) TRACKER_ID: Test a tracker configuration")
        print("  --uploader (-u) NAME: Set uploader name")
    
    # Save the configuration
    if args.add or args.uploader:
        saved = config_manager.save()
        if saved:
            print("\nConfiguration saved successfully.")
        else:
            print("\nError saving configuration.")

if __name__ == "__main__":
    main()
