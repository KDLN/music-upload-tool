"""
Tag processor module for Music-Upload-Assistant.
Handles extraction and normalization of audio file metadata across different formats.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
import mutagen
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

# Import format handlers
from modules.audio_analyzer.format_handlers.base_handler import FormatHandler
from modules.audio_analyzer.format_handlers.flac_handler import FlacHandler
from modules.audio_analyzer.format_handlers.mp3_handler import Mp3Handler

logger = logging.getLogger(__name__)

class TagProcessor:
    """
    Handles extraction and normalization of music file tags across different formats.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tag processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.handlers = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """Register available format handlers."""
        try:
            # Register FLAC handler
            flac_handler = FlacHandler()
            for ext in flac_handler.extensions:
                self.handlers[ext] = flac_handler
            
            # Register MP3 handler
            mp3_handler = Mp3Handler()
            for ext in mp3_handler.extensions:
                self.handlers[ext] = mp3_handler
            
            # Additional format handlers will be registered here as they're implemented
            
            logger.info(f"Registered format handlers: {', '.join(self.handlers.keys())}")
        except Exception as e:
            logger.error(f"Error registering format handlers: {e}")
    
    def get_handler_for_file(self, file_path: str) -> Optional[FormatHandler]:
        """
        Get the appropriate format handler for a file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            FormatHandler: Format handler or None if not supported
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext.startswith('.'):
            ext = ext[1:]
        
        handler = self.handlers.get(ext)
        if not handler:
            logger.warning(f"No handler available for .{ext} files")
        
        return handler
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            dict: Extracted metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get the appropriate handler
        handler = self.get_handler_for_file(file_path)
        if not handler:
            raise ValueError(f"Unsupported file format: {os.path.splitext(file_path)[1]}")
        
        # Use the handler to extract metadata
        metadata = handler.get_track_info(file_path)
        
        return metadata
    
    def write_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Write metadata to an audio file.
        
        Args:
            file_path: Path to the audio file
            metadata: Metadata to write
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get the appropriate handler
        handler = self.get_handler_for_file(file_path)
        if not handler:
            raise ValueError(f"Unsupported file format: {os.path.splitext(file_path)[1]}")
        
        # Use the handler to write metadata
        return handler.write_metadata(file_path, metadata)
    
    def extract_artwork(self, file_path: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Extract embedded artwork from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            tuple: (artwork_data, mime_type) or (None, None) if not found
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get the appropriate handler
        handler = self.get_handler_for_file(file_path)
        if not handler:
            raise ValueError(f"Unsupported file format: {os.path.splitext(file_path)[1]}")
        
        # Use the handler to extract artwork
        return handler.read_embedded_artwork(file_path)
    
    def save_artwork(self, file_path: str, output_path: str) -> bool:
        """
        Extract and save artwork from an audio file.
        
        Args:
            file_path: Path to the audio file
            output_path: Path to save the artwork
            
        Returns:
            bool: Success status
        """
        artwork_data, mime_type = self.extract_artwork(file_path)
        
        if not artwork_data:
            logger.warning(f"No artwork found in {file_path}")
            return False
        
        try:
            with open(output_path, 'wb') as f:
                f.write(artwork_data)
            
            logger.info(f"Saved artwork to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving artwork to {output_path}: {e}")
            return False
    
    def normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize metadata to ensure consistent formatting.
        
        Args:
            metadata: Metadata to normalize
            
        Returns:
            dict: Normalized metadata
        """
        normalized = metadata.copy()
        
        # Ensure core fields exist
        core_fields = ['title', 'artists', 'album', 'album_artists', 'track_number',
                      'total_tracks', 'disc_number', 'total_discs', 'year', 'genres']
        
        for field in core_fields:
            if field not in normalized:
                if field in ['artists', 'album_artists', 'genres']:
                    normalized[field] = []
                else:
                    normalized[field] = None
        
        # Convert track number and disc number to integers
        for field in ['track_number', 'total_tracks', 'disc_number', 'total_discs']:
            if normalized.get(field) and not isinstance(normalized[field], int):
                try:
                    normalized[field] = int(normalized[field])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {field} to integer: {normalized[field]}")
                    normalized[field] = None
        
        # Ensure list fields are actually lists
        for field in ['artists', 'album_artists', 'genres', 'composers', 'performers']:
            if field in normalized and not isinstance(normalized[field], list):
                normalized[field] = [normalized[field]]
        
        # Ensure year is an integer if present
        if normalized.get('year') and not isinstance(normalized['year'], int):
            try:
                normalized['year'] = int(normalized['year'])
            except (ValueError, TypeError):
                logger.warning(f"Could not convert year to integer: {normalized['year']}")
        
        return normalized
    
    def merge_metadata(self, base_metadata: Dict[str, Any], 
                     new_metadata: Dict[str, Any], prefer_new: bool = False) -> Dict[str, Any]:
        """
        Merge two metadata dictionaries.
        
        Args:
            base_metadata: Base metadata
            new_metadata: New metadata to merge
            prefer_new: Whether to prefer new values over existing ones
            
        Returns:
            dict: Merged metadata
        """
        merged = base_metadata.copy()
        
        for key, value in new_metadata.items():
            # Skip None values
            if value is None:
                continue
            
            # Skip empty lists
            if isinstance(value, list) and not value:
                continue
            
            # Skip empty strings
            if isinstance(value, str) and not value.strip():
                continue
            
            # If prefer_new or field doesn't exist in base, use new value
            if prefer_new or key not in merged or merged[key] is None:
                merged[key] = value
            
            # For list fields, merge lists without duplicates
            elif isinstance(value, list) and isinstance(merged[key], list):
                merged[key] = list(set(merged[key] + value))
        
        return merged
    
    def clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean metadata by removing unnecessary fields.
        
        Args:
            metadata: Metadata to clean
            
        Returns:
            dict: Cleaned metadata
        """
        # Fields to keep
        essential_fields = [
            'title', 'artists', 'album', 'album_artists', 'track_number',
            'total_tracks', 'disc_number', 'total_discs', 'year', 'date',
            'genres', 'composers', 'performers', 'label', 'catalog_number',
            'release_country', 'musicbrainz_release_id', 'musicbrainz_recording_id',
            'musicbrainz_artist_ids', 'musicbrainz_album_artist_ids',
            'discogs_release_id', 'format', 'sample_rate', 'bit_depth',
            'channels', 'bitrate', 'codec', 'compression', 'duration',
            'file_size'
        ]
        
        # Return a new dict with only the essential fields
        cleaned = {}
        for field in essential_fields:
            if field in metadata and metadata[field] is not None:
                cleaned[field] = metadata[field]
        
        return cleaned


if __name__ == "__main__":
    import sys
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python tag_processor.py <audio_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    processor = TagProcessor()
    
    try:
        metadata = processor.extract_metadata(file_path)
        normalized = processor.normalize_metadata(metadata)
        
        print("\n=== Raw Metadata ===")
        for key, value in metadata.items():
            if key != 'artwork':  # Skip binary data
                print(f"{key}: {value}")
        
        print("\n=== Normalized Metadata ===")
        for key, value in normalized.items():
            if key != 'artwork':  # Skip binary data
                print(f"{key}: {value}")
        
        # Extract and save artwork if present
        if 'artwork' in metadata and metadata['artwork']:
            output_path = os.path.splitext(file_path)[0] + '.jpg'
            if processor.save_artwork(file_path, output_path):
                print(f"\nArtwork saved to: {output_path}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)