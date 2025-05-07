# Scalable Tracker System for Music-Upload-Assistant

This document explains the scalable tracker system implemented in the Music-Upload-Assistant tool, which allows for easy addition of new trackers without modifying the core code.

## Overview

The Music-Upload-Assistant now features a flexible, extensible architecture for supporting multiple music trackers. The system includes:

1. **Dynamic Tracker Configuration**: Add new trackers through a simple command-line interface
2. **Generic Base Classes**: Implement new trackers by extending provided base classes
3. **Dynamic Module Loading**: Trackers are loaded dynamically at runtime based on configuration
4. **Template-Based Creation**: Generate new tracker modules automatically with a utility script

## How the System Works

The system consists of several key components:

1. **ConfigManager**: Handles loading, saving, and accessing tracker configurations
2. **TrackerManager**: Dynamically loads and initializes tracker modules
3. **GenericTracker**: Base class that provides common functionality for all trackers
4. **Tracker Modules**: Specific implementations for each supported tracker

## Adding New Trackers

There are three ways to add a new tracker to the system:

### 1. Using the Configuration Utility

The simplest way to add a new tracker is through the configuration utility:

```bash
python configure_tracker.py --add YOUR_TRACKER_ID
```

This interactive script will prompt you for the necessary configuration details and save them to your config file.

### 2. Using the Tracker Generator

For a more customized implementation, use the tracker generator utility:

```bash
python create_tracker.py YOUR_TRACKER_ID
```

This will:
- Create a new tracker module based on the template
- Create a test script for your tracker
- Provide instructions for configuration and testing

### 3. Manual Implementation

For complete control, you can manually create a tracker module by:

1. Creating a new Python file in `modules/upload/trackers/your_tracker_id_tracker.py`
2. Implementing a class that extends `GenericTracker`
3. Configuring the tracker using `configure_tracker.py`

## Testing Your Tracker

After adding a new tracker, you can test it using:

```bash
# Test the configuration
python configure_tracker.py --test YOUR_TRACKER_ID

# Test with debug mode (simulates upload without actually uploading)
python music_upload_assistant.py /path/to/album --tracker YOUR_TRACKER_ID --debug
```

## Customizing Tracker Behavior

Each tracker can customize these key aspects of the upload process:

1. **Form Data**: Customize what data is sent to the tracker (`_build_form_data`)
2. **Authentication**: Control how the tracker authenticates (`api_auth_type`)
3. **Upload Process**: Customize the actual upload request (`upload`)
4. **Error Handling**: Parse tracker-specific error responses (`_handle_error_response`)

## Example: Adding a New Tracker

Here's an example workflow for adding support for a new tracker called "MusicHaven":

1. **Add the configuration**:
   ```bash
   python configure_tracker.py --add MH
   ```

2. **Generate the tracker module**:
   ```bash
   python create_tracker.py MH
   ```

3. **Customize the implementation** (if needed):
   Edit `modules/upload/trackers/mh_tracker.py` to implement any special requirements

4. **Test the tracker**:
   ```bash
   python configure_tracker.py --test MH
   ```

5. **Use in a real upload**:
   ```bash
   python music_upload_assistant.py /path/to/album --tracker MH --create-torrent --upload
   ```

## Advanced Tracker Configuration

Trackers can have advanced configuration options set in the configuration file:

```json
{
  "trackers": {
    "MH": {
      "api_auth_type": "bearer",
      "api_format": "json",
      "custom_endpoint": "special/upload",
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

## Troubleshooting

Common issues and solutions:

- **Module not found**: Make sure your tracker module is named correctly (`lowercase_tracker_id_tracker.py`)
- **Class not found**: Ensure your tracker class follows the naming convention (`TrackerIdTracker`)
- **Authentication failures**: Verify API keys and authentication method
- **Format/Category ID errors**: Double-check the IDs required by your tracker

## Adding Advanced Features

For trackers with special requirements, consider implementing these advanced features:

1. **Custom authentication flows**: For trackers requiring login sessions
2. **Special field handling**: For trackers with unusual data requirements
3. **Response parsing**: For trackers with complex response formats
4. **Cover art processing**: For trackers with special image requirements

## Available Tracker Templates

The Music-Upload-Assistant includes these base templates:

1. **GenericTracker**: Basic functionality for all trackers
2. **Template Tracker**: Starting point for new implementations
3. **YUS Tracker**: Example implementation for the YUS tracker
4. **SP Tracker**: Example implementation for the SP tracker
