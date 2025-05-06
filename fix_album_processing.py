#!/usr/bin/env python3
"""
Fix Album Processing Script for Music-Upload-Assistant.
This script enhances the cover art extraction and processing for YUS uploads.
"""

import os
import sys
import shutil
import logging
from PIL import Image
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix-album-processing")

def process_cover_art(album_path, output_path=None):
    """
    Process album cover art and prepare a copy that works well with trackers.
    
    Args:
        album_path: Path to album directory
        output_path: Optional path to save the processed cover
        
    Returns:
        str: Path to the processed cover art or None if not found
    """
    logger.info(f"Processing cover art for album: {album_path}")
    
    # Find all image files in the directory
    image_files = []
    for filename in os.listdir(album_path):
        if not os.path.isfile(os.path.join(album_path, filename)):
            continue
            
        # Check for image extensions
        ext = os.path.splitext(filename.lower())[1]
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            image_files.append(os.path.join(album_path, filename))
    
    if not image_files:
        logger.warning(f"No image files found in {album_path}")
        return None
    
    # Score the images to find the most likely cover
    best_image = None
    best_score = -1
    
    for img_path in image_files:
        score = 0
        filename = os.path.basename(img_path).lower()
        
        # Prefer files with "cover" in the name
        if 'cover' in filename:
            score += 20
        if 'front' in filename:
            score += 15
        if 'folder' in filename:
            score += 10
        if 'art' in filename:
            score += 5
            
        # Check if the image is square (likely album art)
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                
                # Prefer square images
                if abs(width - height) < 10:
                    score += 15
                
                # Prefer larger images
                area = width * height
                score += min(10, area // 10000)
                
                # Prefer JPEG format
                if img_path.lower().endswith('.jpg') or img_path.lower().endswith('.jpeg'):
                    score += 5
        except Exception as e:
            logger.warning(f"Error checking image dimensions: {e}")
            
        if score > best_score:
            best_score = score
            best_image = img_path
    
    if not best_image:
        logger.warning("Could not determine best cover image")
        return None
        
    logger.info(f"Selected cover image: {best_image} (score: {best_score})")
    
    # Process the image
    if not output_path:
        output_dir = os.path.join("temp", "cover_prep")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "cover.jpg")
    
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Open, process and save the image
        with Image.open(best_image) as img:
            # If it's not a JPEG, convert it
            if not best_image.lower().endswith('.jpg') and not best_image.lower().endswith('.jpeg'):
                # Convert to RGB if needed (e.g., for PNG with transparency)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Make a reasonable size for tracker uploads
                max_size = 1000
                if img.width > max_size or img.height > max_size:
                    # Maintain aspect ratio
                    if img.width > img.height:
                        new_size = (max_size, int(img.height * max_size / img.width))
                    else:
                        new_size = (int(img.width * max_size / img.height), max_size)
                    img = img.resize(new_size, Image.LANCZOS)
                
                # Save as JPEG
                img.save(output_path, 'JPEG', quality=90)
                logger.info(f"Converted and saved cover image to: {output_path}")
            else:
                # Just copy the file
                shutil.copy2(best_image, output_path)
                logger.info(f"Copied cover image to: {output_path}")
                
        return output_path
    except Exception as e:
        logger.error(f"Error processing cover image: {e}")
        # Try a simple file copy as fallback
        try:
            shutil.copy2(best_image, output_path)
            logger.info(f"Fallback: Copied cover image to: {output_path}")
            return output_path
        except Exception as e2:
            logger.error(f"Failed to copy cover image: {e2}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Fix Album Processing for Music-Upload-Assistant')
    parser.add_argument('album_path', help='Path to album directory')
    parser.add_argument('--output', '-o', help='Output path for cover image')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.album_path):
        logger.error(f"Album path is not a directory: {args.album_path}")
        return 1
    
    cover_path = process_cover_art(args.album_path, args.output)
    
    if cover_path:
        print(f"Successfully processed cover art: {cover_path}")
        return 0
    else:
        print("Failed to process cover art")
        return 1

if __name__ == "__main__":
    sys.exit(main())
