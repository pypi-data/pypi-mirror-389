"""
Qwen video provider implementation using DashScope API.
Extracts frames from video and sends them directly with each request.
"""

import base64
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import cv2
from openai import AsyncOpenAI
from .base import BaseVideoProvider

BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-vl-max"
TARGET_FPS = 1.0  # Extract 1 frame per second
MAX_FRAMES = 512  # Maximum frames to extract


class QwenVideoService(BaseVideoProvider):
    """Qwen video analysis service using DashScope API."""

    def __init__(self, api_key: str):
        """Initialize Qwen service with API key."""
        if not api_key:
            raise ValueError("DashScope API key is required")

        self.api_key = api_key
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=BASE_URL,
        )

        # Store video paths for API compatibility
        self._video_paths = {}

    def _extract_video_frames(self, video_path: Path, target_fps: float = TARGET_FPS, max_frames: int = MAX_FRAMES) -> List[str]:
        """
        Extract frames from video as base64-encoded images.
        This is synchronous since cv2 operations are blocking.
        """
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)

        if total_frames == 0 or video_fps == 0:
            raise ValueError(f"Could not read video: {video_path}")

        # Calculate frame interval for target FPS
        frame_interval = int(video_fps / target_fps)
        if frame_interval < 1:
            frame_interval = 1

        # Get frame indices at target FPS
        frame_indices = list(range(0, total_frames, frame_interval))

        # Limit to max_frames if needed
        if len(frame_indices) > max_frames:
            step = len(frame_indices) / max_frames
            frame_indices = [frame_indices[int(i * step)] for i in range(max_frames)]

        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Encode as JPEG with high quality
                _, buffer = cv2.imencode('.jpg', frame_rgb, [cv2.IMWRITE_JPEG_QUALITY, 95])
                # Base64 encode
                frame_b64 = base64.b64encode(buffer).decode('utf-8')
                frames.append(frame_b64)

        cap.release()
        return frames

    async def upload_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Register video path for processing.

        Note: Unlike Gemini, Qwen doesn't have a file upload API.
        This method just stores the video path and returns a reference ID.
        Frames are extracted fresh for each API call.
        """
        # Generate a unique identifier for this video session
        file_id = f"qwen_{file_path.stem}_{id(file_path)}"

        # Store the path for later use
        self._video_paths[file_id] = file_path

        # Return metadata in the same format as other providers for API compatibility
        return {
            "name": file_id,
            "uri": file_id,  # Use file_id as URI for consistency with API
            "mime_type": "video/mp4",
            "size_bytes": file_path.stat().st_size,
            "state": "ACTIVE",
            "display_name": file_path.name,
        }

    async def delete_file(self, file_uri: str) -> bool:
        """
        Clean up video path reference.

        Note: This doesn't delete any uploaded file (since Qwen doesn't upload),
        it just removes the path reference from memory.
        """
        if file_uri in self._video_paths:
            del self._video_paths[file_uri]
        return True

    async def query_video_with_file(self, file_uri: str, prompt: str) -> str:
        """Query video with a prompt by extracting frames and sending them."""
        # Get video path
        if file_uri not in self._video_paths:
            raise ValueError(f"Video not found: {file_uri}")

        video_path = self._video_paths[file_uri]

        # Extract frames in executor to not block event loop
        loop = asyncio.get_event_loop()
        frames = await loop.run_in_executor(None, self._extract_video_frames, video_path)

        # Build content for OpenAI format
        content = []

        # Add frames as images
        for frame in frames:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{frame}"}
            })

        # Add text prompt
        content.append({
            "type": "text",
            "text": prompt
        })

        # Call Qwen API
        response = await self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": content}],
            max_tokens=2048,
            temperature=0.7,
        )

        return response.choices[0].message.content

    async def find_timestamp_with_file(self, file_uri: str, query: str) -> Dict[str, Any]:
        """Find specific timestamp in video."""
        prompt = f"""Analyze the video frames and find the exact timestamp when: {query}

Return your answer in JSON format:
{{
    "timestamp": "X.Xs",
    "confidence": 0.0 to 1.0,
    "description": "brief description of what was found"
}}"""

        response = await self.query_video_with_file(file_uri, prompt)

        # Parse JSON response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if response is not JSON
            return {
                "timestamp": "0s",
                "confidence": 0.5,
                "description": response[:100]
            }

    async def find_multiple_timestamps_with_file(self, file_uri: str, query: str) -> Dict[str, Any]:
        """Find multiple occurrences of an event in video."""
        prompt = f"""Analyze the video frames and find ALL occurrences when: {query}

Return your answer in JSON format:
{{
    "timestamps": [
        {{
            "timestamp": "X.Xs",
            "confidence": 0.0 to 1.0,
            "description": "brief description"
        }}
    ]
}}"""

        response = await self.query_video_with_file(file_uri, prompt)

        # Parse JSON response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if response is not JSON
            return {"timestamps": []}


    async def analyze_video_range(
        self,
        file_uri: str,
        start_time: str,
        end_time: str,
        prompt: str
    ) -> str:
        """Analyze specific time range in video."""
        range_prompt = f"""Analyze the video between timestamps {start_time} and {end_time}.
Focus only on this specific time range.

{prompt}"""

        return await self.query_video_with_file(file_uri, range_prompt)