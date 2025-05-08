"""
SP tracker module for Music-Upload-Assistant.
Handles uploading to the SP tracker.
"""

import os
import requests
import logging
import json
from urllib.parse import urljoin
from typing import Dict, Any, Tuple, Optional

from modules.upload.trackers.generic_tracker import GenericTracker

logger = logging.getLogger(__name__)

class SPTracker(GenericTracker):
    """Tracker implementation for SP."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SP tracker.
        
        Args:
            config: Main configuration dictionary
        """
        super().__init__(config, "SP")
        
        # Get SP-specific configuration
        sp_config = config.get('trackers', {}).get('SP', {})
        
        # Configure SP-specific settings
        self.api_auth_type = sp_config.get('api_auth_type', 'bearer')  # 'bearer', 'token', 'param'
        self.api_format = sp_config.get('api_format', 'json')  # 'json', 'form'
        
        # Specific endpoint configurations
        self.category_endpoint = sp_config.get('category_endpoint', '')
        self.format_endpoint = sp_config.get('format_endpoint', '')
        
        # Log configuration
        logger.info(f"[SP CONFIG] Initialized with API auth type: {self.api_auth_type}")
    
    def is_configured(self) -> bool:
        """
        Check if the SP tracker is properly configured.
        
        Returns:
            bool: True if configured, False otherwise
        """
        # For SP tracker, we only need an API key and upload URL
        if not self.api_key:
            return False
        
        if not (self.upload_url or self.site_url):
            return False
            
        # If we have an API key and a URL, we're good to go
        return True
    
    def _build_form_data(self, metadata: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Build form data for SP tracker upload.
        
        Args:
            metadata: Track or album metadata
            description: Release description
            
        Returns:
            dict: Form data for upload
        """
        # Get format type and create proper type_id
        # First check if type_id is directly provided in metadata
        if 'type_id' in metadata:
            # Use the directly provided type ID
            type_id = metadata['type_id']
            logger.info(f"Using provided type_id: {type_id} on SP")
        else:
            # Otherwise determine based on format
            format_type = metadata.get('format', 'FLAC').upper()
            
            # Get format ID based on SP's requirements
            tr_cfg = self.config.get('trackers', {}).get('SP', {})
            format_ids = tr_cfg.get('format_ids', {})
            type_id = format_ids.get(format_type, '1')  # Default to 1 (DISC) if not found
            logger.info(f"Using type_id: {type_id} for format: {format_type} on SP")
        
        # Get resolution ID (required by SP) - default to 'OTHER'
        resolution_ids = tr_cfg.get('resolution_ids', {})
        resolution_id = resolution_ids.get('OTHER', '10')
        
        # Get category ID based on the release type (album, single, etc.)
        # First check if a specific category_id is directly provided in metadata
        if 'category_id' in metadata:
            # Use the directly provided category ID
            category_id = metadata['category_id']
            logger.info(f"Using provided category_id: {category_id} for music content on SP")
        else:
            # Otherwise check the configured category IDs from the tracker config
            release_type = metadata.get('release_type', 'ALBUM').upper()
            tr_cfg = self.config.get('trackers', {}).get('SP', {})
            category_ids = tr_cfg.get('category_ids', {})
            
            # Use the category ID for the release type, defaulting to '1' (MOVIE) if not found
            category_id = category_ids.get(release_type, '1')  
            logger.info(f"Using category_id: {category_id} for {release_type} music content on SP")
        
        # Create upload name, ensuring format matches actual file format
        upload_name = self._create_upload_name(metadata)
        if format_type == 'FLAC' and ' MP3' in upload_name:
            upload_name = upload_name.replace(' MP3', ' FLAC')
            logger.info(f"Fixed format mismatch in release name: {upload_name}")
        
        # Build the form data based on SP.py requirements
        data = {
            'name': upload_name,
            'description': description,
            'category_id': category_id,
            'type_id': type_id,
            'resolution_id': resolution_id,
            'tmdb': '0',  # Required field but not relevant for music
            'imdb': '0',  # Required field but not relevant for music
            'tvdb': '0',  # Required field but not relevant for music
            'mal': '0',   # Required field but not relevant for music
            'igdb': '0',  # Required field but not relevant for music
            'anonymous': "1" if self.anon else "0",
            'stream': '0',  # No stream for music 
            'sd': '0',      # Not SD content
            'keywords': metadata.get('genres', []) if isinstance(metadata.get('genres', []), list) else [],
            'personal_release': '0',
            'internal': '0',
            'featured': '0',
            'free': '0',
            'doubleup': '0',
            'sticky': '0'
        }
        
        # Try to get mediainfo if available
        if 'mediainfo_path' in metadata and os.path.exists(metadata['mediainfo_path']):
            try:
                with open(metadata['mediainfo_path'], 'r', encoding='utf-8') as f:
                    data['mediainfo'] = f.read()
            except Exception as e:
                logger.error(f"Error reading mediainfo: {e}")
        
        # Extract available metadata fields
        if 'album' in metadata:
            # For SP, add album info to description or keywords
            album = metadata.get('album', '')
            if album and 'keywords' in data and isinstance(data['keywords'], list):
                data['keywords'].append(album)
                
        return data
    
    def upload(self,
               torrent_path: str,
               description: str,
               metadata: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Upload a torrent to the SP tracker.
        
        Args:
            torrent_path: Path to torrent file
            description: Release description
            metadata: Track or album metadata
            
        Returns:
            tuple: (success, message)
        """
        # Preconditions
        if not self.is_configured():
            return False, "SP tracker not configured"
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"
        
        # Prepare cover art
        cover_path = self._prepare_cover_image(metadata)
        
        # Build form data
        data = self._build_form_data(metadata, description)
        
        # Build file payload - SP expects only the torrent file
        files = {
            'torrent': (
                os.path.basename(torrent_path),
                open(torrent_path, 'rb'),
                'application/x-bittorrent'
            )
        }
        
        # Add cover image if available
        if cover_path and os.path.exists(cover_path):
            files['image'] = (
                os.path.basename(cover_path),
                open(cover_path, 'rb'),
                'image/jpeg' if cover_path.lower().endswith('.jpg') or cover_path.lower().endswith('.jpeg') else 'image/png'
            )
            logger.info(f"Added cover art to tracker upload request: {cover_path}")
        
        # Debug mode: just print what would happen
        if self.debug_mode:
            logger.info("=== DEBUG MODE SP UPLOAD ===")
            logger.info(f"POST URL: {self.upload_url}")
            
            # Log API key or token info if present
            if self.api_key:
                logger.info(f"API Token: {self.api_key[:4]}****")
            
            logger.info(f"DATA: {data}")
            logger.info(f"FILES: {list(files.keys())}")
            
            # Close file handles
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            
            return True, "Debug mode: SP upload simulation successful"
        
        # Prepare upload endpoint
        upload_url = self.upload_url
        
        # If URL doesn't look like a full API endpoint, construct it
        if not upload_url.startswith('http'):
            upload_url = urljoin(self.site_url, upload_url)
        
        # Add API token as URL parameter (following SP.py example)
        params = {
            'api_token': self.api_key.strip()
        }
        
        # Set User-Agent header according to SP.py example
        headers = {
            'User-Agent': f'Music-Upload-Tool/{self.config.get("app_version", "1.0.0")}'
        }
        
        # Perform the upload
        try:
            logger.info(f"Uploading torrent to SP at {upload_url}")
            logger.info(f"Request data: {data}")
            logger.info(f"Request files: {list(files.keys())}")
            logger.info(f"Request params: {params}")
            
            # Execute the upload request with params and form data
            response = self.session.post(
                url=upload_url,
                params=params,
                headers=headers,
                data=data,
                files=files,
                timeout=60
            )
            
            # Close file handles
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            
            # Process the response
            if not response.ok:
                # Try to parse error response as JSON
                try:
                    error_data = response.json()
                    logger.error(f"API error response: {error_data}")
                    
                    if 'message' in error_data:
                        error_message = error_data['message']
                        # If there are validation errors, include them in detail
                        if 'errors' in error_data:
                            logger.error(f"Validation errors: {error_data['errors']}")
                            for field, errors in error_data['errors'].items():
                                if isinstance(errors, list):
                                    error_message += f"\n- {field}: {', '.join(errors)}"
                                else:
                                    error_message += f"\n- {field}: {errors}"
                        return False, error_message
                except Exception:
                    # Fallback to generic error handling
                    error_message = self._handle_error_response(response)
                    return False, error_message
            
            # Try to parse success response
            try:
                if 'application/json' in response.headers.get('Content-Type', ''):
                    result = response.json()
                    if isinstance(result, dict):
                        # Check for various success indicators
                        if 'success' in result and result['success']:
                            # Extract success message if available
                            message = result.get('message', 'SP upload successful')
                            # If there's a data field with a torrent ID, include it
                            if 'data' in result:
                                message += f" - Torrent ID: {result['data']}"
                            return True, message
                        elif 'message' in result:
                            return True, result['message']
                        elif 'data' in result:
                            return True, f"SP upload successful - {result['data']}"
            except Exception as e:
                logger.warning(f"Could not parse success response: {e}")
            
            # Default success
            return True, "SP upload successful"
            
        except Exception as e:
            # Close file handles on exception
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            
            logger.error(f"Exception during SP upload: {e}")
            return False, f"Exception during SP upload: {e}"