#!/usr/bin/env python3
"""
Fix Upload Format script for Music-Upload-Assistant.
This script takes a path to an album and generates a "perfect" format upload
following the format shown in the example.
"""

import os
import sys
import logging
import argparse
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix-upload-format")

# Import perfect format utilities
try:
    from modules.utils.perfect_format import generate_perfect_name, generate_perfect_description
    from modules.utils.file_utils import find_audio_files
    from modules.audio_analyzer.audio_analyzer import AudioAnalyzer
    from modules.metadata.tag_processor import TagProcessor
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    logger.error("Make sure you run this script from the root directory of the project")
    sys.exit(1)

def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from a file."""
    # Default config
    config = {
        'app_name': 'Music-Upload-Assistant',
        'app_version': '0.1.0',
        'uploader_name': 'R&H',
        'description': {
            'template': 'perfect_album'
        }
    }
    
    # If config path provided, load it
    if config_path and os.path.exists(config_path):
        try:
            if config_path.endswith('.py'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                
                # Extract the config dictionary using exec
                config_dict = {}
                exec(config_content, config_dict)
                
                if 'config' in config_dict:
                    config.update(config_dict['config'])
            elif config_path.endswith('.json'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    config.update(loaded_config)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    return config

def analyze_album(album_path: str) -> Dict[str, Any]:
    """Analyze an album directory and extract metadata."""
    # Find audio files
    audio_files = find_audio_files(album_path)
    if not audio_files:
        logger.error(f"No audio files found in {album_path}")
        return {}
    
    # Use audio analyzer
    analyzer = AudioAnalyzer()
    tag_processor = TagProcessor()
    
    # Process each file
    track_info = []
    album_metadata = {}
    
    for file_path in audio_files:
        try:
            # Extract metadata
            metadata = tag_processor.extract_metadata(file_path)
            
            # Convert to standard format
            duration_str = "00:00"
            if 'duration' in metadata:
                duration_seconds = metadata['duration']
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                duration_str = f"{minutes:02d}:{seconds:02d}"
            
            track_info.append({
                'title': metadata.get('title', os.path.basename(file_path)),
                'artists': metadata.get('artists', [os.path.basename(album_path)]),
                'track_number': metadata.get('track_number', 0),
                'disc_number': metadata.get('disc_number', 1),
                'duration': duration_str,
                'duration_seconds': metadata.get('duration', 0),
                'file_size_bytes': metadata.get('file_size', 0) or os.path.getsize(file_path)
            })
            
            # If this is the first file, use it for album metadata
            if not album_metadata:
                album_metadata = {
                    'album': metadata.get('album', os.path.basename(album_path)),
                    'album_artists': metadata.get('album_artists', metadata.get('artists', [os.path.basename(album_path)])),
                    'year': metadata.get('year', ''),
                    'format': metadata.get('format', 'FLAC'),
                    'media': metadata.get('media', 'WEB'),
                    'bit_depth': metadata.get('bit_depth', 16),
                    'sample_rate': metadata.get('sample_rate', 44100),
                    'channels': metadata.get('channels', 2),
                    'barcode': metadata.get('barcode', metadata.get('catalog_number', ''))
                }
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    return {
        'album_metadata': album_metadata,
        'track_info': track_info
    }

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Fix Upload Format for Music-Upload-Assistant')
    parser.add_argument('album_path', help='Path to album directory')
    parser.add_argument('--output', '-o', help='Output directory for generated files')
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--format', choices=['FLAC', 'MP3', 'AAC', 'WAV'], help='Override audio format')
    parser.add_argument('--media', help='Override media source (e.g., WEB, CD)')
    parser.add_argument('--uploader', help='Uploader name to use in release name')
    parser.add_argument('--barcode', help='Barcode number to include in release name')
    
    args = parser.parse_args()
    
    # Check if path exists
    if not os.path.isdir(args.album_path):
        logger.error(f"Album path is not a directory: {args.album_path}")
        return 1
    
    # Load config
    config = load_config(args.config)
    
    # Apply command-line overrides
    if args.uploader:
        config['uploader_name'] = args.uploader
    
    # Analyze album
    album_data = analyze_album(args.album_path)
    if not album_data:
        logger.error("Failed to analyze album")
        return 1
    
    album_metadata = album_data['album_metadata']
    track_info = album_data['track_info']
    
    # Apply command-line overrides to metadata
    if args.format:
        album_metadata['format'] = args.format
    if args.media:
        album_metadata['media'] = args.media
    if args.barcode:
        album_metadata['barcode'] = args.barcode
    
    # Generate perfect name
    perfect_name = generate_perfect_name(album_metadata, config)
    logger.info(f"Generated perfect name: {perfect_name}")
    
    # Generate perfect description
    perfect_description = generate_perfect_description(album_metadata, track_info, config)
    
    # Determine output directory
    output_dir = args.output or os.path.join('output', os.path.basename(args.album_path))
    os.makedirs(output_dir, exist_ok=True)
    
    # Save perfect name
    name_file = os.path.join(output_dir, "perfect_name.txt")
    with open(name_file, 'w', encoding='utf-8') as f:
        f.write(perfect_name)
    
    # Save perfect description
    desc_file = os.path.join(output_dir, "perfect_description.txt")
    with open(desc_file, 'w', encoding='utf-8') as f:
        f.write(perfect_description)
    
    print(f"\nGenerated perfect upload format for: {album_metadata['album']}")
    print(f"Release Name: {perfect_name}")
    print(f"Files saved to: {output_dir}")
    print(f"  - Name: {name_file}")
    print(f"  - Description: {desc_file}")
    
    # Suggest next steps
    print("\nNext steps:")
    print("1. Use the generated name for your upload")
    print("2. Copy the description from the text file")
    print("3. Run the main tool with the --perfect option for future uploads:")
    print(f"   python music_upload_assistant.py \"{args.album_path}\" --tracker YUS --create-torrent --upload --perfect")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
