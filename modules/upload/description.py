"""
Description Generator module for Music-Upload-Assistant.
Generates formatted descriptions for music uploads to various trackers.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import datetime
import re

logger = logging.getLogger(__name__)

class DescriptionGenerator:
    """
    Generates formatted descriptions for music uploads.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the description generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.templates_dir = config.get('templates_dir', os.path.join('data', 'templates'))
    
    def generate_track_description(self, metadata: Dict[str, Any], quality: Dict[str, Any]) -> str:
        """
        Generate a description for a single track.
        
        Args:
            metadata: Track metadata
            quality: Audio quality information
            
        Returns:
            str: Formatted description
        """
        # Get appropriate template for the track format
        template_name = self._get_template_name(metadata, quality)
        template = self._load_template(template_name)
        
        # Prepare template variables
        template_vars = self._prepare_template_vars(metadata, quality)
        
        # Process template
        description = self._process_template(template, template_vars)
        
        return description
    
    def generate_album_description(self, metadata: Dict[str, Any], quality_list: List[Dict[str, Any]]) -> str:
        """
        Generate a description for an album.
        
        Args:
            metadata: Album metadata
            quality_list: List of audio quality information for all tracks
            
        Returns:
            str: Formatted description
        """
        # Get appropriate template for the album format
        template_name = self._get_album_template_name(metadata, quality_list)
        template = self._load_template(template_name)
        
        # Prepare template variables
        template_vars = self._prepare_album_template_vars(metadata, quality_list)
        
        # Process template
        description = self._process_template(template, template_vars)
        
        return description
    
    def _get_template_name(self, metadata: Dict[str, Any], quality: Dict[str, Any]) -> str:
        """
        Determine the appropriate template name based on metadata and quality.
        
        Args:
            metadata: Track metadata
            quality: Audio quality information
            
        Returns:
            str: Template name
        """
        # Determine template based on format, quality, etc.
        format_type = quality.get('format', 'unknown').lower()
        
        # Check for specific template for the tracker if specified
        tracker = self.config.get('tracker')
        if tracker:
            # Specific tracker and format template
            specific_template = f"{tracker.lower()}_{format_type}_track.txt"
            if os.path.exists(os.path.join(self.templates_dir, specific_template)):
                return specific_template
            
            # Generic tracker template
            tracker_template = f"{tracker.lower()}_track.txt"
            if os.path.exists(os.path.join(self.templates_dir, tracker_template)):
                return tracker_template
        
        # Format-specific template
        format_template = f"{format_type}_track.txt"
        if os.path.exists(os.path.join(self.templates_dir, format_template)):
            return format_template
        
        # Default template
        return "default_track.txt"
    
    def _get_album_template_name(self, metadata: Dict[str, Any], quality_list: List[Dict[str, Any]]) -> str:
        """
        Determine the appropriate album template name.
        
        Args:
            metadata: Album metadata
            quality_list: List of audio quality information for all tracks
            
        Returns:
            str: Template name
        """
        # Determine primary format from quality list
        formats = [q.get('format', '').lower() for q in quality_list if 'format' in q]
        primary_format = formats[0] if formats else 'unknown'
        
        # Check if mixed format
        is_mixed = len(set(formats)) > 1 if formats else False
        
        # Check for specific template for the tracker if specified
        tracker = self.config.get('tracker')
        if tracker:
            # Specific tracker, format, and mixed/single format template
            mixed_str = "mixed" if is_mixed else primary_format
            specific_template = f"{tracker.lower()}_{mixed_str}_album.txt"
            if os.path.exists(os.path.join(self.templates_dir, specific_template)):
                return specific_template
            
            # Generic tracker template
            tracker_template = f"{tracker.lower()}_album.txt"
            if os.path.exists(os.path.join(self.templates_dir, tracker_template)):
                return tracker_template
        
        # Format-specific template (or mixed)
        format_str = "mixed" if is_mixed else primary_format
        format_template = f"{format_str}_album.txt"
        if os.path.exists(os.path.join(self.templates_dir, format_template)):
            return format_template
        
        # Default template
        return "default_album.txt"
    
    def _load_template(self, template_name: str) -> str:
        """
        Load a template from the templates directory.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            str: Template content
        """
        template_path = os.path.join(self.templates_dir, template_name)
        
        # Check if template exists
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_path}")
            # Return basic fallback template
            return self._get_fallback_template(template_name)
        
        # Load template
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading template {template_path}: {str(e)}")
            return self._get_fallback_template(template_name)
    
    def _get_fallback_template(self, template_name: str) -> str:
        """
        Get a fallback template if the requested one is not found.
        
        Args:
            template_name: Name of the template that wasn't found
            
        Returns:
            str: Fallback template content
        """
        if 'track' in template_name:
            return """[b]${title}[/b] by [b]${artists}[/b]

[b]Album:[/b] ${album}
[b]Year:[/b] ${year}
[b]Format:[/b] ${format} ${sample_rate} ${bit_depth}
[b]Bitrate:[/b] ${bitrate}

[b]Download:[/b] Uploaded with Music-Upload-Assistant
"""
        else:  # Album template
            return """[b]${album}[/b] by [b]${album_artists}[/b]

[b]Year:[/b] ${year}
[b]Label:[/b] ${label}
[b]Catalog Number:[/b] ${catalog_number}
[b]Format:[/b] ${format} ${sample_rate} ${bit_depth}
[b]Tracks:[/b] ${track_count}

[b]Track List:[/b]
${track_list}

[b]Download:[/b] Uploaded with Music-Upload-Assistant
"""
    
    def _prepare_template_vars(self, metadata: Dict[str, Any], quality: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare variables for template processing for a single track.
        
        Args:
            metadata: Track metadata
            quality: Audio quality information
            
        Returns:
            dict: Template variables
        """
        # Prepare base variables
        template_vars = {
            'title': metadata.get('title', 'Unknown'),
            'artists': self._format_list(metadata.get('artists', ['Unknown'])),
            'album': metadata.get('album', 'Unknown'),
            'album_artists': self._format_list(metadata.get('album_artists', metadata.get('artists', ['Unknown']))),
            'year': metadata.get('year', ''),
            'date': metadata.get('date', ''),
            'genres': self._format_list(metadata.get('genres', [])),
            'track_number': metadata.get('track_number', ''),
            'total_tracks': metadata.get('total_tracks', ''),
            'disc_number': metadata.get('disc_number', ''),
            'total_discs': metadata.get('total_discs', ''),
            'label': metadata.get('label', ''),
            'catalog_number': metadata.get('catalog_number', ''),
            'media': metadata.get('media', ''),
            'release_country': metadata.get('release_country', ''),
            'format': quality.get('format', 'Unknown'),
            'compression': quality.get('compression', ''),
            'sample_rate': quality.get('sample_rate', ''),
            'bit_depth': quality.get('bit_depth', ''),
            'channels': quality.get('channels', ''),
            'bitrate': quality.get('bitrate', ''),
            'duration': quality.get('duration', ''),
            'file_size': quality.get('file_size', ''),
            'encoder': quality.get('encoder', ''),
            'upload_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'dynamic_range': quality.get('dynamic_range', '')
        }
        
        # Add any specific warnings
        if 'warnings' in quality and quality['warnings']:
            template_vars['warnings'] = '\n'.join(quality['warnings'])
        else:
            template_vars['warnings'] = ''
        
        # Add any additional variables from metadata
        for key, value in metadata.items():
            if key not in template_vars and isinstance(value, (str, int, float)):
                template_vars[key] = str(value)
        
        return template_vars
    
    def _prepare_album_template_vars(self, metadata: Dict[str, Any], quality_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Prepare variables for template processing for an album.
        
        Args:
            metadata: Album metadata
            quality_list: List of audio quality information for all tracks
            
        Returns:
            dict: Template variables
        """
        # Prepare base variables
        template_vars = {
            'album': metadata.get('album', 'Unknown'),
            'album_artists': self._format_list(metadata.get('album_artists', ['Unknown'])),
            'year': metadata.get('year', ''),
            'date': metadata.get('date', ''),
            'genres': self._format_list(metadata.get('genres', [])),
            'total_tracks': metadata.get('total_tracks', str(len(quality_list))),
            'total_discs': metadata.get('total_discs', '1'),
            'label': metadata.get('label', ''),
            'catalog_number': metadata.get('catalog_number', ''),
            'media': metadata.get('media', ''),
            'release_country': metadata.get('release_country', ''),
            'upload_date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        # Calculate album stats from quality list
        if quality_list:
            formats = set(q.get('format', '') for q in quality_list if 'format' in q)
            sample_rates = set(q.get('sample_rate', '') for q in quality_list if 'sample_rate' in q)
            bit_depths = set(q.get('bit_depth', '') for q in quality_list if 'bit_depth' in q)
            
            template_vars['format'] = '/'.join(formats) if len(formats) > 1 else next(iter(formats), 'Unknown')
            template_vars['sample_rate'] = '/'.join(sample_rates) if len(sample_rates) > 1 else next(iter(sample_rates), '')
            template_vars['bit_depth'] = '/'.join(bit_depths) if len(bit_depths) > 1 else next(iter(bit_depths), '')
            
            # Calculate total size and duration
            total_size = sum(float(q.get('file_size', '0').replace(' MB', '').replace(',', '.')) for q in quality_list if 'file_size' in q)
            template_vars['total_size'] = f"{total_size:.2f} MB"
            
            # Generate track list
            track_list = []
            for i, quality in enumerate(quality_list):
                track_num = i + 1
                track_list.append(f"{track_num}. {quality.get('title', f'Track {track_num}')} ({quality.get('duration', '')})")
            
            template_vars['track_list'] = '\n'.join(track_list)
        
        # Add any additional variables from metadata
        for key, value in metadata.items():
            if key not in template_vars and isinstance(value, (str, int, float)):
                template_vars[key] = str(value)
        
        return template_vars
    
    def _process_template(self, template: str, template_vars: Dict[str, str]) -> str:
        """
        Process a template by substituting variables.
        
        Args:
            template: Template content
            template_vars: Variables to substitute
            
        Returns:
            str: Processed template
        """
        # Replace template variables ${var}
        result = template
        
        # Find all variables in the template
        variables = re.findall(r'\${([^}]+)}', template)
        
        # Replace each variable
        for var in variables:
            if var in template_vars and template_vars[var]:
                # Replace with actual value
                result = result.replace(f"${{{var}}}", str(template_vars[var]))
            else:
                # Variable not found or empty, replace with empty string
                result = result.replace(f"${{{var}}}", "")
        
        # Process conditionals [if:var]...[endif]
        result = self._process_conditionals(result, template_vars)
        
        # Remove empty lines (more than 2 consecutive)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
    
    def _process_conditionals(self, template: str, template_vars: Dict[str, str]) -> str:
        """
        Process conditional blocks in a template.
        
        Args:
            template: Template content
            template_vars: Variables to check
            
        Returns:
            str: Processed template
        """
        # Process [if:var]...[endif] blocks
        pattern = r'\[if:([^\]]+)\](.*?)\[endif\]'
        
        def replace_conditional(match):
            condition = match.group(1)
            content = match.group(2)
            
            # Check if the condition is satisfied (variable exists and is not empty)
            if condition in template_vars and template_vars[condition]:
                return content
            else:
                return ''
        
        # Process nested conditionals repeatedly until no more changes
        result = template
        while re.search(pattern, result, re.DOTALL):
            result = re.sub(pattern, replace_conditional, result, flags=re.DOTALL)
        
        return result
    
    def _format_list(self, items: List[str]) -> str:
        """
        Format a list of items as a string.
        
        Args:
            items: List of items
            
        Returns:
            str: Formatted string
        """
        if not items:
            return ""
        
        if len(items) == 1:
            return items[0]
        
        if len(items) == 2:
            return f"{items[0]} & {items[1]}"
        
        return ", ".join(items[:-1]) + f" & {items[-1]}"


# Example templates for demonstration
DEFAULT_TRACK_TEMPLATE = """[b]${title}[/b] by [b]${artists}[/b]

[b]Album:[/b] ${album}
[if:year][b]Year:[/b] ${year}[endif]
[b]Format:[/b] ${format} ${sample_rate} ${bit_depth}
[b]Bitrate:[/b] ${bitrate}

[if:warnings][b]Warnings:[/b]
${warnings}[endif]

[b]Download:[/b] Uploaded with Music-Upload-Assistant
"""

DEFAULT_ALBUM_TEMPLATE = """[b]${album}[/b] by [b]${album_artists}[/b]

[if:year][b]Year:[/b] ${year}[endif]
[if:label][b]Label:[/b] ${label}[endif]
[if:catalog_number][b]Catalog Number:[/b] ${catalog_number}[endif]
[b]Format:[/b] ${format} ${sample_rate} ${bit_depth}
[b]Tracks:[/b] ${total_tracks}[if:total_discs] on ${total_discs} discs[endif]
[if:total_size][b]Size:[/b] ${total_size}[endif]

[b]Track List:[/b]
${track_list}

[b]Download:[/b] Uploaded with Music-Upload-Assistant
"""

if __name__ == "__main__":
    import sys
    import json
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create template directory if needed
    os.makedirs('data/templates', exist_ok=True)
    
    # Create default templates for demonstration
    with open('data/templates/default_track.txt', 'w', encoding='utf-8') as f:
        f.write(DEFAULT_TRACK_TEMPLATE)
    
    with open('data/templates/default_album.txt', 'w', encoding='utf-8') as f:
        f.write(DEFAULT_ALBUM_TEMPLATE)
    
    if len(sys.argv) < 2:
        print("Usage: python description_generator.py <track|album> [template_name]")
        sys.exit(1)
    
    mode = sys.argv[1]
    template_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    config = {'templates_dir': 'data/templates'}
    generator = DescriptionGenerator(config)
    
    # Sample metadata and quality for demonstration
    if mode == 'track':
        metadata = {
            'title': 'Sample Track',
            'artists': ['Artist Name', 'Featured Artist'],
            'album': 'Sample Album',
            'album_artists': ['Artist Name'],
            'year': 2023,
            'genres': ['Electronic', 'Ambient'],
            'track_number': 1,
            'total_tracks': 10,
            'label': 'Sample Label',
            'catalog_number': 'SMP-123'
        }
        
        quality = {
            'format': 'FLAC',
            'compression': 'Lossless',
            'sample_rate': '44.1 kHz',
            'bit_depth': '16-bit',
            'channels': 'Stereo',
            'bitrate': '1411 kbps',
            'duration': '3:45',
            'file_size': '30.5 MB'
        }
        
        description = generator.generate_track_description(metadata, quality)
        print(description)
    
    elif mode == 'album':
        metadata = {
            'album': 'Sample Album',
            'album_artists': ['Artist Name'],
            'year': 2023,
            'genres': ['Electronic', 'Ambient'],
            'total_tracks': 10,
            'total_discs': 1,
            'label': 'Sample Label',
            'catalog_number': 'SMP-123',
            'release_country': 'United States'
        }
        
        quality_list = [
            {
                'title': f'Track {i}',
                'format': 'FLAC',
                'compression': 'Lossless',
                'sample_rate': '44.1 kHz',
                'bit_depth': '16-bit',
                'duration': f"{3 + i // 2}:{(30 + i) % 60:02d}",
                'file_size': f"{25 + i * 2}.5 MB"
            }
            for i in range(1, 11)
        ]
        
        description = generator.generate_album_description(metadata, quality_list)
        print(description)
    
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)