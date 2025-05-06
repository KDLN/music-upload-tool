# Perfect Format for Music-Upload-Assistant

This document explains the "Perfect Format" feature added to the Music-Upload-Assistant tool based on the example upload you provided.

## Example Perfect Upload Format

```
Name: INXS-The.Very.Best [Barcode-7935344] 2011 WEB 16bit 44.1kHz FLAC-R&H

Description:
---------------------------------------------------------------------
                        INXS - The.Very.Best
---------------------------------------------------------------------
Source...............: WEB-DL [img]https://i.ibb.co/9ZZCM1x/Tidal.png[/img]
Included.............: NFO, M3U, LOG (Folder.auCDtect)
Channels.............: Stereo / 44100 HZ / 16 Bit
Codec................: Free Lossless Audio Codec (FLAC)
---------------------------------------------------------------------
                       Tracklisting CD 1
---------------------------------------------------------------------
   1. INXS - Need You Tonight                                 [03:02]
   ...
Playing Time.........: 57:06
Total Size...........: 413,66 MB
```

## New Features

### 1. Perfect Release Name Format

The tool now generates release names in the format:
```
Artist-Album [Barcode-Number] Year Source BitDepth SampleRate Format-Uploader
```

For example:
```
INXS-The.Very.Best [Barcode-7935344] 2011 WEB 16bit 44.1kHz FLAC-R&H
```

Key features:
- Spaces in artist name and album title are replaced with dots
- Barcode/catalog number is included in square brackets
- Technical details (sample rate, bit depth) are included
- Uploader name is appended at the end

### 2. Perfect Description Format

The tool now generates descriptions with the exact format from the example:
- Source information with optional Tidal image
- Technical information in the same format
- Properly formatted track listing with times
- Playing time and total size calculations
- Multi-disc support

### 3. Easy Format Switching

Added a `--perfect` command-line flag to enable the perfect format:
```bash
python music_upload_assistant.py /path/to/album --tracker YUS --create-torrent --perfect
```

## How to Use the Perfect Format

### Option 1: Use the main tool with `--perfect` flag

```bash
python music_upload_assistant.py /path/to/album --create-torrent --tracker YUS --perfect
```

### Option 2: Use the dedicated fix script

For existing albums that you want to convert to the perfect format:

```bash
python fix_upload_format.py /path/to/album
```

This will create:
- A perfect release name in `output/perfect_name.txt`
- A perfect description in `output/perfect_description.txt`

You can customize the output format with these options:
- `--format FLAC` - Override the detected format
- `--media WEB` - Specify the media source
- `--uploader "YourName"` - Set a custom uploader tag
- `--barcode "123456789"` - Specify a barcode or catalog number

## Customizing the Perfect Format

Edit the `config.py` file to set default options:

```python
# Add to your config.py
'uploader_name': 'R&H',  # Your uploader tag

'description': {
    'template': 'perfect_album',
    'include_cover_in_description': True
}
```

## Detailed Release Name Format

The perfect release name format has these components:

1. **Artist-Album** - Artist and album with dots instead of spaces
2. **[Barcode-Number]** - Optional barcode in square brackets
3. **Year** - Release year
4. **Source** - Media source (WEB, CD, Vinyl, etc.)
5. **BitDepth** - Bit depth for FLAC (16bit, 24bit)
6. **SampleRate** - Sample rate (44.1kHz, 48kHz, 96kHz, etc.)
7. **Format** - Audio format (FLAC, MP3, etc.)
8. **-Uploader** - Your uploader name/tag

## Detailed Description Format

The perfect description format includes:

1. **Header** - Artist and album name with separator lines
2. **Source** - Media source with optional Tidal/source image
3. **Technical Info** - Channels, sample rate, bit depth
4. **Codec** - Full codec name (e.g., "Free Lossless Audio Codec (FLAC)")
5. **Track List** - Numbered tracks with properly aligned durations
6. **Timing Info** - Total playing time and file size
7. **Footer** - Generation date and time

The description will automatically handle multi-disc albums, with separate track listings for each disc.
