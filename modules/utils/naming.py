"""
Naming utilities for Music-Upload-Assistant.
Handles standardized formatting of torrent and file names.
"""

import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def generate_release_name(metadata: Dict[str, Any], config: Dict[str, Any], options: Dict[str, Any] = None) -> str:
    """
    Generate a standardized release name based on metadata.
    Follows format:
    "Artist-Album [Barcode-Number] Year Source BitDepth SampleRate Format-Uploader"
    
    Args:
        metadata: Track or album metadata
        config: Configuration dictionary
        options: Optional processing options with overrides
        
    Returns:
        str: Formatted release name
    """
    options = options or {}
    
    # Get basic release info
    artist = ""
    if 'album_artists' in metadata and metadata['album_artists']:
        if isinstance(metadata['album_artists'], list):
            artist = metadata['album_artists'][0]
        else:
            artist = metadata['album_artists']
    elif 'artists' in metadata and metadata['artists']:
        if isinstance(metadata['artists'], list):
            artist = metadata['artists'][0]
        else:
            artist = metadata['artists']
    else:
        artist = "Unknown Artist"
    
    album = metadata.get('album', 'Unknown Album')
    year = metadata.get('year', '')
    barcode = metadata.get('barcode', metadata.get('catalog_number', ''))
    
    # Get uploader name from config
    uploader = config.get('uploader_name', '')  # Default to empty if not specified
    
    # Only include uploader tag if it's set
    include_uploader = uploader and len(uploader.strip()) > 0
    
    # Apply format override if specified
    if 'format_override' in options:
        format_type = options['format_override']
    elif 'format' in metadata:
        format_type = metadata['format']
    else:
        format_type = 'FLAC' if metadata.get('compression') == 'Lossless' else 'MP3'
    
    # Apply media override if specified
    if 'media_override' in options:
        media = options['media_override']
    else:
        media = metadata.get('media', 'WEB')  # Default to WEB if not specified
    
    # Apply bit depth override if specified
    if 'bitdepth_override' in options:
        bit_depth = options['bitdepth_override']
    elif 'bit_depth' in metadata and metadata['bit_depth']:
        bit_depth = str(metadata['bit_depth'])
    else:
        bit_depth = '16'  # Default to 16-bit if not specified
    
    # Get sample rate
    sample_rate = "44.1 kHz"  # Default with space
    if 'sample_rate' in metadata:
        rate = metadata.get('sample_rate', 44100)
        if isinstance(rate, (int, float)):
            if rate == 44100:
                sample_rate = "44.1 kHz"
            elif rate == 48000:
                sample_rate = "48 kHz"
            elif rate == 88200:
                sample_rate = "88.2 kHz"
            elif rate == 96000:
                sample_rate = "96 kHz"
            elif rate == 176400:
                sample_rate = "176.4 kHz"
            elif rate == 192000:
                sample_rate = "192 kHz"
            else:
                sample_rate = f"{rate/1000:.1f} kHz"
    
    # Remove spaces from artist and album
    artist = artist.replace(' ', '.')
    album = album.replace(' ', '.')
    
    # Format based on example: "INXS-The.Very.Best [Barcode-7935344] 2011 WEB 16bit 44.1kHz FLAC-R&H"
    parts = []
    
    # Artist-Album
    parts.append(f"{artist}-{album}")
    
    # Add barcode if available
    if barcode:
        parts.append(f"[Barcode-{barcode}]")
    
    # Add year if available
    if year:
        parts.append(str(year))
    
    # Add media source
    parts.append(media)
    
    # Add technical specs
    if format_type == 'FLAC':
        parts.append(f"{bit_depth}bit")
        parts.append(sample_rate)
    
    # Add format
    parts.append(format_type)
    
    # Add uploader only if it's set
    if include_uploader:
        parts.append(f"-{uploader}")
    
    # Join everything
    release_name = " ".join(parts)
    
    # Sanitize for filesystem use
    release_name = sanitize_filename(release_name)
    
    logger.info(f"Generated release name: {release_name}")
    return release_name

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for use as a filename.
    
    Args:
        name: String to sanitize
        
    Returns:
        str: Sanitized string
    """
    # Remove characters that are problematic in filenames
    # Windows disallows: \ / : * ? " < > |
    illegal_chars = r'[\\/*?:"<>|]'
    name = re.sub(illegal_chars, '_', name)
    
    # Replace multiple spaces with a single space
    name = re.sub(r'\s+', ' ', name)
    
    # Remove leading/trailing periods and spaces
    name = name.strip('. ')
    
    # Limit length (some filesystems have limits)
    if len(name) > 240:
        name = name[:240]
    
    # Ensure the name is not empty
    if not name:
        name = "Unnamed"
    
    return name
