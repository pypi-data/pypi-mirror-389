"""
Main processing pipeline for video intelligence.

Integrates:
1. Event-based preprocessor (RT-DETR) - detects when something happens
2. Video clip creation - converts events to video clips
3. Gemini VLM analysis - understands what happened

Usage:
    pipeline = Pipeline(api_key="your_key")
    pipeline.process_video("video.mp4", prompt="What happens in this video?")
"""

import os
import asyncio
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from vlm.core.config import SDKConfig
from vlm.core.types import Frame
from vlm.preprocessors.detector.core import DetectorPreprocessor
from vlm.preprocessors.detector.events import Event


@dataclass
class PipelineResult:
    """Result from pipeline processing"""
    event_start: float
    event_end: float
    event_duration: float
    frames_analyzed: int
    detected_objects: List[str]
    vlm_response: str
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]


class Pipeline:
    """
    End-to-end video processing pipeline.

    Combines intelligent frame selection (preprocessor) with VLM analysis (Gemini).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[SDKConfig] = None,
        preprocessor_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize pipeline.

        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var)
            config: SDK configuration
            preprocessor_config: Configuration for RT-DETR preprocessor
        """
        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY env var or pass api_key parameter"
            )

        # Initialize Gemini client
        if genai is None:
            raise ImportError("google-genai package required. Install with: pip install google-genai")

        self.client = genai.Client(api_key=self.api_key)
        self.model = 'gemini-2.0-flash-exp'

        # Configuration
        self.config = config or SDKConfig()

        # Initialize preprocessor
        preprocessor_config = preprocessor_config or {
            'preset_profile': 'security',
            'event_mode': True,
            'min_event_duration': 1.0,
            'event_grace_period': 2.0,
        }
        self.preprocessor = DetectorPreprocessor(config=preprocessor_config)

        # Statistics
        self.stats = {
            'events_detected': 0,
            'events_analyzed': 0,
            'frames_processed': 0,
            'frames_in_events': 0,
            'total_processing_time': 0.0,
        }

        print(f"Pipeline initialized")
        print(f"  Model: {self.model}")
        print(f"  Preprocessor: Event-based RT-DETR")

    def process_video(
        self,
        video_path: str,
        prompt: str = "Describe what happens in this video.",
        output_fps: int = 1,
        max_events: Optional[int] = None
    ) -> List[PipelineResult]:
        """
        Process video end-to-end: detect events -> create clips -> analyze with Gemini.

        Args:
            video_path: Path to video file
            prompt: Question/prompt for Gemini
            output_fps: FPS for event clips sent to Gemini (lower = cheaper)
            max_events: Maximum events to process (None = all)

        Returns:
            List of PipelineResult objects, one per event
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        print(f"\n{'='*70}")
        print(f"PROCESSING VIDEO: {video_path.name}")
        print(f"{'='*70}")

        # Step 1: Detect events
        print("\n[Step 1/3] Detecting events with RT-DETR preprocessor...")
        events = self._detect_events(video_path)

        if not events:
            print("No events detected in video")
            return []

        print(f"Detected {len(events)} events")

        # Limit events if specified
        if max_events and len(events) > max_events:
            print(f"  (Processing first {max_events} events)")
            events = events[:max_events]

        # Step 2: Create video clips and analyze
        print(f"\n[Step 2/3] Creating event clips and uploading to Gemini...")
        results = []

        for i, event in enumerate(events, 1):
            print(f"\n--- Event {i}/{len(events)} ---")
            print(f"  Duration: {event.duration:.2f}s")
            print(f"  Frames: {event.frame_count}")
            print(f"  Objects: {', '.join(event.detected_objects)}")

            # Create video clip for this event
            clip_path = self._create_event_clip(
                video_path, event, output_fps, temp_prefix=f"event_{i}"
            )

            # Analyze with Gemini
            print(f"  Analyzing with Gemini...")
            analysis = self._analyze_with_gemini(clip_path, prompt)

            # Store result
            result = PipelineResult(
                event_start=event.start_timestamp,
                event_end=event.end_timestamp,
                event_duration=event.duration,
                frames_analyzed=event.frame_count,
                detected_objects=list(event.detected_objects),
                vlm_response=analysis['response'],
                confidence=event.average_confidence,
                processing_time=analysis['processing_time'],
                metadata=event.to_dict()
            )
            results.append(result)

            print(f"   Analysis complete")
            print(f"  Response: {analysis['response'][:100]}...")

            # Cleanup temp file
            clip_path.unlink()

            self.stats['events_analyzed'] += 1

        # Step 3: Summary
        print(f"\n{'='*70}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*70}")
        self._print_summary(results)

        return results

    def _detect_events(self, video_path: Path) -> List[Event]:
        """Detect events in video using preprocessor"""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"  Video: {total_frames} frames @ {fps:.1f} fps")

        events = []
        frame_count = 0

        try:
            while True:
                ret, frame_data = cap.read()
                if not ret:
                    break

                frame_count += 1
                timestamp = frame_count / fps

                # Create Frame object
                frame = Frame(
                    data=frame_data,
                    timestamp=timestamp,
                    frame_number=frame_count,
                    metadata={}
                )

                # Process frame
                result = self.preprocessor(frame)

                # Check if event completed
                if result.should_process and result.metadata.get('event_status') == 'completed':
                    # Extract event info from metadata
                    event = Event(
                        start_timestamp=result.metadata['event_start'],
                        start_frame_num=result.metadata.get('event_start_frame', 0),
                        trigger_reason=result.metadata.get('trigger_reason', 'unknown'),
                        end_timestamp=result.metadata['event_end'],
                        end_frame_num=result.metadata.get('event_end_frame', frame_count),
                    )
                    event.frames = list(range(
                        result.metadata.get('event_start_frame', 0),
                        result.metadata.get('event_end_frame', frame_count)
                    ))
                    event.detected_objects = set(result.metadata.get('detected_objects', []))
                    events.append(event)

                    print(f"  Event detected: {event.duration:.2f}s", end='\r')

                self.stats['frames_processed'] += 1

        finally:
            cap.release()

            # Get any pending events
            pending = self.preprocessor.get_pending_events()
            events.extend(pending)

        return events

    def _create_event_clip(
        self,
        video_path: Path,
        event: Event,
        output_fps: int,
        temp_prefix: str = "event"
    ) -> Path:
        """Create video clip for an event"""
        # Create temp directory
        temp_dir = Path("/tmp/ob-gemvision")
        temp_dir.mkdir(exist_ok=True)

        output_path = temp_dir / f"{temp_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        # Open video
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Calculate frame sampling
        frame_skip = max(1, int(fps / output_fps))

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, output_fps, (width, height))

        # Seek to event start
        start_frame = int(event.start_timestamp * fps)
        end_frame = int(event.end_timestamp * fps)

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Write frames
        current_frame = start_frame
        frames_written = 0

        while current_frame <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            # Sample frames
            if (current_frame - start_frame) % frame_skip == 0:
                out.write(frame)
                frames_written += 1

            current_frame += 1

        cap.release()
        out.release()

        print(f"  Created clip: {frames_written} frames @ {output_fps} fps")

        return output_path

    def _analyze_with_gemini(self, video_clip: Path, prompt: str) -> Dict[str, Any]:
        """Analyze video clip with Gemini"""
        start_time = datetime.now()

        async def upload_and_analyze():
            # Upload video
            uploaded_file = await self.client.aio.files.upload(file=video_clip)

            # Wait for processing
            while uploaded_file.state == "PROCESSING":
                await asyncio.sleep(0.5)
                uploaded_file = await self.client.aio.files.get(name=uploaded_file.name)

            if uploaded_file.state == "FAILED":
                raise Exception(f"File upload failed: {uploaded_file.error}")

            # Analyze
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[uploaded_file, prompt]
            )

            # Cleanup
            await self.client.aio.files.delete(name=uploaded_file.name)

            return response.text

        try:
            response_text = asyncio.run(upload_and_analyze())
            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                'response': response_text,
                'processing_time': processing_time,
                'model': self.model
            }

        except Exception as e:
            print(f"   Error: {e}")
            raise

    def _print_summary(self, results: List[PipelineResult]):
        """Print processing summary"""
        if not results:
            return

        total_duration = sum(r.event_duration for r in results)
        total_frames = sum(r.frames_analyzed for r in results)
        total_time = sum(r.processing_time for r in results)

        print(f"\nEvents Analyzed: {len(results)}")
        print(f"Total Event Duration: {total_duration:.2f}s")
        print(f"Total Frames: {total_frames}")
        print(f"Processing Time: {total_time:.2f}s")

        print(f"\n--- COST ANALYSIS ---")
        # Traditional approach: per-frame
        traditional_cost = total_frames * 0.002
        # Our approach: per-event
        event_cost = len(results) * 0.002
        savings = traditional_cost - event_cost
        savings_pct = (savings / traditional_cost * 100) if traditional_cost > 0 else 0

        print(f"Frame-by-frame cost: ${traditional_cost:.4f} ({total_frames} frames)")
        print(f"Event-based cost: ${event_cost:.4f} ({len(results)} events)")
        print(f"Savings: ${savings:.4f} ({savings_pct:.1f}%)")

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return self.stats.copy()
