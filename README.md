# Music-Upload-Assistant

A tool for preparing and uploading music files to various trackers.

## What's New - Version 0.2.0

- **Centralized Configuration System**: A new ConfigManager makes it easier to manage settings
- **Tracker Manager**: Better management of tracker connections with a unified interface
- **Configuration Utility**: New script for easy tracker setup (`configure_tracker.py`)
- **Improved Release Naming**: Customizable uploader tag based on your configuration
- **JSON Configuration**: Support for both Python and JSON configuration files

## Features

- Audio file analysis (FLAC, MP3)
- Metadata extraction and enrichment
- Quality analysis (sample rate, bit depth, bitrate)
- Description generation using customizable templates
- Torrent creation
- Upload to supported trackers
- Cover art detection and handling

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a configuration file:
   ```bash
   cp data/config.sample.json data/config.json
   ```
4. Configure your trackers and settings:
   ```bash
   python configure_tracker.py --add YUS
   python configure_tracker.py --uploader "YourName"
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

### Use Perfect Format

```bash
python music_upload_assistant.py /path/to/album/directory --album --create-torrent --tracker YUS --perfect
```

### Testing Without Uploading

```bash
python test_script.py /path/to/audio/file.flac
```

## Configuration

Edit `data/config.json` to configure:

- API keys for external services (MusicBrainz, Discogs, AcoustID)
- Tracker credentials and settings
- Torrent creation settings
- File paths and logging preferences

For easier configuration, use the configuration utility:

```bash
python configure_tracker.py --help
```

## Supported Trackers

- YU-Scene (YUS)
- Additional trackers can be added by implementing tracker-specific modules

## License

MIT License
