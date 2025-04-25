"""
Audio analyzer module for Music-Upload-Assistant.
Handles technical analysis of audio files to extract quality information.
"""

import os
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

# Try to import format handlers
try:
    from modules.audio_analyzer.format_handlers.base_handler import FormatHandler
    from modules.audio_analyzer.format_handlers.flac_handler import FlacHandler
    from modules.audio_analyzer.format_handlers.mp3_handler import Mp3Handler
except ImportError as e:
    logging.error(f"Error importing format handlers: {e}")

logger = logging.getLogger(__name__)

class AudioFormat(Enum):
    """Supported audio formats."""
    FLAC = "FLAC"
    MP3 = "MP3"
    AAC = "AAC"
    OGG = "OGG"
    WAV = "WAV"
    ALAC = "ALAC"
    DSD = "DSD"
    UNKNOWN = "Unknown"

class CompressionType(Enum):
    """Audio compression classifications."""
    LOSSLESS = "Lossless"
    LOSSY = "Lossy"
    UNCOMPRESSED = "Uncompressed"
    UNKNOWN = "Unknown"

class AudioQuality:
    """Class to store audio quality metrics."""
    
    def __init__(self):
        self.format: AudioFormat = AudioFormat.UNKNOWN
        self.compression: CompressionType = CompressionType.UNKNOWN
        self.duration: float = 0.0  # In seconds
        self.sample_rate: int = 0  # In Hz
        self.bit_depth: Optional[int] = None  # None for lossy formats
        self.channels: int = 0
        self.bitrate: int = 0  # In kbps
        self.file_size: int = 0  # In bytes
        self.codec: str = ""
        self.encoder: Optional[str] = None
        self.dynamic_range: Optional[float] = None
        self.album_gain: Optional[float] = None
        self.track_gain: Optional[float] = None
        self.spectral_flatness: Optional[float] = None
        self.spectral_bandwidth: Optional[int] = None
        self.detected_cutoff: Optional[int] = None
        self.potential_transcode: bool = False
        self.potential_upsampling: bool = False
        self.warnings: List[str] = []

