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
        format_type = metadata.get('format', 'FLAC').upper()
        
        # Use hardcoded values for specific formats
        type_id = None
        if format_type == 'FLAC':
            type_id = '1'  # Adjust this for SP's actual FLAC format ID
            logger.info(f"Using hardcoded type_id: {type_id} for FLAC on SP")
        else:
            # Try to get from format_ids, or use fallback
            type_id = self.format_ids.get(format_type)
            if not type_id:
                format_fallbacks = {
                    'FLAC': '1',
                    'MP3': '2',
                    'AAC': '3'
                    # Add more as needed
                }
                type_id = format_fallbacks.get(format_type, '1')  # Default to FLAC (1) if not found
        
        # Get music category ID for SP - adjust as needed
        category_id = '1'  # Adjust this for SP's actual music category ID
        logger.info(f"Using category_id: {category_id} for music content on SP")
        
        # Create upload name, ensuring format matches actual file format
        upload_name = self._create_upload_name(metadata)
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
        
        # Add any SP-specific fields
        # data['sp_specific_field'] = 'value'
        
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
        
        # Build file payload
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
        
        # Prepare auth params and headers based on API auth type
        auth_params = {}
        auth_headers = {}
        
        # For SP tracker, we always include the API key regardless of use_api flag
        if self.api_key:
            # Choose authentication method based on config
            if self.api_auth_type == 'bearer':
                # Use Bearer token in Authorization header
                auth_headers = {
                    'Authorization': f"Bearer {self.api_key}"
                }
                logger.info("Using Bearer token authentication")
            elif self.api_auth_type == 'param':
                # Use API key as URL parameter
                auth_params = {'api_token': self.api_key}
                logger.info("Using URL parameter authentication")
            elif self.api_auth_type == 'token':
                # Use API key as a token parameter in form data
                data['api_token'] = self.api_key
                logger.info("Using form token authentication")
            else:
                # Add API key to form data by default for SP
                data['api_token'] = self.api_key
                logger.info("Adding API key to form data")
        else:
            # If no API key but we have username/password, might need to implement form login first
            logger.info("No API key available - form login may be required")
        
        # Set content type based on API format
        if self.api_format == 'json':
            auth_headers['Content-Type'] = 'application/json'
            # Convert data to JSON string for some APIs
            if files:
                logger.info("Using multipart upload with JSON data")
            else:
                # For JSON-only APIs with no files
                data = json.dumps(data)
                logger.info("Using JSON-only upload format")
        
        # Perform the upload
        try:
            logger.info(f"Uploading torrent to SP at {upload_url}")
            
            # Execute the upload request
            response = self.session.post(
                url=upload_url,
                params=auth_params,
                headers=auth_headers,
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
                error_message = self._handle_error_response(response)
                return False, error_message
            
            # Try to parse success response
            try:
                if 'application/json' in response.headers.get('Content-Type', ''):
                    result = response.json()
                    if isinstance(result, dict):
                        if 'success' in result and result['success']:
                            # Extract success message if available
                            message = result.get('message', 'SP upload successful')
                            return True, message
                        elif 'message' in result:
                            return True, result['message']
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