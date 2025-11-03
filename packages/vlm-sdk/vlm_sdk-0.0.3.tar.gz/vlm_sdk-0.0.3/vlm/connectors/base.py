"""
Base connector class for video sources.

Connectors handle input from various video sources (RTSP, ONVIF, USB, files)
and provide a unified interface for frame retrieval.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Iterator
from vlm.core.types import Frame
import time


class BaseConnector(ABC):
    """
    Abstract base class for video source connectors.

    All connectors must implement:
    - connect(): Establish connection to video source
    - read_frame(): Read next frame from source
    - disconnect(): Clean up and close connection
    - is_connected(): Check connection status
    """

    def __init__(self, source: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize connector.

        Args:
            source: Video source identifier (URL, device ID, file path, etc.)
            config: Optional configuration dictionary
        """
        self.source = source
        self.config = config or {}
        self.connected = False
        self.frame_count = 0
        self.start_time: Optional[float] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to video source.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def read_frame(self) -> Optional[Frame]:
        """
        Read next frame from source.

        Returns:
            Frame object if successful, None otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Clean up and close connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connector is connected.

        Returns:
            True if connected, False otherwise
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the video source.

        Returns:
            Dictionary with source metadata (fps, resolution, codec, etc.)
        """
        return {
            'source': self.source,
            'frame_count': self.frame_count,
            'connected': self.connected
        }

    def stream_frames(self) -> Iterator[Frame]:
        """
        Generator that yields frames continuously.

        Yields:
            Frame objects
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError(f"Failed to connect to {self.source}")

        if self.start_time is None:
            self.start_time = time.time()

        try:
            while self.is_connected():
                frame = self.read_frame()
                if frame is None:
                    break
                yield frame
        finally:
            self.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
