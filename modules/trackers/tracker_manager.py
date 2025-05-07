"""
Tracker manager module for Music-Upload-Tool.
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
            # Convert string 'True'/'False' to boolean if needed
            enabled = tracker_config.get('enabled', True)
            if isinstance(enabled, str):
                enabled = enabled.lower() == 'true'
                
            if not enabled:
                logger.debug(f"Tracker {tracker_id} is disabled")
                continue
                
            try:
                # Normalize tracker ID
                tracker_id = tracker_id.upper()
                
                # Try to dynamically load the tracker module
                try:
                    # Build the expected module name
                    module_name = f"modules.trackers.{tracker_id.lower()}_tracker"
                    
                    # Try to import the module
                    try:
                        module = importlib.import_module(module_name)
                        logger.debug(f"Successfully imported module: {module_name}")
                    except ImportError as e:
                        logger.warning(f"Could not import tracker module {module_name}: {e}")
                        # Try to use BaseTracker as fallback
                        from modules.trackers.base_tracker import BaseTracker
                        logger.info(f"Using BaseTracker for {tracker_id}")
                        
                        # Create a custom class on-the-fly
                        class DynamicTracker(BaseTracker):
                            def __init__(self, config):
                                super().__init__(config, tracker_id)
                        
                        # Add the tracker
                        tracker = DynamicTracker(self.config)
                        if tracker.is_configured():
                            self.trackers[tracker_id] = tracker
                            logger.info(f"Created dynamic tracker for: {tracker_id}")
                        else:
                            logger.warning(f"Dynamic tracker {tracker_id} is not properly configured")
                        continue
                    
                    # Get the expected class name (YusTracker, etc.)
                    expected_class_name = None
                    if tracker_id == 'YUS':
                        expected_class_name = 'YusTracker'
                    else:
                        # Build class name based on tracker ID
                        expected_class_name = f"{tracker_id.capitalize()}Tracker"
                    
                    # Try to get the class from the module
                    if hasattr(module, expected_class_name):
                        tracker_class = getattr(module, expected_class_name)
                    else:
                        # Look for any class that ends with "Tracker"
                        tracker_class = None
                        for attr_name in dir(module):
                            if attr_name.endswith("Tracker") and attr_name != "BaseTracker":
                                tracker_class = getattr(module, attr_name)
                                logger.debug(f"Found tracker class: {attr_name}")
                                break
                        
                        if not tracker_class:
                            raise AttributeError(f"No tracker class found in module {module_name}")
                    
                    # Create an instance of the tracker class
                    tracker = tracker_class(self.config)
                    
                    # Check if properly configured
                    if hasattr(tracker, 'is_configured') and tracker.is_configured():
                        self.trackers[tracker_id] = tracker
                        logger.info(f"Loaded tracker: {tracker_id}")
                    else:
                        logger.warning(f"Tracker {tracker_id} is not properly configured")
                        
                except Exception as e:
                    logger.error(f"Error loading tracker {tracker_id}: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error initializing tracker {tracker_id}: {e}")
    
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
