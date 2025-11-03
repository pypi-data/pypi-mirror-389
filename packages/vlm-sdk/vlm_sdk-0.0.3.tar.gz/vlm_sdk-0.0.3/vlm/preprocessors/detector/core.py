"""
Event-based RT-DETR preprocessor with timestamp tracking.

Instead of processing individual frames, we track events (continuous periods
of motion/activity) and send complete video clips to the VLM. This reduces
costs by 10-15x compared to frame-by-frame processing.

Key patterns:
- Temporal Redundancy (process every Nth frame)
- Event-based tracking (motion start/stop timestamps)
- Object tracking between frames
- Adaptive thresholds
- Frame caching
"""

from typing import Optional, Dict, Any, List, Tuple
from collections import deque, defaultdict
import time
import numpy as np
import cv2
import torch
from PIL import Image

try:
    from transformers import RTDetrForObjectDetection, RTDetrImageProcessor
    RTDETR_AVAILABLE = True
except ImportError:
    RTDETR_AVAILABLE = False
    RTDetrForObjectDetection = None
    RTDetrImageProcessor = None

from vlm.preprocessors.base import BasePreprocessor
from vlm.core.types import Frame, PreprocessingResult, FrameSelectionReason, BoundingBox
from vlm.preprocessors.detector.caching import TemporalCache
from vlm.preprocessors.detector.events import Event, EventBuffer
from vlm.preprocessors.detector.motion_tracker import MotionTracker


