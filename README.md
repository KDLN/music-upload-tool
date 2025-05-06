# Music-Upload-Assistant

A tool for preparing and uploading music files to various trackers.

## Features

- Audio file analysis (FLAC, MP3)
- Metadata extraction and enrichment
- Quality analysis (sample rate, bit depth, bitrate)
- Description generation using customizable templates
- Torrent creation
- Upload to supported trackers

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a configuration file:
   ```bash
   cp data/config.example.py data/config.py
   ```
4. Edit the configuration file to add your API keys and tracker credentials

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
python music_upload_assistant.py /path/to/album/directory --album --create-torrent --tracker YUS
```

### Testing Without Uploading

```bash
python test_script.py /path/to/audio/file.flac
```

## Configuration

Edit `data/config.py` to configure:

- API keys for external services (MusicBrainz, Discogs, AcoustID)
- Tracker credentials and settings
- Torrent creation settings
- File paths and logging preferences

## Supported Trackers

- YU-Scene (YUS)
- Additional trackers can be added by implementing tracker-specific modules

## License

MIT License