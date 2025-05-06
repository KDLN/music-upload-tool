import os
import time
import logging
import hashlib
from typing import Dict, Any, Union, List

try:
    import bencodepy
except ImportError:
    logging.getLogger(__name__).error(
        "bencodepy module not found. Please install it with 'pip install bencodepy'"
    )
    bencodepy = None

logger = logging.getLogger(__name__)

class TorrentCreator:
    """
    Creates .torrent files for music uploads.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.torrent_config = config.get('torrent', {})
        self.default_comment = self.torrent_config.get('comment', 'Created with Music-Upload-Assistant')
        self.default_source  = self.torrent_config.get('source', 'MUA')
        self.default_private = self.torrent_config.get('private', True)

    def create_torrent(self,
                       path: str,
                       announce_url: str = None,
                       source: str     = None,
                       comment: str    = None,
                       private: bool   = None,
                       created_by: str = None,
                       piece_size: Union[int, str] = None
    ) -> str:
        """
        Create a .torrent file for a music file or directory.
        """
        if not bencodepy:
            raise ImportError("bencodepy module is required for torrent creation")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        # Determine announce URL
        announce_url = (
            announce_url
            or self.torrent_config.get('announce_url')
            or self.config.get('announce_url')
        )
        if not announce_url:
            raise ValueError("Announce URL not specified")

        source     = source or self.default_source
        comment    = comment or self.default_comment
        private    = private if private is not None else self.default_private
        created_by = created_by or "Music-Upload-Assistant"

        # Calculate appropriate piece size
        if piece_size == 'auto' or piece_size is None:
            piece_size = self._calculate_piece_size(path)
        else:
            piece_size = int(piece_size) * 1024

        logger.info(f"Creating torrent for {path} with piece size {piece_size//1024}KB")

        # Build torrent metadata
        info = self._build_info_dict(path, piece_size)
        metainfo = {
            'announce':       announce_url,
            'info':           info,
            'creation date':  int(time.time()),
            'created by':     created_by,
            'comment':        comment
        }
        if source:
            metainfo['info']['source'] = source
        if private:
            metainfo['info']['private'] = 1

        # Generate output filename
        if os.path.isdir(path):
            base = os.path.basename(path) or os.path.basename(os.path.dirname(path))
        else:
            base = os.path.splitext(os.path.basename(path))[0]
        if not base or base == '.':
            base = f"album_{int(time.time())}"
        base = self._sanitize_filename(base)

        output_dir  = self.config.get('output_dir', os.path.dirname(path))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{base}.torrent")

        try:
            encoded = bencodepy.encode(metainfo)
            with open(output_path, 'wb') as f:
                f.write(encoded)
            logger.info(f"Torrent file created: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating torrent file: {e}")
            raise

    def create_tracker_specific_torrent(self,
                                       original_torrent_path: str,
                                       tracker_id: str,
                                       announce_url: str,
                                       source: str = None
    ) -> str:
        """
        Create a tracker-specific torrent from an existing torrent file.
        """
        if not bencodepy:
            raise ImportError("bencodepy module is required for torrent creation")
        try:
            with open(original_torrent_path, 'rb') as f:
                torrent_data = f.read()
            metainfo = bencodepy.decode(torrent_data)
            metainfo[b'announce'] = announce_url.encode()
            if source:
                metainfo[b'info'][b'source'] = source.encode()
            base_name = os.path.splitext(os.path.basename(original_torrent_path))[0]
            output_name = f"{base_name}[{tracker_id}].torrent"
            output_dir = os.path.dirname(original_torrent_path)
            output_path = os.path.join(output_dir, output_name)
            encoded = bencodepy.encode(metainfo)
            with open(output_path, 'wb') as f:
                f.write(encoded)
            logger.info(f"Tracker-specific torrent file created: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating tracker-specific torrent file: {e}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        invalid_chars = r'<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = filename.strip('. ')
        if not filename:
            filename = f"album_{int(time.time())}"
        return filename

    def _calculate_piece_size(self, path: str) -> int:
        total_size = 0
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    total_size += os.path.getsize(os.path.join(root, file))
        else:
            total_size = os.path.getsize(path)
        # Recommendations
        if total_size < 50*1024*1024:
            return 16*1024
        elif total_size < 150*1024*1024:
            return 32*1024
        elif total_size < 350*1024*1024:
            return 64*1024
        elif total_size < 512*1024*1024:
            return 128*1024
        elif total_size < 1*1024*1024*1024:
            return 256*1024
        elif total_size < 2*1024*1024*1024:
            return 512*1024
        elif total_size < 4*1024*1024*1024:
            return 1024*1024
        elif total_size < 8*1024*1024*1024:
            return 2*1024*1024
        else:
            return 4*1024*1024

    def _build_info_dict(self, path: str, piece_size: int) -> Dict[str, Any]:
        if os.path.isdir(path):
            return self._build_multi_file_info(path, piece_size)
        else:
            return self._build_single_file_info(path, piece_size)

    def _build_single_file_info(self, file_path: str, piece_size: int) -> Dict[str, Any]:
        file_size = os.path.getsize(file_path)
        pieces = self._calculate_pieces(file_path, piece_size)
        return {
            'name': file_path.split(os.sep)[-1],
            'length': file_size,
            'piece length': piece_size,
            'pieces': pieces
        }

    def _build_multi_file_info(self, dir_path: str, piece_size: int) -> Dict[str, Any]:
        name = os.path.basename(dir_path) or os.path.basename(os.path.dirname(dir_path))
        if not name or name == '.':
            name = f"album_{int(time.time())}"
        files = []
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                full = os.path.join(root, filename)
                rel = os.path.relpath(full, dir_path).split(os.sep)
                files.append({'length': os.path.getsize(full), 'path': rel})
        files.sort(key=lambda x: x['path'])
        pieces = self._calculate_pieces_for_files(dir_path, files, piece_size)
        return {'name': name, 'files': files, 'piece length': piece_size, 'pieces': pieces}

    def _calculate_pieces(self, file_path: str, piece_size: int) -> bytes:
        pieces = b""
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(piece_size)
                if not data:
                    break
                sha1.update(data)
                pieces += sha1.digest()
                sha1 = hashlib.sha1()
        return pieces

    def _calculate_pieces_for_files(self, base_dir: str, files: List[Dict[str, Any]], piece_size: int) -> bytes:
        pieces = b""
        piece_data = b""
        sha1 = hashlib.sha1()
        for fi in files:
            path = os.path.join(base_dir, *fi['path'])
            with open(path, 'rb') as f:
                while True:
                    need = piece_size - len(piece_data)
                    data = f.read(need)
                    if not data:
                        break
                    piece_data += data
                    if len(piece_data) == piece_size:
                        sha1.update(piece_data)
                        pieces += sha1.digest()
                        sha1 = hashlib.sha1()
                        piece_data = b""
        if piece_data:
            sha1.update(piece_data)
            pieces += sha1.digest()
        return pieces

# End of TorrentCreator
