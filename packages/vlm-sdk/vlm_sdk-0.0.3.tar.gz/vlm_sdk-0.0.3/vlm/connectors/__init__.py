"""
Video source connectors for ob-gemvision.

Connectors provide a unified interface for reading video frames from various real-time sources:
- RTSP streams (IP cameras)
- ONVIF cameras (with auto-discovery and PTZ control)
- UDP streams
- WebRTC streams

Example usage:
    from vlm.connectors import RTSPConnector

    # RTSP stream
    rtsp = RTSPConnector("rtsp://camera.local/stream1")
    with rtsp:
        for frame in rtsp.stream_frames():
            # Process frame
            pass
"""

from vlm.connectors.base import BaseConnector
from vlm.connectors.rtsp import RTSPConnector
from vlm.connectors.udp import UDPConnector

# Optional connectors (require additional dependencies)
try:
    from vlm.connectors.webrtc import WebRTCConnector
except ImportError:
    WebRTCConnector = None

try:
    from vlm.connectors.onvif import ONVIFConnector
except ImportError:
    ONVIFConnector = None

__all__ = [
    'BaseConnector',
    'RTSPConnector',
    'UDPConnector',
    'WebRTCConnector',
    'ONVIFConnector',
]
