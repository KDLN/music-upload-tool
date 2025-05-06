"""
Torrent creator module for Music-Upload-Assistant.
Handles creating .torrent files for music uploads.
"""

import os
import math
import time
import logging
import hashlib
from typing import Dict, List, Union, Optional, Any, BinaryIO

logger = logging.getLogger(__name__)

try:
    import bencodepy
except ImportError:
    logger.error("bencodepy module not found. Please install it with 'pip install bencodepy'")
    bencodepy = None

class TorrentCreator:
    """
    Creates .torrent files for music uploads.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the torrent creator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.torrent_config = config.get('torrent', {})
        self.default_comment = self.torrent_config.get('comment', 'Created with Music-Upload-Assistant')
        self.default_source = self.torrent_config.get('source', 'MUA')
        self.default_private = self.torrent_config.get('private', True)
    
        def create_torrent(self, path: str, announce_url: str = None, 
                       source: str = None, comment: str = None, 
                       private: bool = None, created_by: str = None,
                       piece_size: Union[int, str] = None) -> str:
            if not bencodepy:
                raise ImportError("bencodepy module is required for torrent creation")
                
            # Check if path exists
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path not found: {path}")
            
            # Determine announce URL, checking CLI first,
            # then the torrent section of config, then top‑level announce_url
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
                # Convert to bytes
                piece_size = int(piece_size) * 1024
            
            logger.info(f"Creating torrent for {path} with piece size {piece_size / 1024}KB")
            
            # Build torrent metadata
            info = self._build_info_dict(path, piece_size)
            
            # Create the metainfo dictionary
            metainfo = {
                'announce':       announce_url,
                'info':           info,
                'creation date':  int(time.time()),
                'created by':     created_by,
                'comment':        comment
            }
            
            # Add source if provided
            if source:
                metainfo['info']['source'] = source
            
            # Add private flag if requested
            if private:
                metainfo['info']['private'] = 1
            
            # Generate output filename
            if os.path.isdir(path):
                base_name = os.path.basename(path) or os.path.basename(os.path.dirname(path))
            else:
                base_name = os.path.splitext(os.path.basename(path))[0]
            
            if not base_name or base_name == ".":
                base_name = f"album_{int(time.time())}"
            
            base_name   = self._sanitize_filename(base_name)
            output_name = f"{base_name}.torrent"
            output_dir  = self.config.get('output_dir', os.path.dirname(path))
            output_path = os.path.join(output_dir, output_name)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Encode and write the torrent file
            try:
                encoded_data = bencodepy.encode(metainfo)
                with open(output_path, 'wb') as f:
                    f.write(encoded_data)
                
                logger.info(f"Torrent file created: {output_path}")
                return output_path
            except Exception as e:
                logger.error(f"Error creating torrent file: {e}")
                raise

    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Replace characters that are problematic in filenames
        invalid_chars = r'<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # If filename is empty after sanitizing, use a default
        if not filename:
            filename = f"album_{int(time.time())}"
            
        return filename
    
    def _calculate_piece_size(self, path: str) -> int:
        """
        Calculate an appropriate piece size for a torrent.
        
        Args:
            path: Path to the file or directory
            
        Returns:
            int: Recommended piece size in bytes
        """
        # Calculate total size
        total_size = 0
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
        else:
            total_size = os.path.getsize(path)
        
        # Piece size recommendations based on total size
        # These are based on common practices in the torrent community
        if total_size < 50 * 1024 * 1024:  # < 50 MB
            return 16 * 1024  # 16 KB
        elif total_size < 150 * 1024 * 1024:  # < 150 MB
            return 32 * 1024  # 32 KB
        elif total_size < 350 * 1024 * 1024:  # < 350 MB
            return 64 * 1024  # 64 KB
        elif total_size < 512 * 1024 * 1024:  # < 512 MB
            return 128 * 1024  # 128 KB
        elif total_size < 1024 * 1024 * 1024:  # < 1 GB
            return 256 * 1024  # 256 KB
        elif total_size < 2 * 1024 * 1024 * 1024:  # < 2 GB
            return 512 * 1024  # 512 KB
        elif total_size < 4 * 1024 * 1024 * 1024:  # < 4 GB
            return 1024 * 1024  # 1 MB
        elif total_size < 8 * 1024 * 1024 * 1024:  # < 8 GB
            return 2 * 1024 * 1024  # 2 MB
        else:
            return 4 * 1024 * 1024  # 4 MB
    
    def _build_info_dict(self, path: str, piece_size: int) -> Dict[str, Any]:
        """
        Build the info dictionary for a torrent file.
        
        Args:
            path: Path to the file or directory
            piece_size: Piece size in bytes
            
        Returns:
            dict: Info dictionary
        """
        if os.path.isdir(path):
            return self._build_multi_file_info(path, piece_size)
        else:
            return self._build_single_file_info(path, piece_size)
    
    def _build_single_file_info(self, file_path: str, piece_size: int) -> Dict[str, Any]:
        """
        Build the info dictionary for a single file torrent.
        
        Args:
            file_path: Path to the file
            piece_size: Piece size in bytes
            
        Returns:
            dict: Info dictionary
        """
        file_size = os.path.getsize(file_path)
        pieces = self._calculate_pieces(file_path, piece_size)
        
        return {
            'name': os.path.basename(file_path),
            'length': file_size,
            'piece length': piece_size,
            'pieces': pieces
        }
    
    def _build_multi_file_info(self, dir_path: str, piece_size: int) -> Dict[str, Any]:
        """
        Build the info dictionary for a multi-file torrent.
        
        Args:
            dir_path: Path to the directory
            piece_size: Piece size in bytes
            
        Returns:
            dict: Info dictionary
        """
        # Get the base name of the directory
        name = os.path.basename(dir_path)
        if not name:  # Handle case with trailing slash
            name = os.path.basename(os.path.dirname(dir_path))
        
        # Make sure we have a valid name
        if not name or name == ".":
            name = f"album_{int(time.time())}"
        
        # Build file list
        files = []
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_size = os.path.getsize(file_path)
                
                # Calculate path relative to the torrent root
                rel_path = os.path.relpath(file_path, dir_path)
                path_list = rel_path.split(os.sep)
                
                files.append({
                    'length': file_size,
                    'path': path_list
                })
        
        # Sort files by path for consistent ordering
        files.sort(key=lambda x: x['path'])
        
        # Calculate pieces
        pieces = self._calculate_pieces_for_files(dir_path, files, piece_size)
        
        return {
            'name': name,
            'files': files,
            'piece length': piece_size,
            'pieces': pieces
        }
    
    def _calculate_pieces(self, file_path: str, piece_size: int) -> bytes:
        """
        Calculate pieces for a single file.
        
        Args:
            file_path: Path to the file
            piece_size: Piece size in bytes
            
        Returns:
            bytes: Concatenated piece hashes
        """
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
        """
        Calculate pieces for multiple files.
        
        Args:
            base_dir: Base directory
            files: List of file dictionaries
            piece_size: Piece size in bytes
            
        Returns:
            bytes: Concatenated piece hashes
        """
        pieces = b""
        piece_data = b""
        sha1 = hashlib.sha1()
        
        for file_info in files:
            # Build the file path
            path_parts = file_info['path']
            file_path = os.path.join(base_dir, *path_parts)
            
            with open(file_path, 'rb') as f:
                while True:
                    # Calculate how much data to read from this file
                    bytes_needed = piece_size - len(piece_data)
                    data = f.read(bytes_needed)
                    
                    if not data:
                        # End of file
                        break
                    
                    piece_data += data
                    
                    # If we have a full piece, hash it
                    if len(piece_data) == piece_size:
                        sha1.update(piece_data)
                        pieces += sha1.digest()
                        piece_data = b""
                        sha1 = hashlib.sha1()
        
        # Hash any remaining data
        if piece_data:
            sha1.update(piece_data)
            pieces += sha1.digest()
        
        return pieces
    
    def create_tracker_specific_torrent(self, original_torrent_path: str, tracker_id: str,
                                      announce_url: str, source: str = None) -> str:
        """
        Create a tracker-specific torrent from an existing torrent file.
        
        Args:
            original_torrent_path: Path to the original torrent file
            tracker_id: Tracker identifier
            announce_url: Tracker announce URL
            source: Source tag
            
        Returns:
            str: Path to the tracker-specific torrent file
        """
        if not bencodepy:
            raise ImportError("bencodepy module is required for torrent creation")
            
        try:
            # Load the original torrent file
            with open(original_torrent_path, 'rb') as f:
                torrent_data = f.read()
            
            metainfo = bencodepy.decode(torrent_data)
            
            # Update the announce URL
            metainfo[b'announce'] = announce_url.encode()
            
            # Update the source tag if provided
            if source:
                metainfo[b'info'][b'source'] = source.encode()
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(original_torrent_path))[0]
            output_name = f"{base_name}[{tracker_id}].torrent"
            output_dir = os.path.dirname(original_torrent_path)
            output_path = os.path.join(output_dir, output_name)
            
            # Encode and write the torrent file
            encoded_data = bencodepy.encode(metainfo)
            with open(output_path, 'wb') as f:
                f.write(encoded_data)
            
            logger.info(f"Tracker-specific torrent file created: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating tracker-specific torrent file: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Sample config
    sample_config = {
        'torrent': {
            'comment': 'Created with Music-Upload-Assistant',
            'source': 'MUA',
            'private': True
        },
        'output_dir': 'output'
    }
    
    # Create torrent creator
    creator = TorrentCreator(sample_config)
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python torrent.py <file_or_directory> [announce_url]")
        sys.exit(1)
    
    path = sys.argv[1]
    announce_url = sys.argv[2] if len(sys.argv) > 2 else "http://example.com/announce"
    
    # Create the torrent
    try:
        torrent_path = creator.create_torrent(path, announce_url)
        print(f"Torrent file created: {torrent_path}")
    except Exception as e:
        print(f"Error creating torrent: {e}")
        sys.exit(1)