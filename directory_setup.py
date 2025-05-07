#!/usr/bin/env python3
"""
Setup script to create the directory structure for Music-Upload-Assistant.
Run this script to set up the initial directory structure and create empty files.
"""
import os
import shutil
import sys

def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")

def create_file(file_path, content=""):
    """Create a file with the given content if it doesn't exist."""
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Created file: {file_path}")
    else:
        print(f"File already exists: {file_path}")

def main():
    """Main function to set up directory structure."""
    # Base directories
    directories = [
        "data/templates",
        "modules/audio_analyzer/format_handlers",
        "modules/metadata",
        "modules/quality",
        "modules/upload/trackers",
        "modules/utils",
        "tests",
        "docs/examples",
        "docs/templates",
        "docs/trackers",
        "temp",
        "output"
    ]

    # Create directories
    for directory in directories:
        create_directory(directory)

    # Create __init__.py files for Python modules
    python_dirs = [
        "modules",
        "modules/audio_analyzer",
        "modules/audio_analyzer/format_handlers",
        "modules/metadata",
        "modules/quality",
        "modules/upload",
        "modules/upload/trackers",
        "modules/utils",
        "tests"
    ]
    
    for directory in python_dirs:
        init_file = os.path.join(directory, "__init__.py")
        create_file(init_file, f'"""\n{directory.replace("/", ".")} package for Music-Upload-Assistant.\n"""\n')

    # Create empty template files
    template_files = [
        "data/templates/default_album.txt",
        "data/templates/default_track.txt",
        "data/templates/flac_album.txt",
        "data/templates/mp3_album.txt",
        "data/templates/yus_default.txt"
    ]
    
    for template_file in template_files:
        create_file(template_file)

    # Create empty module files
    module_files = [
        "modules/audio_analyzer/audio_analyzer.py",
        "modules/audio_analyzer/format_handlers/base_handler.py",
        "modules/audio_analyzer/format_handlers/flac_handler.py",
        "modules/audio_analyzer/format_handlers/mp3_handler.py",
        "modules/metadata/tag_processor.py",
        "modules/metadata/musicbrainz.py",
        "modules/metadata/acoustid.py",
        "modules/quality/transcode_detector.py",
        "modules/quality/dynamic_range.py",
        "modules/upload/torrent.py",
        "modules/upload/description.py",
        "modules/upload/trackers/yus_tracker.py",
        "modules/utils/file_utils.py"
    ]
    
    for module_file in module_files:
        create_file(module_file, f'"""\n{os.path.basename(module_file)} module for Music-Upload-Assistant.\n"""\n')

    # Create main files
    main_files = [
        "music_upload_assistant.py",
        "test_script.py",
        "requirements.txt",
        "README.md"
    ]
    
    for main_file in main_files:
        create_file(main_file)

    # Create example config file
    config_content = """
# Example configuration for Music-Upload-Assistant
config = {
    'app_name': 'Music-Upload-Assistant',
    'app_version': '0.1.0',
    'templates_dir': 'data/templates',
    'temp_dir': 'temp',
    'output_dir': 'output',
    'logging': {
        'level': 'INFO',
        'file': 'music_upload_assistant.log'
    }
}
"""
    create_file("data/config.example.py", config_content)

    # Create .gitignore file
    gitignore_content = """# Python-specific
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
venv/
env/
ENV/

# User-specific files
data/config.py
temp/
output/

# Logs
*.log
logs/

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*,cover
.hypothesis/

# Editors
.idea/
.vscode/
*.swp
*.swo
*~
"""
    create_file(".gitignore", gitignore_content)

    # Success message
    print("\nDirectory structure created successfully!")
    print("Next steps:")
    print("1. Copy or implement the module code files")
    print("2. Install the required dependencies with: pip install -r requirements.txt")
    print("3. Run the main script with: python music_upload_assistant.py --help")

if __name__ == "__main__":
    main()