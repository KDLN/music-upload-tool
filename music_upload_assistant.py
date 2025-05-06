#!/usr/bin/env python3
"""
Music-Upload-Assistant: A tool for preparing and uploading music files to various trackers.

This is the main entry point script that handles command-line arguments and
coordinates the overall workflow of the application.
"""

import os
import sys
import time
import json
import logging
import argparse
import asyncio
import shutil
from typing import Dict, List, Optional, Any, Union

# Import modules
from modules.audio_analyzer.audio_analyzer import AudioAnalyzer
from modules.metadata.tag_processor import TagProcessor
from modules.metadata.musicbrainz import MusicBrainzClient
from modules.metadata.acoustid import AcoustIDClient
from modules.upload.torrent import TorrentCreator
from modules.upload.description import DescriptionGenerator
from modules.utils.file_utils import (
    find_audio_files, get_album_structure, find_cover_art, 
    create_output_directory, copy_file_with_metadata
)
from modules.utils.naming import generate_release_name
from modules.utils.config_manager import ConfigManager
from modules.upload.tracker_manager import TrackerManager

# Import torrent client modules
try:
    from modules.upload.clients.qbittorrent import QBittorrentClient
except ImportError as e:
    logger.warning(f"qBittorrent client module not available: {e}")
    logger.warning("Torrent client features will be disabled")

# Set up logger
logger = logging.getLogger("music_upload_assistant")

# Try to import format handlers
try:
    from modules.audio_analyzer.format_handlers.flac_handler import FlacHandler
    from modules.audio_analyzer.format_handlers.mp3_handler import Mp3Handler
except ImportError as e:
    logger.error(f"Error importing format handlers: {e}")
    logger.error("Please make sure all required modules are available")
    sys.exit(1)


def setup_logging(config: Dict[str, Any]):
    """
    Set up logging based on configuration.
    
    Args:
        config: Configuration dictionary
    """
    log_config = config.get('logging', {})
    log_level_name = log_config.get('level', 'INFO')
    log_level = getattr(logging, log_level_name)
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_file = log_config.get('file', 'music_upload_assistant.log')
    
    handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # Create file handler if requested
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")
    
    # Configure root logger
    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)
    
    logger.info(f"Logging initialized with level {log_level_name}")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file using the ConfigManager.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        dict: Configuration dictionary
    """
    # Create a config manager
    config_manager = ConfigManager(config_path)
    
    # Return the loaded config
    return config_manager.get_config()


def format_handler_factory(file_path: str) -> Optional[Any]:
    """
    Create an appropriate format handler for a given file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        object: Format handler or None if not supported
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.flac':
        return FlacHandler()
    elif ext == '.mp3':
        return Mp3Handler()
    # Add more handlers as they are implemented
    
    logger.warning(f"No handler available for {ext} files")
    return None


