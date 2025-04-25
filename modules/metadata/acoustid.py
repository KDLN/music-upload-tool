"""
AcoustID client module for Music-Upload-Assistant.
Handles audio fingerprinting and lookup through the AcoustID service.
"""

import os
import time
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

try:
    import acoustid
    ACOUSTID_AVAILABLE = True
except ImportError:
    logger.warning("pyacoustid not installed. Audio fingerprinting will not be available.")
    ACOUSTID_AVAILABLE = False

class AcoustIDClient:
    """
    Client for the AcoustID audio fingerprinting service.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AcoustID client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.api_key = config.get('acoustid_api_key')
        
        if not self.api_key:
            logger.warning("AcoustID API key not set in config. Audio fingerprinting will not be available.")
        
        self.delay = 1.0  # Rate limit: 1 request per second
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce AcoustID rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fingerprint_file(self, file_path: str) -> Optional[Tuple[float, str]]:
        """
        Generate an AcoustID fingerprint for an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            tuple: (duration, fingerprint) or None if failed
        """
        if not ACOUSTID_AVAILABLE:
            logger.error("pyacoustid is required for fingerprinting")
            return None
        
        if not self.api_key:
            logger.error("AcoustID API key not set")
            return None
        
        try:
            # Generate fingerprint
            duration, fingerprint = acoustid.fingerprint_file(file_path)
            logger.info(f"Generated fingerprint for {file_path}: {fingerprint[:20]}...")
            return duration, fingerprint
        except acoustid.FingerprintGenerationError as e:
            logger.error(f"Error generating fingerprint for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fingerprinting file {file_path}: {e}")
            return None
    
    def lookup_fingerprint(self, fingerprint: str, duration: float) -> Optional[List[Dict[str, Any]]]:
        """
        Look up a fingerprint in the AcoustID database.
        
        Args:
            fingerprint: Audio fingerprint
            duration: Audio duration in seconds
            
        Returns:
            list: List of matches or None if failed
        """
        if not ACOUSTID_AVAILABLE:
            logger.error("pyacoustid is required for fingerprint lookup")
            return None
        
        if not self.api_key:
            logger.error("AcoustID API key not set")
            return None
        
        self._rate_limit()
        
        try:
            # Look up fingerprint
            results = acoustid.lookup(self.api_key, fingerprint, duration, meta='recordings releases')
            logger.info(f"Found {len(results)} matches for fingerprint")
            return results
        except acoustid.WebServiceError as e:
            logger.error(f"AcoustID web service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error looking up fingerprint: {e}")
            return None
    
    def identify_file(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Identify an audio file using AcoustID.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            list: List of matches or None if failed
        """
        if not ACOUSTID_AVAILABLE:
            logger.error("pyacoustid is required for file identification")
            return None
        
        if not self.api_key:
            logger.error("AcoustID API key not set")
            return None
        
        self._rate_limit()
        
        try:
            # Identify file directly
            results = acoustid.match(self.api_key, file_path, meta='recordings releases')
            logger.info(f"Found {len(results)} matches for {file_path}")
            return results
        except acoustid.FingerprintGenerationError as e:
            logger.error(f"Error generating fingerprint for {file_path}: {e}")
            return None
        except acoustid.WebServiceError as e:
            logger.error(f"AcoustID web service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error identifying file {file_path}: {e}")
            return None
    
    def get_best_match(self, matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Get the best match from a list of AcoustID matches.
        
        Args:
            matches: List of matches from AcoustID
            
        Returns:
            dict: Best match or None if no good match
        """
        if not matches:
            return None
        
        # Sort by score (higher is better)
        sorted_matches = sorted(matches, key=lambda m: m.get('score', 0), reverse=True)
        
        # Get the best match
        best_match = sorted_matches[0]
        
        # Only return if score is good enough
        if best_match.get('score', 0) < 0.5:
            logger.warning(f"Best match score {best_match.get('score', 0)} is too low")
            return None
        
        return best_match
    
    def extract_metadata(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from an AcoustID match.
        
        Args:
            match: AcoustID match
            
        Returns:
            dict: Extracted metadata
        """
        metadata = {}
        
        # Get the recording info
        if 'recordings' in match:
            recording = match['recordings'][0]
            
            # Basic metadata
            metadata['title'] = recording.get('title')
            
            # Artists
            if 'artists' in recording:
                artists = [artist.get('name') for artist in recording['artists']]
                metadata['artists'] = artists
            
            # MusicBrainz ID
            metadata['musicbrainz_recording_id'] = recording.get('id')
            
            # Get the best release
            if 'releases' in recording:
                release = recording['releases'][0]
                
                # Release metadata
                metadata['album'] = release.get('title')
                
                # Release MusicBrainz ID
                metadata['musicbrainz_release_id'] = release.get('id')
                
                # Track number
                if 'mediums' in release:
                    for medium in release['mediums']:
                        for track in medium.get('tracks', []):
                            if track.get('id') == recording.get('id'):
                                metadata['track_number'] = track.get('position')
                                metadata['disc_number'] = medium.get('position')
                                break
                
                # Date
                if 'date' in release:
                    metadata['date'] = release['date'].get('year')
                
                # Album artists
                if 'artists' in release:
                    album_artists = [artist.get('name') for artist in release['artists']]
                    metadata['album_artists'] = album_artists
        
        return metadata
    
    async def identify_and_enrich(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify a file and enrich its metadata.
        
        Args:
            file_path: Path to the audio file
            metadata: Existing metadata to enrich
            
        Returns:
            dict: Enriched metadata
        """
        # Check if we already have good metadata
        if self._has_sufficient_metadata(metadata):
            logger.info(f"File {file_path} already has sufficient metadata")
            return metadata
        
        # Identify the file
        matches = self.identify_file(file_path)
        if not matches:
            logger.warning(f"No AcoustID matches found for {file_path}")
            return metadata
        
        # Get the best match
        best_match = self.get_best_match(matches)
        if not best_match:
            logger.warning(f"No good AcoustID match found for {file_path}")
            return metadata
        
        # Extract metadata from the match
        acoustid_metadata = self.extract_metadata(best_match)
        
        # Merge with existing metadata
        enriched_metadata = self._merge_metadata(metadata, acoustid_metadata)
        
        logger.info(f"Enriched metadata for {file_path} using AcoustID")
        return enriched_metadata
    
    def _has_sufficient_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if metadata is sufficient.
        
        Args:
            metadata: Metadata to check
            
        Returns:
            bool: True if sufficient, False otherwise
        """
        # Check if we have the essential metadata
        essential_fields = ['title', 'artists', 'album']
        
        return all(field in metadata and metadata[field] for field in essential_fields)
    
    def _merge_metadata(self, original: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge original metadata with new metadata, preferring original.
        
        Args:
            original: Original metadata
            new: New metadata
            
        Returns:
            dict: Merged metadata
        """
        # Start with a copy of the original
        merged = original.copy()
        
        # Add new fields that don't exist in the original
        for key, value in new.items():
            if key not in merged or not merged[key]:
                merged[key] = value
        
        return merged
    
    def submit_fingerprint(self, file_path: str, musicbrainz_recording_id: str) -> bool:
        """
        Submit a fingerprint to the AcoustID database.
        
        Args:
            file_path: Path to the audio file
            musicbrainz_recording_id: MusicBrainz recording ID
            
        Returns:
            bool: Success status
        """
        if not ACOUSTID_AVAILABLE:
            logger.error("pyacoustid is required for fingerprint submission")
            return False
        
        if not self.api_key:
            logger.error("AcoustID API key not set")
            return False
        
        try:
            # Generate fingerprint
            duration, fingerprint = acoustid.fingerprint_file(file_path)
            
            # Submit fingerprint
            acoustid.submit(self.api_key, musicbrainz_recording_id, fingerprint, duration)
            
            logger.info(f"Submitted fingerprint for {file_path} to AcoustID")
            return True
        except Exception as e:
            logger.error(f"Error submitting fingerprint: {e}")
            return False


if __name__ == "__main__":
    import sys
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python acoustid_client.py <audio_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Create a sample config with a placeholder API key
    # You need to replace this with your own API key
    config = {
        'acoustid_api_key': 'YOUR_API_KEY'
    }
    
    # Create the client
    client = AcoustIDClient(config)
    
    # Check if the client is available
    if not ACOUSTID_AVAILABLE or not client.api_key:
        print("AcoustID client not available. Please install pyacoustid and set an API key.")
        sys.exit(1)
    
    # Identify the file
    print(f"Identifying {file_path}...")
    matches = client.identify_file(file_path)
    
    if not matches:
        print("No matches found.")
        sys.exit(1)
    
    # Get the best match
    best_match = client.get_best_match(matches)
    
    if not best_match:
        print("No good match found.")
        sys.exit(1)
    
    # Extract and print metadata
    metadata = client.extract_metadata(best_match)
    print("\nExtracted metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")