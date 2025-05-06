async def process_album(album_path: str, options: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an album directory.
    
    Args:
        album_path: Path to the album directory
        options: Processing options
        config: Configuration dictionary
        
    Returns:
        dict: Processing results
    """
    logger.info(f"Processing album: {album_path}")
    
    # Find audio files
    audio_files = find_audio_files(album_path)
    if not audio_files:
        return {
            'success': False,
            'error': f"No supported audio files found in {album_path}"
        }
    
    # Analyze album structure
    album_structure = get_album_structure(audio_files)
    
    # Create a unique working directory for this album
    album_name = os.path.basename(album_path)
    temp_dir = os.path.join(config['temp_dir'], f"album_{album_name}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Find cover art
    cover_art_path = album_structure.get('cover_art') or find_cover_art(album_path)
    
    # Create a modified options dict for track processing that disables torrent creation
    # This prevents creating individual torrents for each track when processing an album
    track_options = options.copy()
    track_options['create_torrent'] = False  # Disable torrent creation for individual tracks
    track_options['upload'] = False  # Disable upload for individual tracks
    
    # Process each file with the modified options
    track_results = []
    
    for file_path in album_structure['files']:
        # Use the modified options that disable torrent creation
        result = await process_file(file_path, track_options, config)
        if result['success']:
            track_results.append(result)
        else:
            logger.warning(f"Error processing {file_path}: {result.get('error', 'Unknown error')}")
    
    if not track_results:
        return {
            'success': False,
            'error': "Failed to process any files in the album"
        }
    
    # Consolidate album metadata
    album_metadata = consolidate_album_metadata(track_results)
    
    # Add cover art
    if cover_art_path:
        album_metadata['cover_art_path'] = cover_art_path
    
    # Generate album description
    if options.get('generate_description', True):
        try:
            description_generator = DescriptionGenerator(config)
            
            # Collect quality info from each track
            quality_info = []
            for result in track_results:
                metadata = result['metadata']
                quality_info.append({
                    'title': metadata.get('title', 'Unknown'),
                    'format': metadata.get('format', 'Unknown'),
                    'sample_rate': f"{metadata.get('sample_rate', 0) / 1000:.1f} kHz",
                    'bit_depth': f"{metadata.get('bit_depth', '')}",
                    'channels': 'Stereo' if metadata.get('channels', 0) == 2 else 'Mono',
                    'bitrate': f"{metadata.get('bitrate', 0)} kbps",
                    'duration': time.strftime('%M:%S', time.gmtime(metadata.get('duration', 0)))
                })
            
            description = description_generator.generate_album_description(album_metadata, quality_info)
            
            description_path = os.path.join(temp_dir, "ALBUM_DESCRIPTION.txt")
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(description)
            album_metadata['description_path'] = description_path
            
            logger.info("Generated album description")
        except Exception as e:
            logger.error(f"Error generating album description: {e}")
    
    # Create torrent if requested
    if options.get('create_torrent', False):
        try:
            torrent_creator = TorrentCreator(config)
            
            # Get tracker config if specified
            tracker_id = options.get('tracker')
            announce_url = options.get('announce_url')
            source = None
            
            if tracker_id:
                tracker_config = get_tracker_config(config, tracker_id)
                if tracker_config:
                    announce_url = tracker_config.get('announce_url', announce_url)
                    source = tracker_config.get('source_name')
            
            # Create torrent
            torrent_path = torrent_creator.create_torrent(
                album_path,
                announce_url=announce_url,
                source=source,
                comment=f"{album_metadata.get('album', 'Unknown')} - "
                       f"{album_metadata.get('album_artists', ['Unknown'])[0]}",
                piece_size=options.get('piece_size', 'auto')
            )
            
            album_metadata['torrent_path'] = torrent_path
            logger.info(f"Created album torrent: {torrent_path}")
        except Exception as e:
            logger.error(f"Error creating album torrent: {e}")
    
    # Upload to tracker if requested
    if options.get('upload', False) and options.get('tracker'):
        try:
            # This would be implemented with the tracker-specific code
            # for now just log that it would be uploaded
            logger.info(f"Would upload album to tracker: {options['tracker']}")
            album_metadata['uploaded'] = False
        except Exception as e:
            logger.error(f"Error uploading album to tracker: {e}")
    
    return {
        'success': True,
        'metadata': album_metadata,
        'track_results': track_results,
        'temp_dir': temp_dir
    }