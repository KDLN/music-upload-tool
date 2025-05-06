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
    Follows format: Artist - Album (Year) [Format (options)]
    
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
        artist = metadata['album_artists'][0] if isinstance(metadata['album_artists'], list) else metadata['album_artists']
    elif 'artists' in metadata and metadata['artists']:
        artist = metadata['artists'][0] if isinstance(metadata['artists'], list) else metadata['artists']
    else:
        artist = "Unknown Artist"
    
    album = metadata.get('album', 'Unknown Album')
    year = metadata.get('year', '')
    
    # Apply media override if specified
    if 'media_override' in options:
        media = options['media_override']
    else:
        media = metadata.get('media', '')
    
    # Apply format override if specified
    if 'format_override' in options:
        format_type = options['format_override']
    elif 'format' in metadata:
        format_type = metadata['format']
    else:
        format_type = 'FLAC' if metadata.get('compression') == 'Lossless' else 'MP3'
    
    # Build format options string
    format_options = []
    
    # Apply bit depth override if specified
    if 'bitdepth_override' in options:
        if format_type in ['FLAC', 'ALAC', 'WAV']:
            format_options.append(f"{options['bitdepth_override']}-bit")
    # Otherwise use bit depth from metadata
    elif format_type in ['FLAC', 'ALAC', 'WAV'] and 'bit_depth' in metadata and metadata['bit_depth']:
        format_options.append(f"{metadata['bit_depth']}-bit")
    
    # Add bitrate for lossy formats
    if format_type in ['MP3', 'AAC', 'OGG'] and 'bitrate' in metadata and metadata['bitrate']:
        format_options.append(f"{metadata['bitrate']} kbps")
    
    # Add media source if known
    if media:
        format_options.append(media)
    
    # Add resolution information if specified
    if 'resolution' in metadata:
        format_options.append(metadata['resolution'])
    
    # Build the final name
    parts = []
    
    # Artist - Album
    parts.append(f"{artist} - {album}")
    
    # Add year if available
    if year:
        parts.append(f"({year})")
    
    # Add format and options
    if format_options:
        format_string = f"{format_type} ({' '.join(format_options)})"
    else:
        format_string = format_type
    
    parts.append(f"[{format_string}]")
    
    # Join everything
    release_name = " ".join(parts)
    
    # Sanitize for filesystem use
    release_name = sanitize_filename(release_name)
    
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
