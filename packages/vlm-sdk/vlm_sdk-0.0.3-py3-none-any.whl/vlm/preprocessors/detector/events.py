"""
Event-based processing for video analysis.

Instead of sending individual frames to VLM, we track events (motion periods)
and send complete video clips. This reduces costs by 10-15x.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np
from vlm.core.types import Frame, BoundingBox


@dataclass
class Event:
    """
    Represents a continuous period of activity/motion in video.

    Events are defined as continuous periods where something interesting
    is happening (motion, objects present, etc.). Instead of sending
    individual frames, we send the entire event as a video clip.

    Attributes:
        start_timestamp: When event started (seconds)
        end_timestamp: When event ended (seconds)
        start_frame_num: Starting frame number
        end_frame_num: Ending frame number
        trigger_reason: What triggered this event
        frames: List of frame numbers in this event
        detected_objects: All unique objects seen during event
        max_objects: Maximum objects seen at once
        has_motion: Whether motion was detected
        confidence: Average confidence across event
    """
    start_timestamp: float
    start_frame_num: int
    trigger_reason: str
    end_timestamp: Optional[float] = None
    end_frame_num: Optional[int] = None
    frames: List[int] = field(default_factory=list)
    detected_objects: set = field(default_factory=set)
    max_objects: int = 0
    has_motion: bool = False
    confidence: float = 0.0
    _confidence_scores: List[float] = field(default_factory=list)

    def add_frame(self, frame: Frame, detections: List[BoundingBox] = None):
        """
        Add a frame to this event.

        Args:
            frame: Frame to add
            detections: Objects detected in this frame
        """
        self.frames.append(frame.frame_number)
        self.end_timestamp = frame.timestamp
        self.end_frame_num = frame.frame_number

        if detections:
            # Track what objects we've seen
            for det in detections:
                self.detected_objects.add(det.label)

            # Track max objects at once
            self.max_objects = max(self.max_objects, len(detections))

            # Track confidence
            if detections:
                avg_conf = np.mean([d.confidence for d in detections])
                self._confidence_scores.append(avg_conf)

    @property
    def duration(self) -> float:
        """Event duration in seconds."""
        if self.end_timestamp:
            return self.end_timestamp - self.start_timestamp
        return 0.0

    @property
    def frame_count(self) -> int:
        """Number of frames in this event."""
        return len(self.frames)

    @property
    def average_confidence(self) -> float:
        """Average detection confidence across event."""
        if self._confidence_scores:
            return np.mean(self._confidence_scores)
        return 0.0

    def should_send(self, min_duration: float = 1.0) -> bool:
        """
        Determine if this event is worth sending to VLM.

        Args:
            min_duration: Minimum event duration in seconds

        Returns:
            True if event should be sent to VLM
        """
        # Skip very short events (likely noise)
        if self.duration < min_duration:
            return False

        # Skip events with no objects and no motion
        if not self.detected_objects and not self.has_motion:
            return False

        return True

    def merge_with(self, other: 'Event') -> 'Event':
        """
        Merge this event with another (for combining nearby events).

        Args:
            other: Event to merge with

        Returns:
            New merged event
        """
        merged = Event(
            start_timestamp=min(self.start_timestamp, other.start_timestamp),
            start_frame_num=min(self.start_frame_num, other.start_frame_num),
            trigger_reason=f"{self.trigger_reason}+{other.trigger_reason}",
            end_timestamp=max(self.end_timestamp, other.end_timestamp),
            end_frame_num=max(self.end_frame_num, other.end_frame_num),
        )

        # Combine data
        merged.frames = sorted(set(self.frames + other.frames))
        merged.detected_objects = self.detected_objects.union(other.detected_objects)
        merged.max_objects = max(self.max_objects, other.max_objects)
        merged.has_motion = self.has_motion or other.has_motion
        merged._confidence_scores = self._confidence_scores + other._confidence_scores

        return merged

    def to_dict(self) -> dict:
        """Convert event to dictionary for API/storage."""
        return {
            'start_timestamp': self.start_timestamp,
            'end_timestamp': self.end_timestamp,
            'duration': self.duration,
            'frame_count': self.frame_count,
            'trigger_reason': self.trigger_reason,
            'detected_objects': list(self.detected_objects),
            'max_objects': self.max_objects,
            'has_motion': self.has_motion,
            'average_confidence': self.average_confidence,
        }


@dataclass
class EventBuffer:
    """
    Manages a buffer of events for batching and processing.

    Collects events and intelligently batches them for efficient
    VLM processing. Can merge nearby events to reduce API calls.

    Attributes:
        events: List of pending events
        max_gap_seconds: Max gap between events to consider merging
        max_batch_duration: Max total duration for a batch
    """
    events: List[Event] = field(default_factory=list)
    max_gap_seconds: float = 5.0  # Merge events within 5 seconds
    max_batch_duration: float = 60.0  # Max 1 minute per batch

    def add_event(self, event: Event) -> Optional[List[Event]]:
        """
        Add an event to the buffer.

        Args:
            event: Event to add

        Returns:
            List of events ready to process, or None
        """
        self.events.append(event)

        # Check if we should process the batch
        if self._should_process_batch():
            return self.get_batch()

        return None

    def _should_process_batch(self) -> bool:
        """Determine if current batch should be processed."""
        if not self.events:
            return False

        # Process if batch duration exceeds limit
        total_duration = sum(e.duration for e in self.events)
        if total_duration >= self.max_batch_duration:
            return True

        # Process if we have many events
        if len(self.events) >= 10:
            return True

        return False

    def get_batch(self) -> List[Event]:
        """
        Get a batch of events for processing.

        Merges nearby events to reduce API calls.

        Returns:
            List of events (possibly merged)
        """
        if not self.events:
            return []

        # Sort by start time
        sorted_events = sorted(self.events, key=lambda e: e.start_timestamp)

        # Merge nearby events
        merged = []
        current = sorted_events[0]

        for next_event in sorted_events[1:]:
            gap = next_event.start_timestamp - current.end_timestamp

            if gap <= self.max_gap_seconds:
                # Merge events
                current = current.merge_with(next_event)
            else:
                # Gap too large, keep separate
                merged.append(current)
                current = next_event

        merged.append(current)

        # Clear buffer
        self.events.clear()

        return merged

    def force_flush(self) -> List[Event]:
        """Force process all pending events."""
        batch = self.get_batch()
        self.events.clear()
        return batch