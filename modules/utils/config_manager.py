"""
Configuration manager module for Music-Upload-Assistant.
Handles loading, merging, and saving configuration.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages configuration loading, merging and saving.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_default_config()
        self.config_path = None
        
        # If no config path provided, look in default locations
        if not config_path:
            for path in ['config.json', 'config.py', 
                       os.path.join('data', 'config.json'),
                       os.path.join('data', 'config.py')]:
                if os.path.exists(path):
                    config_path = path
                    break
        
        # Load configuration if a path is found
        if config_path and os.path.exists(config_path):
            self.config_path = config_path
            self._load_config(config_path)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """
        Load default configuration.
        
        Returns:
            dict: Default configuration
        """
        return {
            'app_name': 'Music-Upload-Assistant',
            'app_version': '0.2.0',
            'templates_dir': os.path.join('data', 'templates'),
            'temp_dir': 'temp',
            'output_dir': 'output',
            'uploader_name': '',  # Default empty, to be set by user
            'logging': {
                'level': 'INFO',
                'file': 'music_upload_assistant.log'
            },
            'trackers': {
                # YUS (Yu-Scene) tracker template
                'YUS': {
                    'enabled': False,  # Disabled by default until configured
                    'name': 'YU-Scene',
                    'url': 'https://yu-scene.net',
                    'announce_url': 'https://yu-scene.net/announce',
                    'api_key': '',
                    'upload_url': 'https://yu-scene.net/api/torrents/upload',
                    'source_name': 'YuScene',
                    'anon': False,
                    'category_ids': {
                        'ALBUM': '7',
                        'SINGLE': '8', 
                        'EP': '9',
                        'COMPILATION': '10',
                        'SOUNDTRACK': '11',
                        'LIVE': '12',
                        'REMIX': '13',
                        'BOOTLEG': '14',
                        'INTERVIEW': '15',
                        'MIXTAPE': '16'
                    },
                    'format_ids': {
                        'FLAC': '1',
                        'MP3': '2',
                        'AAC': '3',
                        'AC3': '4',
                        'DTS': '5',
                        'OGG': '6',
                        'ALAC': '7',
                        'DSD': '8',
                        'WAV': '9',
                        'MQA': '10'
                    },
                    'description_template': 'yus_default.txt'
                }
            },
            'torrent': {
                'piece_size': 'auto',
                'private': True,
                'comment': 'Created with Music-Upload-Assistant'
            },
            'qbittorrent': {
                'enabled': False,
                'host': 'http://localhost:8080',
                'username': '',
                'password': '',
                'auto_start': True,
                'default_save_path': ''
            },
            'description': {
                'template': 'default_album',
                'include_cover_in_description': True
            }
        }
    
    def _load_config(self, config_path: str):
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            # For Python-based config
            if config_path.endswith('.py'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_content = f.read()
                
                # Extract the config dictionary using exec
                config_dict = {}
                exec(config_content, config_dict)
                
                if 'config' in config_dict:
                    loaded_config = config_dict['config']
                else:
                    # Try to find a dictionary assignment in the file
                    for key, value in config_dict.items():
                        if isinstance(value, dict) and key != '__builtins__':
                            loaded_config = value
                            break
                    else:
                        logger.warning(f"Could not find config dictionary in {config_path}")
                        loaded_config = {}
            
            # For JSON-based config
            elif config_path.endswith('.json'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
            
            # Update config with loaded values
            self._deep_update(self.config, loaded_config)
            logger.info(f"Loaded configuration from {config_path}")
        
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            logger.warning("Using default configuration with partial updates")
    
    def _deep_update(self, d: Dict, u: Dict) -> Dict:
        """
        Recursively update a dictionary with another dictionary.
        
        Args:
            d: Base dictionary to update
            u: Dictionary with updates
            
        Returns:
            dict: Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.
        
        Returns:
            dict: Complete configuration
        """
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        # Handle nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        # Handle nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            config = self.config
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            self.config[key] = value
    
    def save(self, path: Optional[str] = None) -> bool:
        """
        Save configuration to a file.
        
        Args:
            path: Path to save to (defaults to original path)
            
        Returns:
            bool: Success status
        """
        save_path = path or self.config_path
        
        if not save_path:
            save_path = os.path.join('data', 'config.json')
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            # Save as JSON by default
            if save_path.endswith('.py'):
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Configuration for Music-Upload-Assistant\n\nconfig = {json.dumps(self.config, indent=4)}\n")
            else:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4)
            
            logger.info(f"Saved configuration to {save_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving configuration to {save_path}: {e}")
            return False
    
    def get_tracker_config(self, tracker_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific tracker.
        
        Args:
            tracker_id: Tracker identifier
            
        Returns:
            dict: Tracker configuration or None if not found
        """
        if 'trackers' not in self.config:
            return None
        
        return self.config['trackers'].get(tracker_id)
