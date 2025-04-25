"""
MP3 format handler for the Music-Upload-Assistant.
Handles parsing and writing metadata for MP3 audio files.
"""

import os
import logging
from typing import Dict, Optional, Tuple, Any, BinaryIO
from mutagen.mp3 import MP3
from mutagen.id3 import (
    ID3, APIC, TIT2, TPE1, TALB, TPE2, TRCK, TPOS, TDRC, TYER, 
    TCON, TCOM, TPUB, TXXX, TBPM, TLEN, USLT, COMM
)
from PIL import Image
import io

from modules.audio_analyzer.format_handlers.base_handler import FormatHandler

logger = logging.getLogger(__name__)

class Mp3Handler(FormatHandler):
    """Handler for MP3 audio files."""
    
    def __init__(self):
        """Initialize the MP3 format handler."""
        super().__init__()
        self.name = "MP3 Handler"
        self.extensions = ["mp3"]
    
    def get_track_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract track metadata and technical info from MP3 file.
        
        Args:
            file_path: Path to the MP3 audio file
            
        Returns:
            Dict: Populated track metadata dictionary
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            mp3_file = MP3(file_path)
            metadata = {}
            
            # Basic file info
            metadata['file_path'] = file_path
            metadata['file_name'] = os.path.basename(file_path)
            metadata['format'] = "MP3"
            metadata['file_size'] = os.path.getsize(file_path)
            metadata['duration'] = mp3_file.info.length
            
            # Technical info
            metadata['sample_rate'] = mp3_file.info.sample_rate
            metadata['channels'] = 2 if mp3_file.info.mode in [0, 1] else 1  # 0=stereo, 1=joint stereo, 2=dual channel, 3=mono
            metadata['bitrate'] = int(mp3_file.info.bitrate / 1000)
            metadata['codec'] = "MP3"
            metadata['compression'] = "Lossy"
            
            # Layer info
            metadata['layer'] = f"Layer {mp3_file.info.layer}"
            
            # Check if ID3 tags exist
            if mp3_file.tags is None:
                logger.warning(f"No ID3 tags found in {file_path}")
                return metadata
            
            # Get ID3 tags
            id3 = mp3_file.tags
            
            # Basic metadata
            if 'TIT2' in id3:  # Title
                metadata['title'] = str(id3['TIT2'])
                
            if 'TPE1' in id3:  # Artist
                metadata['artists'] = id3['TPE1'].text
                
            if 'TALB' in id3:  # Album
                metadata['album'] = str(id3['TALB'])
                
            if 'TPE2' in id3:  # Album Artist
                metadata['album_artists'] = id3['TPE2'].text
                
            # Track information
            if 'TRCK' in id3:  # Track number
                try:
                    track_info = str(id3['TRCK'])
                    if '/' in track_info:
                        track_num, total_tracks = track_info.split('/')
                        metadata['track_number'] = int(track_num)
                        metadata['total_tracks'] = int(total_tracks)
                    else:
                        metadata['track_number'] = int(track_info)
                except (ValueError, IndexError):
                    logger.warning(f"Invalid track number format: {id3['TRCK']}")
                    
            # Disc information
            if 'TPOS' in id3:  # Disc number
                try:
                    disc_info = str(id3['TPOS'])
                    if '/' in disc_info:
                        disc_num, total_discs = disc_info.split('/')
                        metadata['disc_number'] = int(disc_num)
                        metadata['total_discs'] = int(total_discs)
                    else:
                        metadata['disc_number'] = int(disc_info)
                except (ValueError, IndexError):
                    logger.warning(f"Invalid disc number format: {id3['TPOS']}")
                    
            # Date information
            if 'TDRC' in id3:  # Recording date
                metadata['date'] = str(id3['TDRC'])
                # Try to extract year from date
                try:
                    metadata['year'] = int(str(id3['TDRC']).split('-')[0])
                except (ValueError, IndexError):
                    pass
            elif 'TYER' in id3:  # Year
                try:
                    metadata['year'] = int(str(id3['TYER']))
                except (ValueError, IndexError):
                    metadata['year'] = str(id3['TYER'])
                    
            # Genre
            if 'TCON' in id3:  # Genre
                metadata['genres'] = id3['TCON'].text
                
            # Participants
            if 'TCOM' in id3:  # Composer
                metadata['composers'] = id3['TCOM'].text
                
            # Publisher/Label
            if 'TPUB' in id3:  # Publisher
                metadata['label'] = str(id3['TPUB'])
                
            # BPM
            if 'TBPM' in id3:  # BPM
                try:
                    metadata['bpm'] = int(str(id3['TBPM']))
                except (ValueError, IndexError):
                    metadata['bpm'] = str(id3['TBPM'])
                
            # Process TXXX frames (custom tags)
            for key in id3.keys():
                if key.startswith('TXXX:'):
                    tag_name = key.replace('TXXX:', '').lower()
                    tag_value = id3[key].text
                    
                    # Handle special cases
                    if tag_name in ['musicbrainz album id', 'musicbrainz_albumid']:
                        metadata['musicbrainz_release_id'] = tag_value[0]
                    elif tag_name in ['musicbrainz track id', 'musicbrainz_trackid']:
                        metadata['musicbrainz_recording_id'] = tag_value[0]
                    elif tag_name in ['musicbrainz artist id', 'musicbrainz_artistid']:
                        metadata['musicbrainz_artist_ids'] = tag_value
                    elif tag_name in ['musicbrainz album artist id', 'musicbrainz_albumartistid']:
                        metadata['musicbrainz_album_artist_ids'] = tag_value
                    elif tag_name in ['discogs_release_id', 'discogs release id']:
                        metadata['discogs_release_id'] = tag_value[0]
                    elif tag_name in ['catalognumber', 'catalog number', 'catalog_number']:
                        metadata['catalog_number'] = tag_value[0]
                    elif tag_name in ['country', 'release country', 'releasecountry']:
                        metadata['release_country'] = tag_value[0]
                    elif tag_name in ['replaygain_album_gain', 'replaygain album gain']:
                        try:
                            metadata['album_gain'] = float(tag_value[0].split(' ')[0])
                        except (ValueError, IndexError):
                            pass
                    elif tag_name in ['replaygain_track_gain', 'replaygain track gain']:
                        try:
                            metadata['track_gain'] = float(tag_value[0].split(' ')[0])
                        except (ValueError, IndexError):
                            pass
                    else:
                        # Store other custom tags
                        metadata[tag_name] = tag_value[0] if len(tag_value) == 1 else tag_value
            
            # Handle comments
            if 'COMM' in id3:
                comments = id3.getall('COMM')
                if comments:
                    metadata['comments'] = []
                    for comment in comments:
                        if comment.lang and comment.desc and comment.text:
                            metadata['comments'].append({
                                'language': comment.lang,
                                'description': comment.desc,
                                'text': comment.text[0]
                            })
            
            # Handle lyrics
            if 'USLT' in id3:
                lyrics = id3.getall('USLT')
                if lyrics:
                    metadata['lyrics'] = []
                    for lyric in lyrics:
                        if lyric.lang and lyric.desc and lyric.text:
                            metadata['lyrics'].append({
                                'language': lyric.lang,
                                'description': lyric.desc,
                                'text': lyric.text
                            })
            
            # Encoder info
            if hasattr(mp3_file.info, 'encoder_info') and mp3_file.info.encoder_info:
                metadata['encoder'] = mp3_file.info.encoder_info
            elif hasattr(mp3_file.info, 'encoder') and mp3_file.info.encoder:
                metadata['encoder'] = mp3_file.info.encoder
            else:
                # Try to guess encoder from some common patterns
                metadata['encoder'] = self._guess_mp3_encoder(id3)
            
            # Extract artwork
            artwork_data, mime_type = self.read_embedded_artwork(file_path)
            if artwork_data:
                metadata['artwork'] = artwork_data
                metadata['artwork_mime_type'] = mime_type
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing MP3 file {file_path}: {str(e)}")
            raise
    
    def _guess_mp3_encoder(self, id3) -> Optional[str]:
        """
        Try to guess the MP3 encoder from ID3 tags.
        
        Args:
            id3: ID3 tag object
            
        Returns:
            str: Encoder name or None if unknown
        """
        # Look for encoding software in common ID3 frames
        encoder_frames = ['TENC', 'TSSE', 'TXXX:Encoded by', 'TXXX:encoding']
        
        for frame in encoder_frames:
            if frame in id3:
                return str(id3[frame])
        
        # Look for common encoder signatures in comment frames
        if 'COMM' in id3:
            comments = id3.getall('COMM')
            for comment in comments:
                text = comment.text[0].lower() if comment.text else ""
                
                if 'lame' in text:
                    return f"LAME {text.split('lame')[1].strip()}" if 'lame' in text.lower() else "LAME"
                elif 'fraunhofer' in text:
                    return "Fraunhofer"
                elif 'xing' in text:
                    return "Xing"
                elif 'blade' in text:
                    return "BladeEnc"
        
        return None
    
    def is_lossless(self, file_path: str) -> bool:
        """
        Determine if the file uses lossless compression.
        MP3 is always lossy.
        
        Args:
            file_path: Path to the MP3 audio file
            
        Returns:
            bool: False (MP3 is always lossy)
        """
        return False
    
    def read_embedded_artwork(self, file_path: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Extract embedded artwork if present.
        
        Args:
            file_path: Path to the MP3 audio file
            
        Returns:
            tuple: (artwork_data, mime_type) or (None, None)
        """
        try:
            id3 = ID3(file_path)
            
            # Try to find APIC frames (attached pictures)
            apic_frames = []
            for key in id3.keys():
                if key.startswith('APIC:'):
                    apic_frames.append(id3[key])
            
            # If no APIC: frames, try regular APIC frames
            if not apic_frames:
                apic_frames = id3.getall('APIC')
            
            if apic_frames:
                # Sort by picture type (prefer front cover)
                front_covers = [frame for frame in apic_frames if frame.type == 3]
                if front_covers:
                    apic = front_covers[0]
                else:
                    apic = apic_frames[0]
                
                return apic.data, apic.mime
            
            return None, None
        except Exception as e:
            logger.warning(f"Error extracting ID3 artwork: {str(e)}")
            return None, None
    
    def write_metadata(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Write metadata to the MP3 file.
        
        Args:
            file_path: Path to the MP3 audio file
            metadata: Metadata dictionary to write
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            # Try to load existing ID3 tags or create new ones
            try:
                id3 = ID3(file_path)
            except:
                # No existing ID3 tags, create new
                id3 = ID3()
            
            # Basic metadata
            if 'title' in metadata:
                id3.add(TIT2(encoding=3, text=metadata['title']))
                
            if 'artists' in metadata:
                id3.add(TPE1(encoding=3, text=metadata['artists']))
                
            if 'album' in metadata:
                id3.add(TALB(encoding=3, text=metadata['album']))
                
            if 'album_artists' in metadata:
                id3.add(TPE2(encoding=3, text=metadata['album_artists']))
                
            # Track information
            if 'track_number' in metadata:
                if 'total_tracks' in metadata:
                    id3.add(TRCK(encoding=3, text=f"{metadata['track_number']}/{metadata['total_tracks']}"))
                else:
                    id3.add(TRCK(encoding=3, text=str(metadata['track_number'])))
                    
            # Disc information
            if 'disc_number' in metadata:
                if 'total_discs' in metadata:
                    id3.add(TPOS(encoding=3, text=f"{metadata['disc_number']}/{metadata['total_discs']}"))
                else:
                    id3.add(TPOS(encoding=3, text=str(metadata['disc_number'])))
                    
            # Date information
            if 'date' in metadata:
                id3.add(TDRC(encoding=3, text=metadata['date']))
            elif 'year' in metadata:
                id3.add(TDRC(encoding=3, text=str(metadata['year'])))
                
            # Genre
            if 'genres' in metadata:
                id3.add(TCON(encoding=3, text=metadata['genres']))
                
            # Participants
            if 'composers' in metadata:
                id3.add(TCOM(encoding=3, text=metadata['composers']))
                
            # Publisher/Label
            if 'label' in metadata:
                id3.add(TPUB(encoding=3, text=metadata['label']))
                
            # MusicBrainz IDs
            if 'musicbrainz_release_id' in metadata:
                id3.add(TXXX(encoding=3, desc='MusicBrainz Album Id', text=metadata['musicbrainz_release_id']))
                
            if 'musicbrainz_recording_id' in metadata:
                id3.add(TXXX(encoding=3, desc='MusicBrainz Track Id', text=metadata['musicbrainz_recording_id']))
                
            if 'musicbrainz_artist_ids' in metadata:
                id3.add(TXXX(encoding=3, desc='MusicBrainz Artist Id', text=metadata['musicbrainz_artist_ids']))
                
            if 'musicbrainz_album_artist_ids' in metadata:
                id3.add(TXXX(encoding=3, desc='MusicBrainz Album Artist Id', text=metadata['musicbrainz_album_artist_ids']))
                
            # Discogs IDs
            if 'discogs_release_id' in metadata:
                id3.add(TXXX(encoding=3, desc='DISCOGS_RELEASE_ID', text=metadata['discogs_release_id']))
                
            # Other custom tags
            if 'catalog_number' in metadata:
                id3.add(TXXX(encoding=3, desc='CATALOGNUMBER', text=metadata['catalog_number']))
                
            if 'release_country' in metadata:
                id3.add(TXXX(encoding=3, desc='COUNTRY', text=metadata['release_country']))
                
            # Save the tags
            id3.save(file_path)
            
            # Handle artwork separately
            if 'artwork' in metadata and metadata['artwork']:
                self._write_artwork(file_path, metadata['artwork'], metadata.get('artwork_mime_type', 'image/jpeg'))
                
            return True
            
        except Exception as e:
            logger.error(f"Error writing metadata to MP3 file {file_path}: {str(e)}")
            return False
    
    def _write_artwork(self, file_path: str, artwork_data: bytes, mime_type: str) -> bool:
        """
        Write artwork to MP3 file.
        
        Args:
            file_path: Path to the MP3 file
            artwork_data: Binary image data
            mime_type: Image MIME type
            
        Returns:
            bool: Success status
        """
        try:
            # Load ID3 tags
            id3 = ID3(file_path)
            
            # Remove existing APIC frames
            for key in list(id3.keys()):
                if key.startswith('APIC:') or key == 'APIC':
                    del id3[key]
            
            # Add new artwork
            id3.add(APIC(
                encoding=3,        # UTF-8
                mime=mime_type,    # Image MIME type
                type=3,            # 3 is for cover image
                desc='Cover',
                data=artwork_data
            ))
            
            # Save the tags
            id3.save(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing artwork to MP3 file {file_path}: {str(e)}")
            return False


if __name__ == "__main__":
    import sys
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python mp3_handler.py <mp3_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    handler = Mp3Handler()
    
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