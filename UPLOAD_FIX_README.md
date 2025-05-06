# Music-Upload-Assistant Fixes and Improvements

This document explains the fixes and improvements made to address issues with upload names and cover art in the Music-Upload-Assistant tool.

## Problems Fixed

1. **Missing Cover Art**: The cover images weren't properly being included in the tracker uploads
2. **Incorrect Upload Names**: The release names weren't matching the format shown in tracker examples

## Solutions Implemented

### 1. Improved Release Name Generation

The naming format has been updated to match what's seen on the tracker:
- Simple format: `Artist - Album (Year) FLAC` or `Artist - Album (Year) FLAC 16-bit`
- Removed the square brackets around format information
- Made release names more consistent with tracker standards

### 2. Enhanced Cover Art Handling

- Improved cover art detection in album directories
- Added failsafes to extract embedded artwork from tracks when no cover file is found
- Added image processing to ensure consistent formats and sizes
- Ensured cover art is properly included in uploads
- Added better debugging information for cover art issues

### 3. YUS Tracker Upload Improvements

- Completely rewrote the cover art handling in the YUS tracker module
- Added a preprocessing step to prepare cover images for the tracker
- Improved file handling to prevent resource leaks
- Enhanced error reporting for upload issues
- Better name handling for uploaded torrents

## How to Use the Improved Version

### Basic Usage

```bash
# Process an album with all the improvements
python music_upload_assistant.py /path/to/album --create-torrent --tracker YUS
```

### Fix Cover Art Issues for Existing Albums

```bash
# Use the new fix_album_processing.py script to prepare cover art
python fix_album_processing.py /path/to/album --output /path/to/save/cover.jpg

# Then use the prepared cover with the main tool
python music_upload_assistant.py /path/to/album --create-torrent --tracker YUS
```

### Format Overrides

You can specify format details explicitly:

```bash
python music_upload_assistant.py /path/to/album --format FLAC --media WEB --bitdepth 24 --create-torrent --tracker YUS
```

## Troubleshooting

If you're still experiencing issues with cover art:

1. Make sure the album directory contains at least one image file
2. Try renaming the cover image to "cover.jpg" to help it be found
3. Run with `--verbose` to see detailed logging:
   ```bash
   python music_upload_assistant.py /path/to/album --create-torrent --tracker YUS --verbose
   ```
4. Use the `fix_album_processing.py` script to manually process cover art

## Technical Changes Made

1. Rewrote the `generate_release_name` function to match tracker formats
2. Enhanced the YUS tracker class with better cover art handling
3. Improved cover art extraction for both single files and albums
4. Added enhanced image handling with PIL when available
5. Improved error handling and logging for cover issues

These changes should ensure that uploads have the correct format names and include proper cover art in your YUS tracker uploads.
