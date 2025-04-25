"""
Tracker configuration examples for Music-Upload-Assistant.
This file provides examples for configuring different music trackers.
"""

# Configuration dictionary
config = {
    # Application settings
    'app_name': 'Music-Upload-Assistant',
    'app_version': '0.1.0',
    
    # API keys for external services
    'musicbrainz_app_id': 'MusicUploadAssistant/0.1.0',
    'musicbrainz_contact': 'your-email@example.com',  # Optional but recommended
    'discogs_token': 'YOUR_DISCOGS_TOKEN',  # Get from https://www.discogs.com/settings/developers
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
    },
    
    # Audio quality settings
    'audio_quality': {
        'minimum_bitrate': {
            'MP3': 320,
            'AAC': 256,
            'OGG': 256
        },
        'preferred_sample_rates': [44100, 48000, 88200, 96000, 176400, 192000],
        'preferred_bit_depths': [16, 24],
        'detect_transcodes': True,
        'analyze_dynamic_range': True,
        'analyze_spectral_content': True
    },
    
    # Default upload preferences
    'upload': {
        'default_format': 'FLAC',
        'default_media': 'CD',
        'default_release_type': 'Album'
    },
    
    # Tracker configurations
    'trackers': {
        # YUS (Yu-Scene) tracker
        'YUS': {
            'name': 'YU-Scene',
            'url': 'https://yu-scene.net',
            'announce_url': 'https://yu-scene.net/announce',
            'api_key': 'YOUR_YUS_API_KEY',
            'upload_url': 'https://yu-scene.net/api/torrents/upload',
            'source_name': 'YuScene',
            'anon': False,  # Set to True for anonymous uploads
            'formats': {
                'FLAC': {
                    'format': 'FLAC',
                    'encoding': 'Lossless'
                },
                'MP3': {
                    'format': 'MP3',
                    'encoding': '320'
                },
                'AAC': {
                    'format': 'AAC',
                    'encoding': '256'
                }
            },
            'media_types': [
                'CD', 'WEB', 'Vinyl', 'DVD', 'SACD', 'DAT', 'Cassette', 
                'Blu-Ray', 'Soundboard'
            ],
            'release_types': [
                'Album', 'EP', 'Single', 'Compilation', 'Soundtrack', 
                'Live', 'Remix', 'Bootleg', 'Interview', 'Mixtape'
            ],
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
            'required_fields': [
                'album', 'album_artists', 'year', 'format', 'media', 'release_type'
            ],
            'description_template': 'yus_default.txt'
        },
        
        # RED (Redacted) tracker
        'RED': {
            'name': 'Redacted',
            'url': 'https://redacted.ch',
            'announce_url': 'https://tracker.redacted.ch/announce',
            'api_key': 'YOUR_RED_API_KEY',
            'username': 'YOUR_RED_USERNAME',
            'password': 'YOUR_RED_PASSWORD',
            'source_name': 'RED',
            'anon': False,
            'formats': {
                'FLAC': {
                    'format': 'FLAC',
                    'encoding': 'Lossless'
                },
                'MP3': {
                    'format': 'MP3',
                    'encoding': '320'
                },
                'MP3': {
                    'format': 'MP3',
                    'encoding': 'V0 (VBR)'
                },
                'MP3': {
                    'format': 'MP3',
                    'encoding': 'V2 (VBR)'
                },
                'AAC': {
                    'format': 'AAC',
                    'encoding': '256'
                }
            },
            'media_types': [
                'CD', 'WEB', 'Vinyl', 'DVD', 'SACD', 'DAT', 'Cassette', 
                'BluRay', 'Soundboard', 'HDTracks'
            ],
            'release_types': [
                'Album', 'Soundtrack', 'EP', 'Anthology', 'Compilation', 
                'Single', 'Live', 'Remix', 'Bootleg', 'Interview', 'Mixtape', 
                'Demo', 'Concert Recording', 'DJ Mix'
            ],
            'description_template': 'red_default.txt'
        },
        
        # OPS (Orpheus) tracker
        'OPS': {
            'name': 'Orpheus',
            'url': 'https://orpheus.network',
            'announce_url': 'https://tracker.orpheus.network/announce',
            'api_key': 'YOUR_OPS_API_KEY',
            'username': 'YOUR_OPS_USERNAME',
            'password': 'YOUR_OPS_PASSWORD',
            'source_name': 'OPS',
            'anon': False,
            'formats': {
                'FLAC': {
                    'format': 'FLAC',
                    'encoding': 'Lossless'
                },
                'MP3': {
                    'format': 'MP3',
                    'encoding': '320'
                },
                'MP3': {
                    'format': 'MP3',
                    'encoding': 'V0 (VBR)'
                }
            },
            'media_types': [
                'CD', 'WEB', 'Vinyl', 'DVD', 'SACD', 'DAT', 'Cassette', 
                'BluRay', 'Soundboard'
            ],
            'release_types': [
                'Album', 'Soundtrack', 'EP', 'Anthology', 'Compilation', 
                'Single', 'Live', 'Remix', 'Bootleg', 'Interview', 'Mixtape', 
                'Demo', 'Concert Recording', 'DJ Mix'
            ],
            'description_template': 'ops_default.txt'
        }
    },
    
    # Log settings
    'logging': {
        'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        'file': 'music_upload_assistant.log',
        'max_size': 1024 * 1024 * 5,  # 5 MB
        'backup_count': 3
    }
}