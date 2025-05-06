"""
MusicBrainz client module for Music-Upload-Assistant.
Handles metadata lookup and enrichment using the MusicBrainz database.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

try:
    import musicbrainzngs
    MUSICBRAINZ_AVAILABLE = True
except ImportError:
    logger.warning("musicbrainzngs not installed. MusicBrainz lookups will not be available.")
    MUSICBRAINZ_AVAILABLE = False

class MusicBrainzClient:
    """
    Client for the MusicBrainz database.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MusicBrainz client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        if not MUSICBRAINZ_AVAILABLE:
            logger.warning("MusicBrainz client not available. Please install musicbrainzngs.")
            return
        
        # Set up MusicBrainz client
        app_id = config.get('musicbrainz_app_id', 'MusicUploadAssistant/0.1.0')
        contact = config.get('musicbrainz_contact', '')
        
        # Set user agent
        musicbrainzngs.set_useragent(app_id, '0.1.0', contact=contact)
        
        # Set rate limiting
        self.delay = 1.0  # MusicBrainz rate limit: 1 request per second
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce MusicBrainz rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_release(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for releases matching the query.
        
        Args:
            query: Search query
            
        Returns:
            list: List of matching releases
        """
        if not MUSICBRAINZ_AVAILABLE:
            logger.error("musicbrainzngs is required for MusicBrainz search")
            return []
        
        self._rate_limit()
        
        try:
            result = musicbrainzngs.search_releases(query=query, limit=5)
            releases = result.get('release-list', [])
            
            logger.info(f"Found {len(releases)} releases matching '{query}'")
            return releases
        except Exception as e:
            logger.error(f"Error searching MusicBrainz: {e}")
            return []
    
    def get_release_by_id(self, mbid: str) -> Optional[Dict[str, Any]]:
        """
        Get a release by its MusicBrainz ID.
        
        Args:
            mbid: MusicBrainz release ID
            
        Returns:
            dict: Release information or None if not found
        """
        if not MUSICBRAINZ_AVAILABLE:
            logger.error("musicbrainzngs is required for MusicBrainz lookup")
            return None
        
        self._rate_limit()
        
        try:
            includes = ['recordings', 'artists', 'release-groups', 'labels']
            result = musicbrainzngs.get_release_by_id(mbid, includes=includes)
            
            release = result.get('release')
            if release:
                logger.info(f"Found release: {release.get('title')}")
                return release
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving release from MusicBrainz: {e}")
            return None
    
    def enrich_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich existing metadata with MusicBrainz data.
        
        Args:
            metadata: Existing metadata
            
        Returns:
            dict: Enriched metadata
        """
        if not MUSICBRAINZ_AVAILABLE:
            logger.error("musicbrainzngs is required for MusicBrainz enrichment")
            return {}
        
        enriched = {}
        
        # Check if we already have a MusicBrainz ID
        mbid = metadata.get('musicbrainz_release_id')
        
        if mbid:
            # Get release by ID
            release = self.get_release_by_id(mbid)
            if release:
                enriched = self._extract_release_metadata(release)
        else:
            # Try to search for the release
            query_parts = []
            
            if 'album' in metadata and metadata['album']:
                query_parts.append(metadata['album'])
            
            album_artists = metadata.get('album_artists') or metadata.get('artists', [])
            if album_artists:
                query_parts.append(album_artists[0])
            
            query = " ".join(query_parts)
            
            if query.strip():
                releases = self.search_release(query)
                if releases:
                    release = releases[0]  # Use the first match
                    enriched = self._extract_release_metadata(release)
                    
                    # Store the MusicBrainz ID
                    if 'id' in release:
                        enriched['musicbrainz_release_id'] = release['id']
        
        return enriched
    
    def _extract_release_metadata(self, release: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a MusicBrainz release.
        
        Args:
            release: MusicBrainz release
            
        Returns:
            dict: Extracted metadata
        """
        metadata = {}
        
        # Basic release info
        if 'title' in release:
            metadata['album'] = release['title']
        
        if 'date' in release:
            metadata['date'] = release['date']
            # Try to extract year
            try:
                metadata['year'] = int(release['date'].split('-')[0])
            except (ValueError, IndexError):
                pass
        
        # Artists
        if 'artist-credit' in release:
            artists = []
            for artist_credit in release['artist-credit']:
                if isinstance(artist_credit, dict) and 'artist' in artist_credit:
                    artists.append(artist_credit['artist']['name'])
            
            if artists:
                metadata['album_artists'] = artists
        
        # Label and catalog number
        if 'label-info-list' in release:
            for label_info in release['label-info-list']:
                if 'label' in label_info:
                    metadata['label'] = label_info['label']['name']
                
                if 'catalog-number' in label_info:
                    metadata['catalog_number'] = label_info['catalog-number']
                
                break  # Use first label
        
        # Release country
        if 'country' in release:
            metadata['release_country'] = release['country']
        
        # Release type
        if 'release-group' in release:
            release_group = release['release-group']
            if 'primary-type' in release_group:
                metadata['release_type'] = release_group['primary-type']
        
        # Medium format
        if 'medium-list' in release:
            formats = set()
            for medium in release['medium-list']:
                if 'format' in medium:
                    formats.add(medium['format'])
            
            if formats:
                metadata['media'] = '/'.join(formats)
        
        return metadata


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if not MUSICBRAINZ_AVAILABLE:
        print("musicbrainzngs not installed. Please install it with 'pip install musicbrainzngs'")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python musicbrainz.py <album> [artist]")
        sys.exit(1)
    
    # Create a sample config
    config = {
        'app_name': 'Music-Upload-Assistant',
        'app_version': '0.1.0',
        'musicbrainz_contact': 'your-email@example.com'
    }
    
    client = MusicBrainzClient(config)
    
    album = sys.argv[1]
    artist = sys.argv[2] if len(sys.argv) > 2 else ""
    
    query = f"{album} {artist}".strip()
    
    print(f"Searching for: {query}")
    releases = client.search_release(query)
    
    if not releases:
        print("No releases found.")
        sys.exit(1)
    
    for i, release in enumerate(releases):
        print(f"\n{i+1}. {release.get('title')} - {release.get('artist-credit-phrase', '')}")
        print(f"   ID: {release.get('id')}")
        print(f"   Date: {release.get('date', 'Unknown')}")
        
        if 'label-info-list' in release:
            for label_info in release['label-info-list']:
                if 'label' in label_info:
                    print(f"   Label: {label_info['label']['name']}")
                if 'catalog-number' in label_info:
                    print(f"   Catalog: {label_info['catalog-number']}")
    
    # Get more details for the first release
    if releases:
        print("\nGetting details for first release...")
        mbid = releases[0]['id']
        release = client.get_release_by_id(mbid)
        
        if release:
            metadata = client._extract_release_metadata(release)
            print("\nExtracted metadata:")
            for key, value in metadata.items():
                print(f"{key}: {value}")
