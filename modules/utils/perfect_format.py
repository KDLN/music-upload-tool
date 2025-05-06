"""
Perfect format generator for Music-Upload-Assistant.
Creates description and naming formats that match the "perfect upload" example.
"""

import os
import re
import logging
import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def generate_perfect_name(metadata: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Generate a perfect upload name based on the example format:
    "Artist-Album [Barcode-Number] Year Source BitDepth SampleRate Format-Uploader"
    
    Args:
        metadata: Album metadata
        config: Configuration dictionary
        
    Returns:
        str: Formatted perfect name
    """
    # Get basic info
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
    
    # Get format details
    format_type = metadata.get('format', 'FLAC')
    media = metadata.get('media', config.get('upload', {}).get('default_media', 'WEB'))
    
    # Get bit depth
    bit_depth = ""
    if 'bit_depth' in metadata and metadata['bit_depth']:
        bit_depth = f"{metadata['bit_depth']}bit"
    else:
        bit_depth = "16bit"  # Default
    
    # Get sample rate
    sample_rate = "44.1kHz"  # Default
    if 'sample_rate' in metadata:
        rate = metadata.get('sample_rate', 44100)
        if isinstance(rate, (int, float)):
            if rate == 44100:
                sample_rate = "44.1kHz"
            elif rate == 48000:
                sample_rate = "48kHz"
            elif rate == 88200:
                sample_rate = "88.2kHz"
            elif rate == 96000:
                sample_rate = "96kHz"
            elif rate == 176400:
                sample_rate = "176.4kHz"
            elif rate == 192000:
                sample_rate = "192kHz"
            else:
                sample_rate = f"{rate/1000:.1f}kHz"
    
    # Get uploader tag
    uploader = config.get('uploader_name', 'R&H')
    
    # Format artist and album with dots instead of spaces
    artist_formatted = artist.replace(' ', '.')
    album_formatted = album.replace(' ', '.')
    
    # Build the perfect name
    parts = []
    
    # Artist-Album
    parts.append(f"{artist_formatted}-{album_formatted}")
    
    # Add barcode if available
    if barcode:
        parts.append(f"[Barcode-{barcode}]")
    
    # Add year
    if year:
        parts.append(str(year))
    
    # Add media source (WEB, CD, etc.)
    parts.append(media)
    
    # Add technical specs for FLAC
    if format_type == 'FLAC':
        parts.append(bit_depth)
        parts.append(sample_rate)
    
    # Add format
    parts.append(format_type)
    
    # Add uploader tag
    parts.append(f"-{uploader}")
    
    # Join everything
    perfect_name = " ".join(parts)
    
    # Sanitize for filesystem
    perfect_name = sanitize_filename(perfect_name)
    
    logger.info(f"Generated perfect name: {perfect_name}")
    return perfect_name

def generate_perfect_description(metadata: Dict[str, Any], track_info: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
    """
    Generate a perfect description based on the example format.
    
    Args:
        metadata: Album metadata
        track_info: List of track information
        config: Configuration dictionary
        
    Returns:
        str: Formatted perfect description
    """
    # Get album and artist info
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
    
    # Get format details
    format_type = metadata.get('format', 'FLAC')
    media = metadata.get('media', config.get('upload', {}).get('default_media', 'WEB'))
    
    sample_rate = "44100 HZ"  # Default
    if 'sample_rate' in metadata:
        sample_rate = f"{metadata.get('sample_rate', 44100)} HZ"
    
    bit_depth = "16 Bit"  # Default
    if 'bit_depth' in metadata:
        bit_depth = f"{metadata.get('bit_depth', 16)} Bit"
    
    # Format codec description
    codec_desc = "Free Lossless Audio Codec (FLAC)"
    if format_type == 'MP3':
        codec_desc = "MPEG-1 Audio Layer III (MP3)"
    elif format_type == 'AAC':
        codec_desc = "Advanced Audio Coding (AAC)"
    
    # Channel info
    channels = "Stereo"  # Default
    if 'channels' in metadata:
        if metadata['channels'] == 1:
            channels = "Mono"
        elif metadata['channels'] > 2:
            channels = f"{metadata['channels']} Channels"
    
    # Get current date and time
    now = datetime.datetime.now()
    date_str = now.strftime('%d/%m/%Y')
    time_str = now.strftime('%H:%M:%S')
    
    # Prepare media source info
    media_img = ""
    if media.upper() == 'WEB':
        media_img = "[img]https://i.ibb.co/9ZZCM1x/Tidal.png[/img]"
    
    # Check for multi-disc album
    is_multi_disc = 'total_discs' in metadata and metadata['total_discs'] > 1
    disc_data = {}
    
    # Prepare track listing
    if is_multi_disc:
        # Group tracks by disc
        tracks_by_disc = {}
        for track in track_info:
            disc_num = track.get('disc_number', 1)
            if disc_num not in tracks_by_disc:
                tracks_by_disc[disc_num] = []
            tracks_by_disc[disc_num].append(track)
        
        # Process each disc
        for disc_num, disc_tracks in sorted(tracks_by_disc.items()):
            # Format track list for this disc
            track_list = []
            total_duration_sec = 0
            total_size_bytes = 0
            
            for i, track in enumerate(disc_tracks):
                title = track.get('title', f'Track {i+1}')
                # Format duration
                duration = "00:00"
                if 'duration' in track:
                    duration = track['duration']
                    # Also add to total duration
                    if 'duration_seconds' in track:
                        total_duration_sec += track['duration_seconds']
                
                # Add to total size
                if 'file_size_bytes' in track:
                    total_size_bytes += track['file_size_bytes']
                
                # Format track entry: "   1. Artist - Title                                     [03:02]"
                track_entry = f"{i+1:3d}. {artist} - {title}"
                # Pad with spaces to align duration
                padding = max(0, 70 - len(track_entry))
                track_entry += " " * padding + f"[{duration}]"
                track_list.append(track_entry)
            
            # Format total duration
            minutes = int(total_duration_sec // 60)
            seconds = int(total_duration_sec % 60)
            total_duration = f"{minutes:02d}:{seconds:02d}"
            
            # Format total size
            total_size_mb = total_size_bytes / (1024 * 1024)
            total_size = f"{total_size_mb:.2f} MB"
            
            # Store disc data
            disc_data[disc_num] = {
                'track_list': "\n".join(track_list),
                'total_duration': total_duration,
                'total_size': total_size
            }
    else:
        # Single disc album
        track_list = []
        total_duration_sec = 0
        total_size_bytes = 0
        
        for i, track in enumerate(track_info):
            title = track.get('title', f'Track {i+1}')
            # Format duration
            duration = "00:00"
            if 'duration' in track:
                duration = track['duration']
                # Also add to total duration
                if 'duration_seconds' in track:
                    total_duration_sec += track['duration_seconds']
            
            # Add to total size
            if 'file_size_bytes' in track:
                total_size_bytes += track['file_size_bytes']
            
            # Format track entry: "   1. Artist - Title                                     [03:02]"
            track_entry = f"{i+1:3d}. {artist} - {title}"
            # Pad with spaces to align duration
            padding = max(0, 70 - len(track_entry))
            track_entry += " " * padding + f"[{duration}]"
            track_list.append(track_entry)
        
        # Format total duration
        minutes = int(total_duration_sec // 60)
        seconds = int(total_duration_sec % 60)
        total_duration = f"{minutes:02d}:{seconds:02d}"
        
        # Format total size
        total_size_mb = total_size_bytes / (1024 * 1024)
        total_size = f"{total_size_mb:.2f} MB"
    
    # Build the description based on the example format
    lines = []
    
    # Header
    lines.append("---------------------------------------------------------------------")
    lines.append(f"                        {artist} - {album}")
    lines.append("---------------------------------------------------------------------")
    
    # Source and technical information
    lines.append(f"Source...............: {media} {media_img}")
    lines.append("Included.............: NFO, M3U, LOG (Folder.auCDtect)")
    lines.append(f"Channels.............: {channels} / {sample_rate} / {bit_depth}")
    lines.append(f"Codec................: {codec_desc}")
    
    if is_multi_disc:
        # Multi-disc album - show each disc separately
        for disc_num, data in sorted(disc_data.items()):
            lines.append("---------------------------------------------------------------------")
            lines.append(f"                       Tracklisting CD {disc_num}")
            lines.append("---------------------------------------------------------------------")
            lines.append(data['track_list'])
            lines.append(f"Playing Time.........: {data['total_duration']}")
            lines.append(f"Total Size...........: {data['total_size']}")
    else:
        # Single disc album
        lines.append("---------------------------------------------------------------------")
        lines.append("                       Tracklisting")
        lines.append("---------------------------------------------------------------------")
        lines.append("\n".join(track_list))
        lines.append(f"Playing Time.........: {total_duration}")
        lines.append(f"Total Size...........: {total_size}")
    
    # Footer
    lines.append(f"NFO generated on.....: {date_str} {time_str}")
    
    # Join everything and return
    description = "\n".join(lines)
    
    return description

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
