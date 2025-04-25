"""
File utilities module for Music-Upload-Assistant.
Provides functions for finding, organizing, and managing music files.
"""

import os
import re
import shutil
import logging
from typing import List, Dict, Tuple, Set, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Audio file extensions that the assistant can process
AUDIO_EXTENSIONS = {
    '.flac', '.mp3', '.m4a', '.aac', '.ogg', '.oga', '.wma', '.wav', 
    '.ape', '.dsf', '.dff', '.wv', '.alac'
}

# Common image file extensions for cover art
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
}

# Common names for cover art files
COVER_ART_FILENAMES = {
    'cover', 'front', 'folder', 'albumart', 'album', 'artwork',
    'jackett', 'scan', 'booklet', 'frontcover'
}


def find_audio_files(path: str) -> List[str]:
    """
    Find all audio files in a directory or a single audio file.
    
    Args:
        path: Path to directory or file
        
    Returns:
        list: List of audio file paths
    """
    # If path is a file, check if it's an audio file
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            return [path]
        else:
            logger.warning(f"File {path} is not a supported audio file")
            return []
    
    # If path is a directory, find all audio files
    if not os.path.isdir(path):
        logger.error(f"Path not found: {path}")
        return []
    
    audio_files = []
    
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext in AUDIO_EXTENSIONS:
                audio_files.append(file_path)
    
    # Sort files by name for consistent ordering
    audio_files.sort()
    
    logger.info(f"Found {len(audio_files)} audio files in {path}")
    return audio_files


def find_cover_art(path: str) -> Optional[str]:
    """
    Find cover art image in a directory.
    
    Args:
        path: Path to directory
        
    Returns:
        str: Path to cover art image or None if not found
    """
    if os.path.isfile(path):
        path = os.path.dirname(path)
    
    if not os.path.isdir(path):
        logger.error(f"Directory not found: {path}")
        return None
    
    # Look for image files
    candidates = []
    
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        
        if not os.path.isfile(file_path):
            continue
        
        file_name, ext = os.path.splitext(file.lower())
        if ext in IMAGE_EXTENSIONS:
            # Score each image to find the most likely cover art
            score = 0
            
            # Prefer files with "cover" in the name
            for cover_name in COVER_ART_FILENAMES:
                if cover_name in file_name:
                    score += 10
            
            # Prefer front cover variants
            if 'front' in file_name:
                score += 5
            
            # Prefer files named exactly like common cover art files
            if file_name in COVER_ART_FILENAMES:
                score += 20
            
            # Prefer certain formats (JPEG > PNG > others)
            if ext in ['.jpg', '.jpeg']:
                score += 3
            elif ext == '.png':
                score += 2
            
            # Prefer files in the root directory
            if os.path.dirname(file_path) == path:
                score += 5
            
            candidates.append((file_path, score))
    
    # Sort by score and return the best match
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Found cover art: {candidates[0][0]}")
        return candidates[0][0]
    
    # If no cover art found in root, look in subdirectories
    for root, _, files in os.walk(path):
        if root == path:
            continue
        
        for file in files:
            file_path = os.path.join(root, file)
            
            file_name, ext = os.path.splitext(file.lower())
            if ext in IMAGE_EXTENSIONS:
                logger.info(f"Found cover art in subdirectory: {file_path}")
                return file_path
    
    logger.warning(f"No cover art found in {path}")
    return None


def get_album_structure(file_paths: List[str]) -> Dict[str, Any]:
    """
    Analyze a list of audio files and determine album structure.
    
    Args:
        file_paths: List of audio file paths
        
    Returns:
        dict: Album structure information
    """
    if not file_paths:
        return {'is_album': False, 'files': []}
    
    # Organize files by directory
    files_by_dir = {}
    for file_path in file_paths:
        directory = os.path.dirname(file_path)
        if directory not in files_by_dir:
            files_by_dir[directory] = []
        files_by_dir[directory].append(file_path)
    
    # If all files are in the same directory, likely an album
    if len(files_by_dir) == 1:
        directory = list(files_by_dir.keys())[0]
        files = files_by_dir[directory]
        
        # Sort files to ensure consistent ordering
        # First try to extract track numbers
        files_with_track_nums = []
        for file_path in files:
            file_name = os.path.basename(file_path)
            # Look for track number patterns (e.g., "01 - ", "Track 1", etc.)
            track_number = extract_track_number(file_name)
            files_with_track_nums.append((file_path, track_number))
        
        # Sort by track number, then by filename for files without track numbers
        files_with_track_nums.sort(key=lambda x: (x[1] if x[1] is not None else float('inf'), x[0]))
        sorted_files = [f[0] for f in files_with_track_nums]
        
        return {
            'is_album': True,
            'directory': directory,
            'files': sorted_files,
            'track_count': len(sorted_files),
            'cover_art': find_cover_art(directory)
        }
    
    # If files are in multiple directories, might be a multi-disc album
    # or a collection of individual tracks
    discs = {}
    for directory, files in files_by_dir.items():
        disc_number = extract_disc_number(directory)
        if disc_number is not None:
            if disc_number not in discs:
                discs[disc_number] = []
            discs[disc_number].extend(files)
    
    # If we have disc numbers, likely a multi-disc album
    if discs:
        all_files = []
        for disc_num in sorted(discs.keys()):
            # Sort files within each disc
            files_with_track_nums = []
            for file_path in discs[disc_num]:
                file_name = os.path.basename(file_path)
                track_number = extract_track_number(file_name)
                files_with_track_nums.append((file_path, track_number))
            
            files_with_track_nums.sort(key=lambda x: (x[1] if x[1] is not None else float('inf'), x[0]))
            sorted_disc_files = [f[0] for f in files_with_track_nums]
            
            discs[disc_num] = sorted_disc_files
            all_files.extend(sorted_disc_files)
        
        # Find the common parent directory
        parent_dir = os.path.commonpath([os.path.dirname(f) for f in all_files])
        
        return {
            'is_album': True,
            'is_multi_disc': True,
            'directory': parent_dir,
            'files': all_files,
            'discs': discs,
            'disc_count': len(discs),
            'track_count': len(all_files),
            'cover_art': find_cover_art(parent_dir)
        }
    
    # If we got here, it's probably a collection of individual tracks
    # Just return all files sorted alphabetically
    all_files = []
    for files in files_by_dir.values():
        all_files.extend(files)
    
    all_files.sort()
    
    return {
        'is_album': False,
        'files': all_files,
        'track_count': len(all_files)
    }


