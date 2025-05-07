# Adding Custom Trackers to Music-Upload-Assistant

This document explains how to add support for new trackers to the Music-Upload-Assistant tool.

## Introduction

The Music-Upload-Assistant is designed to be easily extendable to support multiple trackers. The system provides a flexible configuration framework and base classes that make it straightforward to add new trackers without modifying the core code.

## Tracker Configuration

### Using the Configure Script

The simplest way to add a new tracker is to use the `configure_tracker.py` script:

```bash
python configure_tracker.py --add YOUR_TRACKER_ID
```

This will guide you through setting up a basic configuration for your tracker. The script will ask for:

- Tracker name
- Base URL
- API Key
- Upload and announce URLs
- Category and format IDs

Example:
```bash
python configure_tracker.py --add SP
```

### Configuration Parameters

Here's a list of the main configuration parameters for trackers:

- `enabled`: Whether the tracker is active
- `name`: Full name of the tracker
- `url`: Base URL of the tracker site
- `announce_url`: Torrent announce URL
- `api_key`: API key for authentication
- `upload_url`: API endpoint for uploads
- `source_name`: Source name for torrents
- `anon`: Whether to upload anonymously
- `category_ids`: Mapping of category names to IDs
- `format_ids`: Mapping of format names to IDs
- `api_auth_type`: How to authenticate ('bearer', 'param', 'token')
- `api_format`: Format of API requests ('json', 'form')

## Creating a Custom Tracker Module

For more control over the upload process, you can create a custom tracker module by following these steps:

1. Create a new Python file in `modules/upload/trackers/` named after your tracker, e.g., `mytracker_tracker.py`
2. Use the template file as a reference: `modules/upload/trackers/template_tracker.py`
3. Implement the necessary methods for your tracker's specific requirements

### Basic Module Structure

```python
from modules.upload.trackers.generic_tracker import GenericTracker

class MyTrackerTracker(GenericTracker):
    def __init__(self, config):
        super().__init__(config, "MYTRACKER")
        # Add tracker-specific initialization

    def _build_form_data(self, metadata, description):
        # Build tracker-specific form data for upload
        # Override this to handle your tracker's specific requirements
        
    def upload(self, torrent_path, description, metadata):
        # Override if you need to customize the upload process
        # In most cases, you can rely on the generic implementation
```

### Customizing the Upload Process

The most important methods to customize are:

1. `_build_form_data`: Create the specific form data required by your tracker
2. `upload`: Customize the upload process if needed
3. `_handle_error_response`: Parse error responses from your tracker

## Testing Your Tracker

After configuring your tracker, you can test it with:

```bash
python configure_tracker.py --test YOUR_TRACKER_ID
```

For a full test, use the debug mode in the main script:

```bash
python music_upload_assistant.py /path/to/album --create-torrent --tracker YOUR_TRACKER_ID --debug
```

This will simulate the upload process without actually uploading.

## Example: Creating a new tracker

Here's an example of implementing a basic tracker for a site called "MusicShare":

1. Add the tracker configuration:

```bash
python configure_tracker.py --add MS
```

2. Create file `modules/upload/trackers/ms_tracker.py`:

```python
from modules.upload.trackers.generic_tracker import GenericTracker

class MSTracker(GenericTracker):
    def __init__(self, config):
        super().__init__(config, "MS")
        # MusicShare specific settings
        ms_config = config.get('trackers', {}).get('MS', {})
        self.api_version = ms_config.get('api_version', 'v1')
        
    def _build_form_data(self, metadata, description):
        data = super()._build_form_data(metadata, description)
        
        # MusicShare requires additional fields
        data['api_version'] = self.api_version
        data['music_type'] = metadata.get('media', 'WEB')
        
        return data
```

3. Test your tracker:

```bash
python configure_tracker.py --test MS
```

## Common Issues and Solutions

- **API Authentication**: Different trackers may use different authentication methods. Configure the `api_auth_type` for your tracker.
- **Format IDs**: Make sure you have the correct format and category IDs for your tracker.
- **Cover Art**: Some trackers have specific requirements for cover art dimensions or format.
- **API Response Parsing**: Different trackers return different response formats. Customize the error handling if needed.

## Advanced Configuration

For trackers with more complex requirements, you can extend the configuration options:

```python
# In your tracker's __init__ method:
tracker_config = config.get('trackers', {}).get(tracker_id, {})
self.custom_option1 = tracker_config.get('custom_option1', 'default')
self.custom_option2 = tracker_config.get('custom_option2', 'default')
```

Then add these options to your tracker config:

```json
{
  "trackers": {
    "MYTRACKER": {
      "custom_option1": "value1",
      "custom_option2": "value2"
    }
  }
}
```