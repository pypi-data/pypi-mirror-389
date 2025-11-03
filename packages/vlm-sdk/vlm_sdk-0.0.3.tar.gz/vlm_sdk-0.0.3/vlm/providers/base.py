"""
Base abstract class for video provider implementations.
Ensures all providers implement the same interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List


class BaseVideoProvider(ABC):
    """Abstract base class for video analysis providers."""

    @abstractmethod
    def __init__(self, api_key: str):
        """
        Initialize the provider with an API key.

        Args:
            api_key: The API key for the provider
        """
        pass

    @abstractmethod
    async def upload_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Upload or register a video file for processing.

        Args:
            file_path: Path to the video file

        Returns:
            Dict containing file metadata including:
            - name: File identifier
            - uri: File URI/reference
            - mime_type: MIME type of the file
            - size_bytes: File size in bytes
            - state: Processing state (e.g., "ACTIVE")
            - display_name: Human-readable file name
        """
        pass

    @abstractmethod
    async def delete_file(self, file_name: str) -> bool:
        """
        Delete or clean up a file reference.

        Args:
            file_name: The file identifier/name to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def query_video_with_file(self, file_uri: str, prompt: str) -> str:
        """
        Query a video with a text prompt.

        Args:
            file_uri: The file identifier/URI
            prompt: The question or analysis prompt

        Returns:
            The analysis response as a string
        """
        pass

    @abstractmethod
    async def find_timestamp_with_file(self, file_uri: str, query: str) -> Dict[str, Any]:
        """
        Find a specific timestamp in the video matching the query.

        Args:
            file_uri: The file identifier/URI
            query: What to search for in the video

        Returns:
            Dict containing:
            - timestamp: The timestamp in seconds or "X.Xs" format
            - confidence: Confidence score (0.0 to 1.0)
            - description: Brief description of what was found
        """
        pass

    @abstractmethod
    async def find_multiple_timestamps_with_file(self, file_uri: str, query: str) -> Dict[str, Any]:
        """
        Find all timestamps in the video matching the query.

        Args:
            file_uri: The file identifier/URI
            query: What to search for in the video

        Returns:
            Dict containing:
            - timestamps: List of timestamp matches, each with:
                - timestamp: The timestamp
                - confidence: Confidence score
                - description: Brief description
            - total_found: Total number of matches (optional)
        """
        pass

    @abstractmethod
    async def analyze_video_range(
        self,
        file_uri: str,
        start_time: str,
        end_time: str,
        prompt: str
    ) -> str:
        """
        Analyze a specific time range in the video.

        Args:
            file_uri: The file identifier/URI
            start_time: Start timestamp (e.g., "10s", "1:30")
            end_time: End timestamp
            prompt: Analysis prompt for this range

        Returns:
            The analysis response as a string
        """
        pass