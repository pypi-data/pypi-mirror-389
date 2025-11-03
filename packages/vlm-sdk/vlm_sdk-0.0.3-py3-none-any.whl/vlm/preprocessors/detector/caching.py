"""
Frame caching utilities for RT-DETR preprocessor.

Implements Pattern 5: Frame Caching - reuse results for similar/identical frames.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from vlm.core.types import BoundingBox, PreprocessingResult


@dataclass
class TemporalCache:
    """
    Cache for frame analysis results to avoid redundant processing.

    Caches detection results for frames that are similar or identical
    to recently processed frames.

    Attributes:
        frame_hash: Hash of the cached frame
        detections: List of detected objects
        timestamp: Unix timestamp when cached
        frame_number: Frame number
        result: Complete preprocessing result
    """
    frame_hash: Optional[int] = None
    detections: List[BoundingBox] = field(default_factory=list)
    timestamp: float = 0.0
    frame_number: int = 0
    result: Optional[PreprocessingResult] = None

    def is_valid(self, current_time: float, max_age: float = 1.0) -> bool:
        """
        Check if cache is still valid.

        Cache expires after max_age seconds.

        Args:
            current_time: Current timestamp
            max_age: Maximum age in seconds (default 1 second)

        Returns:
            True if cache is valid and can be reused
        """
        if self.result is None:
            return False

        age = current_time - self.timestamp
        return age < max_age

    def clear(self):
        """Clear all cached data."""
        self.frame_hash = None
        self.detections = []
        self.timestamp = 0.0
        self.frame_number = 0
        self.result = None
