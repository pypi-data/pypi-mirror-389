"""
Common types and data structures used across the SDK
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import numpy as np


class FrameSelectionReason(Enum):
    """Reasons why a frame was selected for processing"""
    SCENE_CHANGE = "scene_change"
    MOTION_DETECTED = "motion_detected"
    OBJECT_DETECTED = "object_detected"
    PERIODIC_SAMPLE = "periodic_sample"
    FORCED = "forced"
    RATE_LIMITED = "rate_limited"
    SKIPPED = "skipped"


class ProcessingStatus(Enum):
    """Status of frame/video processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Frame:
    """
    Represents a single video frame
    
    Attributes:
        data: Frame data as numpy array (height, width, channels)
        timestamp: Frame timestamp in seconds
        frame_number: Sequential frame number
        metadata: Additional frame metadata
    """
    data: np.ndarray
    timestamp: float
    frame_number: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def shape(self):
        """Get frame shape (height, width, channels)"""
        return self.data.shape
    
    @property
    def height(self):
        """Frame height in pixels"""
        return self.data.shape[0]
    
    @property
    def width(self):
        """Frame width in pixels"""
        return self.data.shape[1]
    
    @property
    def channels(self):
        """Number of color channels"""
        return self.data.shape[2] if len(self.data.shape) > 2 else 1


@dataclass
class BoundingBox:
    """
    Bounding box for object detection
    
    Attributes:
        x1: Top-left x coordinate
        y1: Top-left y coordinate
        x2: Bottom-right x coordinate
        y2: Bottom-right y coordinate
        label: Object label/class
        confidence: Detection confidence (0.0-1.0)
        track_id: Optional tracking ID for multi-frame tracking
    """
    x1: float
    y1: float
    x2: float
    y2: float
    label: str
    confidence: float
    track_id: Optional[int] = None
    
    def area(self) -> float:
        """Calculate bounding box area"""
        return (self.x2 - self.x1) * (self.y2 - self.y1)
    
    def center(self) -> tuple[float, float]:
        """Get bounding box center point"""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "label": self.label,
            "confidence": self.confidence,
            "track_id": self.track_id,
        }


@dataclass
class DetectionResult:
    """
    Result of object detection on a frame
    
    Attributes:
        frame: The analyzed frame
        boxes: List of detected bounding boxes
        processing_time: Time taken to process (seconds)
        metadata: Additional detection metadata
    """
    frame: Frame
    boxes: List[BoundingBox]
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def num_detections(self) -> int:
        """Number of objects detected"""
        return len(self.boxes)
    
    def filter_by_label(self, label: str) -> List[BoundingBox]:
        """Filter boxes by label"""
        return [box for box in self.boxes if box.label == label]
    
    def filter_by_confidence(self, min_confidence: float) -> List[BoundingBox]:
        """Filter boxes by minimum confidence"""
        return [box for box in self.boxes if box.confidence >= min_confidence]


@dataclass
class AnalysisResult:
    """
    Result of AI provider analysis
    
    Attributes:
        frame: The analyzed frame
        text: Text response from AI
        timestamp: When analysis was performed
        provider: Which AI provider was used
        model: Which model was used
        confidence: Optional confidence score
        metadata: Additional analysis metadata
    """
    frame: Frame
    text: str
    timestamp: datetime
    provider: str
    model: str
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "frame_timestamp": self.frame.timestamp,
            "frame_number": self.frame.frame_number,
            "provider": self.provider,
            "model": self.model,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class PreprocessingResult:
    """
    Result of frame preprocessing
    
    Attributes:
        should_process: Whether frame should be sent to AI
        reason: Reason for selection/rejection
        confidence: Confidence in the decision
        detections: Optional object detections
        motion_level: Optional motion level (0.0-1.0)
        metadata: Additional preprocessing metadata
    """
    should_process: bool
    reason: FrameSelectionReason
    confidence: float = 1.0
    detections: Optional[List[BoundingBox]] = None
    motion_level: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "should_process": self.should_process,
            "reason": self.reason.value,
            "confidence": self.confidence,
            "num_detections": len(self.detections) if self.detections else 0,
            "motion_level": self.motion_level,
            "metadata": self.metadata,
        }


@dataclass
class StreamInfo:
    """
    Information about a video stream
    
    Attributes:
        source: Stream source (URL, file path, etc.)
        fps: Frames per second
        width: Frame width in pixels
        height: Frame height in pixels
        total_frames: Total number of frames (if known)
        duration: Total duration in seconds (if known)
        codec: Video codec
        metadata: Additional stream metadata
    """
    source: str
    fps: float
    width: int
    height: int
    total_frames: Optional[int] = None
    duration: Optional[float] = None
    codec: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "total_frames": self.total_frames,
            "duration": self.duration,
            "codec": self.codec,
            "metadata": self.metadata,
        }