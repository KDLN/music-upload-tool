import os
import requests
import logging
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

        data = {
            'name':           metadata.get('album', 'Unknown Album'),
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
        art = metadata.get('artwork_path')
        if art and os.path.exists(art):
            files['cover'] = (
                os.path.basename(art),
                open(art, 'rb'),
                'image/jpeg'
            )

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
            response = self.session.post(
                url     = self.upload_url,
                params  = {'api_token': self.api_key},
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
