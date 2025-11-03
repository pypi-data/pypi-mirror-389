"""
Motion tracking system based on IoU matching and motion states.

Based on ByteTrack/DeepSORT principles:
1. Track individual objects with unique IDs
2. Use IoU (Intersection over Union) for matching
3. Maintain motion states (stationary/moving)
4. Handle occlusions and detection jitter
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque
import numpy as np
import logging
from vlm.core.types import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class TrackedObject:
    """Represents a tracked object with motion history."""
    track_id: int
    object_class: str
    last_bbox: BoundingBox
    history: deque = field(default_factory=lambda: deque(maxlen=30))
    stationary_count: int = 0
    moving_count: int = 0
    last_seen_frame: int = 0
    motion_state: str = 'stationary'  # 'stationary', 'moving', 'uncertain'

    def update(self, bbox: BoundingBox, frame_num: int):
        """Update track with new detection."""
        if self.last_bbox:
            # Calculate movement between OLD bbox and NEW bbox
            old_center = self.last_bbox.center()
            new_center = bbox.center()
            movement = np.sqrt(
                (new_center[0] - old_center[0])**2 +
                (new_center[1] - old_center[1])**2
            )

            # Update motion counters - adjusted based on real data
            # Observed: stationary jitter is 1-5px, real movement is 40-270px
            if movement < 10:  # Less than 10 pixels - stationary/jitter
                self.stationary_count += 1
                self.moving_count = max(0, self.moving_count - 1)
            elif movement > 25:  # More than 25 pixels - definite movement
                self.moving_count += 1
                self.stationary_count = 0
                # Strong movement immediately triggers moving state
                if movement > 50:
                    self.moving_count = max(self.moving_count, 3)
            # Between 10-25 pixels = uncertain, slight adjustments
            else:
                self.moving_count = max(0, self.moving_count - 1)
                self.stationary_count = max(0, self.stationary_count - 1)

            # Update motion state based on counters
            if self.stationary_count > 15:  # Need 0.5s of stillness
                self.motion_state = 'stationary'
            elif self.moving_count >= 2:  # Need 2 frames of clear movement (>25px) - balance sensitivity
                self.motion_state = 'moving'
            else:
                self.motion_state = 'uncertain'

        # NOW update the stored bbox
        self.history.append((frame_num, bbox))
        self.last_bbox = bbox
        self.last_seen_frame = frame_num

    def calculate_movement(self, new_bbox: BoundingBox) -> float:
        """Calculate movement distance in pixels."""
        old_center = self.last_bbox.center()
        new_center = new_bbox.center()

        # Calculate distance
        distance = np.sqrt(
            (new_center[0] - old_center[0])**2 +
            (new_center[1] - old_center[1])**2
        )

        return distance

    @property
    def is_lost(self) -> bool:
        """Check if track is lost (not seen for 10+ frames)."""
        return len(self.history) > 0 and self.last_seen_frame < self.history[-1][0] - 10


class MotionTracker:
    """
    IoU-based motion tracker inspired by ByteTrack.

    Key principles:
    1. Match detections to existing tracks using IoU
    2. Maintain motion states per object
    3. Only trigger motion when state transitions from stationary to moving
    """

    def __init__(self, iou_threshold: float = 0.3):
        self.tracks: Dict[int, TrackedObject] = {}
        self.next_track_id = 1
        self.iou_threshold = iou_threshold
        self.frame_count = 0

        # Motion detection state
        self.motion_events = []
        self.current_motion = False

    def update(self, detections: List[BoundingBox]) -> Tuple[bool, bool, Optional[str]]:
        """
        Update tracker with new detections.

        Returns:
            Tuple of (motion_started, motion_ended, reason)
        """
        self.frame_count += 1
        motion_started = False
        motion_reason = None

        # Match detections to existing tracks
        unmatched_detections = []
        matched_track_ids = set()

        for det in detections:
            best_iou = 0
            best_track_id = None

            # Find best matching track
            for track_id, track in self.tracks.items():
                if track_id in matched_track_ids:
                    continue
                if track.object_class != det.label:
                    continue

                iou = self.calculate_iou(det, track.last_bbox)
                if iou > best_iou and iou > self.iou_threshold:
                    best_iou = iou
                    best_track_id = track_id

            if best_track_id:
                # Update existing track
                track = self.tracks[best_track_id]
                old_state = track.motion_state

                # Calculate movement BEFORE updating (to compare old vs new)
                movement = 0.0
                old_center = None
                if track.last_bbox:
                    movement = track.calculate_movement(det)
                    old_center = track.last_bbox.center()  # Save old center BEFORE update

                # Now update the track
                track.update(det, self.frame_count)
                new_state = track.motion_state

                # Debug logging
                if self.frame_count % 15 == 0:  # Log every 0.5 seconds
                    logger.debug(f"Track #{best_track_id} {det.label}: movement={movement:.1f}px, state={new_state}, IoU={best_iou:.2f}")
                    logger.debug(f"  Counters: moving={track.moving_count}, stationary={track.stationary_count}")
                    if old_center:
                        new_c = det.center()
                        logger.debug(f"  Centers: ({old_center[0]:.1f},{old_center[1]:.1f}) -> ({new_c[0]:.1f},{new_c[1]:.1f})")

                # Check for state transition
                if old_state == 'stationary' and new_state == 'moving':
                    motion_started = True
                    motion_reason = f"{det.label} #{best_track_id} started moving"
                    logger.info(f"Motion detected: {motion_reason}")

                matched_track_ids.add(best_track_id)
            else:
                # No match found
                unmatched_detections.append(det)

        # Create new tracks for unmatched detections
        for det in unmatched_detections:
            # Only create track for confident detections
            if det.confidence > 0.5:
                track = TrackedObject(
                    track_id=self.next_track_id,
                    object_class=det.label,
                    last_bbox=det,
                    last_seen_frame=self.frame_count
                )
                self.tracks[self.next_track_id] = track
                logger.debug(f"New track #{self.next_track_id}: {det.label} (conf: {det.confidence:.2f})")
                self.next_track_id += 1

        # Clean up lost tracks
        lost_tracks = [tid for tid, track in self.tracks.items()
                      if self.frame_count - track.last_seen_frame > 30]
        for tid in lost_tracks:
            del self.tracks[tid]

        # Check if any tracked object is moving
        moving_objects = [t for t in self.tracks.values()
                         if t.motion_state == 'moving']

        # Global motion state
        was_motion = self.current_motion
        self.current_motion = len(moving_objects) > 0

        # Detect motion end
        motion_ended = False
        if was_motion and not self.current_motion:
            # Motion has ended
            motion_ended = True

        return motion_started, motion_ended, motion_reason

    def calculate_iou(self, box1: BoundingBox, box2: BoundingBox) -> float:
        """Calculate Intersection over Union between two boxes."""
        # Calculate intersection
        x1 = max(box1.x1, box2.x1)
        y1 = max(box1.y1, box2.y1)
        x2 = min(box1.x2, box2.x2)
        y2 = min(box1.y2, box2.y2)

        if x2 < x1 or y2 < y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)

        # Calculate union
        area1 = box1.area()
        area2 = box2.area()
        union = area1 + area2 - intersection

        if union == 0:
            return 0.0

        return intersection / union

    def get_motion_summary(self) -> Dict:
        """Get current motion tracking summary."""
        return {
            'total_tracks': len(self.tracks),
            'moving_objects': sum(1 for t in self.tracks.values()
                                if t.motion_state == 'moving'),
            'stationary_objects': sum(1 for t in self.tracks.values()
                                    if t.motion_state == 'stationary'),
            'uncertain_objects': sum(1 for t in self.tracks.values()
                                   if t.motion_state == 'uncertain'),
        }