"""
Dynamic range calculation module for Music-Upload-Assistant.
Calculates dynamic range and related audio quality metrics.
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("librosa not installed. Dynamic range calculation will not be available.")
    LIBROSA_AVAILABLE = False

class DynamicRangeCalculator:
    """
    Calculates dynamic range and related audio quality metrics.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dynamic range calculator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
    
    def calculate_dynamic_range(self, file_path: str) -> Optional[float]:
        """
        Calculate the dynamic range of an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            float: Dynamic range in dB or None if calculation failed
        """
        if not LIBROSA_AVAILABLE:
            logger.error("librosa is required for dynamic range calculation")
            return None
        
        try:
            # Load audio file
            y, sr = self._load_audio(file_path)
            if y is None:
                return None
            
            # Calculate RMS energy in frames
            frame_length = int(sr * 0.05)  # 50ms frames
            hop_length = int(sr * 0.025)   # 25ms hop
            S = librosa.stft(y, n_fft=frame_length, hop_length=hop_length)
            rms = librosa.feature.rms(S=S)[0]
            
            # Calculate dynamic range using