"""
Tracker manager module for Music-Upload-Assistant.
Handles tracker configuration and loading.
"""

import os
import logging
import importlib
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class TrackerManager:
    """
    Manages tracker configurations and handles tracker selection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the tracker manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.trackers = {}
        self._load_trackers()
    
    def _load_trackers(self):
        """Load all configured trackers."""
        if 'trackers' not in self.config:
            logger.warning("No trackers configured")
            return
            
        for tracker_id, tracker_config in self.config.get('trackers', {}).items():
            # Skip trackers without required fields or if not enabled
            if not tracker_config.get('enabled', True):
                logger.debug(f"Tracker {tracker_id} is disabled")
                continue
                
            try:
                # Import the appropriate tracker class
                if tracker_id.upper() == 'YUS':
                    from modules.upload.trackers.yus_tracker import YUSTracker
                    tracker = YUSTracker(self.config)
                    if tracker.is_configured():
                        self.trackers[tracker_id.upper()] = tracker
                        logger.info(f"Loaded tracker: {tracker_id}")
                    else:
                        logger.warning(f"Tracker {tracker_id} is not properly configured")
                
                # Add more trackers here as they're implemented
                # elif tracker_id.upper() == 'RED':
                #     from modules.upload.trackers.red_tracker import REDTracker
                #     self.trackers[tracker_id.upper()] = REDTracker(self.config)
                
                else:
                    # Try to dynamically load the tracker module
                    try:
                        module_name = f"modules.upload.trackers.{tracker_id.lower()}_tracker"
                        module = importlib.import_module(module_name)
                        
                        # Get the tracker class (assuming it's named [Name]Tracker)
                        class_name = f"{tracker_id.capitalize()}Tracker"
                        tracker_class = getattr(module, class_name)
                        
                        # Create an instance
                        tracker = tracker_class(self.config)
                        if hasattr(tracker, 'is_configured') and tracker.is_configured():
                            self.trackers[tracker_id.upper()] = tracker
                            logger.info(f"Dynamically loaded tracker: {tracker_id}")
                        else:
                            logger.warning(f"Tracker {tracker_id} is not properly configured")
                    except (ImportError, AttributeError) as e:
                        logger.error(f"Failed to dynamically load tracker {tracker_id}: {e}")
            
            except Exception as e:
                logger.error(f"Error loading tracker {tracker_id}: {e}")
    
    def get_tracker(self, tracker_id: str):
        """
        Get tracker by ID.
        
        Args:
            tracker_id: Tracker identifier
            
        Returns:
            object: Tracker instance or None if not found
        """
        return self.trackers.get(tracker_id.upper())
    
    def get_available_trackers(self) -> List[str]:
        """
        Get a list of available tracker IDs.
        
        Returns:
            list: Available tracker IDs
        """
        return list(self.trackers.keys())
    
    def is_tracker_available(self, tracker_id: str) -> bool:
        """
        Check if a tracker is available.
        
        Args:
            tracker_id: Tracker identifier
            
        Returns:
            bool: True if available, False otherwise
        """
        return tracker_id.upper() in self.trackers
