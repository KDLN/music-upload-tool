"""
YUS tracker module for Music-Upload-Tool.
Handles uploading to the YU-Scene tracker.
"""

import os
import requests
import logging
from urllib.parse import urljoin
from typing import Dict, Any, Tuple, Optional

from .base_tracker import BaseTracker

logger = logging.getLogger(__name__)

class YusTracker(BaseTracker):
    """YUS (YU-Scene) tracker implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the YUS tracker.
        
        Args:
            config: Main configuration dictionary
        """
        super().__init__(config, "YUS")
    
    def is_configured(self) -> bool:
        """
        Check if YUS tracker is properly configured.
        
        Returns:
            bool: True if configured, False otherwise
        """
        # YUS requires API key
        if not self.api_key:
            return False
        
        # Need upload URL or site URL to construct it
        if not (self.upload_url or self.site_url):
            return False
        
        return True
    
    def upload(self, torrent_path: str, description: str, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Upload a torrent to YUS tracker.
        
        Args:
            torrent_path: Path to torrent file
            description: Release description
            metadata: Track or album metadata
            
        Returns:
            tuple: (success, message)
        """
        # Check preconditions
        if not self.is_configured():
            return False, "YUS tracker not configured"
        
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"
        
        # Prepare cover art
        cover_path = self._prepare_cover_image(metadata)
        
        # Build form data
        data = self._build_form_data(metadata, description)
        
        # Build file payload
        files = self._build_file_payload(torrent_path, cover_path)
        
        # Debug mode: just print what would happen
        if self.debug_mode:
            logger.info("=== DEBUG MODE YUS UPLOAD ===")
            logger.info(f"POST URL: {self.upload_url}")
            logger.info(f"DATA: {data}")
            logger.info(f"FILES: {list(files.keys())}")
            
            # Close file handles
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            
            return True, "Debug mode: YUS upload simulation successful"
        
        # Use API endpoint
        api_url = self.upload_url
        
        # If the URL doesn't include 'api', automatically convert it to the API endpoint
        if '/api/' not in api_url.lower():
            # Construct proper API URL - usually /api/torrents/upload
            api_url = urljoin(self.site_url, '/api/torrents/upload')
            logger.info(f"Converting to API endpoint: {api_url}")
        
        # Prepare API parameters
        api_params = {
            'api_token': self.api_key
        }
        
        # Perform the upload
        try:
            logger.info(f"Uploading torrent via API to {api_url}")
            response = self.session.post(
                url=api_url,
                params=api_params,
                data=data,
                files=files,
                timeout=60  # Give it more time for uploads
            )
            
            # Close file handles
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            
            if not response.ok:
                error_message = f"{response.status_code} - {response.text[:200]}"
                
                # Try to parse the JSON error response
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_message = error_data['message']
                        
                        # If there are validation errors, show them in detail
                        if 'data' in error_data and isinstance(error_data['data'], dict):
                            for field, errors in error_data['data'].items():
                                if isinstance(errors, list):
                                    error_message += f"\n- {field}: {', '.join(errors)}"
                                else:
                                    error_message += f"\n- {field}: {errors}"
                except Exception as e:
                    logger.warning(f"Could not parse error response as JSON: {e}")
                
                return False, error_message
            
            return True, "API upload successful"
            
        except Exception as e:
            # Ensure files are closed on exception
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            logger.error(f"Exception during API upload: {e}")
            return False, f"Exception during API upload: {e}"
    
    def _build_form_data(self, metadata: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Build form data for YUS tracker upload.
        
        Args:
            metadata: Track or album metadata
            description: Release description
            
        Returns:
            dict: Form data for upload
        """
        # Determine category ID - hardcoded to 8 for Music
        category_id = self.cat_ids.get('ALBUM', '8')  # Default to 8 if not found
        logger.info(f"Using category_id: {category_id} for music content")
        
        # Determine format ID - default to FLAC (16)
        format_type = metadata.get('format', 'FLAC').upper()
        
        # For FLAC files, always use type_id 16
        if format_type == 'FLAC':
            type_id = '16'
            logger.info(f"Using type_id: 16 for FLAC content")
        else:
            # Try to get format ID from config
            type_id = self.format_ids.get(format_type, '16')  # Default to FLAC if not found
        
        # Create upload name
        upload_name = self._create_upload_name(metadata)
        
        # Fix format mismatch if present (e.g., MP3 in name but FLAC in files)
        if format_type == 'FLAC' and ' MP3' in upload_name:
            upload_name = upload_name.replace(' MP3', ' FLAC')
            logger.info(f"Fixed format mismatch in release name: {upload_name}")
        
        # Build the form data
        data = {
            'name': upload_name,
            'description': description,
            'category_id': category_id,
            'type_id': type_id,
            'anonymous': "1" if self.anon else "0"
        }
        
        return data