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
    Follows format seen on trackers:
    "Artist - Album (Year) FLAC"
    
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
        media = metadata.get('media', '')
    
    # Apply bit depth override if specified
    if 'bitdepth_override' in options:
        bit_depth = options['bitdepth_override']
    elif 'bit_depth' in metadata and metadata['bit_depth']:
        bit_depth = str(metadata['bit_depth'])
    else:
        bit_depth = ''
    
    # Simple format - example: "Artist - Album (Year) FLAC"
    # Based on your screenshot, this seems to be the preferred format
    parts = []
    
    # Artist - Album
    parts.append(f"{artist} - {album}")
    
    # Add year if available
    if year:
        parts.append(f"({year})")
    
    # Add format (FLAC, MP3, etc.)
    parts.append(format_type)
    
    # For FLAC formats, add bit depth if available
    if format_type == 'FLAC' and bit_depth:
        parts[-1] += f" {bit_depth}-bit"
    
    # Add media source if specified (e.g., WEB, CD)
    if media:
        parts.append(media)
    
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
