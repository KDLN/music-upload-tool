#!/bin/bash

echo "Music-Upload-Assistant Permission Fix Script"
echo "------------------------------------------"

# Create essential directories with proper permissions
echo "Creating essential directories..."
mkdir -p temp output
chmod 755 temp output

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found, creating a new one..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install minimal dependencies that shouldn't cause permission issues
echo "Installing minimal dependencies..."
pip install requests mutagen pillow

echo ""
echo "Basic setup complete!"
echo ""
echo "Try running the simplest test with:"
echo "python test_script.py -h"
echo ""
echo "If you still encounter permissions errors, you may need to:"
echo "1. Check file ownership: ls -la"
echo "2. Fix permissions: chmod -R 755 ."
echo "3. Install packages one by one: pip install packagename"
