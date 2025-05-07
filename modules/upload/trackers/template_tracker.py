"""
Template tracker module for Music-Upload-Assistant.
Use this as a starting point for creating your own tracker implementations.
"""

import os
import requests
import logging
import json
from urllib.parse import urljoin
from typing import Dict, Any, Tuple, Optional

from modules.upload.trackers.generic_tracker import GenericTracker

logger = logging.getLogger(__name__)

class TemplateTracker(GenericTracker):
    """
    Template tracker implementation.
    Rename this class to match your tracker, e.g., MyTrackerTracker
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the tracker.
        
        Args:
            config: Main configuration dictionary
        """
        # Set your tracker ID here - should match the config key
        tracker_id = "TEMPLATE"
        
        # Initialize the base class with the tracker ID
        super().__init__(config, tracker_id)
        
        # Get tracker-specific configuration
        tracker_config = config.get('trackers', {}).get(tracker_id, {})
        
        # Configure tracker-specific settings
        self.api_auth_type = tracker_config.get('api_auth_type', 'bearer')  # 'bearer', 'token', 'param'
        self.api_format = tracker_config.get('api_format', 'json')  # 'json', 'form'
        
        # Add any other custom properties your tracker needs
        self.custom_setting = tracker_config.get('custom_setting', '')
        
        # Log configuration
        logger.info(f"[{tracker_id} CONFIG] Initialized with auth type: {self.api_auth_type}")
    
    def is_configured(self) -> bool:
        """
        Check if the tracker is properly configured.
        Override this if your tracker has specific requirements.
        
        Returns:
            bool: True if configured, False otherwise
        """
        # Call parent method first
        if not super().is_configured():
            return False
        
        # Add your own validation logic here, for example:
        # if not self.custom_setting:
        #     return False
        
        return True
    
    def _build_form_data(self, metadata: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Build form data for tracker upload.
        
        Args:
            metadata: Track or album metadata
            description: Release description
            
        Returns:
            dict: Form data for upload
        """
        # Get format type from metadata
        format_type = metadata.get('format', 'FLAC').upper()
        
        # Determine format ID based on tracker's requirements
        # First check if we have a mapping in the config
        format_id = self.format_ids.get(format_type)
        if not format_id:
            # Fallback values
            format_fallbacks = {
                'FLAC': '1',
                'MP3': '2',
                'AAC': '3'
                # Add more fallbacks as needed
            }
            format_id = format_fallbacks.get(format_type, '1')  # Default to FLAC (1) if not found
        
        # Determine category ID based on release type
        release_type = metadata.get('release_type', 'ALBUM').upper()
        category_id = self.cat_ids.get(release_type, self.cat_ids.get('ALBUM', '1'))
        
        # Create upload name
        upload_name = self._create_upload_name(metadata)
        
        # Build the form data
        data = {
            'name': upload_name,
            'description': description,
            'format_id': format_id,
            'category_id': category_id,
            'anonymous': "1" if self.anon else "0"
            # Add other fields required by your tracker
        }
        
        return data
    
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
            return False, f"{self.tracker_id} tracker not configured"
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
            
            # Log API key info
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
            
            return True, f"Debug mode: {self.tracker_id} upload simulation successful"
        
        # Prepare upload endpoint
        upload_url = self.upload_url
        
        # If URL doesn't look like a full API endpoint, construct it
        if not upload_url.startswith('http'):
            upload_url = urljoin(self.site_url, upload_url)
        
        # Prepare auth params and headers based on API auth type
        auth_params = {}
        auth_headers = {}
        
        if self.use_api and self.api_key:
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
                # Fallback to Bearer token
                auth_headers = {
                    'Authorization': f"Bearer {self.api_key}"
                }
                logger.info("Using default Bearer token authentication")
        else:
            # For non-API uploads, might need to login first
            logger.info("Using web form upload (non-API)")
        
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
            logger.info(f"Uploading torrent to {self.tracker_id} at {upload_url}")
            
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
                            message = result.get('message', f'{self.tracker_id} upload successful')
                            return True, message
                        elif 'message' in result:
                            return True, result['message']
            except Exception as e:
                logger.warning(f"Could not parse success response: {e}")
            
            # Default success
            return True, f"{self.tracker_id} upload successful"
            
        except Exception as e:
            # Close file handles on exception
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            
            logger.error(f"Exception during {self.tracker_id} upload: {e}")
            return False, f"Exception during {self.tracker_id} upload: {e}"
            
    def _handle_error_response(self, response) -> str:
        """
        Handle error responses from the tracker.
        Override this if your tracker has specific error formats.
        
        Args:
            response: Response object from request
            
        Returns:
            str: Error message
        """
        # Start with default error message
        error_message = f"{response.status_code} - {response.text[:200]}"
        
        # Try to parse JSON responses
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                data = response.json()
                if isinstance(data, dict):
                    # Different APIs use different keys for error messages
                    for key in ['error', 'message', 'error_message', 'msg', 'errorMsg']:
                        if key in data:
                            return f"{data[key]}"
                            
                    # Check for validation errors
                    if 'errors' in data and isinstance(data['errors'], dict):
                        errors = []
                        for field, msgs in data['errors'].items():
                            if isinstance(msgs, list):
                                errors.append(f"{field}: {', '.join(msgs)}")
                            else:
                                errors.append(f"{field}: {msgs}")
                        return f"Validation errors: {'; '.join(errors)}"
            except Exception as e:
                logger.warning(f"Could not parse JSON error response: {e}")
        
        return error_message