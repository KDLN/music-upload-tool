# Music-Upload-Assistant Quick Start Guide

This guide will help you get started with the Music-Upload-Assistant tool quickly and effectively.

## Installation

1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create configuration:
   ```bash
   cp data/config.sample.json data/config.json
   ```

## Configuration

### Setting Up Your Identity

Set your uploader name that will be used for release naming:

```bash
python configure_tracker.py --uploader "YourName"
```

### Setting Up YU-Scene Tracker

Configure the YU-Scene tracker with your credentials:

```bash
python configure_tracker.py --add YUS
```

This will prompt you for:
- API Key (required)
- Upload URL (default is provided)
- Announce URL (default is provided)
- Anonymous uploads preference

### Verify Configuration

Check your current configuration:

```bash
python configure_tracker.py --list
```

## Basic Usage Examples

### Processing a Single Track

To analyze a track without uploading:

```bash
python music_upload_assistant.py /path/to/track.flac
```

### Processing an Album

To analyze an album without uploading:

```bash
python music_upload_assistant.py /path/to/album/directory --album
```

### Creating a Torrent

To create a torrent file without uploading:

```bash
python music_upload_assistant.py /path/to/album/directory --album --create-torrent
```

### Uploading to YU-Scene

To upload an album to YU-Scene:

```bash
python music_upload_assistant.py /path/to/album/directory --album --create-torrent --tracker YUS --upload
```

### Using Perfect Upload Format

For releases with the perfect format (including barcode, bit depth, etc.):

```bash
python music_upload_assistant.py /path/to/album/directory --album --perfect --create-torrent --tracker YUS --upload
```

## Format Override Options

You can override certain metadata when uploading:

```bash
python music_upload_assistant.py /path/to/album --format FLAC --media WEB --bitdepth 24 --create-torrent --tracker YUS
```

## Testing & Debugging

### Debug Mode

To test the upload process without actually uploading:

```bash
python music_upload_assistant.py /path/to/album --tracker YUS --create-torrent --upload --debug
```

### Test Script

To run a simple analysis on an audio file:

```bash
python test_script.py /path/to/track.flac
```

## Help

For all available options:

```bash
python music_upload_assistant.py --help
```

For tracker configuration help:

```bash
python configure_tracker.py --help
```
