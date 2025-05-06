"""
qBittorrent client module for Music-Upload-Assistant.
Handles adding torrents to qBittorrent for seeding.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class QBittorrentClient:
    """
    Client for interacting with qBittorrent WebUI API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the qBittorrent client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        qbt_config = config.get('qbittorrent', {})
        
        # API configuration
        self.host = qbt_config.get('host', 'http://localhost:8080')
        self.username = qbt_config.get('username', '')
        self.password = qbt_config.get('password', '')
        self.auto_start = qbt_config.get('auto_start', True)
        self.default_save_path = qbt_config.get('default_save_path', '')
        
        # Remove trailing slash if present
        if self.host.endswith('/'):
            self.host = self.host[:-1]
        
        # Create session
        self.session = requests.Session()
        
        # Check for debug mode
        self.debug_mode = config.get('debug', False)
        
        logger.info(f"[QBITTORRENT CONFIG] host={self.host}, " 
                    f"username={'SET' if self.username else 'MISSING'}, "
                    f"save_path={'SET' if self.default_save_path else 'DEFAULT'}")
    
    def login(self) -> bool:
        """
        Login to qBittorrent WebUI.
        
        Returns:
            bool: Success status
        """
        if self.debug_mode:
            logger.info("DEBUG MODE: Skipping qBittorrent login")
            return True
        
        url = f"{self.host}/api/v2/auth/login"
        data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = self.session.post(url, data=data)
            
            if response.status_code == 200 and response.text == "Ok.":
                logger.info("Successfully logged in to qBittorrent")
                return True
            else:
                logger.error(f"Failed to login to qBittorrent: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to qBittorrent: {e}")
            return False
    
    def add_torrent(self, torrent_path: str, save_path: Optional[str] = None, 
                  cover_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Add a torrent file to qBittorrent.
        
        Args:
            torrent_path: Path to the .torrent file
            save_path: Path where files should be saved (default from config if None)
            cover_path: Path to album artwork to set as torrent cover
            
        Returns:
            tuple: (success, message)
        """
        # Debug mode simulation
        if self.debug_mode:
            logger.info(f"DEBUG MODE: Would add torrent {torrent_path} to qBittorrent")
            logger.info(f"Save path would be: {save_path or self.default_save_path or 'DEFAULT'}")
            if cover_path:
                logger.info(f"Would set cover art: {cover_path}")
            return True, "Debug mode: torrent add simulation successful"
            
        # Login to qBittorrent
        if not self.login():
            return False, "Failed to login to qBittorrent"
        
        # Check if torrent file exists
        if not os.path.exists(torrent_path):
            return False, f"Torrent file not found: {torrent_path}"
        
        # Prepare API call
        url = f"{self.host}/api/v2/torrents/add"
        
        # Use specified save path or default from config
        if not save_path:
            save_path = self.default_save_path
        
        # Prepare form data
        form_data = {}
        
        # Add save path if specified
        if save_path:
            form_data['savepath'] = save_path
        
        # Set auto start/pause
        form_data['paused'] = "false" if self.auto_start else "true"
        
        # Prepare files
        files = {
            'torrents': (
                os.path.basename(torrent_path),
                open(torrent_path, 'rb'),
                'application/x-bittorrent'
            )
        }
        
        try:
            # Make API call to add torrent
            response = self.session.post(url, data=form_data, files=files)
            
            # Close file handle
            files['torrents'][1].close()
            
            # Check response
            if response.status_code != 200:
                logger.error(f"Failed to add torrent: {response.text}")
                return False, f"Failed to add torrent: {response.text}"
                
            # If cover art was provided and torrent was added successfully, set it
            if cover_path and os.path.exists(cover_path):
                # Get hash of added torrent
                hash_response = self._get_torrent_hash(os.path.basename(torrent_path))
                if hash_response[0]:
                    torrent_hash = hash_response[1]
                    cover_result = self.set_torrent_cover(torrent_hash, cover_path)
                    if not cover_result[0]:
                        logger.warning(f"Torrent added but failed to set cover: {cover_result[1]}")
                        return True, "Torrent added successfully but failed to set cover art"
                else:
                    logger.warning(f"Torrent added but couldn't get hash to set cover: {hash_response[1]}")
                    return True, "Torrent added successfully but couldn't set cover art"
            
            logger.info(f"Successfully added torrent to qBittorrent: {torrent_path}")
            return True, "Torrent added successfully"
                
        except Exception as e:
            # Ensure file handle is closed
            try:
                files['torrents'][1].close()
            except:
                pass
                
            logger.error(f"Error adding torrent to qBittorrent: {e}")
            return False, f"Error adding torrent: {e}"
    
    def _get_torrent_hash(self, torrent_name: str) -> Tuple[bool, str]:
        """
        Get the hash of a torrent by its name.
        
        Args:
            torrent_name: Name of the torrent to find
            
        Returns:
            tuple: (success, hash or error message)
        """
        if self.debug_mode:
            return True, "1234567890abcdef1234567890abcdef12345678"
            
        # Make sure we're logged in
        if not self.login():
            return False, "Failed to login to qBittorrent"
        
        try:
            # Get list of torrents
            url = f"{self.host}/api/v2/torrents/info"
            response = self.session.get(url)
            
            if response.status_code != 200:
                return False, f"Failed to get torrent list: {response.text}"
            
            # Parse response
            torrents = response.json()
            
            # Find the torrent by name
            for torrent in torrents:
                if torrent['name'] == torrent_name or torrent['name'] == os.path.splitext(torrent_name)[0]:
                    return True, torrent['hash']
            
            return False, f"Torrent '{torrent_name}' not found"
            
        except Exception as e:
            logger.error(f"Error getting torrent hash: {e}")
            return False, f"Error getting torrent hash: {e}"
    
    def set_torrent_cover(self, torrent_hash: str, cover_path: str) -> Tuple[bool, str]:
        """
        Set the cover image for a torrent.
        
        Args:
            torrent_hash: Hash of the torrent
            cover_path: Path to the cover image file
            
        Returns:
            tuple: (success, message)
        """
        if self.debug_mode:
            logger.info(f"DEBUG MODE: Would set cover for torrent {torrent_hash} to {cover_path}")
            return True, "Debug mode: cover set simulation successful"
            
        # Make sure we're logged in
        if not self.login():
            return False, "Failed to login to qBittorrent"
        
        # Check if cover file exists
        if not os.path.exists(cover_path):
            return False, f"Cover file not found: {cover_path}"
        
        try:
            # Prepare API call
            url = f"{self.host}/api/v2/torrents/setCoverArt"
            
            # Read the image file
            with open(cover_path, 'rb') as f:
                cover_data = f.read()
            
            # Prepare files
            files = {
                'image': (
                    os.path.basename(cover_path),
                    cover_data,
                    'image/jpeg' if cover_path.lower().endswith('.jpg') or cover_path.lower().endswith('.jpeg') else 'image/png'
                )
            }
            
            # Prepare form data
            form_data = {
                'hash': torrent_hash
            }
            
            # Make API call
            response = self.session.post(url, data=form_data, files=files)
            
            # Check response
            if response.status_code == 200:
                logger.info(f"Successfully set cover for torrent {torrent_hash}")
                return True, "Cover set successfully"
            else:
                logger.error(f"Failed to set cover: {response.text}")
                return False, f"Failed to set cover: {response.text}"
                
        except Exception as e:
            logger.error(f"Error setting torrent cover: {e}")
            return False, f"Error setting torrent cover: {e}"
    
    def check_connection(self) -> bool:
        """
        Check if connection to qBittorrent works.
        
        Returns:
            bool: True if connection works
        """
        if self.debug_mode:
            logger.info("DEBUG MODE: Skipping qBittorrent connection check")
            return True
            
        # Try to login
        return self.login()
