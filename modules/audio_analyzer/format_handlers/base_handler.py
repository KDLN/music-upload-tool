"""
Base format handler for the Music-Upload-Assistant.
Defines the interface that all format-specific handlers must implement.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any, BinaryIO

logger = logging.getLogger(__name__)

class FormatHandler(ABC):
    """Base abstract class for audio format handlers."""
    
    def __init__(self):
        """Initialize the format handler."""
        self.name = "Base Format Handler"
        self.extensions = []
    
    @abstractmethod
    def get_track_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract track metadata and technical info.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dict: Populated track metadata dictionary
        """
        pass
    
    @abstractmethod
    def is_lossless(self, file_path: str) -> bool:
        """
        Determine if the file uses lossless compression.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            bool: True if lossless, False if lossy
        """
        pass
    
    @abstractmethod
    def read_embedded_artwork(self, file_path: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Extract embedded artwork if present.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            tuple: (artwork_data, mime_type) or (None, None)
        """
        pass
    
    @abstractmethod
    def write_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Write metadata to the file.
        
        Args:
            file_path: Path to the audio file
            metadata: Metadata dictionary to write
            
        Returns:
            bool: Success status
        """
        pass
    
    def supports_extension(self, file_extension: str) -> bool:
        """
        Check if this handler supports the given file extension.
        
        Args:
            file_extension: File extension (with or without leading dot)
            
        Returns:
            bool: True if supported, False otherwise
        """
        # Normalize extension to lowercase without leading dot
        if file_extension.startswith("."):
            file_extension = file_extension[1:]
        
        return file_extension.lower() in [ext.lower() for ext in self.extensions]
    
    def get_mediainfo(self, file_path: str) -> str:
        """
        Generate MediaInfo-style technical metadata.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            str: Formatted technical metadata
        """
        # This should be implemented by each format handler
        # to provide a standardized technical description
        try:
            track_info = self.get_track_info(file_path)
            
            # Create a standardized format regardless of the audio format
            mediainfo = []
            mediainfo.append(f"GENERAL")
            mediainfo.append(f"Complete name          : {os.path.basename(file_path)}")
            mediainfo.append(f"Format                 : {track_info.get('format', 'Unknown')}")
            
            if 'duration' in track_info:
                duration_sec = track_info['duration']
                minutes = int(duration_sec // 60)
                seconds = int(duration_sec % 60)
                ms = int((duration_sec % 1) * 1000)
                mediainfo.append(f"Duration               : {minutes}m {seconds}s {ms}ms")
            
            if 'bitrate' in track_info:
                mediainfo.append(f"Overall bit rate       : {track_info['bitrate']} kb/s")
            
            mediainfo.append(f"\nAUDIO")
            mediainfo.append(f"Format                 : {track_info.get('codec', 'Unknown')}")
            
            if 'compression' in track_info:
                mediainfo.append(f"Compression mode       : {track_info['compression']}")
            
            if 'channels' in track_info:
                channel_str = "Mono" if track_info['channels'] == 1 else \
                             "Stereo" if track_info['channels'] == 2 else \
                             f"{track_info['channels']} channels"
                mediainfo.append(f"Channel(s)             : {channel_str}")
            
            if 'sample_rate' in track_info:
                mediainfo.append(f"Sampling rate          : {track_info['sample_rate']} Hz")
            
            if 'bit_depth' in track_info and track_info['bit_depth']:
                mediainfo.append(f"Bit depth              : {track_info['bit_depth']} bits")
            
            return "\n".join(mediainfo)
            
        except Exception as e:
            logger.error(f"Error generating MediaInfo for {file_path}: {str(e)}")
            return f"Error generating MediaInfo: {str(e)}"