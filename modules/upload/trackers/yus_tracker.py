import os
import requests
import logging
import shutil
import re
import time
from urllib.parse import urljoin
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class YUSTracker:
    def __init__(self, config):
        self.config = config  # Store the entire config for later use
        tr_cfg = config.get('trackers', {}).get('YUS', {})
        self.api_key = tr_cfg.get('api_key', '').strip()
        self.upload_url = tr_cfg.get('upload_url', '').strip()
        self.announce_url = tr_cfg.get('announce_url', '').strip()
        self.site_url = tr_cfg.get('url', 'https://yu-scene.net').strip()
        self.use_api = True  # Always use API
        self.anon = bool(tr_cfg.get('anon', False))

        logger.info(f"[YUS CONFIG] api_key={'SET' if self.api_key else 'MISSING'}, "
                   f"upload_url={self.upload_url or 'MISSING'}, "
                   f"site_url={self.site_url}, "
                   f"use_api={self.use_api}")

        # For debug simulation
        self.debug_mode = config.get('debug', False)

        # Create a session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f"Music-Upload-Assistant/{config.get('app_version','0.2.0')}",
            'Referer': self.site_url,
            'Origin': self.site_url
        })

    def is_configured(self) -> bool:
        """
        Returns True if API key and either upload_url or site_url are present.
        """
        return bool(self.api_key and (self.upload_url or self.site_url))

    def _prepare_cover_image(self, metadata: Dict[str, Any]) -> str:
        """
        Prepare cover image for upload by finding and possibly converting image file.
        
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

    def upload(self,
               torrent_path: str,
               description: str,
               metadata: Dict[str, Any],
               category: str = None,
               format_id: str = None,
               media: str = None
    ) -> Tuple[bool, str]:
        """
        Upload a torrent file + metadata to Yu‑Scene via their API.
        """
        # Preconditions
        if not self.is_configured():
            return False, "Tracker not configured"
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"

        # Build form‐data fields
        tr_cfg = self.config.get('trackers', {}).get('YUS', {})
        cat_ids = tr_cfg.get('category_ids', {})
        format_ids = tr_cfg.get('format_ids', {})
        
        # Determine category ID - hardcoded to 8 for Music
        category_id = '8'  # Music category
        logger.info(f"Using hardcoded category_id: {category_id} for music content")
        
        # Determine format ID - default to FLAC (1)
        format_type = metadata.get('format', 'FLAC').upper()
        
        # Log available format IDs for debugging
        logger.info(f"Available format IDs: {format_ids}")
        logger.info(f"Format type: {format_type}")
        
        # First try to get the format ID from the format_ids mapping
        type_id = format_id or format_ids.get(format_type)
        
        # If not found, use a hardcoded fallback based on common YU-Scene format IDs
        if not type_id:
            format_fallbacks = {
                'FLAC': '16',  # Updated to 16 for FLAC
                'MP3': '2',
                'AAC': '3',
                'AC3': '4',
                'DTS': '5',
                'OGG': '6',
                'ALAC': '7',
                'DSD': '8',
                'WAV': '9',
                'MQA': '10'
            }
            type_id = format_fallbacks.get(format_type, '16')  # Default to FLAC (16) if not found
            
        logger.info(f"Using type_id: {type_id} for format: {format_type}")
        
        # Create proper name for upload
        if 'release_name' in metadata:
            upload_name = metadata['release_name']
        else:
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

        # Build common form data
        data = {
            'name': upload_name,
            'description': description,
            'category_id': category_id,
            'type_id': type_id,
            'anonymous': "1" if self.anon else "0"
        }
        
        # Prepare the file payload
        files = {
            'torrent': (
                os.path.basename(torrent_path),
                open(torrent_path, 'rb'),
                'application/x-bittorrent'
            )
        }
        
        # Prepare cover art for upload
        cover_path = self._prepare_cover_image(metadata)
        
        # Add cover file to upload if found
        cover_file_handle = None
        if cover_path and os.path.exists(cover_path):
            try:
                cover_file_handle = open(cover_path, 'rb')
                mime_type = 'image/jpeg'  # Default to jpeg
                if cover_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif cover_path.lower().endswith('.gif'):
                    mime_type = 'image/gif'
                    
                files['image'] = (  # Most API endpoints use 'image' as the field name
                    os.path.basename(cover_path),
                    cover_file_handle,
                    mime_type
                )
                logger.info(f"Added cover art to tracker upload request: {cover_path}")
            except Exception as e:
                logger.error(f"Error adding cover to upload: {e}")
                if cover_file_handle:
                    cover_file_handle.close()
        
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
        
        # Debug all the API request details
        logger.info(f"API URL: {api_url}")
        logger.info(f"API Token: {self.api_key[:4]}****")
        logger.info(f"Category ID: {category_id} for release type: {release_type}")
        logger.info(f"Type ID: {type_id} for format: {format_type}")
        logger.info(f"Upload Name: {upload_name}")
        
        # Debug mode: just print what would happen
        if self.debug_mode:
            logger.info("=== DEBUG MODE API UPLOAD ===")
            logger.info("POST URL: %s", api_url)
            logger.info("PARAMS: %s", api_params)
            logger.info("DATA: %s", data)
            logger.info("FILES: %s", list(files.keys()))
            # Close file handles
            for _, f in files.items():
                f[1].close()
            return True, "Debug mode: API upload simulation successful"
        
        # Real upload
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
                f[1].close()
            
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
