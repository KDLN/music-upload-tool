"""
URL manager module for Music-Upload-Tool.
Handles URL building and category mapping for trackers.
"""

import os
import logging
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class UrlManager:
    """Manages URL building and category mapping for trackers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the URL manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
    
    def get_upload_url(self, tracker_id: str) -> Optional[str]:
        """
        Get the upload URL for a tracker.
        Constructs the URL if not fully specified.
        
        Args:
            tracker_id: Tracker identifier
            
        Returns:
            str: Upload URL or None if not configured
        """
        tr_cfg = self.config.get('trackers', {}).get(tracker_id, {})
        
        # Get upload URL from config
        upload_url = tr_cfg.get('upload_url', '').strip()
        
        # If it's a full URL, use it
        if upload_url and (upload_url.startswith('http://') or upload_url.startswith('https://')):
            return upload_url
        
        # If it's a path, construct with base URL
        if upload_url and not (upload_url.startswith('http://') or upload_url.startswith('https://')):
            site_url = tr_cfg.get('url', '').strip()
            if site_url:
                return urljoin(site_url, upload_url)
        
        # If no upload URL, try to construct a default based on tracker
        site_url = tr_cfg.get('url', '').strip()
        if site_url:
            if tracker_id == 'YUS':
                return urljoin(site_url, '/api/torrents/upload')
            # Add more trackers as needed
        
        logger.warning(f"Could not determine upload URL for tracker {tracker_id}")
        return None
    
    def get_category_id(self, tracker_id: str, category_type: str) -> Optional[str]:
        """
        Get category ID for a tracker and category type.
        
        Args:
            tracker_id: Tracker identifier
            category_type: Category type (e.g., 'ALBUM', 'SINGLE')
            
        Returns:
            str: Category ID or None if not found
        """
        tr_cfg = self.config.get('trackers', {}).get(tracker_id, {})
        category_ids = tr_cfg.get('category_ids', {})
        
        # Try to get category ID
        category_id = category_ids.get(category_type.upper())
        
        # If not found, use default mappings
        if not category_id:
            if tracker_id == 'YUS':
                defaults = {
                    'ALBUM': '8',
                    'SINGLE': '9',
                    'EP': '9',
                    'COMPILATION': '8'
                }
                category_id = defaults.get(category_type.upper())
            # Add more trackers as needed
        
        if not category_id:
            logger.warning(f"No category ID found for {tracker_id} and type {category_type}")
        
        return category_id
    
    def get_format_id(self, tracker_id: str, format_type: str) -> Optional[str]:
        """
        Get format ID for a tracker and format type.
        
        Args:
            tracker_id: Tracker identifier
            format_type: Format type (e.g., 'FLAC', 'MP3')
            
        Returns:
            str: Format ID or None if not found
        """
        tr_cfg = self.config.get('trackers', {}).get(tracker_id, {})
        format_ids = tr_cfg.get('format_ids', {})
        
        # Try to get format ID
        format_id = format_ids.get(format_type.upper())
        
        # If not found, use default mappings
        if not format_id:
            if tracker_id == 'YUS':
                defaults = {
                    'FLAC': '16',
                    'MP3': '2',
                    'AAC': '3',
                    'WAV': '9'
                }
                format_id = defaults.get(format_type.upper())
            # Add more trackers as needed
        
        if not format_id:
            logger.warning(f"No format ID found for {tracker_id} and format {format_type}")
        
        return format_id
    
    def build_download_url(self, tracker_id: str, torrent_id: str) -> Optional[str]:
        """
        Build a download URL for a tracker and torrent ID.
        
        Args:
            tracker_id: Tracker identifier
            torrent_id: Torrent ID from upload response
            
        Returns:
            str: Download URL or None if not possible
        """
        tr_cfg = self.config.get('trackers', {}).get(tracker_id, {})
        site_url = tr_cfg.get('url', '').strip()
        
        if not site_url or not torrent_id:
            return None
        
        # Build URL based on tracker
        if tracker_id == 'YUS':
            return urljoin(site_url, f'/torrents/{torrent_id}')
        # Add more trackers as needed
        
        return None