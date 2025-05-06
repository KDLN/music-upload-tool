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
    
    def upload(self,
           torrent_path: str,
           description: str,
           metadata: Dict[str, Any],
           category: str = None,
           format_id: str = None,
           media: str = None
) -> Tuple[bool, str]:
        if not self.is_configured():
            return False, "Tracker not properly configured"
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"

        # Prepare upload data (api_key moves into header)
        upload_data = {
            'title':       metadata.get('album', 'Unknown Album'),
            'description': description,
            'anonymous':   str(int(self.config.get('trackers', {}).get('YUS', {}).get('anon', False))),
        }

        # Build YU‑Scene’s cat ID
        tracker_cfg = self.config.get('trackers', {}).get('YUS', {})
        cat_ids     = tracker_cfg.get('category_ids', {})

        if category:
            cat_value = category
        elif metadata.get('release_type'):
            rt = metadata['release_type'].upper()
            cat_value = cat_ids.get(rt, cat_ids.get('ALBUM', '7'))
        else:
            cat_value = cat_ids.get('ALBUM', '7')

        # *** HERE: use "cat" instead of "category" ***
        upload_data['cat'] = cat_value

        # Format & media (names usually match, but double‑check your site's form)
        fmt_ids = tracker_cfg.get('format_ids', {})
        if format_id:
            upload_data['format'] = format_id
        elif metadata.get('format'):
            f = metadata['format'].upper()
            if f in fmt_ids:
                upload_data['format'] = fmt_ids[f]

        if media:
            upload_data['media'] = media
        elif metadata.get('media'):
            upload_data['media'] = metadata['media']

        # Files
        files = {
            'torrent': (
                os.path.basename(torrent_path),
                open(torrent_path, 'rb'),
                'application/x-bittorrent'
            )
        }
        art = metadata.get('artwork_path')
        if art and os.path.exists(art):
            files['cover'] = (
                os.path.basename(art),
                open(art, 'rb'),
                'image/jpeg'
            )

        # Debug?
        if self.debug_mode:
            logger.info(f"Debug: upload to {self.upload_url} with {upload_data}")
            logger.info(f"Debug: files {list(files.keys())}")
            return True, "Debug simulation"

        # Real upload w/ header auth
        headers = {
            'User-Agent':    'Music-Upload-Assistant/0.1.0',
            'Authorization': f"Bearer {self.api_key}"
        }

        try:
            resp = requests.post(self.upload_url,
                                data=upload_data,
                                files=files,
                                headers=headers)
            if not resp.ok:
                msg = resp.text[:200]
                logger.error(f"Upload error {resp.status_code}: {msg}")
                return False, f"{resp.status_code} - {msg}"
            logger.info(f"Uploaded: {resp.text[:200]}")
            return True, "Upload successful"

        except Exception as e:
            logger.error(f"Upload exception: {e}")
            return False, f"Exception: {e}"

        finally:
            for _, ft in files.items():
                ft[1].close()


    
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
