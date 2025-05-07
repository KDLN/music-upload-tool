"""
Artwork handler module for Music-Upload-Tool.
Handles album art extraction, processing, and embedding.
"""

import os
import shutil
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    logger.warning("Pillow not installed. Image processing will be limited.")
    PILLOW_AVAILABLE = False

try:
    import mutagen
    from mutagen.flac import FLAC, Picture
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    MUTAGEN_AVAILABLE = True
except ImportError:
    logger.warning("Mutagen not installed. Embedded artwork extraction will be limited.")
    MUTAGEN_AVAILABLE = False

class ArtworkHandler:
    """Handles album art extraction, processing, and embedding."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the artwork handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.temp_dir = config.get('temp_dir', 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_embedded_artwork(self, file_path: str) -> Optional[Tuple[bytes, str]]:
        """
        Extract embedded artwork from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            tuple: (artwork_data, mime_type) or None if not found
        """
        if not MUTAGEN_AVAILABLE:
            logger.error("Mutagen is required for artwork extraction")
            return None
        
        try:
            ext = os.path.splitext(file_path.lower())[1]
            
            if ext == '.flac':
                return self._extract_flac_artwork(file_path)
            elif ext == '.mp3':
                return self._extract_mp3_artwork(file_path)
            else:
                logger.warning(f"Unsupported file format for artwork extraction: {ext}")
                return None
        
        except Exception as e:
            logger.error(f"Error extracting artwork: {e}")
            return None
    
    def _extract_flac_artwork(self, file_path: str) -> Optional[Tuple[bytes, str]]:
        """Extract artwork from FLAC file."""
        try:
            flac = FLAC(file_path)
            pictures = flac.pictures
            
            if pictures:
                # Prefer front cover
                front_covers = [p for p in pictures if p.type == 3]
                pic = front_covers[0] if front_covers else pictures[0]
                
                return pic.data, pic.mime
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting FLAC artwork: {e}")
            return None
    
    def _extract_mp3_artwork(self, file_path: str) -> Optional[Tuple[bytes, str]]:
        """Extract artwork from MP3 file."""
        try:
            id3 = ID3(file_path)
            
            for key in id3.keys():
                if key.startswith('APIC:'):
                    apic = id3[key]
                    return apic.data, apic.mime
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting MP3 artwork: {e}")
            return None
    
    def find_cover_art(self, directory: str) -> Optional[str]:
        """
        Find cover art image in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            str: Path to cover art or None if not found
        """
        if not os.path.isdir(directory):
            logger.warning(f"Not a directory: {directory}")
            return None
        
        # Common cover art filenames
        common_names = [
            'cover', 'front', 'folder', 'albumart', 'album', 'artwork',
            'scan', 'booklet', 'frontcover'
        ]
        
        # Common image extensions
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        # Look for images with common names
        for name in common_names:
            for ext in image_exts:
                path = os.path.join(directory, f"{name}{ext}")
                if os.path.exists(path):
                    logger.info(f"Found cover art: {path}")
                    return path
        
        # If not found, look for any image file
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                ext = os.path.splitext(filename.lower())[1]
                if ext in image_exts:
                    logger.info(f"Found image file: {path}")
                    return path
        
        logger.warning(f"No cover art found in {directory}")
        return None
    
    def prepare_cover_art(self, artwork_path: Optional[str] = None, 
                         audio_file: Optional[str] = None) -> Optional[str]:
        """
        Prepare cover art for upload (resize, format conversion).
        
        Args:
            artwork_path: Path to artwork file (optional)
            audio_file: Path to audio file to extract artwork from (optional)
            
        Returns:
            str: Path to prepared artwork or None if not available
        """
        # First check if we have an artwork path
        if artwork_path and os.path.exists(artwork_path):
            return self._process_image(artwork_path)
        
        # If not, try to extract from audio file
        if audio_file and os.path.exists(audio_file):
            artwork_data = self.extract_embedded_artwork(audio_file)
            if artwork_data:
                # Save extracted artwork to temp file
                temp_path = os.path.join(self.temp_dir, "extracted_cover.jpg")
                try:
                    with open(temp_path, 'wb') as f:
                        f.write(artwork_data[0])
                    
                    logger.info(f"Extracted artwork saved to {temp_path}")
                    return self._process_image(temp_path)
                except Exception as e:
                    logger.error(f"Error saving extracted artwork: {e}")
        
        logger.warning("No artwork available")
        return None
    
    def _process_image(self, image_path: str) -> str:
        """
        Process image (resize, convert) for optimal tracker compatibility.
        
        Args:
            image_path: Path to image file
            
        Returns:
            str: Path to processed image
        """
        if not PILLOW_AVAILABLE:
            # If Pillow not available, just copy the file
            processed_path = os.path.join(self.temp_dir, "cover.jpg")
            shutil.copy2(image_path, processed_path)
            return processed_path
        
        try:
            # Open image
            img = Image.open(image_path)
            
            # Create output path
            processed_path = os.path.join(self.temp_dir, "cover.jpg")
            
            # Convert to RGB if needed (e.g., PNG with transparency)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            max_size = 900  # Most trackers prefer < 1000px
            if img.width > max_size or img.height > max_size:
                # Maintain aspect ratio
                ratio = min(max_size / img.width, max_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Save as JPEG
            img.save(processed_path, 'JPEG', quality=90)
            logger.info(f"Processed artwork saved to {processed_path}")
            
            return processed_path
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            # Fallback: just copy the file
            processed_path = os.path.join(self.temp_dir, "cover.jpg")
            shutil.copy2(image_path, processed_path)
            return processed_path
    
    def embed_artwork(self, audio_file: str, artwork_path: str) -> bool:
        """
        Embed artwork into an audio file.
        
        Args:
            audio_file: Path to audio file
            artwork_path: Path to artwork file
            
        Returns:
            bool: Success status
        """
        if not MUTAGEN_AVAILABLE:
            logger.error("Mutagen is required for artwork embedding")
            return False
        
        try:
            ext = os.path.splitext(audio_file.lower())[1]
            
            if ext == '.flac':
                return self._embed_flac_artwork(audio_file, artwork_path)
            elif ext == '.mp3':
                return self._embed_mp3_artwork(audio_file, artwork_path)
            else:
                logger.warning(f"Unsupported file format for artwork embedding: {ext}")
                return False
        
        except Exception as e:
            logger.error(f"Error embedding artwork: {e}")
            return False
    
    def _embed_flac_artwork(self, audio_file: str, artwork_path: str) -> bool:
        """Embed artwork into FLAC file."""
        try:
            # Read image file
            with open(artwork_path, 'rb') as f:
                image_data = f.read()
            
            # Determine MIME type
            mime_type = 'image/jpeg'  # Default
            ext = os.path.splitext(artwork_path.lower())[1]
            if ext == '.png':
                mime_type = 'image/png'
            elif ext == '.gif':
                mime_type = 'image/gif'
            
            # Create picture
            picture = Picture()
            picture.data = image_data
            picture.type = 3  # Front cover
            picture.mime = mime_type
            
            # Get image dimensions
            if PILLOW_AVAILABLE:
                with Image.open(artwork_path) as img:
                    picture.width, picture.height = img.size
                    picture.depth = 24  # Color depth (default)
            
            # Open FLAC file
            flac = FLAC(audio_file)
            
            # Remove existing pictures
            flac.clear_pictures()
            
            # Add new picture
            flac.add_picture(picture)
            
            # Save file
            flac.save()
            
            logger.info(f"Embedded artwork in {audio_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error embedding FLAC artwork: {e}")
            return False
    
    def _embed_mp3_artwork(self, audio_file: str, artwork_path: str) -> bool:
        """Embed artwork into MP3 file."""
        try:
            # Read image file
            with open(artwork_path, 'rb') as f:
                image_data = f.read()
            
            # Determine MIME type
            mime_type = 'image/jpeg'  # Default
            ext = os.path.splitext(artwork_path.lower())[1]
            if ext == '.png':
                mime_type = 'image/png'
            elif ext == '.gif':
                mime_type = 'image/gif'
            
            # Get or create ID3 tags
            try:
                id3 = ID3(audio_file)
            except:
                # Create new ID3 tag if not present
                id3 = ID3()
            
            # Remove existing APIC frames
            for key in list(id3.keys()):
                if key.startswith('APIC'):
                    del id3[key]
            
            # Add new artwork
            id3['APIC'] = APIC(
                encoding=3,  # UTF-8
                mime=mime_type,
                type=3,  # Front cover
                desc='Cover',
                data=image_data
            )
            
            # Save file
            id3.save(audio_file)
            
            logger.info(f"Embedded artwork in {audio_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error embedding MP3 artwork: {e}")
            return False