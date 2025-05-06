import os
import requests
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class YUSTracker:
    def __init__(self, config: Dict[str, Any]):
        # Save full config
        self.config     = config
        tr_cfg          = config.get('trackers', {}).get('YUS', {})

        # API key goes in URL params
        self.api_key    = tr_cfg.get('api_key', '').strip()

        # Endpoint that Audionut’s working script uses
        self.upload_url = 'https://yu-scene.net/api/torrents/upload'

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
        """
        Synchronous upload() matching the call from music_upload_assistant.
        Uses api_token in params, form-data for fields, and files for the .torrent.
        """
        # 1) Preconditions
        if not self.is_configured():
            return False, "Tracker not configured"
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"

        # 2) Core form fields
        tracker_cfg = self.config['trackers']['YUS']
        data = {
            'name':         metadata.get('album', 'Unknown Album'),
            'description':  description,
            'category_id':  category or tracker_cfg.get('category_ids', {}).get(
                                metadata.get('release_type','ALBUM').upper(), '7'),
            'type_id':      format_id or tracker_cfg.get('format_ids', {}).get(
                                metadata.get('format','').upper(), '0'),
            'resolution_id': media or tracker_cfg.get('resolution_ids', {}).get(
                                metadata.get('resolution','1080p'), '2'),
            'anonymous':     int(metadata.get('anonymous', False)),
            'personal_release': int(metadata.get('personalrelease', False)),
            # add any extra flags like free/doubleup/etc if you need them
        }

        # 3) Files payload
        files = {
            'torrent': (
                os.path.basename(torrent_path),
                open(torrent_path, 'rb'),
                'application/x-bittorrent'
            )
        }
        art = metadata.get('artwork_path')
        if art and os.path.exists(art):
            files['cover'] = (
                os.path.basename(art),
                open(art, 'rb'),
                'image/jpeg'
            )

        # 4) Debug simulation
        if self.debug_mode:
            logger.info("=== DEBUG MODE ===")
            logger.info("POST URL: %s", self.upload_url)
            logger.info("PARAMS: %s", {'api_token': self.api_key})
            logger.info("DATA keys: %s", list(data.keys()))
            logger.info("FILES keys: %s", list(files.keys()))
            for _, f in files.items():
                f[1].close()
            return True, "Debug mode: upload simulation successful"

        # 5) Real upload
        try:
            resp = requests.post(
                url    = self.upload_url,
                params = {'api_token': self.api_key},
                data   = data,
                files  = files,
                headers= {'User-Agent': 'Music-Upload-Assistant/1.0'}
            )
            # close file handles
            for _, f in files.items():
                f[1].close()

            if not resp.ok:
                return False, f"{resp.status_code} - {resp.text[:200]}"
            return True, "Upload successful"

        except Exception as e:
            # ensure files get closed on exception
            for _, f in files.items():
                try: f[1].close()
                except: pass
            logger.error("Exception during upload: %s", e)
            return False, f"Exception during upload: {e}"