class AudioAnalyzer:
    """
    Main class for analyzing audio files and extracting technical information.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the audio analyzer.
        
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
            
            # Add more handlers here as they're implemented
            
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
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze an audio file and return results.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            dict: Analysis results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get the appropriate handler
        handler = self.get_handler_for_file(file_path)
        if not handler:
            raise ValueError(f"Unsupported file format: {os.path.splitext(file_path)[1]}")
        
        # Get basic metadata and technical info
        metadata = handler.get_track_info(file_path)
        
        # Perform quality analysis
        quality = self._analyze_quality(metadata)
        
        # Add quality info to metadata
        metadata['quality'] = quality
        
        return metadata
    
    def _analyze_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze audio quality based on metadata.
        
        Args:
            metadata: Audio metadata
            
        Returns:
            dict: Quality analysis results
        """
        quality = {}
        warnings = []
        
        # Basic quality info
        quality['format'] = metadata.get('format', 'Unknown')
        quality['compression'] = metadata.get('compression', 'Unknown')
        quality['lossless'] = metadata.get('format') == 'FLAC' or 'ALAC' in metadata.get('format', '')
        quality['sample_rate'] = metadata.get('sample_rate', 0)
        quality['bit_depth'] = metadata.get('bit_depth')
        quality['channels'] = metadata.get('channels', 0)
        quality['bitrate'] = metadata.get('bitrate', 0)
        
        # Check for expected quality based on format
        if quality['format'] == 'FLAC':
            # FLAC should be lossless
            if not quality['lossless']:
                warnings.append("FLAC file marked as non-lossless")
            
            # FLAC usually has bit depth
            if not quality['bit_depth']:
                warnings.append("FLAC file missing bit depth information")
            
            # Check for good sample rate
            if quality['sample_rate'] < 44100:
                warnings.append(f"Low sample rate for FLAC: {quality['sample_rate']} Hz")
            
            # Check for unusual bit depth
            if quality['bit_depth'] and quality['bit_depth'] not in [16, 24, 32]:
                warnings.append(f"Unusual bit depth for FLAC: {quality['bit_depth']} bits")
        
        elif quality['format'] == 'MP3':
            # MP3 should be lossy
            if quality['lossless']:
                warnings.append("MP3 file marked as lossless (impossible)")
            
            # Check for good bitrate
            if quality['bitrate'] < 192:
                warnings.append(f"Low bitrate for MP3: {quality['bitrate']} kbps")
            elif quality['bitrate'] > 320:
                warnings.append(f"Suspiciously high bitrate for MP3: {quality['bitrate']} kbps")
        
        # Add warnings to quality info
        quality['warnings'] = warnings
        
        return quality
    
    def analyze_album(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Analyze a collection of files as an album.
        
        Args:
            file_paths: List of audio file paths
            
        Returns:
            dict: Album analysis results
        """
        if not file_paths:
            raise ValueError("No files provided for album analysis")
        
        # Analyze each file
        file_results = []
        for file_path in file_paths:
            try:
                result = self.analyze_file(file_path)
                file_results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
        
        if not file_results:
            raise ValueError("Failed to analyze any files in the album")
        
        # Consolidate album info
        album_info = self._consolidate_album_info(file_results)
        
        return {
            'album_info': album_info,
            'file_results': file_results
        }
    
    def _consolidate_album_info(self, file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolidate album information from individual file results.
        
        Args:
            file_results: List of file analysis results
            
        Returns:
            dict: Consolidated album information
        """
        album_info = {}
        
        # Basic album info from first file
        first_file = file_results[0]
        album_info['album'] = first_file.get('album', 'Unknown Album')
        album_info['album_artists'] = first_file.get('album_artists', first_file.get('artists', ['Unknown Artist']))
        album_info['year'] = first_file.get('year')
        album_info['total_tracks'] = len(file_results)
        
        # Collect format info
        formats = set(r.get('format', 'Unknown') for r in file_results)
        album_info['formats'] = sorted(list(formats))
        album_info['mixed_format'] = len(formats) > 1
        
        # Collect quality info
        quality_info = {}
        
        # Sample rates
        sample_rates = set(r.get('quality', {}).get('sample_rate', 0) for r in file_results)
        quality_info['sample_rates'] = sorted(list(sample_rates))
        quality_info['mixed_sample_rate'] = len(sample_rates) > 1
        
        # Bit depths for lossless formats
        bit_depths = set()
        for r in file_results:
            if r.get('quality', {}).get('lossless', False) and r.get('quality', {}).get('bit_depth'):
                bit_depths.add(r.get('quality', {}).get('bit_depth'))
        quality_info['bit_depths'] = sorted(list(bit_depths))
        quality_info['mixed_bit_depth'] = len(bit_depths) > 1
        
        # Bitrates for lossy formats
        bitrates = set()
        for r in file_results:
            if not r.get('quality', {}).get('lossless', False):
                bitrates.add(r.get('quality', {}).get('bitrate', 0))
        quality_info['bitrates'] = sorted(list(bitrates))
        quality_info['mixed_bitrate'] = len(bitrates) > 1
        
        # Overall quality assessment
        quality_info['all_lossless'] = all(r.get('quality', {}).get('lossless', False) for r in file_results)
        quality_info['all_lossy'] = all(not r.get('quality', {}).get('lossless', False) for r in file_results)
        quality_info['mixed_compression'] = not quality_info['all_lossless'] and not quality_info['all_lossy']
        
        # Collect warnings
        warnings = []
        for r in file_results:
            file_warnings = r.get('quality', {}).get('warnings', [])
            for warning in file_warnings:
                warnings.append(f"{r.get('title', 'Unknown track')}: {warning}")
        quality_info['warnings'] = warnings
        
        # Calculate total duration
        total_duration = sum(r.get('duration', 0) for r in file_results)
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        quality_info['total_duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Calculate total size
        total_size = sum(r.get('file_size', 0) for r in file_results)
        quality_info['total_size'] = total_size
        quality_info['total_size_mb'] = total_size / (1024 * 1024)
        
        album_info['quality'] = quality_info
        
        return album_info
    
    def get_audio_summary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a human-readable summary of audio quality.
        
        Args:
            metadata: Audio metadata with quality info
            
        Returns:
            dict: Summary information
        """
        quality = metadata.get('quality', {})
        format_name = quality.get('format', 'Unknown')
        compression = quality.get('compression', 'Unknown')
        
        summary = {
            "format": format_name,
            "compression": compression,
        }
        
        if 'duration' in metadata:
            minutes = int(metadata['duration'] // 60)
            seconds = int(metadata['duration'] % 60)
            summary["duration"] = f"{minutes}:{seconds:02d}"
        
        if 'file_size' in metadata:
            summary["file_size"] = f"{metadata['file_size'] / (1024 * 1024):.2f} MB"
        
        if 'sample_rate' in metadata:
            summary["sample_rate"] = f"{metadata['sample_rate'] / 1000:.1f} kHz"
        
        if quality.get('bit_depth'):
            summary["bit_depth"] = f"{quality['bit_depth']}-bit"
        
        if 'channels' in metadata:
            if metadata['channels'] == 1:
                summary["channels"] = "Mono"
            elif metadata['channels'] == 2:
                summary["channels"] = "Stereo"
            else:
                summary["channels"] = f"{metadata['channels']} channels"
        
        if 'bitrate' in metadata:
            summary["bitrate"] = f"{metadata['bitrate']} kbps"
        
        if quality.get('warnings'):
            summary["warnings"] = quality['warnings']
        
        return summary
    
    def get_album_summary(self, album_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a human-readable summary of album quality.
        
        Args:
            album_info: Album information
            
        Returns:
            dict: Summary information
        """
        quality = album_info.get('quality', {})
        
        summary = {
            "album": album_info.get('album', 'Unknown Album'),
            "artist": ', '.join(album_info.get('album_artists', ['Unknown Artist'])),
            "tracks": album_info.get('total_tracks', 0),
        }
        
        if 'year' in album_info and album_info['year']:
            summary["year"] = album_info['year']
        
        if 'formats' in quality:
            summary["formats"] = ', '.join(quality.get('formats', ['Unknown']))
        
        if 'sample_rates' in quality:
            sample_rates = [f"{sr / 1000:.1f} kHz" for sr in quality.get('sample_rates', [])]
            summary["sample_rates"] = ', '.join(sample_rates)
        
        if 'bit_depths' in quality:
            bit_depths = [f"{bd}-bit" for bd in quality.get('bit_depths', [])]
            if bit_depths:
                summary["bit_depths"] = ', '.join(bit_depths)
        
        if 'total_duration' in quality:
            summary["duration"] = quality['total_duration']
        
        if 'total_size_mb' in quality:
            summary["size"] = f"{quality['total_size_mb']:.2f} MB"
        
        if quality.get('warnings'):
            summary["warnings"] = quality['warnings']
        
        if quality.get('mixed_format'):
            summary["notes"] = []
            if quality.get('mixed_format'):
                summary["notes"].append("Mixed formats")
            if quality.get('mixed_sample_rate'):
                summary["notes"].append("Mixed sample rates")
            if quality.get('mixed_bit_depth'):
                summary["notes"].append("Mixed bit depths")
            if quality.get('mixed_compression'):
                summary["notes"].append("Mixed compression (lossless and lossy)")
        
        return summary


if __name__ == "__main__":
    import sys
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python audio_analyzer.py <audio_file> [--album]")
        sys.exit(1)
    
    path = sys.argv[1]
    is_album = "--album" in sys.argv
    
    analyzer = AudioAnalyzer()
    
    try:
        if is_album and os.path.isdir(path):
            # Find audio files in directory
            audio_files = []
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    if ext[1:] in analyzer.handlers:
                        audio_files.append(file_path)
            
            if not audio_files:
                print(f"No supported audio files found in {path}")
                sys.exit(1)
            
            # Analyze as album
            result = analyzer.analyze_album(audio_files)
            album_summary = analyzer.get_album_summary(result['album_info'])
            
            print("\n=== Album Analysis ===")
            for key, value in album_summary.items():
                if key != "warnings" and key != "notes":
                    print(f"{key.capitalize()}: {value}")
            
            if "notes" in album_summary:
                print("\nNotes:")
                for note in album_summary["notes"]:
                    print(f"  - {note}")
            
            if "warnings" in album_summary:
                print("\nWarnings:")
                for warning in album_summary["warnings"]:
                    print(f"  - {warning}")
        else:
            # Analyze single file
            result = analyzer.analyze_file(path)
            summary = analyzer.get_audio_summary(result)
            
            print("\n=== Audio Analysis ===")
            for key, value in summary.items():
                if key != "warnings":
                    print(f"{key.capitalize()}: {value}")
            
            if "warnings" in summary and summary["warnings"]:
                print("\nWarnings:")
                for warning in summary["warnings"]:
                    print(f"  - {warning}")
    
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        sys.exit(1)