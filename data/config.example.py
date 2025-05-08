"""
Music-Upload-Assistant configuration.
"""

config = {
    'app_name': 'Music-Upload-Assistant',
    'app_version': '0.1.0',
    'announce_url': 'https://your-tracker.net/announce/YOUR_ANNOUNCE_TOKEN',
    # API keys for external services
    'musicbrainz_app_id': 'MUA',
    'musicbrainz_contact': 'your-email@example.com',  # Optional but recommended
    'discogs_token': '',  # Get from https://www.discogs.com/settings/developers
    'acoustid_api_key': 'YOUR_ACOUSTID_API_KEY',  # Get from https://acoustid.org/api-key
    
    # Paths and directories
    'templates_dir': 'data/templates',
    'temp_dir': 'temp',
    'output_dir': 'output',
    
    # Torrent creation settings
    'torrent': {
        'piece_size': 'auto',  # in KB, or 'auto'
        'private': True,
        'comment': 'Created with Music-Upload-Assistant',
        # Announce URL for torrent creation
        'announce_url': 'https://your-tracker.net/announce/YOUR_ANNOUNCE_TOKEN',
    },
    
    # Default upload preferences
    'upload': {
        'default_format': 'FLAC',
        'default_media': 'WEB',
        'default_release_type': 'Album'
    },
    
    # Uploader info
    'uploader_name': 'YOUR_NAME',
    
    # Description settings
    'description': {
        'template': 'perfect_album',
        'include_cover_in_description': True,
        'include_technical_info': True
    },
    
    # qBittorrent client settings
    'qbittorrent': {
        'enabled': True,                         # Set to False to disable qBittorrent integration
        'host': 'http://localhost:8080',         # qBittorrent WebUI address
        'username': 'admin',                     # qBittorrent WebUI username
        'password': 'YOUR_PASSWORD',             # qBittorrent WebUI password
        'auto_start': True,                      # Automatically start torrents
        'default_save_path': '',                 # Leave empty to use qBittorrent default
        'use_original_path': True                # Use the original path of files for seeding
    },
    
    # Tracker configurations
    'trackers': {
        # YUS (Yu-Scene) tracker example
        'YUS': {
            'name': 'YU-Scene',
            'url':  'https://yu-scene.net',
            'base_url': 'https://yu-scene.net',
            'announce_url': 'https://yu-scene.net/announce/YOUR_ANNOUNCE_TOKEN',
            'api_key': 'YOUR_API_KEY',
            'upload_url': 'https://yu-scene.net/api/torrents/upload',
            'source_name': 'YuScene',
            'anon': False,

            # Category IDs (form field "category_id")
            'category_ids': {
                'ALBUM':       '7',
                'SINGLE':      '8',
                'EP':          '9',
                'COMPILATION': '10',
                'SOUNDTRACK':  '11',
                'LIVE':        '12',
                'REMIX':       '13',
                'BOOTLEG':     '14'
            },

            # Format IDs (if you need them elsewhere)
            'format_ids': {
                'FLAC': '1',
                'MP3':  '2',
                'AAC':  '3'
            },

            # Type IDs (the "type_id" field for API)
            'type_ids': {
                'FLAC':      '16',  # audio FLAC
                'DISC':      '17',
                'REMUX':     '2',
                'WEBDL':     '4',
                'WEBRIP':    '5',
                'HDTV':      '6',
                'ENCODE':    '3'
            },

            # Resolution IDs (the "resolution_id" field for API)
            'resolution_ids': {
                '8640P': '10','4320P': '1','2160P': '2','1440P': '3',
                '1080P': '3','1080I': '4','720P':  '5','576P': '6',
                '576I': '7','480P': '8','480I': '9'
            },

            'description_template': 'yus_default.txt'
        },
        
        # SP (Seedpool) tracker example
        'SP': {
            'enabled': False,
            'name': 'Seedpool',
            'url': 'https://seedpool.org',
            'announce_url': 'https://seedpool.org/announce',
            'api_key': 'YOUR_API_KEY',
            'upload_url': 'https://seedpool.org/api/torrents/upload',
            'source_name': 'seedpool.org',
            'anon': False,
            'api_auth_type': 'param',
            'api_format': 'form',
            'category_ids': {
                'MOVIE': '1',
                'TV': '2',
                'ANIME': '6',
                'SPORTS': '8',
                'BOXSET': '13',
                'ALBUM': '5',  # Use category 5 for music
                'SINGLE': '5',
                'EP': '5',
                'COMPILATION': '5',
                'SOUNDTRACK': '5',
                'LIVE': '5'
            },
            'format_ids': {
                'DISC': '1',
                'REMUX': '2',
                'ENCODE': '3',
                'WEBDL': '4',
                'WEBRIP': '5',
                'HDTV': '6',
                'FLAC': '1',  # Map to DISC
                'MP3': '3',   # Map to ENCODE
                'AAC': '3',
                'AC3': '3',
                'DTS': '3',
                'OGG': '3',
                'ALAC': '3',
                'WAV': '3'
            },
            'resolution_ids': {
                '4320p': '1',
                '2160p': '2',
                '1080p': '3',
                '1080i': '4',
                '720p': '5',
                '576p': '6',
                '576i': '7',
                '480p': '8',
                '480i': '9',
                'OTHER': '10'
            }
        }
    },
    
    # Log settings
    'logging': {
        'level': 'INFO',
        'file': 'music_upload_assistant.log',
    }
}