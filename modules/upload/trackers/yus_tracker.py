import os
import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class YUSTracker:
    def __init__(self, config: Dict[str, Any]):
        self.config     = config
        tr_cfg          = config.get('trackers', {}).get('YUS', {})
        self.api_key    = tr_cfg.get('api_key', '')
        # We always greet the create form
        self.create_url = "https://yu-scene.net/torrents/create"
        self.session    = requests.Session()
        self.debug_mode = config.get('debug', False)

    def is_configured(self) -> bool:
        return bool(self.api_key)

        async def upload(self,
                     torrent_path: str,
                     description: str,
                     metadata: Dict[str, Any],
                     category: str = None,
                     format_id: str = None,
                     media: str = None
    ) -> Tuple[bool, str]:
            if not os.path.exists(torrent_path):
                return False, f"Torrent file not found: {torrent_path}"
            tracker_cfg = self.config['trackers']['YUS']
            api_key     = tracker_cfg['api_key'].strip()

            # 2) Prepare core form‐fields
            #    Field names taken from Audionut’s working script
            data = {
                'name':           metadata.get('album', 'Unknown Album'),
                'description':    description,
                'mediainfo':      open(metadata.get('mediainfo_path', ''), 'r', encoding='utf-8').read()
                                    if metadata.get('mediainfo_path') else '',
                'bdinfo':         '',  # if you have a BD summary file, read it here
                'category_id':    category or tracker_cfg.get('category_ids', {}).get(
                                    metadata.get('release_type','ALBUM').upper(), '7'
                                ),
                'type_id':        format_id   or tracker_cfg.get('format_ids', {}).get(
                                    metadata.get('format','').upper(), '0'
                                ),
                'resolution_id':  media       or tracker_cfg.get('resolution_ids', {}).get(
                                    metadata.get('resolution','1080p'), '2'
                                ),
                # Any other fields you need—e.g. tmdb/imdb if you track those:
                # 'tmdb': metadata.get('tmdb_id', ''),
                # 'imdb': metadata.get('imdb_id', ''),
                # …
                'anonymous':      int(metadata.get('anonymous', False)),
                'personal_release': int(metadata.get('personalrelease', False)),
                # add freeleech, sticky, etc. if desired:
                'free':           0,
                'doubleup':       0,
                'sticky':         0,
            }

            # 3) Open files
            files = {
                'torrent': (
                    os.path.basename(torrent_path),
                    open(torrent_path, 'rb'),
                    'application/x-bittorrent'
                )
            }
            # optional cover art
            art = metadata.get('artwork_path')
            if art and os.path.exists(art):
                files['cover'] = (
                    os.path.basename(art),
                    open(art, 'rb'),
                    'image/jpeg'
                )

            # 4) Debug simulation
            if metadata.get('debug') or self.config.get('debug'):
                logger.info("=== DEBUG MODE ===")
                logger.info("POST URL: %s", self.upload_url)
                logger.info("PARAMS: %s", {'api_token': api_key})
                logger.info("DATA keys: %s", list(data.keys()))
                logger.info("FILES keys: %s", list(files.keys()))
                # close file handles
                for f in files.values():
                    f[1].close()
                return True, "Debug mode: upload simulation successful"

            # 5) Real upload
            try:
                response = requests.post(
                    url=self.upload_url,
                    params={'api_token': api_key},
                    data=data,
                    files=files,
                    headers={'User-Agent': 'Music-Upload-Assistant/1.0'}
                )
                # close files
                for f in files.values():
                    f[1].close()

                if not response.ok:
                    return False, f"{response.status_code} - {response.text[:200]}"

                # Optionally parse JSON reply:
                # resp_data = response.json()
                return True, "Upload successful"

            except Exception as e:
                # ensure files get closed on exception
                for f in files.values():
                    try: f[1].close()
                    except: pass
                logger.error("Exception during upload: %s", e)
                return False, f"Exception during upload: {e}"
