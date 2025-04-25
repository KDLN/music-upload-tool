#!/usr/bin/env python3
"""
Test script for Music-Upload-Assistant.
This script allows testing the core functionality without doing actual uploads.
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-music-upload-assistant")

# Try to import required modules
try:
    from modules.audio_analyzer.audio_analyzer import AudioAnalyzer
    from modules.metadata.tag_processor import TagProcessor
    from modules.utils.file_utils import find_audio_files, get_album_structure
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    logger.error("Please run this script from the root directory of the project")
    sys.exit(1)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Music Upload Assistant Test Script'
    )
    
    parser.add_argument('path', help='Path to audio file or album directory')
    parser.add_argument('--album', '-a', action='store_true', 
                      help='Force processing as album even for single file')
    parser.add_argument('--verbose', '-v', action='store_true', 
                      help='Enable verbose output')
    parser.add_argument('--output', '-o', 
                      help='Output file for JSON results')
    
    return parser.parse_args()

async def process_file(file_path: str) -> Dict[str, Any]:
    """
    Process a single audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        dict: Processing results
    """
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Create tag processor
        tag_processor = TagProcessor()
        
        # Extract metadata
        metadata = tag_processor.extract_metadata(file_path)
        logger.info(f"Extracted metadata from {file_path}")
        
        # Normalize metadata
        normalized = tag_processor.normalize_metadata(metadata)
        
        # Create audio analyzer
        audio_analyzer = AudioAnalyzer()
        
        # Analyze audio quality
        quality_info = audio_analyzer.get_audio_summary(metadata)
        
        # Extract and save artwork if present
        artwork_path = None
        if 'artwork' in metadata and metadata['artwork']:
            try:
                artwork_path = os.path.join(os.path.dirname(file_path), 
                                         f"{os.path.splitext(os.path.basename(file_path))[0]}_cover.jpg")
                with open(artwork_path, 'wb') as f:
                    f.write(metadata['artwork'])
                logger.info(f"Saved artwork to {artwork_path}")
            except Exception as e:
                logger.error(f"Error saving artwork: {e}")
        
        # Create result dictionary
        result = {
            'file_path': file_path,
            'metadata': {k: v for k, v in normalized.items() if k != 'artwork'},
            'quality': quality_info,
            'artwork_path': artwork_path
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return {
            'file_path': file_path,
            'error': str(e)
        }

async def process_album(album_path: str) -> Dict[str, Any]:
    """
    Process an album directory.
    
    Args:
        album_path: Path to the album directory
        
    Returns:
        dict: Processing results
    """
    logger.info(f"Processing album: {album_path}")
    
    # Find audio files
    audio_files = find_audio_files(album_path)
    if not audio_files:
        return {
            'album_path': album_path,
            'error': f"No supported audio files found in {album_path}"
        }
    
    # Analyze album structure
    album_structure = get_album_structure(audio_files)
    
    # Process each file
    track_results = []
    for file_path in album_structure['files']:
        result = await process_file(file_path)
        track_results.append(result)
    
    # Create audio analyzer for album analysis
    audio_analyzer = AudioAnalyzer()
    
    # Extract metadata from track results
    track_metadata = []
    for result in track_results:
        if 'metadata' in result:
            track_metadata.append(result['metadata'])
    
    # Analyze album as a whole
    try:
        # Consolidate album info
        album_info = {}
        
        if track_metadata:
            first_track = track_metadata[0]
            album_info['album'] = first_track.get('album', 'Unknown Album')
            album_info['album_artists'] = first_track.get('album_artists', 
                                                        first_track.get('artists', ['Unknown Artist']))
            album_info['year'] = first_track.get('year')
            album_info['total_tracks'] = len(track_results)
            
            # List all unique genres across tracks
            genres = set()
            for track in track_metadata:
                if 'genres' in track and track['genres']:
                    for genre in track['genres']:
                        genres.add(genre)
            
            if genres:
                album_info['genres'] = sorted(list(genres))
            
            # Get other album metadata
            for field in ['label', 'catalog_number', 'release_country', 
                         'musicbrainz_release_id', 'discogs_release_id']:
                if field in first_track and first_track[field]:
                    album_info[field] = first_track[field]
        
        # Calculate total duration
        total_duration = sum(track.get('duration', 0) for track in track_metadata)
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        album_info['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Check for mixed formats
        formats = set(track.get('format', 'Unknown') for track in track_metadata)
        album_info['formats'] = sorted(list(formats))
        album_info['mixed_format'] = len(formats) > 1
        
        # Get album cover art if available
        album_info['cover_art'] = album_structure.get('cover_art')
        
        # Use audio analyzer to get album quality summary
        album_quality = audio_analyzer._consolidate_album_info({'file_results': track_metadata})
        album_summary = audio_analyzer.get_album_summary(album_quality)
        
        # Create result dictionary
        result = {
            'album_path': album_path,
            'album_info': album_info,
            'album_quality': album_summary,
            'track_results': track_results,
            'is_multi_disc': album_structure.get('is_multi_disc', False),
            'disc_count': album_structure.get('disc_count', 1)
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing album: {e}")
        return {
            'album_path': album_path,
            'track_results': track_results,
            'error': str(e)
        }

async def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if path exists
    if not os.path.exists(args.path):
        logger.error(f"Path not found: {args.path}")
        sys.exit(1)
    
    # Process the path
    try:
        if os.path.isfile(args.path) and not args.album:
            # Process as single file
            result = await process_file(args.path)
            
            # Print file results
            print("\n===== File Analysis Results =====")
            print(f"File: {result['file_path']}")
            
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                metadata = result['metadata']
                print(f"\nTitle: {metadata.get('title', 'Unknown')}")
                print(f"Artist: {', '.join(metadata.get('artists', ['Unknown']))}")
                print(f"Album: {metadata.get('album', 'Unknown')}")
                
                if 'track_number' in metadata:
                    track_info = f"Track {metadata['track_number']}"
                    if 'total_tracks' in metadata:
                        track_info += f" of {metadata['total_tracks']}"
                    print(track_info)
                
                print(f"\nFormat: {metadata.get('format', 'Unknown')}")
                if 'sample_rate' in metadata:
                    print(f"Sample Rate: {metadata.get('sample_rate', 0) / 1000:.1f} kHz")
                if 'bit_depth' in metadata:
                    print(f"Bit Depth: {metadata.get('bit_depth')} bits")
                print(f"Channels: {metadata.get('channels', 0)}")
                if 'bitrate' in metadata:
                    print(f"Bitrate: {metadata.get('bitrate', 0)} kbps")
                
                if 'duration' in metadata:
                    minutes = int(metadata['duration'] // 60)
                    seconds = int(metadata['duration'] % 60)
                    print(f"Duration: {minutes}:{seconds:02d}")
                
                if 'file_size' in metadata:
                    size_mb = metadata['file_size'] / (1024 * 1024)
                    print(f"File Size: {size_mb:.2f} MB")
                
                if 'quality' in result:
                    print("\nQuality Assessment:")
                    for key, value in result['quality'].items():
                        if key != 'warnings':
                            print(f"  {key.capitalize()}: {value}")
                
                if 'warnings' in result.get('quality', {}):
                    print("\nWarnings:")
                    for warning in result['quality']['warnings']:
                        print(f"  - {warning}")
                
                if result.get('artwork_path'):
                    print(f"\nArtwork saved to: {result['artwork_path']}")
        else:
            # Process as album
            result = await process_album(args.path)
            
            # Print album results
            print("\n===== Album Analysis Results =====")
            print(f"Album: {result.get('album_path')}")
            
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                album_info = result['album_info']
                print(f"\nAlbum: {album_info.get('album', 'Unknown')}")
                print(f"Artist: {', '.join(album_info.get('album_artists', ['Unknown']))}")
                
                if 'year' in album_info:
                    print(f"Year: {album_info['year']}")
                
                if 'total_tracks' in album_info:
                    print(f"Tracks: {album_info['total_tracks']}")
                
                if 'formats' in album_info:
                    print(f"Formats: {', '.join(album_info['formats'])}")
                
                if 'duration' in album_info:
                    print(f"Duration: {album_info['duration']}")
                
                if 'genres' in album_info:
                    print(f"Genres: {', '.join(album_info['genres'])}")
                
                if 'label' in album_info:
                    print(f"Label: {album_info['label']}")
                
                if 'catalog_number' in album_info:
                    print(f"Catalog Number: {album_info['catalog_number']}")
                
                if 'release_country' in album_info:
                    print(f"Release Country: {album_info['release_country']}")
                
                if 'cover_art' in album_info and album_info['cover_art']:
                    print(f"Cover Art: {album_info['cover_art']}")
                
                if 'mixed_format' in album_info and album_info['mixed_format']:
                    print("\nNote: Album contains mixed formats")
                
                if result.get('is_multi_disc'):
                    print(f"Multi-disc album with {result.get('disc_count', 0)} discs")
                
                # Print track list
                print("\nTrack List:")
                for i, track in enumerate(result['track_results']):
                    if 'error' in track:
                        print(f"  {i+1}. Error: {track['error']}")
                    else:
                        metadata = track['metadata']
                        format_info = f"[{metadata.get('format', 'Unknown')}"
                        if 'bitrate' in metadata:
                            format_info += f" {metadata['bitrate']} kbps"
                        elif 'bit_depth' in metadata:
                            format_info += f" {metadata['bit_depth']}-bit"
                        format_info += "]"
                        
                        print(f"  {i+1}. {metadata.get('title', 'Unknown')} - "
                              f"{', '.join(metadata.get('artists', ['Unknown']))} {format_info}")
                
                if 'album_quality' in result:
                    quality = result['album_quality']
                    print("\nAlbum Quality Assessment:")
                    
                    if 'notes' in quality:
                        print("Notes:")
                        for note in quality['notes']:
                            print(f"  - {note}")
                    
                    if 'warnings' in quality:
                        print("Warnings:")
                        for warning in quality['warnings']:
                            print(f"  - {warning}")
        
        # Save JSON output if requested
        if args.output:
            # Create a serializable result (remove binary data)
            serializable_result = json.loads(json.dumps(result, default=str))
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, indent=2)
            
            print(f"\nResults saved to {args.output}")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Fix for Windows asyncio event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())