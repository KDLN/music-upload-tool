"""
Generic tracker module for Music-Upload-Assistant.
Base class for implementing common tracker functionality.
"""

import os
import requests
import logging
import shutil
import json
from urllib.parse import urljoin
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class GenericTracker:
    """Base class for tracker implementations."""
    
    def __init__(self, config: Dict[str, Any], tracker_id: str):
        """
        Initialize the tracker.
        
        Args:
            config: Main configuration dictionary
            tracker_id: Tracker identifier
        """
        self.config = config  # Store the entire config for later use
        self.tracker_id = tracker_id
        tr_cfg = config.get('trackers', {}).get(tracker_id, {})
        
        # Basic configuration
        self.api_key = tr_cfg.get('api_key', '').strip()
        self.username = tr_cfg.get('username', '').strip()
        self.password = tr_cfg.get('password', '').strip()
        self.upload_url = tr_cfg.get('upload_url', '').strip()
        self.announce_url = tr_cfg.get('announce_url', '').strip()
        self.site_url = tr_cfg.get('url', '').strip()
        self.use_api = bool(tr_cfg.get('use_api', 'api' in self.upload_url.lower()))
        self.anon = bool(tr_cfg.get('anon', False))
        
        # Get tracker-specific settings
        self.cat_ids = tr_cfg.get('category_ids', {})
        self.format_ids = tr_cfg.get('format_ids', {})
        
        # Debug mode
        self.debug_mode = config.get('debug', False)
        
        # Set up HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f"Music-Upload-Assistant/{config.get('app_version', '0.2.0')}",
            'Referer': self.site_url,
            'Origin': self.site_url
        })
        
        # Log configuration
        self._log_config()
    
    def _log_config(self):
        """Log tracker configuration for debugging."""
        logger.info(f"[{self.tracker_id} CONFIG] " 
                   f"api_key={'SET' if self.api_key else 'MISSING'}, "
                   f"username={'SET' if self.username else 'MISSING'}, "
                   f"upload_url={self.upload_url or 'MISSING'}, "
                   f"site_url={self.site_url or 'MISSING'}, "
                   f"use_api={self.use_api}")
    
    def is_configured(self) -> bool:
        """
        Check if the tracker is properly configured.
        
        Returns:
            bool: True if configured, False otherwise
        """
        # Basic validation - subclasses may override for specific requirements
        
        # First check for API key - most trackers use this even for non-API endpoints
        if not self.api_key:
            # If no API key, check for username/password (for traditional form logins)
            if not (self.username and self.password):
                return False
        
        # We need at least one URL to work with
        if not (self.upload_url or self.site_url):
            return False
        
        return True
    
    def _prepare_cover_image(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Prepare cover image for upload.
        
        Args:
            metadata: Track or album metadata
            
        Returns:
            str: Path to prepared cover image or None if not found
        """
        cover_path = None
        
        # Check for paths to artwork in this priority order
        possible_paths = [
            metadata.get('artwork_path'),
            metadata.get('cover_art_path')
        ]
        
        # Find first valid path
        for path in possible_paths:
            if path and os.path.exists(path):
                cover_path = path
                break
        
        if not cover_path:
            logger.warning("No cover image found in metadata")
            return None
            
        # Create a temporary directory for cover preparation if needed
        temp_dir = os.path.join(self.config.get('temp_dir', 'temp'), 'cover_prep')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Copy and ensure proper format for tracker
        try:
            # Prepare image file
            output_path = os.path.join(temp_dir, "cover.jpg")
            
            # Simple file copy for now
            # In the future could add resizing/conversion using PIL if needed
            shutil.copy2(cover_path, output_path)
            logger.info(f"Prepared cover image for upload: {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error preparing cover image: {e}")
            return cover_path  # Return original path as fallback
    
    def _create_upload_name(self, metadata: Dict[str, Any]) -> str:
        """
        Create a standardized upload name.
        
        Args:
            metadata: Track or album metadata
            
        Returns:
            str: Formatted upload name
        """
        if 'release_name' in metadata:
            return metadata['release_name']
        
        # Generate a standard name
        album = metadata.get('album', 'Unknown Album')
        artist = ""
        if 'album_artists' in metadata and metadata['album_artists']:
            if isinstance(metadata['album_artists'], list):
                artist = metadata['album_artists'][0]
            else:
                artist = metadata['album_artists'] 
        elif 'artists' in metadata and metadata['artists']:
            if isinstance(metadata['artists'], list):
                artist = metadata['artists'][0]
            else:
                artist = metadata['artists']
        
        year = metadata.get('year', '')
        format_type = metadata.get('format', 'FLAC')
        
        upload_name = f"{artist} - {album}"
        if year:
            upload_name += f" ({year})"
        upload_name += f" {format_type}"
        
        return upload_name
    
    def _build_form_data(self, metadata: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Build form data for the tracker upload.
        
        Args:
            metadata: Track or album metadata
            description: Release description
            
        Returns:
            dict: Form data for upload
        """
        # This is just a template - subclasses should override
        return {
            'name': self._create_upload_name(metadata),
            'description': description,
            'anonymous': "1" if self.anon else "0"
        }
    
    def _build_file_payload(self, torrent_path: str, cover_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Build file payload for the tracker upload.
        
        Args:
            torrent_path: Path to torrent file
            cover_path: Path to cover image
            
        Returns:
            dict: Files for upload
        """
        files = {
            'torrent': (
                os.path.basename(torrent_path),
                open(torrent_path, 'rb'),
                'application/x-bittorrent'
            )
        }
        
        # Add cover file to upload if found
        if cover_path and os.path.exists(cover_path):
            try:
                cover_file_handle = open(cover_path, 'rb')
                mime_type = 'image/jpeg'  # Default to jpeg
                if cover_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif cover_path.lower().endswith('.gif'):
                    mime_type = 'image/gif'
                    
                files['image'] = (  # Most trackers use 'image' as the field name
                    os.path.basename(cover_path),
                    cover_file_handle,
                    mime_type
                )
                logger.info(f"Added cover art to tracker upload request: {cover_path}")
            except Exception as e:
                logger.error(f"Error adding cover to upload: {e}")
                if 'cover_file_handle' in locals():
                    cover_file_handle.close()
        
        return files
    
    def upload(self,
               torrent_path: str,
               description: str,
               metadata: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Upload a torrent to the tracker.
        
        Args:
            torrent_path: Path to torrent file
            description: Release description
            metadata: Track or album metadata
            
        Returns:
            tuple: (success, message)
        """
        # Preconditions
        if not self.is_configured():
            return False, f"Tracker {self.tracker_id} not configured"
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
            logger.info(f"=== DEBUG MODE {self.tracker_id} UPLOAD ===")
            logger.info(f"POST URL: {self.upload_url}")
            logger.info(f"DATA: {data}")
            logger.info(f"FILES: {list(files.keys())}")
            # Close file handles
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            return True, f"Debug mode: {self.tracker_id} upload simulation successful"
        
        # Actual upload - subclasses should implement this
        logger.warning(f"Generic upload not implemented for {self.tracker_id}")
        
        # Close file handles before returning
        for _, f in files.items():
            try:
                f[1].close()
            except:
                pass
        
        return False, "Upload not implemented in generic tracker"
    
    def _handle_error_response(self, response) -> str:
        """
        Handle error responses from the tracker.
        
        Args:
            response: Response object from request
            
        Returns:
            str: Error message
        """
        error_message = f"{response.status_code} - {response.text[:200]}"
        
        # Try to parse JSON responses
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                data = response.json()
                if isinstance(data, dict):
                    if 'error' in data:
                        error_message = data['error']
                    elif 'message' in data:
                        error_message = data['message']
            except Exception as e:
                logger.warning(f"Could not parse JSON error response: {e}")
        
        return error_message