def extract_track_number(filename: str) -> Optional[int]:
    """
    Extract track number from a filename.
    
    Args:
        filename: Filename to analyze
        
    Returns:
        int: Track number or None if not found
    """
    # Remove extension
    base_name = os.path.splitext(os.path.basename(filename))[0].lower()
    
    # Common patterns for track numbers
    patterns = [
        r'^(\d{1,3})[_.\s-]',              # "01 - Track Name" or "01_Track_Name" or "01.Track Name"
        r'^track\s*(\d{1,3})[_.\s-]?',     # "Track 01 - Name" or "Track01 Name"
        r'^\[(\d{1,3})\]',                 # "[01] Track Name"
        r'\((\d{1,3})\)',                  # "Track Name (01)"
        r'\s(\d{1,3})[-_.\s]of[-_.\s]\d+'  # "Track 01 of 12"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, base_name, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    
    return None


def extract_disc_number(directory: str) -> Optional[int]:
    """
    Extract disc number from a directory name.
    
    Args:
        directory: Directory name to analyze
        
    Returns:
        int: Disc number or None if not found
    """
    # Get the directory name without path
    dir_name = os.path.basename(directory).lower()
    
    # Common patterns for disc numbers
    patterns = [
        r'disc\s*(\d+)',     # "Disc 1" or "disc1"
        r'disk\s*(\d+)',     # "Disk 1" or "disk1"
        r'cd\s*(\d+)',       # "CD 1" or "cd1"
        r'd(\d+)',           # "D1"
        r'volume\s*(\d+)',   # "Volume 1"
        r'vol\.\s*(\d+)',    # "Vol. 1"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, dir_name, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    
    return None


def create_output_directory(base_dir: str, metadata: Dict[str, Any]) -> str:
    """
    Create an organized output directory for an album or track.
    
    Args:
        base_dir: Base output directory
        metadata: Album or track metadata
        
    Returns:
        str: Path to the created directory
    """
    # Extract necessary information for directory naming
    artist = metadata.get('album_artists', metadata.get('artists', ['Unknown Artist']))[0]
    album = metadata.get('album', 'Unknown Album')
    year = metadata.get('year', '')
    
    # Sanitize names for filesystem use
    artist = sanitize_filename(artist)
    album = sanitize_filename(album)
    
    # Create directory structure
    if year:
        album_dir = f"{artist}/{album} ({year})"
    else:
        album_dir = f"{artist}/{album}"
    
    output_dir = os.path.join(base_dir, album_dir)
    
    # Create the directory
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Created output directory: {output_dir}")
    return output_dir


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
    # Some filesystems have issues with leading/trailing periods and spaces
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


def copy_file_with_metadata(source_path: str, dest_dir: str, metadata: Dict[str, Any]) -> str:
    """
    Copy a file to a destination directory with a standardized name based on metadata.
    
    Args:
        source_path: Path to the source file
        dest_dir: Destination directory
        metadata: File metadata
        
    Returns:
        str: Path to the copied file
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    if not os.path.exists(dest_dir):
        raise FileNotFoundError(f"Destination directory not found: {dest_dir}")
    
    # Extract information for filename
    track_number = metadata.get('track_number', 0)
    title = metadata.get('title', os.path.splitext(os.path.basename(source_path))[0])
    ext = os.path.splitext(source_path)[1].lower()
    
    # Sanitize title for filename
    title = sanitize_filename(title)
    
    # Create filename
    if track_number:
        filename = f"{track_number:02d} - {title}{ext}"
    else:
        filename = f"{title}{ext}"
    
    dest_path = os.path.join(dest_dir, filename)
    
    # Copy the file
    shutil.copy2(source_path, dest_path)
    
    logger.info(f"Copied file: {source_path} -> {dest_path}")
    return dest_path


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python file_utils.py <directory_or_file>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    # Test finding audio files
    audio_files = find_audio_files(path)
    print(f"Found {len(audio_files)} audio files:")
    for file in audio_files[:5]:  # Print first 5 files
        print(f"  - {file}")
    if len(audio_files) > 5:
        print(f"  ... and {len(audio_files) - 5} more")
    
    # Test album structure detection
    if audio_files:
        structure = get_album_structure(audio_files)
        print("\nAlbum structure:")
        for key, value in structure.items():
            if key != 'files':  # Don't print the full file list
                print(f"  {key}: {value}")
    
    # Test cover art detection
    if os.path.isdir(path):
        cover = find_cover_art(path)
        print(f"\nCover art: {cover}")