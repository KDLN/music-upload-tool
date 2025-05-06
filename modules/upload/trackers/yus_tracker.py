import os
import requests
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class YUSTracker:
    def __init__(self, config: Dict[str, Any]):
        # Pull YUS settings from your main config
        tr_cfg = config.get('trackers', {}).get('YUS', {})
        self.config     = config

        # Your API key for header auth
        self.api_key = tr_cfg.get('api_key', '')

        # Base URL for the site (default to yu‑scene.net)
        self.base_url = tr_cfg.get('base_url', 'https://yu-scene.net').rstrip('/')

        # POST to the UI form endpoint, not /api
        self.upload_url = f"{self.base_url}/torrents/create"

        # HTTP session + debug flag
        self.session    = requests.Session()
        self.debug_mode = config.get('debug', False)

    def is_configured(self) -> bool:
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

        # Prepare form fields (API key goes in header)
        upload_data = {
            'title':       metadata.get('album', 'Unknown Album'),
            'description': description,
            'anonymous':   str(int(self.config.get('trackers', {}).get('YUS', {}).get('anon', False))),
        }

        # Determine 'cat' value
        tr_cfg      = self.config['trackers']['YUS']
        cat_ids     = tr_cfg.get('category_ids', {})
        if category:
            cat_value = category
        elif metadata.get('release_type'):
            rt = metadata['release_type'].upper()
            cat_value = cat_ids.get(rt, cat_ids.get('ALBUM', '7'))
        else:
            cat_value = cat_ids.get('ALBUM', '7')
        upload_data['cat'] = cat_value

        # Determine format field
        fmt_ids = tr_cfg.get('format_ids', {})
        if format_id:
            upload_data['format'] = format_id
        elif metadata.get('format'):
            f = metadata['format'].upper()
            if f in fmt_ids:
                upload_data['format'] = fmt_ids[f]

        # Determine media field
        if media:
            upload_data['media'] = media
        elif metadata.get('media'):
            upload_data['media'] = metadata['media']

        # Prepare files
        files = {
            'torrent': (
                os.path.basename(torrent_path),
                open(torrent_path, 'rb'),
                'application/x-bittorrent'
            )
        }
        art_path = metadata.get('artwork_path')
        if art_path and os.path.exists(art_path):
            files['cover'] = (
                os.path.basename(art_path),
                open(art_path, 'rb'),
                'image/jpeg'
            )

        # Debug simulation
        if self.debug_mode:
            logger.info(f"Debug: upload to {self.upload_url} with {upload_data}")
            logger.info(f"Debug: files {list(files.keys())}")
            return True, "Debug mode: Upload simulation successful"

        # Real upload with header auth
        headers = {
            'User-Agent':    'Music-Upload-Assistant/0.1.0',
            'Authorization': f"Bearer {self.api_key}"
        }

        try:
            response = self.session.post(
                self.upload_url,
                data=upload_data,
                files=files,
                headers=headers
            )
            if not response.ok:
                msg = response.text[:200]
                logger.error(f"Upload error {response.status_code}: {msg}")
                return False, f"{response.status_code} - {msg}"

            logger.info(f"Uploaded successfully: {response.text[:200]}")
            return True, "Upload successful"

        except Exception as e:
            logger.error(f"Upload exception: {e}")
            return False, f"Exception during upload: {e}"

        finally:
            for _, filetuple in files.items():
                filetuple[1].close()
