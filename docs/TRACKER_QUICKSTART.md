# Quick Start: Adding New Trackers

This quick start guide will help you add a new tracker to the Music-Upload-Assistant in just a few minutes.

## Option 1: Add a New Tracker Configuration (Easiest)

If your tracker works similarly to existing trackers, just configure it:

```bash
# Add a new tracker configuration
python configure_tracker.py --add TRACKER_ID
```

You'll be prompted for:
- Tracker name
- Base URL
- API key
- Upload and announce URLs
- Optional: Category IDs and format IDs

## Option 2: Generate a Custom Tracker Module (Recommended)

If your tracker needs custom behavior, generate a module:

```bash
# Generate a custom tracker module
python create_tracker.py TRACKER_ID

# Configure the tracker
python configure_tracker.py --add TRACKER_ID

# Test the configuration
python configure_tracker.py --test TRACKER_ID
```

This creates a customizable tracker module in `modules/upload/trackers/tracker_id_tracker.py` that you can edit as needed.

## Option 3: Full Manual Implementation (Advanced)

For complete control, manually implement your tracker:

1. Create a file `modules/upload/trackers/your_tracker_id_tracker.py`
2. Extend the `GenericTracker` class
3. Override methods as needed
4. Configure with `python configure_tracker.py --add YOUR_TRACKER_ID`

## Testing Your Tracker

Before a real upload, test in debug mode:

```bash
# Simulate upload without actually uploading
python music_upload_assistant.py /path/to/album --tracker YOUR_TRACKER_ID --debug
```

## Troubleshooting Common Issues

### "Tracker is not properly configured"

If you see this error even after setting up the tracker:

```
Tracker SP is not properly configured
```

Check these common issues:

1. **Missing API key**: Make sure you've set an API key when configuring the tracker.

2. **API vs Form Authentication**: Some trackers use API keys even though they don't use a traditional API URL. 
   - Try setting the `api_auth_type` to one of: `bearer`, `param`, or `token`
   - For many trackers, the API key is sent as a form parameter

3. **URLs**: Ensure both the site URL and upload URL are properly configured.

4. **Custom is_configured**: Some trackers need a custom implementation. Edit the tracker module to override the `is_configured` method.

### How to Fix Authentication Issues

If a tracker uses an API key but doesn't have "api" in its URL (common for trackers like SP), you have two options:

1. **Simple Fix**: Set the `use_api` flag manually in your config:
   ```json
   "SP": {
      "enabled": true,
      "use_api": true,
      "api_key": "your_key",
      ...
   }
   ```

2. **Better Fix**: Customize your tracker module:
   - Edit `modules/upload/trackers/your_tracker_tracker.py`
   - Override the `is_configured` method to check only what's needed
   - Update the upload method to include the API key appropriately

Remember that each tracker has different requirements. Check the tracker's API documentation if available.

## Example: Common Tracker Setup

```python
# Configuration in data/config.json
{
  "trackers": {
    "YOUR_TRACKER": {
      "enabled": true,
      "name": "Your Tracker",
      "url": "https://yourtracker.example.com",
      "api_key": "your_api_key",
      "upload_url": "https://yourtracker.example.com/api/upload",
      "announce_url": "https://yourtracker.example.com/announce",
      "api_auth_type": "bearer",
      "category_ids": {
        "ALBUM": "5",
        "SINGLE": "6"
      },
      "format_ids": {
        "FLAC": "10",
        "MP3": "11"
      }
    }
  }
}
```

## Getting Help

For more detailed information, see:
- `docs/CUSTOM_TRACKERS_README.md` - Detailed guide for custom trackers
- `SCALABLE_TRACKERS_README.md` - Overview of the tracker system
- The example trackers in `modules/upload/trackers/`
