"""
YU-Scene tracker implementation for Music-Upload-Assistant.
Handles authentication and uploads to the YU-Scene music tracker.
"""

import os
import logging
import requests
from typing import Dict, Optional, Any, List, Tuple

logger = logging.getLogger(__name__)

class YUSTracker:
    """
    Handles uploads to the YU-Scene tracker.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YUS tracker handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Get tracker config
        tracker_config = config.get('trackers', {}).get('YUS', {})
        
        self.name = tracker_config.get('name', 'YU-Scene')
        self.url = tracker_config.get('url', 'https://yu-scene.net')
        self.api_key = tracker_config.get('api_key')
        self.upload_url = tracker_config.get('upload_url')
        self.announce_url = tracker_config.get('announce_url')
        self.source_name = tracker_config.get('source_name', 'YuScene')
        self.debug_mode = config.get('debug', False)
        
        # Check if we have the required config
        if not self.api_key:
            logger.warning("API key not set for YUS tracker. Uploads will not be possible.")
        
        if not self.upload_url:
            logger.warning("Upload URL not set for YUS tracker. Uploads will not be possible.")
    
    def is_configured(self) -> bool:
        """
        Check if the tracker is properly configured.
        
        Returns:
            bool: True if configured, False otherwise
        """
        return bool(self.api_key and self.upload_url)
    
    def upload(self, torrent_path: str, description: str, metadata: Dict[str, Any],
              category: str = None, format_id: str = None, media: str = None) -> Tuple[bool, str]:
        """
        Upload a torrent to the tracker.
        
        Args:
            torrent_path: Path to the .torrent file
            description: Upload description
            metadata: File metadata
            category: Upload category
            format_id: Format identifier
            media: Media type
            
        Returns:
            tuple: (success, message)
        """
        if not self.is_configured():
            return False, "Tracker not properly configured"
        
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"
        
        # Prepare upload data
        upload_data = {
            'api_key': self.api_key,
            'title': metadata.get('album', 'Unknown Album'),
            'description': description,
            'anonymous': str(int(self.config.get('trackers', {}).get('YUS', {}).get('anon', False))),
        }
        
        # Set category
        tracker_config = self.config.get('trackers', {}).get('YUS', {})
        category_ids = tracker_config.get('category_ids', {})
        
        if category:
            upload_data['category'] = category
        elif metadata.get('release_type'):
            release_type = metadata['release_type'].upper()
            if release_type in category_ids:
                upload_data['category'] = category_ids[release_type]
            else:
                # Default to ALBUM
                upload_data['category'] = category_ids.get('ALBUM', '7')
        else:
            # Default to ALBUM
            upload_data['category'] = category_ids.get('ALBUM', '7')
        
        # Set format
        format_ids = tracker_config.get('format_ids', {})
        
        if format_id:
            upload_data['format'] = format_id
        elif metadata.get('format'):
            format_type = metadata['format'].upper()
            if format_type in format_ids:
                upload_data['format'] = format_ids[format_type]
        
        # Set media type
        if media:
            upload_data['media'] = media
        elif metadata.get('media'):
            upload_data['media'] = metadata['media']
        
        # Validate required fields
        required_fields = tracker_config.get('required_fields', [])
        for field in required_fields:
            if field not in upload_data and field not in metadata:
                return False, f"Missing required field: {field}"
        
        # Prepare files
        files = {
            'torrent': (os.path.basename(torrent_path), open(torrent_path, 'rb'), 'application/x-bittorrent')
        }
        
        # Add cover art if available
        if 'artwork_path' in metadata and os.path.exists(metadata['artwork_path']):
            files['cover'] = (os.path.basename(metadata['artwork_path']), 
                             open(metadata['artwork_path'], 'rb'), 'image/jpeg')
        
        # Check for debug mode
        if self.debug_mode:
            logger.info(f"Debug mode: Would upload to {self.upload_url} with data: {upload_data}")
            logger.info(f"Debug mode: Would include files: {list(files.keys())}")
            return True, "Debug mode: Upload simulation successful"
        
        # Perform the actual upload
        try:
            response = requests.post(self.upload_url, data=upload_data, files=files)
            
            # Check if the upload was successful
            if response.ok:
                logger.info(f"Successfully uploaded to {self.name}: {response.text}")
                return True, f"Successfully uploaded to {self.name}"
            else:
                logger.error(f"Error uploading to {self.name}: {response.status_code} - {response.text}")
                return False, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"Exception during upload to {self.name}: {str(e)}")
            return False, f"Exception during upload: {str(e)}"
        finally:
            # Close file handles
            for file in files.values():
                file[1].close()
    
    def check_duplicate(self, metadata: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if an upload would be a duplicate.
        
        Args:
            metadata: Metadata to check
            
        Returns:
            tuple: (is_duplicate, duplicate_url or None)
        """
        # In a real implementation, this would query the tracker API
        # For now, just simulate no duplicate
        return False, None


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Sample configuration
    config = {
        'trackers': {
            'YUS': {
                'name': 'YU-Scene',
                'url': 'https://yu-scene.net',
                'api_key': 'SAMPLE_API_KEY',
                'upload_url': 'https://yu-scene.net/api/torrents/upload',
                'announce_url': 'https://yu-scene.net/announce',
                'source_name': 'YuScene',
                'category_ids': {
                    'ALBUM': '7',
                    'SINGLE': '8',
                    'EP': '9'
                },
                'format_ids': {
                    'FLAC': '1',
                    'MP3': '2',
                    'AAC': '3'
                }
            }
        }
    }
    
    # Create the tracker handler
    tracker = YUSTracker(config)
    
    print(f"Tracker: {tracker.name}")
    print(f"Configured: {tracker.is_configured()}")
    
    # Test duplicate check with sample metadata
    metadata = {
        'album': 'Test Album',
        'album_artists': ['Test Artist'],
        'format': 'FLAC',
        'release_type': 'Album'
    }
    
    is_dupe, dupe_url = tracker.check_duplicate(metadata)
    print(f"Duplicate check: {is_dupe}")
    
    if len(sys.argv) > 1:
        # Test upload with supplied torrent file
        torrent_path = sys.argv[1]
        description = "Test upload description"
        
        success, message = tracker.upload(torrent_path, description, metadata)
        print(f"Upload result: {success}")
        print(f"Message: {message}")