class RTDETRPreprocessor(BasePreprocessor):
    """
    Event-based RT-DETR preprocessor for intelligent frame selection.

    Instead of sending individual frames to VLM, we track events (periods of
    activity) and send complete video clips. This dramatically reduces costs
    while maintaining full context for the VLM.

    Features:
    - Event-based processing: Track motion start/stop timestamps
    - Temporal redundancy: Full detection every N frames
    - Object tracking: Track objects across frames
    - Adaptive thresholds: Adjust sensitivity based on scene
    - Smart batching: Combine nearby events
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RT-DETR preprocessor.

        Config options:
            model_name: Model name from HuggingFace, default 'PekingU/rtdetr_r50vd'
            full_detection_interval: Frames between full detection runs, default 8
            confidence_threshold: Min confidence for detections, default 0.5
            interesting_objects: Object classes to trigger on, default ['person', 'car']
            motion_threshold_pixels: Movement to trigger, default 50
            track_objects: Enable multi-frame tracking, default True
            adaptive_thresholds: Enable adaptive sensitivity, default True
            enable_caching: Enable result caching, default True
            enable_anomaly_detection: Detect non-object anomalies, default True
            preset_profile: Preset config (security/retail/traffic), default None
            event_mode: Enable event-based processing, default True
            min_event_duration: Minimum event duration in seconds, default 1.0
            event_grace_period: Seconds to wait after motion stops, default 2.0
            event_max_gap: Max gap between events to merge, default 5.0
            device: Device to run model on ('cuda', 'cpu', 'mps'), default auto-detect
        """
        if not RTDETR_AVAILABLE:
            raise ImportError(
                "transformers package required for RTDETRPreprocessor. "
                "Install with: pip install transformers"
            )

        super().__init__(config)

    def initialize(self) -> None:
        """Initialize detection model and tracking structures"""
        # Load preset profile if specified
        preset = self.config.get('preset_profile')
        if preset:
            self._apply_preset(preset)

        # Configuration
        self.model_name = self.config.get('model_name', 'PekingU/rtdetr_r50vd')
        self.full_detection_interval = self.config.get('full_detection_interval', 8)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.interesting_objects = set(self.config.get('interesting_objects', ['person', 'car', 'truck']))
        self.motion_threshold = self.config.get('motion_threshold_pixels', 50)
        self.track_objects = self.config.get('track_objects', True)
        self.adaptive_thresholds = self.config.get('adaptive_thresholds', True)
        self.enable_caching = self.config.get('enable_caching', True)
        self.enable_anomaly = self.config.get('enable_anomaly_detection', True)

        # Event-based processing config
        self.event_mode = self.config.get('event_mode', True)
        self.min_event_duration = self.config.get('min_event_duration', 2.0)
        self.min_object_area_ratio = self.config.get('min_object_area_ratio', 0.02)
        self.event_grace_period = self.config.get('event_grace_period', 2.0)
        self.event_max_gap = self.config.get('event_max_gap', 5.0)

        # Determine device
        device = self.config.get('device', 'auto')
        if device == 'auto':
            if torch.cuda.is_available():
                self.device = 'cuda'
            elif torch.backends.mps.is_available():
                self.device = 'mps'
            else:
                self.device = 'cpu'
        else:
            self.device = device

        # Initialize RT-DETR model
        print(f"Loading RT-DETR model: {self.model_name} on {self.device}...")
        self.image_processor = RTDetrImageProcessor.from_pretrained(self.model_name)
        self.model = RTDetrForObjectDetection.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode

        # Get label mapping from model config
        self.id2label = self.model.config.id2label
        self.label2id = {v: k for k, v in self.id2label.items()}

        # Tracking state
        self.frame_count = 0
        self.previous_detections: List[BoundingBox] = []
        self.last_full_detection_frame = -1

        # Motion tracker (ByteTrack-inspired)
        self.motion_tracker = MotionTracker(iou_threshold=0.3)

        # Frame cache
        self.cache = TemporalCache()

        # Event tracking
        self.current_event: Optional[Event] = None
        self.event_buffer = EventBuffer(max_gap_seconds=self.event_max_gap)
        self.frames_since_last_activity = 0

        # Anomaly detection state
        self.baseline_brightness = None
        self.baseline_histogram = None
        self.previous_frame_gray = None

        # Adaptive thresholds state
        self.recent_activity_scores = deque(maxlen=30)  # Last 30 frames
        self.current_activity_level = 'medium'

        mode = "EVENT-BASED" if self.event_mode else "FRAME-BASED"
        print(f"RT-DETR Preprocessor initialized in {mode} mode with {len(self.interesting_objects)} object classes")

    def _apply_preset(self, preset: str):
        """Apply preset configuration profiles"""
        presets = {
            'security': {
                'interesting_objects': ['person', 'car', 'truck', 'motorcycle'],
                'motion_threshold_pixels': 80,
                'confidence_threshold': 0.6,
                'full_detection_interval': 8,
                'min_event_duration': 2.0,
                'event_grace_period': 2.0,
            },
            'retail': {
                'interesting_objects': ['person'],
                'motion_threshold_pixels': 20,
                'confidence_threshold': 0.5,
                'full_detection_interval': 5,
                'min_event_duration': 2.0,
                'event_grace_period': 3.0,
            },
            'traffic': {
                'interesting_objects': ['car', 'truck', 'bus', 'motorcycle'],
                'motion_threshold_pixels': 50,
                'confidence_threshold': 0.7,
                'full_detection_interval': 10,
                'min_event_duration': 2.0,
                'event_grace_period': 1.0,
            },
        }

        if preset in presets:
            self.config.update(presets[preset])
            print(f"Applied preset profile: {preset}")

    def process_frame(self, frame: Frame) -> PreprocessingResult:
        """
        Process frame with event-based tracking.

        In event mode, we track when activity starts and stops, then
        send complete events as video clips rather than individual frames.
        """
        self.frame_count += 1
        current_time = time.time()

        # Check cache first
        if self.enable_caching and self.cache.is_valid(current_time):
            frame_hash = self._compute_frame_hash(frame.data)
            if frame_hash == self.cache.frame_hash:
                result = self.cache.result
                result.metadata['cache_hit'] = True
                return result

        # Determine if we should run full RT-DETR detection
        should_run_full_detection = (
            self.frame_count == 1 or  # First frame
            self.frame_count - self.last_full_detection_frame >= self.full_detection_interval or
            len(self.motion_tracker.tracks) == 0  # Lost all tracks
        )

        if should_run_full_detection:
            # Temporal Redundancy - Full detection
            detections = self._run_full_rtdetr_detection(frame)
            self.last_full_detection_frame = self.frame_count
        else:
            # Track existing objects (lightweight)
            detections = self._track_existing_objects(frame)

        # Calculate activity score (simplified, importance calculation commented out)
        # importance_score = self._calculate_semantic_importance(detections, frame)
        # For now, just use detection count as activity score
        activity_score = min(len(detections) / 5.0, 1.0) if detections else 0.0

        # Adaptive thresholds
        if self.adaptive_thresholds:
            self._update_adaptive_thresholds(activity_score)

        # Detect anomalies if no objects
        anomaly_detected = False
        anomaly_type = None
        if self.enable_anomaly and len(detections) == 0:
            anomaly_detected, anomaly_type = self._detect_anomalies(frame)

        # Use new motion tracker
        motion_started, motion_ended, motion_reason = self.motion_tracker.update(detections)

        # Check for activity (motion continuing or starting)
        has_activity = self.motion_tracker.current_motion or anomaly_detected

        # Determine activity reason for logging
        activity_reason = None
        if motion_started:
            activity_reason = motion_reason
        elif anomaly_detected:
            activity_reason = f"Anomaly: {anomaly_type}"

        # Event-based processing
        if self.event_mode:
            result = self._process_event_mode(
                frame, detections, has_activity, motion_ended,
                anomaly_detected, anomaly_type, activity_reason
            )
        else:
            # Traditional frame-by-frame mode
            result = self._process_frame_mode(
                frame, detections, has_activity,
                activity_score, anomaly_detected, anomaly_type
            )

        # Update state
        self.previous_detections = detections

        # Update cache
        if self.enable_caching:
            self.cache = TemporalCache(
                frame_hash=self._compute_frame_hash(frame.data),
                detections=detections,
                timestamp=current_time,
                frame_number=self.frame_count,
                result=result
            )

        return result

    def _process_event_mode(
        self,
        frame: Frame,
        detections: List[BoundingBox],
        has_activity: bool,
        motion_ended: bool,
        anomaly_detected: bool,
        anomaly_type: Optional[str],
        activity_reason: Optional[str] = None
    ) -> PreprocessingResult:
        """
        Process frame in event-based mode.

        Track when events start and stop, collecting frames into
        complete events rather than processing individually.
        """
        # Check if we should start a new event
        if has_activity and not self.current_event:
            # Start new event
            trigger_reason = self._get_trigger_reason(
                detections, anomaly_detected, anomaly_type
            )
            self.current_event = Event(
                start_timestamp=frame.timestamp,
                start_frame_num=frame.frame_number,
                trigger_reason=trigger_reason
            )
            self.frames_since_last_activity = 0

            # Add this frame to event
            self.current_event.add_frame(frame, detections)

            # Return "collecting event" status
            return PreprocessingResult(
                should_process=False,  # Don't send yet, collecting event
                reason=FrameSelectionReason.RATE_LIMITED,
                confidence=0.0,
                detections=detections,
                metadata={
                    'event_status': 'started',
                    'event_start': frame.timestamp,
                    'num_objects': len(detections),
                    'activity_reason': activity_reason,
                }
            )

        elif self.current_event and has_activity:
            # Continue current event
            self.current_event.add_frame(frame, detections)
            self.frames_since_last_activity = 0

            return PreprocessingResult(
                should_process=False,  # Still collecting
                reason=FrameSelectionReason.RATE_LIMITED,
                confidence=0.0,
                detections=detections,
                metadata={
                    'event_status': 'continuing',
                    'event_duration': self.current_event.duration,
                    'num_objects': len(detections),
                }
            )

        elif self.current_event and (motion_ended or not has_activity):
            # Motion just ended OR no activity continuing
            if motion_ended:
                # Motion just stopped - start grace period
                self.frames_since_last_activity = 1
            else:
                # Continue counting frames since last activity
                self.frames_since_last_activity += 1

            grace_frames = int(self.event_grace_period * 30)  # Assuming 30fps

            if self.frames_since_last_activity >= grace_frames:
                # End event after grace period
                event = self.current_event
                self.current_event = None
                self.frames_since_last_activity = 0

                # Check if event is worth sending
                if event.should_send(self.min_event_duration):
                    return PreprocessingResult(
                        should_process=True,  # Send complete event
                        reason=FrameSelectionReason.OBJECT_DETECTED,
                        confidence=event.average_confidence,
                        detections=detections,
                        metadata={
                            'event_status': 'completed',
                            'event_start': event.start_timestamp,
                            'event_end': event.end_timestamp,
                            'event_duration': event.duration,
                            'event_frames': event.frame_count,
                            'detected_objects': list(event.detected_objects),
                        }
                    )
                else:
                    # Event too short, discard
                    return PreprocessingResult(
                        should_process=False,
                        reason=FrameSelectionReason.SKIPPED,
                        confidence=0.0,
                        detections=detections,
                        metadata={
                            'event_status': 'discarded',
                            'event_duration': event.duration,
                        }
                    )
            else:
                # Within grace period, keep collecting
                self.current_event.add_frame(frame, detections)
                return PreprocessingResult(
                    should_process=False,
                    reason=FrameSelectionReason.RATE_LIMITED,
                    confidence=0.0,
                    detections=detections,
                    metadata={
                        'event_status': 'grace_period',
                        'frames_since_activity': self.frames_since_last_activity,
                    }
                )

        # No activity and no current event
        return PreprocessingResult(
            should_process=False,
            reason=FrameSelectionReason.SKIPPED,
            confidence=0.0,
            detections=detections,
            metadata={
                'event_status': 'idle',
                'num_objects': len(detections),
            }
        )

    def _get_trigger_reason(
        self,
        detections: List[BoundingBox],
        anomaly_detected: bool,
        anomaly_type: Optional[str]
    ) -> str:
        """Get human-readable trigger reason for event."""
        if detections:
            objects = set(d.label for d in detections)
            return f"objects_detected:{','.join(objects)}"
        elif anomaly_detected:
            return f"anomaly:{anomaly_type}"
        else:
            return "motion_detected"

    def _run_full_rtdetr_detection(self, frame: Frame) -> List[BoundingBox]:
        """Run full RT-DETR detection on frame"""
        # Convert BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame.data, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # Process image
        inputs = self.image_processor(images=pil_image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Post-process results
        height, width = frame.data.shape[:2]
        target_sizes = torch.tensor([[height, width]], device=self.device)
        results = self.image_processor.post_process_object_detection(
            outputs,
            target_sizes=target_sizes,
            threshold=self.confidence_threshold
        )[0]  # Get first (and only) result

        # Convert to BoundingBox format
        detections = []
        if results is not None and len(results["scores"]) > 0:
            for score, label_id, box in zip(
                results["scores"].cpu(),
                results["labels"].cpu(),
                results["boxes"].cpu()
            ):
                label = self.id2label.get(label_id.item(), f"class_{label_id.item()}")

                # Filter by interesting objects if specified
                if self.interesting_objects and label not in self.interesting_objects:
                    continue

                x1, y1, x2, y2 = box.tolist()

                bbox = BoundingBox(
                    x1=float(x1), y1=float(y1),
                    x2=float(x2), y2=float(y2),
                    label=label,
                    confidence=float(score.item()),
                    track_id=None  # RT-DETR doesn't have built-in tracking
                )
                detections.append(bbox)

        return detections

    def _track_existing_objects(self, frame: Frame) -> List[BoundingBox]:
        """Track existing objects without full RT-DETR detection (lightweight)"""
        # For now, return previous detections
        # In production, could use optical flow or lighter tracking
        return self.previous_detections

    def _update_adaptive_thresholds(self, activity_score: float):
        """Update thresholds based on recent activity"""
        self.recent_activity_scores.append(activity_score)

        if len(self.recent_activity_scores) < 10:
            return

        avg_activity = np.mean(self.recent_activity_scores)

        if avg_activity > 0.7:
            self.current_activity_level = 'high'
            self.full_detection_interval = max(5, self.full_detection_interval - 1)
        elif avg_activity < 0.3:
            self.current_activity_level = 'low'
            self.full_detection_interval = min(15, self.full_detection_interval + 1)
        else:
            self.current_activity_level = 'medium'


    def _detect_anomalies(self, frame: Frame) -> Tuple[bool, Optional[str]]:
        """Detect non-object anomalies (lighting, blur, etc.)"""
        gray = cv2.cvtColor(frame.data, cv2.COLOR_BGR2GRAY)

        # Initialize baseline
        if self.baseline_brightness is None:
            self.baseline_brightness = np.mean(gray)
            self.baseline_histogram = cv2.calcHist([gray], [0], None, [256], [0, 256])
            self.previous_frame_gray = gray
            return False, None

        # Check 1: Brightness change (lighting change, fire, etc.)
        current_brightness = np.mean(gray)
        brightness_change = abs(current_brightness - self.baseline_brightness)

        if brightness_change > 30:  # Significant brightness change
            self.baseline_brightness = current_brightness  # Update baseline
            return True, 'brightness_change'

        # Check 2: Blur detection (camera obscured, smoke, fog)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 50:  # Very low variance = blur
            return True, 'blur_detected'

        # Check 3: Histogram change (color shift, weather change)
        current_hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_correlation = cv2.compareHist(
            self.baseline_histogram,
            current_hist,
            cv2.HISTCMP_CORREL
        )

        if hist_correlation < 0.7:  # Low correlation = scene changed
            self.baseline_histogram = current_hist
            return True, 'scene_changed'

        self.previous_frame_gray = gray
        return False, None

    def _compute_frame_hash(self, frame_data: np.ndarray) -> int:
        """Compute simple hash of frame for caching"""
        # Downsample and hash for speed
        small = cv2.resize(frame_data, (32, 32))
        return hash(small.tobytes())

    def get_pending_events(self) -> List[Event]:
        """
        Get any pending events that are ready for processing.

        Returns:
            List of completed events
        """
        events = []

        # Flush current event if it exists
        if self.current_event:
            event = self.current_event
            event.end_timestamp = event.start_timestamp + event.duration
            event.end_frame_num = event.frames[-1] if event.frames else event.start_frame_num
            self.current_event = None
            if event.should_send():
                events.append(event)

        # Add any buffered events
        events.extend(self.event_buffer.force_flush())

        return events

    def update_tracked_objects(self, objects: List[str]) -> None:
        """
        Update the list of objects to track at runtime.

        Args:
            objects: List of object class names to track
        """
        self.interesting_objects = set(objects)
        print(f"Updated tracked objects to: {', '.join(objects)}")

    def get_available_objects(self) -> List[str]:
        """
        Get list of all objects that can be detected by the current model.

        Returns:
            List of object class names
        """
        if hasattr(self, 'id2label'):
            return list(self.id2label.values())
        return []

    def cleanup(self) -> None:
        """Clean up resources"""
        # Flush any pending events
        if self.current_event:
            self.event_buffer.add_event(self.current_event)

        self.previous_detections.clear()
        if hasattr(self, 'model'):
            # Move model to CPU before deletion to free GPU memory
            self.model.cpu()
            del self.model
        if hasattr(self, 'image_processor'):
            del self.image_processor
        print("RT-DETR Preprocessor cleaned up")


# Backward compatibility alias
DetectorPreprocessor = RTDETRPreprocessor