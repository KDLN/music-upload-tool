# Tracker Field Reference

This document explains the field names used by different trackers, particularly for cover images and category IDs.

## Cover Image Field Names

Different trackers use different field names for uploading cover images:

| Tracker | Cover Image Field Name | Notes |
|---------|------------------------|-------|
| SP (Seedpool) | `torrent_cover` | UNIT3D standard field name |
| YUS | `image` | Common default field name |
| Most Others | `image` | General convention |

## Category IDs for Music Content

Music content should use the appropriate category IDs:

| Tracker | Music Category IDs | Notes |
|---------|-------------------|-------|
| SP (Seedpool) | `5` | General music category |
| YUS | `8` (album), `9` (single/EP) | Two categories for music |

## UNIT3D-Based Trackers

Many trackers (including Seedpool) use the UNIT3D codebase, which has specific field validation:

```php
'torrent_cover' => 'nullable|image|mimes:jpg,jpeg,png,webp',
'cover_url'     => 'nullable|url',
'banner_url'    => 'nullable|url',
```

This means that cover images should:
1. Use the field name `torrent_cover` (with underscore)
2. Be in jpg, jpeg, png, or webp format
3. Be correctly identified as an image file

## Troubleshooting

If you encounter issues with tracker uploads:

1. Enable debug mode to see what fields are being sent:
   ```
   python music_upload_assistant.py --path /path/to/music --tracker SP --upload --debug
   ```

2. Check if you're using the correct field names:
   - For SP: `torrent_cover` (not `torrent-cover` or `image`)
   - For most others: `image`

3. Verify the image format is supported (usually jpg, png)

4. Ensure your category IDs are correct for the content type
