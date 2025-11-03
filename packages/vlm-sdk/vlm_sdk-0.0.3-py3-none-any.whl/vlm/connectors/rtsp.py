"""
RTSP connector for IP cameras and RTSP streams.

Supports:
- RTSP/RTSPS streams
- Configurable transport (TCP/UDP)
- Authentication
- Reconnection logic
"""

from typing import Optional, Dict, Any
import cv2
import time
from vlm.connectors.base import BaseConnector
from vlm.core.types import Frame


class RTSPConnector(BaseConnector):
    """
    Connector for RTSP video streams.

    Example URLs:
        rtsp://username:password@192.168.1.100:554/stream1
        rtsp://camera.local/live.sdp
        rtsps://secure-camera.com/stream
    """

    def __init__(self, source: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RTSP connector.

        Args:
            source: RTSP URL
            config: Optional configuration:
                - transport: 'tcp' or 'udp' (default: 'tcp')
                - buffer_size: Number of frames to buffer (default: 1)
                - timeout: Connection timeout in seconds (default: 10)
                - reconnect: Auto-reconnect on failure (default: True)
                - reconnect_delay: Delay between reconnect attempts (default: 5)
        """
        super().__init__(source, config)
        self.transport = self.config.get('transport', 'tcp')
        self.buffer_size = self.config.get('buffer_size', 1)
        self.timeout = self.config.get('timeout', 10)
        self.reconnect_enabled = self.config.get('reconnect', True)
        self.reconnect_delay = self.config.get('reconnect_delay', 5)

        self.cap: Optional[cv2.VideoCapture] = None
        self.last_frame_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    def connect(self) -> bool:
        """Establish connection to RTSP stream."""
        try:
            # Build OpenCV VideoCapture with RTSP options
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)

            # Set RTSP transport protocol
            if self.transport.lower() == 'tcp':
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))

            # Set buffer size (lower = less latency, higher = more stable)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

            # Test connection
            if not self.cap.isOpened():
                print(f"Failed to open RTSP stream: {self.source}")
                return False

            # Try to read first frame to verify stream
            ret, _ = self.cap.read()
            if not ret:
                print(f"Failed to read from RTSP stream: {self.source}")
                self.cap.release()
                return False

            self.connected = True
            self.start_time = time.time()
            self.frame_count = 0
            self.reconnect_attempts = 0
            print(f"Connected to RTSP stream: {self.source}")
            return True

        except Exception as e:
            print(f"Error connecting to RTSP stream: {e}")
            return False

    def read_frame(self) -> Optional[Frame]:
        """Read next frame from RTSP stream."""
        if not self.is_connected():
            if self.reconnect_enabled and self.reconnect_attempts < self.max_reconnect_attempts:
                print(f"Attempting to reconnect... (attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                time.sleep(self.reconnect_delay)
                self.reconnect_attempts += 1
                if self.connect():
                    return self.read_frame()
            return None

        try:
            ret, frame_data = self.cap.read()
            if not ret or frame_data is None:
                print("Failed to read frame from RTSP stream")
                self.connected = False
                return None

            current_time = time.time()
            timestamp = current_time - self.start_time if self.start_time else 0
            self.frame_count += 1
            self.last_frame_time = current_time

            return Frame(
                data=frame_data,
                timestamp=timestamp,
                frame_number=self.frame_count,
                metadata={
                    'source': self.source,
                    'source_type': 'rtsp',
                    'transport': self.transport
                }
            )

        except Exception as e:
            print(f"Error reading frame: {e}")
            self.connected = False
            return None

    def disconnect(self) -> None:
        """Close RTSP connection."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.connected = False
        print(f"Disconnected from RTSP stream: {self.source}")

    def is_connected(self) -> bool:
        """Check if RTSP stream is connected."""
        return self.connected and self.cap is not None and self.cap.isOpened()

    def get_metadata(self) -> Dict[str, Any]:
        """Get RTSP stream metadata."""
        metadata = super().get_metadata()
        if self.cap is not None and self.cap.isOpened():
            metadata.update({
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'codec': int(self.cap.get(cv2.CAP_PROP_FOURCC)),
                'transport': self.transport,
                'buffer_size': self.buffer_size
            })
        return metadata
