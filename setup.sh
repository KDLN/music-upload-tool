#!/bin/bash

echo "Music-Upload-Assistant Setup Script"
echo "----------------------------------"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Make sure python3-venv is installed:"
        echo "sudo apt install python3-venv python3-full"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install minimal dependencies
echo "Installing essential dependencies..."
pip install requests mutagen pillow bencodepy musicbrainzngs pyacoustid colorama

# Run setup script
echo "Setting up directory structure..."
python directory_setup.py

echo ""
echo "Setup complete! You can now run the tool with:"
echo "source venv/bin/activate"
echo "python music_upload_assistant.py /path/to/music"
echo ""
echo "To test the tool without uploading:"
echo "python test_script.py /path/to/music"
