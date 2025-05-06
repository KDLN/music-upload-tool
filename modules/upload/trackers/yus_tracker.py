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

    def upload(self,
               torrent_path: str,
               description: str,
               metadata: Dict[str, Any],
               category: str = None,
               format_id: str = None,
               media: str = None
    ) -> Tuple[bool, str]:
        # Preconditions
        if not self.is_configured():
            return False, "Tracker not configured"
        if not os.path.exists(torrent_path):
            return False, f"Torrent not found: {torrent_path}"

        # 1) GET the form
        resp_form = self.session.get(self.create_url)
        if not resp_form.ok:
            return False, f"Failed to fetch form: {resp_form.status_code}"

        # 2) Parse CSRF token + form action
        soup = BeautifulSoup(resp_form.text, 'html.parser')
        form = soup.find('form', id='upload-form')
        if not form:
            return False, "Upload form not found in HTML"
        action_url = form['action']  # e.g. "/torrents"
        token = form.find('input', {'name': '_token'})['value']

        # Build absolute POST URL
        if action_url.startswith('http'):
            post_url = action_url
        else:
            post_url = f"https://yu-scene.net{action_url}"

        # 3) Build form data
        data = {
            '_token':      token,
            'title':       metadata.get('album', 'Unknown Album'),
            'description': description,
            'anonymous':   str(int(self.config['trackers']['YUS'].get('anon', False))),
        }

        # Category → must match <select name="cat">
        cat_ids = self.config['trackers']['YUS'].get('category_ids', {})
        if category:
            data['cat'] = category
        elif metadata.get('release_type'):
            rt = metadata['release_type'].upper()
            data['cat'] = cat_ids.get(rt, cat_ids.get('ALBUM', '7'))
        else:
            data['cat'] = cat_ids.get('ALBUM', '7')

        # Format (name="format")
        fmt_ids = self.config['trackers']['YUS'].get('format_ids', {})
        if format_id:
            data['format'] = format_id
        elif metadata.get('format'):
            f = metadata['format'].upper()
            if f in fmt_ids:
                data['format'] = fmt_ids[f]

        # Media (name="media")
        if media:
            data['media'] = media
        elif metadata.get('media'):
            data['media'] = metadata['media']

        # 4) Prepare files
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

        # Debug simulation
        if self.debug_mode:
            logger.info(f"DEBUG: POST to {post_url} data={list(data.keys())} files={list(files.keys())}")
            return True, "Debug: would POST upload"

        # 5) POST with cookies + CSRF
        headers = {'User-Agent': 'Music-Upload-Assistant/0.1.0'}
        try:
            resp = self.session.post(post_url, data=data, files=files, headers=headers)
            if not resp.ok:
                logger.error(f"Upload failed {resp.status_code}: {resp.text[:200]}")
                return False, f"{resp.status_code} - {resp.text[:200]}"
            return True, "Upload successful"
        finally:
            for f in files.values():
                f[1].close()
