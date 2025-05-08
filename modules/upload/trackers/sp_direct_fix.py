"""
This is a direct fix for the SP tracker cover field issue.
Simply replace the relevant part of your current SP tracker implementation.
"""

# Add this method to your SPTracker class to override the generic implementation:

def _build_file_payload(self, torrent_path: str, cover_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Build file payload for the SP tracker upload.
    Always uses 'torrent-cover' for the cover image field.
    
    Args:
        torrent_path: Path to torrent file
        cover_path: Path to cover image
        
    Returns:
        dict: Files for upload
    """
    files = {
        'torrent': (
            os.path.basename(torrent_path),
            open(torrent_path, 'rb'),
            'application/x-bittorrent'
        )
    }
    
    # Add cover file to upload if found - HARDCODED to use 'torrent-cover'
    if cover_path and os.path.exists(cover_path):
        try:
            cover_file_handle = open(cover_path, 'rb')
            mime_type = 'image/jpeg'  # Default to jpeg
            if cover_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif cover_path.lower().endswith('.gif'):
                mime_type = 'image/gif'
                
            # ALWAYS use 'torrent-cover' for SP tracker
            files['torrent-cover'] = (
                os.path.basename(cover_path),
                cover_file_handle,
                mime_type
            )
            logger.info(f"Added cover art to SP tracker using field name 'torrent-cover': {cover_path}")
        except Exception as e:
            logger.error(f"Error adding cover to upload: {e}")
            if 'cover_file_handle' in locals():
                cover_file_handle.close()
    
    return files
