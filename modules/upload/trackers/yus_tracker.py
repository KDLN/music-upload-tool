import os
import requests
import logging
import shutil
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class YUSTracker:
    def __init__(self, config):
        self.config = config  # Store the entire config for later use
        tr_cfg = config.get('trackers', {}).get('YUS', {})
        self.api_key    = tr_cfg.get('api_key', '').strip()
        self.upload_url = tr_cfg.get('upload_url','').strip()

        logger.info(f"[YUS CONFIG] api_key={'SET' if self.api_key else 'MISSING'}, "
                    f"upload_url={self.upload_url or 'MISSING'}")

        # For debug simulation
        self.debug_mode  = config.get('debug', False)

        # Create a session for connection reuse
        self.session     = requests.Session()
        self.session.headers.update({
            'User-Agent': f"Music-Upload-Assistant/{config.get('app_version','0.1.0')}"
        })

    def is_configured(self) -> bool:
        """
        Returns True if api_key and upload_url are present.
        """
        return bool(self.api_key and self.upload_url)

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
        Upload a torrent file + metadata to Yu‑Scene via their JSON API.
        """
        # Preconditions
        if not self.is_configured():
            return False, "Tracker not configured"
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"

        # Build form‐data fields
        tr_cfg    = self.config['trackers']['YUS']
        cat_ids   = tr_cfg.get('category_ids', {})
        type_ids  = tr_cfg.get('type_ids', {})
        res_ids   = tr_cfg.get('resolution_ids', {})

        # Create proper name for upload
        # Use release_name if available or generate a standard name
        if 'release_name' in metadata:
            upload_name = metadata['release_name']
        else:
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

        # Build upload data
        data = {
            'name':           upload_name,
            'description':    description,
            'category_id':    category or cat_ids.get(
                                  metadata.get('release_type','ALBUM').upper(),
                                  cat_ids.get('ALBUM','7')
                              ),
            'type_id':        format_id or type_ids.get(
                                  metadata.get('format','').upper(),
                                  type_ids.get('FLAC','16')
                              ),
            'resolution_id':  media or res_ids.get(
                                  metadata.get('resolution','1080p').upper(),
                                  res_ids.get('1080P','3')
                              ),
            'anonymous':      int(metadata.get('anonymous', False)),
            'personal_release': int(metadata.get('personalrelease', False)),
            # You can add more flags here if needed (e.g. free, doubleup, sticky)
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
                    
                files['cover'] = (
                    os.path.basename(cover_path),
                    cover_file_handle,
                    mime_type
                )
                logger.info(f"Added cover art to tracker upload request: {cover_path}")
            except Exception as e:
                logger.error(f"Error adding cover to upload: {e}")
                if cover_file_handle:
                    cover_file_handle.close()

        # Debug mode: just print what would happen
        if self.debug_mode:
            logger.info("=== DEBUG MODE ===")
            logger.info("POST URL: %s", self.upload_url)
            logger.info("PARAMS: %s", {'api_token': self.api_key})
            logger.info("DATA: %s", data)
            logger.info("FILES: %s", list(files.keys()))
            # Close file handles
            for _, f in files.items():
                f[1].close()
            return True, "Debug mode: upload simulation successful"

        # Perform the real upload
        try:
            # Determine if we're using the API or the web form
            is_api = 'api' in self.upload_url.lower()
            
            logger.info(f"Uploading torrent to {self.upload_url} with name: {upload_name}")
            
            # If using API endpoint
            if is_api:
                response = self.session.post(
                    url     = self.upload_url,
                    params  = {'api_token': self.api_key},
                    data    = data,
                    files   = files
                )
            # If using web form endpoint
            else:
                # For web form, add token to the form data
                data['_token'] = self.api_key
                response = self.session.post(
                    url     = self.upload_url,
                    data    = data,
                    files   = files
                )
            # Close file handles
            for _, f in files.items():
                f[1].close()

            if not response.ok:
                return False, f"{response.status_code} - {response.text[:200]}"
            return True, "Upload successful"

        except Exception as e:
            # Ensure files are closed on exception
            for _, f in files.items():
                try:
                    f[1].close()
                except:
                    pass
            logger.error("Exception during upload: %s", e)
            return False, f"Exception during upload: {e}"