def get_tracker_config(config: Dict[str, Any], tracker_id: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific tracker.
    
    Args:
        config: Main configuration dictionary
        tracker_id: Tracker identifier
        
    Returns:
        dict: Tracker configuration or None if not found
    """
    if 'trackers' not in config:
        return None
    
    return config['trackers'].get(tracker_id)


async def process_file(file_path: str, options: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single audio file.
    
    Args:
        file_path: Path to the audio file
        options: Processing options
        config: Configuration dictionary
        
    Returns:
        dict: Processing results
    """
    logger.info(f"Processing file: {file_path}")
    
    # Create a unique working directory for this file
    temp_dir = os.path.join(config['temp_dir'], os.path.basename(file_path))
    os.makedirs(temp_dir, exist_ok=True)
    
    # Get format handler
    format_handler = format_handler_factory(file_path)
    if not format_handler:
        return {
            'success': False,
            'error': f"Unsupported file format: {os.path.splitext(file_path)[1]}"
        }
    
    # Extract metadata
    try:
        metadata = format_handler.get_track_info(file_path)
        logger.info(f"Extracted metadata from {file_path}")
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return {
            'success': False,
            'error': f"Error extracting metadata: {str(e)}"
        }
    
    # Enrich metadata if requested
    if options.get('use_musicbrainz', False):
        try:
            mb_client = MusicBrainzClient(config)
            enriched_metadata = mb_client.enrich_metadata(metadata)
            metadata.update(enriched_metadata)
            logger.info("Enriched metadata with MusicBrainz")
        except Exception as e:
            logger.error(f"Error enriching metadata with MusicBrainz: {e}")
    
    if options.get('use_acoustid', False):
        try:
            acoustid_client = AcoustIDClient(config)
            await acoustid_client.identify_and_enrich(file_path, metadata)
            logger.info("Enriched metadata with AcoustID")
        except Exception as e:
            logger.error(f"Error enriching metadata with AcoustID: {e}")
    
    # Extract artwork to file if needed
    if 'artwork' in metadata and metadata['artwork']:
        artwork_path = os.path.join(temp_dir, "cover.jpg")
        try:
            with open(artwork_path, 'wb') as f:
                f.write(metadata['artwork'])
            metadata['artwork_path'] = artwork_path
            logger.info(f"Saved artwork to {artwork_path}")
        except Exception as e:
            logger.error(f"Error saving artwork: {e}")
    
    # Try to find a cover image if we don't have embedded artwork
    if 'artwork_path' not in metadata:
        try:
            # Check if there's a cover image in the same directory
            dir_path = os.path.dirname(file_path)
            cover_path = find_cover_art(dir_path)
            if cover_path:
                metadata['cover_art_path'] = cover_path
                logger.info(f"Found external cover art: {cover_path}")
                
                # Copy to temp_dir to ensure it's available
                temp_cover = os.path.join(temp_dir, "cover.jpg")
                shutil.copy2(cover_path, temp_cover)
                metadata['artwork_path'] = temp_cover
                logger.info(f"Copied cover art to {temp_cover}")
        except Exception as e:
            logger.error(f"Error finding/copying cover art: {e}")
    
    # Extract technical info
    try:
        mediainfo = format_handler.get_mediainfo(file_path)
        mediainfo_path = os.path.join(temp_dir, "MEDIAINFO.txt")
        with open(mediainfo_path, 'w', encoding='utf-8') as f:
            f.write(mediainfo)
        metadata['mediainfo_path'] = mediainfo_path
    except Exception as e:
        logger.error(f"Error generating MediaInfo: {e}")
    
    # Generate description
    if options.get('generate_description', True):
        try:
            description_generator = DescriptionGenerator(config)
            description = description_generator.generate_track_description(metadata, {
                'format': metadata.get('format', 'Unknown'),
                'sample_rate': f"{metadata.get('sample_rate', 0) / 1000:.1f} kHz",
                'bit_depth': f"{metadata.get('bit_depth', '')}",
                'channels': 'Stereo' if metadata.get('channels', 0) == 2 else 'Mono',
                'bitrate': f"{metadata.get('bitrate', 0)} kbps",
                'duration': time.strftime('%M:%S', time.gmtime(metadata.get('duration', 0)))
            })
            
            description_path = os.path.join(temp_dir, "DESCRIPTION.txt")
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(description)
            metadata['description_path'] = description_path
            
            logger.info("Generated description")
        except Exception as e:
            logger.error(f"Error generating description: {e}")
    
    # Create torrent if requested
    if options.get('create_torrent', False):
        try:
            torrent_creator = TorrentCreator(config)
            
            # Get tracker config if specified
            tracker_id = options.get('tracker')
            announce_url = options.get('announce_url')
            source = None
            
            if tracker_id:
                tracker_config = get_tracker_config(config, tracker_id)
                if tracker_config:
                    announce_url = tracker_config.get('announce_url', announce_url)
                    source = tracker_config.get('source_name')
            
            # Generate standardized release name
            # Check if perfect format is enabled in config
            if config.get('description', {}).get('template', '') == 'perfect_album':
                release_name = generate_perfect_name(metadata, config)
            else:
                release_name = generate_release_name(metadata, config, options)
            
            # Create torrent
            torrent_path = torrent_creator.create_torrent(
                file_path,
                announce_url=announce_url,
                source=source,
                comment=f"{metadata.get('title', 'Unknown')} - {metadata.get('artists', ['Unknown'])[0]}",
                piece_size=options.get('piece_size', 'auto'),
                custom_name=release_name
            )
            
            metadata['torrent_path'] = torrent_path
            metadata['release_name'] = release_name
            logger.info(f"Created torrent: {torrent_path}")
            
            # Add to qBittorrent if enabled
            qbt_config = config.get('qbittorrent', {})
            if qbt_config.get('enabled', False):
                try:
                    qbt_client = QBittorrentClient(config)
                    
                    # Determine save path
                    save_path = None
                    if qbt_config.get('use_original_path', True):
                        # Use the directory containing the original file
                        save_path = os.path.dirname(os.path.abspath(file_path))
                    
                    # Get cover art path if available
                    cover_path = metadata.get('artwork_path')
                    
                    # Add to qBittorrent
                    success, message = qbt_client.add_torrent(torrent_path, save_path, cover_path)
                    if success:
                        logger.info(f"Added torrent to qBittorrent: {message}")
                        metadata['added_to_client'] = True
                    else:
                        logger.error(f"Failed to add torrent to qBittorrent: {message}")
                        metadata['added_to_client'] = False
                except Exception as e:
                    logger.error(f"Error adding torrent to qBittorrent: {e}")
                    metadata['added_to_client'] = False
            
        except Exception as e:
            logger.error(f"Error creating torrent: {e}")
    
    # Upload to tracker if requested
    if options.get('upload', False) and options.get('tracker'):
        try:
            # Use tracker manager to get the tracker
            tracker_id = options.get('tracker')
            tracker_manager = TrackerManager(config)
            tracker_module = tracker_manager.get_tracker(tracker_id)
            
            if tracker_module:
                # Get description
                description_path = metadata.get('description_path')
                if description_path and os.path.exists(description_path):
                    with open(description_path, 'r', encoding='utf-8') as f:
                        description = f.read()
                else:
                    description = f"{metadata.get('title', 'Unknown')} by {', '.join(metadata.get('artists', ['Unknown']))}"
                
                # Get torrent path
                torrent_path = metadata.get('torrent_path')
                if torrent_path and os.path.exists(torrent_path):
                    # Upload torrent
                    success, message = tracker_module.upload(torrent_path, description, metadata)
                    if success:
                        logger.info(f"Uploaded to tracker {tracker_id}: {message}")
                        metadata['uploaded'] = True
                    else:
                        logger.error(f"Failed to upload to tracker {tracker_id}: {message}")
                        metadata['uploaded'] = False
                else:
                    logger.error(f"Torrent file not found for upload: {torrent_path}")
            else:
                # If no available tracker, show available ones
                available_trackers = tracker_manager.get_available_trackers()
                if available_trackers:
                    logger.warning(f"Tracker {tracker_id} not available. Available trackers: {', '.join(available_trackers)}")
                else:
                    logger.warning(f"No trackers are configured and available")
                    
                logger.info(f"Would upload to tracker: {options['tracker']}")
                metadata['uploaded'] = False
        except Exception as e:
            logger.error(f"Error uploading to tracker: {e}")
            metadata['uploaded'] = False
    
    return {
        'success': True,
        'metadata': metadata,
        'temp_dir': temp_dir
    }


async def process_album(album_path: str, options: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an album directory.
    
    Args:
        album_path: Path to the album directory
        options: Processing options
        config: Configuration dictionary
        
    Returns:
        dict: Processing results
    """
    logger.info(f"Processing album: {album_path}")
    
    # Find audio files
    audio_files = find_audio_files(album_path)
    if not audio_files:
        return {
            'success': False,
            'error': f"No supported audio files found in {album_path}"
        }
    
    # Analyze album structure
    album_structure = get_album_structure(audio_files)
    
    # Create a unique working directory for this album
    album_name = os.path.basename(album_path)
    temp_dir = os.path.join(config['temp_dir'], f"album_{album_name}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Find cover art
    cover_art_path = album_structure.get('cover_art') or find_cover_art(album_path)
    
    # Create a modified options dict for track processing that disables torrent creation
    # This prevents creating individual torrents for each track when processing an album
    track_options = options.copy()
    track_options['create_torrent'] = False  # Disable torrent creation for individual tracks
    track_options['upload'] = False  # Disable upload for individual tracks
    
    # Process each file with the modified options
    track_results = []
    
    for file_path in album_structure['files']:
        # Use the modified options that disable torrent creation
        result = await process_file(file_path, track_options, config)
        if result['success']:
            track_results.append(result)
        else:
            logger.warning(f"Error processing {file_path}: {result.get('error', 'Unknown error')}")
    
    if not track_results:
        return {
            'success': False,
            'error': "Failed to process any files in the album"
        }
    
    # Consolidate album metadata
    album_metadata = consolidate_album_metadata(track_results)
    
    # Add cover art
    if cover_art_path:
        album_metadata['cover_art_path'] = cover_art_path
    
    # Generate album description
    if options.get('generate_description', True):
        try:
            # Check if perfect format is enabled
            if config.get('description', {}).get('template', '') == 'perfect_album':
                # Collect track info in the format needed for perfect description
                track_info = []
                for result in track_results:
                    track_metadata = result['metadata']
                    
                    # Convert duration to string format
                    duration_str = "00:00"
                    if 'duration' in track_metadata:
                        duration_seconds = track_metadata['duration']
                        minutes = int(duration_seconds // 60)
                        seconds = int(duration_seconds % 60)
                        duration_str = f"{minutes:02d}:{seconds:02d}"
                    
                    # Calculate file size in bytes
                    file_size_bytes = 0
                    if 'file_size' in track_metadata:
                        file_size_bytes = track_metadata['file_size']
                    
                    track_info.append({
                        'title': track_metadata.get('title', 'Unknown'),
                        'artists': track_metadata.get('artists', []),
                        'track_number': track_metadata.get('track_number', 0),
                        'disc_number': track_metadata.get('disc_number', 1),
                        'duration': duration_str,
                        'duration_seconds': track_metadata.get('duration', 0),
                        'file_size_bytes': file_size_bytes
                    })
                
                # Generate perfect description
                description = generate_perfect_description(album_metadata, track_info, config)
            else:
                # Use standard description generator
                description_generator = DescriptionGenerator(config)
                
                # Collect quality info from each track
                quality_info = []
                for result in track_results:
                    metadata = result['metadata']
                    quality_info.append({
                        'title': metadata.get('title', 'Unknown'),
                        'format': metadata.get('format', 'Unknown'),
                        'sample_rate': f"{metadata.get('sample_rate', 0) / 1000:.1f} kHz",
                        'bit_depth': f"{metadata.get('bit_depth', '')}",
                        'channels': 'Stereo' if metadata.get('channels', 0) == 2 else 'Mono',
                        'bitrate': f"{metadata.get('bitrate', 0)} kbps",
                        'duration': time.strftime('%M:%S', time.gmtime(metadata.get('duration', 0)))
                    })
                
                description = description_generator.generate_album_description(album_metadata, quality_info)
            
            description_path = os.path.join(temp_dir, "ALBUM_DESCRIPTION.txt")
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(description)
            album_metadata['description_path'] = description_path
            
            logger.info("Generated album description")
        except Exception as e:
            logger.error(f"Error generating album description: {e}")
    
    # Create torrent if requested
    if options.get('create_torrent', False):
        try:
            torrent_creator = TorrentCreator(config)
            
            # Get tracker config if specified
            tracker_id = options.get('tracker')
            announce_url = options.get('announce_url')
            source = None
            
            if tracker_id:
                tracker_config = get_tracker_config(config, tracker_id)
                if tracker_config:
                    announce_url = tracker_config.get('announce_url', announce_url)
                    source = tracker_config.get('source_name')
            
            # Generate standardized release name
            # Check if perfect format is enabled in config
            if config.get('description', {}).get('template', '') == 'perfect_album':
                release_name = generate_perfect_name(album_metadata, config)
            else:
                release_name = generate_release_name(album_metadata, config, options)
            
            # Create torrent
            torrent_path = torrent_creator.create_torrent(
                album_path,
                announce_url=announce_url,
                source=source,
                comment=f"{album_metadata.get('album', 'Unknown')} - "
                       f"{album_metadata.get('album_artists', ['Unknown'])[0]}",
                piece_size=options.get('piece_size', 'auto'),
                custom_name=release_name
            )
            
            album_metadata['torrent_path'] = torrent_path
            album_metadata['release_name'] = release_name
            logger.info(f"Created album torrent: {torrent_path}")
            
            # Add to qBittorrent if enabled
            qbt_config = config.get('qbittorrent', {})
            if qbt_config.get('enabled', False):
                try:
                    qbt_client = QBittorrentClient(config)
                    
                    # Determine save path
                    save_path = None
                    if qbt_config.get('use_original_path', True):
                        # Use the directory containing the album
                        save_path = os.path.abspath(album_path)
                    
                    # Get cover art path if available
                    cover_path = album_metadata.get('cover_art_path')
                    
                    # Add to qBittorrent
                    success, message = qbt_client.add_torrent(torrent_path, save_path, cover_path)
                    if success:
                        logger.info(f"Added album torrent to qBittorrent: {message}")
                        album_metadata['added_to_client'] = True
                    else:
                        logger.error(f"Failed to add album torrent to qBittorrent: {message}")
                        album_metadata['added_to_client'] = False
                except Exception as e:
                    logger.error(f"Error adding album torrent to qBittorrent: {e}")
                    album_metadata['added_to_client'] = False
                    
        except Exception as e:
            logger.error(f"Error creating album torrent: {e}")
    
    # Upload to tracker if requested
    if options.get('upload', False) and options.get('tracker'):
        try:
            # Use tracker manager to get the tracker
            tracker_id = options.get('tracker')
            tracker_manager = TrackerManager(config)
            tracker_module = tracker_manager.get_tracker(tracker_id)
            
            if tracker_module:
                # Get description
                description_path = album_metadata.get('description_path')
                if description_path and os.path.exists(description_path):
                    with open(description_path, 'r', encoding='utf-8') as f:
                        description = f.read()
                else:
                    description = f"{album_metadata.get('album', 'Unknown')} by {', '.join(album_metadata.get('album_artists', ['Unknown']))}"
                
                # Get torrent path
                torrent_path = album_metadata.get('torrent_path')
                if torrent_path and os.path.exists(torrent_path):
                    # Upload torrent
                    success, message = tracker_module.upload(torrent_path, description, album_metadata)
                    if success:
                        logger.info(f"Uploaded album to tracker {tracker_id}: {message}")
                        album_metadata['uploaded'] = True
                    else:
                        logger.error(f"Failed to upload album to tracker {tracker_id}: {message}")
                        album_metadata['uploaded'] = False
                else:
                    logger.error(f"Album torrent file not found for upload: {torrent_path}")
            else:
                # If no available tracker, show available ones
                available_trackers = tracker_manager.get_available_trackers()
                if available_trackers:
                    logger.warning(f"Tracker {tracker_id} not available. Available trackers: {', '.join(available_trackers)}")
                else:
                    logger.warning(f"No trackers are configured and available")
                    
                logger.info(f"Would upload album to tracker: {options['tracker']}")
                album_metadata['uploaded'] = False
        except Exception as e:
            logger.error(f"Error uploading album to tracker: {e}")
            album_metadata['uploaded'] = False
    
    return {
        'success': True,
        'metadata': album_metadata,
        'track_results': track_results,
        'temp_dir': temp_dir
    }


def consolidate_album_metadata(track_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Consolidate metadata from multiple tracks into album metadata.
    
    Args:
        track_results: List of track processing results
        
    Returns:
        dict: Consolidated album metadata
    """
    if not track_results:
        return {}
    
    # Start with the metadata from the first track
    first_track = track_results[0]['metadata']
    album_metadata = {
        'album': first_track.get('album', 'Unknown Album'),
        'album_artists': first_track.get('album_artists', first_track.get('artists', ['Unknown Artist'])),
        'year': first_track.get('year'),
        'date': first_track.get('date'),
        'genres': first_track.get('genres', []),
        'label': first_track.get('label'),
        'catalog_number': first_track.get('catalog_number'),
        'release_country': first_track.get('release_country'),
        'total_tracks': len(track_results),
        'musicbrainz_release_id': first_track.get('musicbrainz_release_id'),
        'discogs_release_id': first_track.get('discogs_release_id')
    }
    
    # Check for multiple disc numbers
    disc_numbers = set()
    for result in track_results:
        if 'disc_number' in result['metadata']:
            disc_numbers.add(result['metadata']['disc_number'])
    
    if disc_numbers:
        album_metadata['total_discs'] = max(disc_numbers)
    
    # Combine genres
    all_genres = set()
    for result in track_results:
        if 'genres' in result['metadata'] and result['metadata']['genres']:
            all_genres.update(result['metadata']['genres'])
    
    if all_genres:
        album_metadata['genres'] = sorted(list(all_genres))
    
    return album_metadata


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Music Upload Assistant - Prepare and upload music files to trackers.'
    )
    
    parser.add_argument('path', help='Path to audio file or album directory')
    parser.add_argument('--tracker', '-t', help='Target tracker for upload')
    parser.add_argument('--album', '-a', action='store_true', 
                      help='Force processing as album even for single file')
    parser.add_argument('--single', '-s', action='store_true', 
                      help='Force processing as single tracks even for directories')
    
    # Media type and format options
    parser.add_argument('--format', choices=['FLAC', 'MP3', 'AAC', 'WAV', 'ALAC'],
                      help='Override audio format for release naming')
    parser.add_argument('--media', choices=['CD', 'WEB', 'Vinyl', 'DVD', 'SACD', 'DAT', 'Cassette', 'Blu-Ray'],
                      help='Specify media source for release naming')
    parser.add_argument('--bitdepth', choices=['16', '24', '32'],
                      help='Specify bit depth for release naming')
    parser.add_argument('--perfect', action='store_true',
                      help='Use perfect upload format for naming and description')
    
    # Metadata sources
    parser.add_argument('--musicbrainz', action='store_true', 
                      help='Use MusicBrainz for metadata lookup')
    parser.add_argument('--acoustid', action='store_true', 
                      help='Use AcoustID fingerprinting for identification')
    
    # Torrent options
    parser.add_argument('--create-torrent', action='store_true', 
                      help='Create torrent file')
    parser.add_argument('--piece-size', type=int, 
                      help='Torrent piece size in KB')
    parser.add_argument('--announce-url', 
                      help='Tracker announce URL for torrent')
    parser.add_argument('--add-to-client', action='store_true',
                      help='Add torrent to configured client (qBittorrent)')
    parser.add_argument('--no-add-to-client', action='store_true',
                      help='Do not add torrent to client even if enabled in config')
    
    # Output options
    parser.add_argument('--output', '-o', 
                      help='Output file for generated description')
    parser.add_argument('--json', action='store_true', 
                      help='Output results as JSON')
    parser.add_argument('--upload', '-u', action='store_true', 
                      help='Upload to tracker')
    
    # Misc options
    parser.add_argument('--config', '-c', 
                      help='Path to config file')
    parser.add_argument('--verbose', '-v', action='store_true', 
                      help='Enable verbose logging')
    parser.add_argument('--debug', '-d', action='store_true',
                      help='Enable debug mode (no actual uploads)')
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    config['debug'] = args.debug
    
    # Set up logging
    if args.verbose:
        config['logging']['level'] = 'DEBUG'
    setup_logging(config)
    
    # Create necessary directories
    os.makedirs(config['temp_dir'], exist_ok=True)
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # Prepare processing options
    options = {
        'use_musicbrainz': args.musicbrainz,
        'use_acoustid': args.acoustid,
        'create_torrent': args.create_torrent,
        'announce_url': args.announce_url,
        'tracker': args.tracker,
        'upload': args.upload,
        'debug': args.debug,
        'generate_description': True
    }
    
    # Handle format override options
    if args.format:
        options['format_override'] = args.format
    
    if args.media:
        options['media_override'] = args.media
        
    if args.bitdepth:
        options['bitdepth_override'] = args.bitdepth
    
    # Handle perfect format option
    if args.perfect:
        config['description'] = config.get('description', {})
        config['description']['template'] = 'perfect_album'
    
    # Handle qBittorrent options
    qbt_config = config.get('qbittorrent', {})
    if args.add_to_client:
        # Enable qBittorrent even if disabled in config
        qbt_config['enabled'] = True
        config['qbittorrent'] = qbt_config
    elif args.no_add_to_client:
        # Disable qBittorrent even if enabled in config
        qbt_config['enabled'] = False
        config['qbittorrent'] = qbt_config
    
    if args.piece_size:
        options['piece_size'] = args.piece_size
    
    # Check if path exists
    if not os.path.exists(args.path):
        logger.error(f"Path not found: {args.path}")
        sys.exit(1)
    
    # Process the path
    try:
        if os.path.isfile(args.path) and not args.album:
            # Process as single file
            result = await process_file(args.path, options, config)
        else:
            # Process as album
            result = await process_album(args.path, options, config)
        
        # Output results
        if args.json:
            # Convert result to JSON-serializable format
            json_result = {}
            for k, v in result.items():
                if k != 'metadata':
                    json_result[k] = v
            
            # Handle metadata separately to avoid binary data
            if 'metadata' in result:
                json_result['metadata'] = {}
                for k, v in result['metadata'].items():
                    if k != 'artwork':  # Skip binary data
                        json_result['metadata'][k] = v
            
            print(json.dumps(json_result, indent=2))
        else:
            # Print human-readable output
            print("\n========== Processing Results ==========")
            
            if not result['success']:
                print(f"Error: {result.get('error', 'Unknown error')}")
                sys.exit(1)
            
            if 'track_results' in result:
                # Album results
                print(f"\nAlbum: {result['metadata'].get('album', 'Unknown')}")
                print(f"Artist: {', '.join(result['metadata'].get('album_artists', ['Unknown']))}")
                print(f"Tracks: {len(result['track_results'])}")
                
                if 'description_path' in result['metadata']:
                    print(f"Description: {result['metadata']['description_path']}")
                
                if 'release_name' in result['metadata']:
                    print(f"\nRelease Name: {result['metadata']['release_name']}")
                
                if 'torrent_path' in result['metadata']:
                    print(f"Torrent: {result['metadata']['torrent_path']}")
                
                if result['metadata'].get('uploaded', False):
                    print(f"Uploaded to: {options['tracker']}")
                    # Check if we have cover art paths
                    if result['metadata'].get('cover_art_path') or result['metadata'].get('artwork_path'):
                        print("Cover art included in tracker upload")
                    
                if result['metadata'].get('added_to_client', False):
                    print("Added to qBittorrent for seeding")
                    if result['metadata'].get('cover_art_path') or result['metadata'].get('artwork_path'):
                        print("Cover art added to torrent")
                
                print("\nProcessed Tracks:")
                for i, track in enumerate(result['track_results']):
                    metadata = track['metadata']
                    print(f"{i+1}. {metadata.get('title', 'Unknown')} - "
                          f"{', '.join(metadata.get('artists', ['Unknown']))}")
            else:
                # Single track results
                metadata = result['metadata']
                print(f"\nTrack: {metadata.get('title', 'Unknown')}")
                print(f"Artist: {', '.join(metadata.get('artists', ['Unknown']))}")
                print(f"Album: {metadata.get('album', 'Unknown')}")
                print(f"Format: {metadata.get('format', 'Unknown')}")
                
                if 'description_path' in metadata:
                    print(f"Description: {metadata['description_path']}")
                
                if 'release_name' in metadata:
                    print(f"\nRelease Name: {metadata['release_name']}")
                
                if 'torrent_path' in metadata:
                    print(f"Torrent: {metadata['torrent_path']}")
                
                if metadata.get('uploaded', False):
                    print(f"Uploaded to: {options['tracker']}")
                    # Check if we have cover art paths
                    if metadata.get('cover_art_path') or metadata.get('artwork_path'):
                        print("Cover art included in tracker upload")
                    
                if metadata.get('added_to_client', False):
                    print("Added to qBittorrent for seeding")
                    if metadata.get('artwork_path'):
                        print("Cover art added to torrent")
        
        # Copy description to output file if requested
        if args.output:
            description_path = (result.get('metadata', {}).get('description_path') or 
                               result.get('track_results', [{}])[0].get('metadata', {}).get('description_path'))
            
            if description_path and os.path.exists(description_path):
                shutil.copy2(description_path, args.output)
                print(f"\nDescription copied to: {args.output}")
            else:
                logger.error(f"Description file not found")
    
    except Exception as e:
        logger.error(f"Error processing {args.path}: {e}", exc_info=True)
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Fix for Windows asyncio event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())