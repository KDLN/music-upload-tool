# Music-Upload-Tool

A tool for preparing and uploading music files to various trackers, with a focus on UNIT3D-based platforms like YU-Scene.

## Features

- Audio file analysis (FLAC, MP3)
- Metadata extraction and quality checking
- Cover art detection, extraction, and embedding
- Torrent creation with correct trackers
- Upload to various trackers including YU-Scene
- Extensible plugin system for adding new trackers

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/music-upload-tool.git
   cd music-upload-tool
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Create and configure settings
   ```bash
   python configure.py --uploader "YourName"
   python configure.py --add YUS
   ```

## Usage

### Basic Usage

```bash
python music_upload_assistant.py /path/to/audio/file.flac
```

### Create Torrent

```bash
python music_upload_assistant.py /path/to/audio/file.flac --create-torrent
```

### Process Album Directory

```bash
python music_upload_assistant.py /path/to/album/directory --album
```

### Upload to Tracker

```bash
python music_upload_assistant.py /path/to/album/directory --album --create-torrent --tracker YUS --upload
```

### Testing Without Uploading

```bash
python music_upload_assistant.py /path/to/album/directory --debug
```

## Configuration

The tool uses a central configuration file (`config.json`) which you can edit directly or through the `configure.py` utility.

### Configure a Tracker

```bash
python configure.py --add YUS
```

This will prompt you for necessary information like API key and upload URL.

### Set Uploader Name

```bash
python configure.py --uploader "YourName"
```

### List Configured Trackers

```bash
python configure.py --list
```

### Test Tracker Configuration

```bash
python configure.py --test YUS
```

## "Perfect Format" Upload

The tool supports a "perfect format" for uploading to YU-Scene, which follows this template:

1. Release Name: `Artist-Album [Barcode-Number] Year Source BitDepth SampleRate Format-Uploader`
2. Description Format:
   ```
   ---------------------------------------------------------------------
                           Artist - Album
   ---------------------------------------------------------------------
   Source...............: WEB [img]https://i.ibb.co/9ZZCM1x/Tidal.png[/img]
   Included.............: NFO, M3U, LOG (Folder.auCDtect)
   Channels.............: Stereo / 44100 HZ / 16 Bit
   Codec................: Free Lossless Audio Codec (FLAC)
   ---------------------------------------------------------------------
                          Tracklisting
   ---------------------------------------------------------------------
      1. Artist - Track Name                                     [03:02]
      ...
   Playing Time.........: 57:06
   Total Size...........: 413.66 MB
   ```

To use this format, use the `--perfect` flag:

```bash
python music_upload_assistant.py /path/to/album --album --perfect --tracker YUS
```

## Adding New Trackers

The tool has a modular tracker system that makes it easy to add support for new trackers. To add a new tracker:

1. Create a new file in `modules/trackers/your_tracker_id_tracker.py`
2. Implement a class that extends `BaseTracker`
3. Configure the tracker using `configure.py --add YOUR_TRACKER_ID`

Example tracker implementation:

```python
from modules.trackers.base_tracker import BaseTracker

class MyTrackerTracker(BaseTracker):
    def __init__(self, config):
        super().__init__(config, "MYTRACKER")
        
    def is_configured(self):
        # Custom configuration validation
        if not self.api_key:
            return False
        return True
    
    def _build_form_data(self, metadata, description):
        # Custom form data for your tracker
        data = {
            'name': self._create_upload_name(metadata),
            'description': description,
            'category': '5',  # Your tracker's category ID for music
            'format': '1',    # Your tracker's format ID for FLAC
            'anonymous': "1" if self.anon else "0"
        }
        return data
```

## UNIT3D API Integration

This tool is compatible with UNIT3D-based trackers like YU-Scene. Key features:

- Uses the UNIT3D API for uploads when available
- Falls back to web form uploads if the API is not available
- Handles category and format IDs automatically
- Properly uploads and embeds album art

## Supported Trackers

- YU-Scene (YUS) - UNIT3D-based music tracker

## License

MIT License
