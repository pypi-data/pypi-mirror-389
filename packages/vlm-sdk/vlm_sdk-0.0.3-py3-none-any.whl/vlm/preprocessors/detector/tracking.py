"""
Object tracking utilities for RT-DETR preprocessor.

Tracks objects across frames to detect motion, calculate trajectories,
and maintain importance scores.
"""

from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np
from vlm.core.types import BoundingBox


@dataclass
class TrackedObject:
    """
    Represents an object tracked across multiple frames.

    Attributes:
        track_id: Unique tracking ID
        bbox: Current bounding box
        first_seen_frame: Frame number when first detected
        last_seen_frame: Frame number when last seen
        trajectory: List of (x, y) center positions over time
        stationary_frames: Number of consecutive frames without movement
        importance_score: Dynamic importance score (decays for stationary objects)
    """
    track_id: int
    bbox: BoundingBox
    first_seen_frame: int
    last_seen_frame: int
    trajectory: List[Tuple[float, float]] = field(default_factory=list)  # (x, y) centers
    stationary_frames: int = 0
    importance_score: float = 1.0

    def update_position(self, bbox: BoundingBox, frame_num: int):
        """
        Update object position and trajectory.

        Args:
            bbox: New bounding box
            frame_num: Current frame number
        """
        self.bbox = bbox
        self.last_seen_frame = frame_num
        center = bbox.center()
        self.trajectory.append(center)

        # Check if object moved significantly
        if len(self.trajectory) >= 2:
            prev_center = self.trajectory[-2]
            distance = np.sqrt((center[0] - prev_center[0])**2 + (center[1] - prev_center[1])**2)
            if distance < 10:  # Less than 10 pixels
                self.stationary_frames += 1
            else:
                self.stationary_frames = 0

    def get_velocity(self) -> float:
        """
        Calculate average velocity over last N frames.

        Returns:
            Average velocity in pixels per frame
        """
        if len(self.trajectory) < 2:
            return 0.0

        recent = self.trajectory[-5:]  # Last 5 positions
        total_distance = 0.0
        for i in range(1, len(recent)):
            dx = recent[i][0] - recent[i-1][0]
            dy = recent[i][1] - recent[i-1][1]
            total_distance += np.sqrt(dx**2 + dy**2)

        return total_distance / (len(recent) - 1)

    def decay_importance(self, current_frame: int, decay_rate: float = 0.95):
        """
        Decay importance score for stationary objects.

        Objects that don't move become less important over time.

        Args:
            current_frame: Current frame number
            decay_rate: Rate at which importance decays (0-1)
        """
        frames_elapsed = current_frame - self.last_seen_frame
        if self.stationary_frames > 30:  # Stationary for >30 frames (~1 second at 30fps)
            self.importance_score *= decay_rate

    def get_age(self, current_frame: int) -> int:
        """
        Get age of tracked object in frames.

        Args:
            current_frame: Current frame number

        Returns:
            Number of frames since first seen
        """
        return current_frame - self.first_seen_frame

    def is_active(self, current_frame: int, max_age: int = 30) -> bool:
        """
        Check if object is still active (recently seen).

        Args:
            current_frame: Current frame number
            max_age: Maximum frames since last seen

        Returns:
            True if object seen recently
        """
        return (current_frame - self.last_seen_frame) <= max_age
