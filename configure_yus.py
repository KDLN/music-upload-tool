#!/usr/bin/env python3
"""
YUS Tracker Configuration Utility for Music-Upload-Assistant.
This script updates the YUS tracker configuration with the correct format and category IDs.
"""

import os
import sys
import json
import logging

# Import the ConfigManager
from modules.utils.config_manager import ConfigManager

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("yus-config")

def update_yus_config():
    """
    Update YUS tracker configuration with correct format and category IDs.
    """
    # Create a config manager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Check if YUS tracker configuration exists
    if 'trackers' not in config or 'YUS' not in config['trackers']:
        logger.error("YUS tracker not configured. Run 'python configure_tracker.py --add YUS' first.")
        return False
    
    # Get YUS tracker configuration
    yus_config = config['trackers']['YUS']
    
    # Update format IDs
    if 'format_ids' not in yus_config:
        yus_config['format_ids'] = {}
    
    # Set FLAC format ID to 16
    yus_config['format_ids']['FLAC'] = '16'
    
    # Update category IDs
    if 'category_ids' not in yus_config:
        yus_config['category_ids'] = {}
    
    # Set ALBUM category ID to 8
    yus_config['category_ids']['ALBUM'] = '8'
    
    # Save the configuration
    config['trackers']['YUS'] = yus_config
    config_manager.save()
    
    logger.info("YUS tracker configuration updated with correct format and category IDs:")
    logger.info(f"- Format ID for FLAC: {yus_config['format_ids']['FLAC']}")
    logger.info(f"- Category ID for ALBUM: {yus_config['category_ids']['ALBUM']}")
    
    return True

if __name__ == "__main__":
    success = update_yus_config()
    
    if success:
        print("\nYUS tracker configuration updated successfully.")
        print("You can now use the following command to upload music files:")
        print("python music_upload_assistant.py /path/to/album --album --create-torrent --tracker YUS --upload")
    else:
        print("\nFailed to update YUS tracker configuration.")
        print("Make sure you've configured the YUS tracker first:")
        print("python configure_tracker.py --add YUS")
