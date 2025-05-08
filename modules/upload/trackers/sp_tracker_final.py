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
        # Set default cover field name for SP before creating parent
        tr_cfg = config.get('trackers', {}).get('SP', {})
        if 'cover_field_name' not in tr_cfg:
            # Set the default cover field name for SP
            if 'trackers' not in config:
                config['trackers'] = {}
            if 'SP' not in config['trackers']:
                config['trackers']['SP'] = {}
            config['trackers']['SP']['cover_field_name'] = 'torrent-cover'
        
        # Call parent constructor with updated config
        super().__init__(config, "SP")
        
        # Configure SP-specific settings
        self.api_auth_type = tr_cfg.get('api_auth_type', 'bearer')  # 'bearer', 'token', 'param'
        self.api_format = tr_cfg.get('api_format', 'json')  # 'json', 'form'
        
        # Specific endpoint configurations
        self.category_endpoint = tr_cfg.get('category_endpoint', '')
        self.format_endpoint = tr_cfg.get('format_endpoint', '')
        
        # Log configuration
        logger.info(f"[SP CONFIG] Initialized with API auth type: {self.api_auth_type}")
    
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
        
        # Try to auto-detect music content for better tracker compatibility
        is_music_content = metadata.get('format', '').upper() in ['FLAC', 'MP3', 'AAC', 'OGG', 'WAV', 'ALAC'] or \
                          'album' in metadata or 'release_type' in metadata
        
        # Get resolution ID (required by SP) - default to 'OTHER'
        tr_cfg = self.config.get('trackers', {}).get('SP', {})
        resolution_ids = tr_cfg.get('resolution_ids', {})
        resolution_id = resolution_ids.get('OTHER', '10')
        
        # Get category ID based on the release type or direct override
        # First check if a specific category_id is directly provided in metadata
        if 'category_id' in metadata:
            # Use the directly provided category ID
            category_id = metadata['category_id']
            logger.info(f"Using provided category_id: {category_id}")
        else:
            # Check the configured category IDs from the tracker config
            category_ids = tr_cfg.get('category_ids', {})
            
            if is_music_content and 'release_type' in metadata:
                # Use the category ID for the specific music release type
                release_type = metadata.get('release_type', 'ALBUM').upper()
                category_id = category_ids.get(release_type, '1')
                logger.info(f"Using category_id: {category_id} for {release_type} music content")
            else:
                # Fall back to default category (typically 1 for MOVIE)
                category_id = '1'
                logger.info(f"Using default category_id: {category_id}")
        
        # Create upload name, ensuring format matches actual file format
        upload_name = self._create_upload_name(metadata)
        if 'format_type' in locals() and format_type == 'FLAC' and ' MP3' in upload_name:
            upload_name = upload_name.replace(' MP3', ' FLAC')
            logger.info(f"Fixed format mismatch in release name: {upload_name}")
        
        # Build the form data based on SP's requirements
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
        
        # Build file payload using the generic method that handles cover field name
        files = self._build_file_payload(torrent_path, cover_path)
        
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
            
            # Check response status and content type for better error handling
            status_code = response.status_code
            logger.info(f"Upload response status code: {status_code}")
            
            # Close file handles
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            
            # Special validation error handling
            if not response.ok and status_code == 422:
                # Most likely a category or field validation error
                logger.error(f"Validation error detected! Response: {response.text[:200]}")
                
                # Get whether this is likely music content
                is_music_content = (
                    metadata.get('format', '').upper() in ['FLAC', 'MP3', 'AAC', 'OGG', 'WAV', 'ALAC'] or
                    'album' in metadata or 'release_type' in metadata
                )
                
                # Check for common issues
                if is_music_content and data.get('category_id') == '1':
                    logger.error("This appears to be a category validation error for music content.")
                    logger.error("The tracker may require a specific category ID for music uploads.")
                    logger.error("Try reconfiguring your tracker settings with 'python configure.py --add SP'")
                    logger.error("And set a different category ID for music content (often category ID 5)")
                    return False, "Validation Error: The tracker requires a different category ID for music content. Try setting category ID 5 for music uploads."
                
                # Check if the cover field name might be wrong
                cover_field = self.cover_field_name
                if cover_field != 'torrent-cover' and cover_path:
                    logger.error(f"The cover art field name '{cover_field}' may be incorrect for SP.")
                    logger.error("SP typically expects 'torrent-cover' as the field name.")
                    logger.error("Try reconfiguring with 'python configure.py --add SP' and set the cover field name to 'torrent-cover'")
                    return False, f"Validation Error: Cover art field name '{cover_field}' may be incorrect for SP. Try using 'torrent-cover'."
            
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
                            
                            # Suggest fixing category IDs if a category error is detected
                            if any('category' in field.lower() for field in error_data.get('errors', {}).keys()):
                                error_message += "\n\nThis appears to be a category validation issue. Try updating your category IDs in the configuration."
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
