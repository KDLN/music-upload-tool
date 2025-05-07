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
        self.use_api = 'api' in self.upload_url.lower()
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

    def _get_csrf_token(self) -> str:
        """
        Get CSRF token from the site.
        
        Returns:
            str: CSRF token or empty string if not found
        """
        try:
            # First try to get it from the login page
            login_url = urljoin(self.site_url, '/login')
            logger.info(f"Getting CSRF token from {login_url}")
            response = self.session.get(login_url)
            
            if response.ok:
                csrf_match = re.search(r'name="_token"\s+value="([^"]+)"', response.text)
                if csrf_match:
                    return csrf_match.group(1)
                
            # If not found, try the upload page
            upload_page = urljoin(self.site_url, '/torrents/create')
            logger.info(f"Getting CSRF token from {upload_page}")
            response = self.session.get(upload_page)
            
            if response.ok:
                csrf_match = re.search(r'name="_token"\s+value="([^"]+)"', response.text)
                if csrf_match:
                    return csrf_match.group(1)
            
            # If we still can't find it, use the API key as a fallback
            logger.warning("No CSRF token found, using API key instead")
            return self.api_key
            
        except Exception as e:
            logger.error(f"Error getting CSRF token: {e}")
            return self.api_key

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
        
        # Determine category ID - default to ALBUM (7)
        release_type = metadata.get('release_type', 'ALBUM').upper()
        category_id = category or cat_ids.get(release_type, cat_ids.get('ALBUM', '7'))
        
        # Determine format ID - default to FLAC (1)
        format_type = metadata.get('format', 'FLAC').upper()
        type_id = format_id or format_ids.get(format_type, format_ids.get('FLAC', '1'))
        
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
        
        # Debug mode: just print what would happen
        if self.debug_mode:
            logger.info("=== DEBUG MODE API UPLOAD ===")
            logger.info("POST URL: %s", api_url)
            logger.info("PARAMS: %s", {'api_token': self.api_key})
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
                params={'api_token': self.api_key},
                data=data,
                files=files,
                timeout=60  # Give it more time for uploads
            )
            
            # Close file handles
            for _, f in files.items():
                f[1].close()
            
            if not response.ok:
                return False, f"{response.status_code} - {response.text[:200]}"
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
    
    def _upload_api(self, torrent_path: str, data: Dict[str, Any], files: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Upload using the API endpoint.
        """
        # Debug mode: just print what would happen
        if self.debug_mode:
            logger.info("=== DEBUG MODE API UPLOAD ===")
            logger.info("POST URL: %s", self.upload_url)
            logger.info("PARAMS: %s", {'api_token': self.api_key})
            logger.info("DATA: %s", data)
            logger.info("FILES: %s", list(files.keys()))
            # Close file handles
            for _, f in files.items():
                f[1].close()
            return True, "Debug mode: API upload simulation successful"
        
        # Real upload
        try:
            logger.info(f"Uploading torrent via API to {self.upload_url}")
            response = self.session.post(
                url=self.upload_url,
                params={'api_token': self.api_key},
                data=data,
                files=files,
                timeout=60  # Give it more time for uploads
            )
            
            # Close file handles
            for _, f in files.items():
                f[1].close()
            
            if not response.ok:
                return False, f"{response.status_code} - {response.text[:200]}"
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
    
    def _upload_web_form(self, torrent_path: str, data: Dict[str, Any], files: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Upload using the web form.
        """
        # Get CSRF token first
        csrf_token = self._get_csrf_token()
        data['_token'] = csrf_token
        
        # Determine upload URL
        if not self.upload_url or '/create' in self.upload_url:
            # If we have the create form URL, switch to the actual submission URL
            if '/create' in self.upload_url:
                upload_url = self.upload_url.replace('/create', '')
            else:
                # Default upload path
                upload_url = urljoin(self.site_url, '/torrents')
        else:
            upload_url = self.upload_url
        
        # Debug mode: just print what would happen
        if self.debug_mode:
            logger.info("=== DEBUG MODE WEB FORM UPLOAD ===")
            logger.info("POST URL: %s", upload_url)
            logger.info("CSRF Token: %s", csrf_token[:10] + '...')
            logger.info("DATA: %s", data)
            logger.info("FILES: %s", list(files.keys()))
            # Close file handles
            for _, f in files.items():
                f[1].close()
            return True, "Debug mode: web form upload simulation successful"
        
        # Real upload
        try:
            logger.info(f"Uploading torrent via web form to {upload_url}")
            
            # Add necessary headers
            headers = {
                'X-CSRF-TOKEN': csrf_token,
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Referer': upload_url
            }
            
            response = self.session.post(
                url=upload_url,
                headers=headers,
                data=data,
                files=files,
                allow_redirects=True,
                timeout=60  # Give it more time for uploads
            )
            
            # Close file handles
            for _, f in files.items():
                f[1].close()
            
            # Some sites respond with a redirect on success
            if response.history:
                logger.info(f"Request was redirected {len(response.history)} times")
                
            if not response.ok:
                return False, f"{response.status_code} - {response.text[:200]}"
            
            # Check for error messages in HTML response
            if 'error' in response.text.lower() or 'alert-danger' in response.text:
                error_match = re.search(r'class=["\']alert[^>]*>(.*?)</div', response.text, re.DOTALL)
                if error_match:
                    error_msg = error_match.group(1)
                    error_msg = re.sub(r'<[^>]*>', ' ', error_msg).strip()
                    return False, f"Upload failed: {error_msg}"
            
            return True, "Web form upload successful"
            
        except Exception as e:
            # Ensure files are closed on exception
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            logger.error(f"Exception during web form upload: {e}")
            return False, f"Exception during web form upload: {e}"
