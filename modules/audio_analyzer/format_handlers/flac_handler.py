"""
FLAC format handler for the Music-Upload-Assistant.
Handles parsing and writing metadata for FLAC audio files.
"""

import os
import logging
from typing import Dict, Optional, Tuple, Any, BinaryIO
from mutagen.flac import FLAC, Picture
from PIL import Image
import io

from modules.audio_analyzer.format_handlers.base_handler import FormatHandler

logger = logging.getLogger(__name__)

class FlacHandler(FormatHandler):
    """Handler for FLAC audio files."""
    
    def __init__(self):
        """Initialize the FLAC format handler."""
        super().__init__()
        self.name = "FLAC Handler"
        self.extensions = ["flac"]
    
    def get_track_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract track metadata and technical info from FLAC file.
        
        Args:
            file_path: Path to the FLAC audio file
            
        Returns:
            Dict: Populated track metadata dictionary
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            flac_file = FLAC(file_path)
            metadata = {}
            
            # Basic file info
            metadata['file_path'] = file_path
            metadata['file_name'] = os.path.basename(file_path)
            metadata['format'] = "FLAC"
            metadata['file_size'] = os.path.getsize(file_path)
            metadata['duration'] = flac_file.info.length
            
            # Technical info
            metadata['bit_depth'] = flac_file.info.bits_per_sample
            metadata['sample_rate'] = flac_file.info.sample_rate
            metadata['channels'] = flac_file.info.channels
            metadata['bitrate'] = int(metadata['file_size'] * 8 / metadata['duration']) if metadata['duration'] > 0 else 0
            metadata['codec'] = "FLAC"
            metadata['compression'] = "Lossless"
            
            # Metadata
            if 'title' in flac_file:
                metadata['title'] = flac_file['title'][0]
                
            if 'artist' in flac_file:
                metadata['artists'] = flac_file['artist']
                
            if 'album' in flac_file:
                metadata['album'] = flac_file['album'][0]
                
            if 'albumartist' in flac_file:
                metadata['album_artists'] = flac_file['albumartist']
            elif 'album artist' in flac_file:
                metadata['album_artists'] = flac_file['album artist']
                
            if 'tracknumber' in flac_file:
                try:
                    track_info = flac_file['tracknumber'][0]
                    if '/' in track_info:
                        track_num, total_tracks = track_info.split('/')
                        metadata['track_number'] = int(track_num)
                        metadata['total_tracks'] = int(total_tracks)
                    else:
                        metadata['track_number'] = int(track_info)
                except (ValueError, IndexError):
                    logger.warning(f"Invalid track number format: {flac_file['tracknumber'][0]}")
                    
            if 'discnumber' in flac_file:
                try:
                    disc_info = flac_file['discnumber'][0]
                    if '/' in disc_info:
                        disc_num, total_discs = disc_info.split('/')
                        metadata['disc_number'] = int(disc_num)
                        metadata['total_discs'] = int(total_discs)
                    else:
                        metadata['disc_number'] = int(disc_info)
                except (ValueError, IndexError):
                    logger.warning(f"Invalid disc number format: {flac_file['discnumber'][0]}")
                    
            if 'date' in flac_file:
                metadata['date'] = flac_file['date'][0]
                # Try to extract year from date
                try:
                    metadata['year'] = int(flac_file['date'][0].split('-')[0])
                except (ValueError, IndexError):
                    pass
            elif 'year' in flac_file:
                try:
                    metadata['year'] = int(flac_file['year'][0])
                except (ValueError, IndexError):
                    metadata['year'] = flac_file['year'][0]
                    
            if 'genre' in flac_file:
                metadata['genres'] = flac_file['genre']
                
            if 'composer' in flac_file:
                metadata['composers'] = flac_file['composer']
                
            if 'performer' in flac_file:
                metadata['performers'] = flac_file['performer']
                
            if 'label' in flac_file:
                metadata['label'] = flac_file['label'][0]
                
            if 'catalognumber' in flac_file:
                metadata['catalog_number'] = flac_file['catalognumber'][0]
                
            if 'country' in flac_file:
                metadata['release_country'] = flac_file['country'][0]
                
            # MusicBrainz IDs
            if 'musicbrainz_albumid' in flac_file:
                metadata['musicbrainz_release_id'] = flac_file['musicbrainz_albumid'][0]
                
            if 'musicbrainz_trackid' in flac_file:
                metadata['musicbrainz_recording_id'] = flac_file['musicbrainz_trackid'][0]
                
            if 'musicbrainz_artistid' in flac_file:
                metadata['musicbrainz_artist_ids'] = flac_file['musicbrainz_artistid']
                
            if 'musicbrainz_albumartistid' in flac_file:
                metadata['musicbrainz_album_artist_ids'] = flac_file['musicbrainz_albumartistid']
                
            # Discogs IDs
            if 'discogs_release_id' in flac_file:
                metadata['discogs_release_id'] = flac_file['discogs_release_id'][0]
                
            # AcoustID
            if 'acoustid_id' in flac_file:
                metadata['acoustid'] = flac_file['acoustid_id'][0]
                
            # ReplayGain
            if 'replaygain_album_gain' in flac_file:
                try:
                    metadata['album_gain'] = float(flac_file['replaygain_album_gain'][0].split(' ')[0])
                except (ValueError, IndexError):
                    pass
                    
            if 'replaygain_track_gain' in flac_file:
                try:
                    metadata['track_gain'] = float(flac_file['replaygain_track_gain'][0].split(' ')[0])
                except (ValueError, IndexError):
                    pass
                    
            # Extract artwork
            artwork_data, mime_type = self.read_embedded_artwork(file_path)
            if artwork_data:
                metadata['artwork'] = artwork_data
                metadata['artwork_mime_type'] = mime_type
                
            # Check for cuesheet
            cue_path = os.path.splitext(file_path)[0] + '.cue'
            if os.path.exists(cue_path):
                with open(cue_path, 'r', encoding='utf-8') as f:
                    metadata['cue_sheet'] = f.read()
                    
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing FLAC file {file_path}: {str(e)}")
            raise
    
    def is_lossless(self, file_path: str) -> bool:
        """
        Determine if the file uses lossless compression.
        FLAC is always lossless.
        
        Args:
            file_path: Path to the FLAC audio file
            
        Returns:
            bool: True (FLAC is always lossless)
        """
        return True
    
    def read_embedded_artwork(self, file_path: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Extract embedded artwork if present.
        
        Args:
            file_path: Path to the FLAC audio file
            
        Returns:
            tuple: (artwork_data, mime_type) or (None, None)
        """
        try:
            flac_file = FLAC(file_path)
            
            # Check for pictures
            pictures = flac_file.pictures
            if pictures:
                # Sort pictures by type (prefer front cover)
                front_covers = [p for p in pictures if p.type == 3]
                if front_covers:
                    picture = front_covers[0]
                else:
                    picture = pictures[0]
                
                return picture.data, picture.mime
            
            return None, None
        except Exception as e:
            logger.warning(f"Error extracting FLAC artwork: {str(e)}")
            return None, None
    
    def write_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Write metadata to the FLAC file.
        
        Args:
            file_path: Path to the FLAC audio file
            metadata: Metadata dictionary to write
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            flac_file = FLAC(file_path)
            
            # Clear existing tags
            flac_file.clear()
            
            # Basic metadata
            if 'title' in metadata:
                flac_file['title'] = str(metadata['title'])
                
            if 'artists' in metadata:
                flac_file['artist'] = metadata['artists']
                
            if 'album' in metadata:
                flac_file['album'] = str(metadata['album'])
                
            if 'album_artists' in metadata:
                flac_file['albumartist'] = metadata['album_artists']
                
            # Track information
            if 'track_number' in metadata:
                if 'total_tracks' in metadata:
                    flac_file['tracknumber'] = f"{metadata['track_number']}/{metadata['total_tracks']}"
                else:
                    flac_file['tracknumber'] = str(metadata['track_number'])
                    
            # Disc information
            if 'disc_number' in metadata:
                if 'total_discs' in metadata:
                    flac_file['discnumber'] = f"{metadata['disc_number']}/{metadata['total_discs']}"
                else:
                    flac_file['discnumber'] = str(metadata['disc_number'])
                    
            # Date information
            if 'date' in metadata:
                flac_file['date'] = str(metadata['date'])
            elif 'year' in metadata:
                flac_file['date'] = str(metadata['year'])
                
            # Genre
            if 'genres' in metadata:
                flac_file['genre'] = metadata['genres']
                
            # Participants
            if 'composers' in metadata:
                flac_file['composer'] = metadata['composers']
                
            if 'performers' in metadata:
                flac_file['performer'] = metadata['performers']
                
            # Release details
            if 'label' in metadata:
                flac_file['label'] = str(metadata['label'])
                
            if 'catalog_number' in metadata:
                flac_file['catalognumber'] = str(metadata['catalog_number'])
                
            if 'release_country' in metadata:
                flac_file['country'] = str(metadata['release_country'])
                
            # MusicBrainz IDs
            if 'musicbrainz_release_id' in metadata:
                flac_file['musicbrainz_albumid'] = str(metadata['musicbrainz_release_id'])
                
            if 'musicbrainz_recording_id' in metadata:
                flac_file['musicbrainz_trackid'] = str(metadata['musicbrainz_recording_id'])
                
            if 'musicbrainz_artist_ids' in metadata:
                flac_file['musicbrainz_artistid'] = metadata['musicbrainz_artist_ids']
                
            if 'musicbrainz_album_artist_ids' in metadata:
                flac_file['musicbrainz_albumartistid'] = metadata['musicbrainz_album_artist_ids']
                
            # Discogs IDs
            if 'discogs_release_id' in metadata:
                flac_file['discogs_release_id'] = str(metadata['discogs_release_id'])
                
            # AcoustID
            if 'acoustid' in metadata:
                flac_file['acoustid_id'] = str(metadata['acoustid'])
                
            # Save tags
            flac_file.save()
            
            # Handle artwork separately
            if 'artwork' in metadata and metadata['artwork']:
                self._write_artwork(file_path, metadata['artwork'], metadata.get('artwork_mime_type', 'image/jpeg'))
                
            return True
            
        except Exception as e:
            logger.error(f"Error writing metadata to FLAC file {file_path}: {str(e)}")
            return False
    
    def _write_artwork(self, file_path: str, artwork_data: bytes, mime_type: str) -> bool:
        """
        Write artwork to FLAC file.
        
        Args:
            file_path: Path to the FLAC file
            artwork_data: Binary image data
            mime_type: Image MIME type
            
        Returns:
            bool: Success status
        """
        try:
            flac_file = FLAC(file_path)
            
            # Clear existing pictures
            flac_file.clear_pictures()
            
            # Create new picture
            picture = Picture()
            picture.data = artwork_data
            picture.mime = mime_type
            picture.type = 3  # Front cover
            
            # Try to get dimensions
            try:
                img = Image.open(io.BytesIO(artwork_data))
                picture.width, picture.height = img.size
                picture.depth = 24  # Default for color images
            except Exception:
                # Default values if we can't read the image
                picture.width = 0
                picture.height = 0
                picture.depth = 0
            
            # Add the picture
            flac_file.add_picture(picture)
            
            # Save the file
            flac_file.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing artwork to FLAC file {file_path}: {str(e)}")
            return False


if __name__ == "__main__":
    import sys
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python flac_handler.py <flac_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    handler = FlacHandler()
    
    try:
        metadata = handler.get_track_info(file_path)
        print("\n=== Metadata ===")
        for key, value in metadata.items():
            if key != 'artwork':  # Skip binary data
                print(f"{key}: {value}")
        
        print("\n=== MediaInfo ===")
        print(handler.get_mediainfo(file_path))
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)