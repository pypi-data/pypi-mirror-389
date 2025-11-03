"""
WebRTC connector for browser-based video streams.

Supports:
- WebRTC signaling (SDP offer/answer) via aiortc
- WHIP (WebRTC-HTTP Ingestion Protocol) via external media server (e.g., MediaMTX)
- Delegation to RTSP when configured (recommended for production ingestion)
- ICE candidate exchange (native path)
- Video track reception

Notes:
- For least resistance with industry standards, terminate WebRTC/WHIP in MediaMTX and
  ingest via RTSP. This connector detects that configuration and delegates to RTSPConnector.
- Native aiortc path remains available for direct offer/answer experiments.
"""

from typing import Optional, Dict, Any
import time
import asyncio
from vlm.connectors.base import BaseConnector
from vlm.core.types import Frame
from vlm.connectors.rtsp import RTSPConnector  # delegate when using WHIP->RTSP

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
    from av import VideoFrame

    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    RTCPeerConnection = None
    RTCSessionDescription = None


class WebRTCConnector(BaseConnector):
    """
    Connector for WebRTC/WHIP video streams.

    Two modes:
    1) Delegated mode (recommended): Use MediaMTX WHIP to terminate WebRTC and provide RTSP.
       Provide 'rtsp_url' in config or pass an RTSP URL as 'source'. Frames are read via RTSPConnector.
    2) Native mode: Use aiortc for SDP offer/answer. Requires separate signaling.
    """

    def __init__(self, source: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize WebRTC connector.

        Args:
            source: Signaling server URL, WHIP/RTSP URL, or "webrtc://browser"
            config: Optional configuration:
                - rtsp_url: RTSP URL to delegate to (e.g., from MediaMTX WHIP)
                - stun_servers: List of STUN server URLs (default: Google STUN)
                - turn_servers: List of TURN server configs (default: None)
                - video_codec: Preferred video codec (default: 'h264')
                - audio: Enable audio track (default: False)
        """
        super().__init__(source, config)

        # Delegation to RTSP if configured
        self.rtsp_url: Optional[str] = None
        if self.config.get("rtsp_url"):
            self.rtsp_url = self.config["rtsp_url"]
        elif self.source.startswith("rtsp://"):
            self.rtsp_url = self.source

        self.delegate_rtsp: Optional[RTSPConnector] = None

        # Native WebRTC (aiortc) settings
        self.stun_servers = self.config.get(
            "stun_servers", ["stun:stun.l.google.com:19302"]
        )
        self.turn_servers = self.config.get("turn_servers", [])
        self.video_codec = self.config.get("video_codec", "h264")
        self.audio_enabled = self.config.get("audio", False)

        self.pc: Optional["RTCPeerConnection"] = None
        self.video_track: Optional["VideoStreamTrack"] = None
        self.frame_queue: Optional[asyncio.Queue] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def _use_delegate(self) -> bool:
        """Return True if we should delegate to RTSPConnector (WHIP->RTSP)."""
        return self.rtsp_url is not None

    def connect(self) -> bool:
        """Establish connection (delegate to RTSP when configured, else native WebRTC)."""
        try:
            if self._use_delegate():
                # Delegate to RTSPConnector (MediaMTX WHIP -> RTSP path)
                self.delegate_rtsp = RTSPConnector(self.rtsp_url, self.config)
                ok = self.delegate_rtsp.connect()
                if ok:
                    self.connected = True
                    self.start_time = time.time()
                    self.frame_count = 0
                    print(
                        f"WebRTCConnector (delegated) -> RTSP connected: {self.rtsp_url}"
                    )
                return ok

            # Native WebRTC (aiortc) path
            if not WEBRTC_AVAILABLE:
                raise ImportError(
                    "aiortc is required for native WebRTC. "
                    "Install it with: pip install aiortc"
                )

            # Create event loop if needed
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

            # Initialize frame queue
            self.frame_queue = asyncio.Queue(maxsize=30)

            # Configure ICE servers
            ice_servers = []
            for stun_url in self.stun_servers:
                ice_servers.append({"urls": stun_url})
            for turn_config in self.turn_servers:
                ice_servers.append(turn_config)

            config = {"iceServers": ice_servers} if ice_servers else None
            self.pc = RTCPeerConnection(configuration=config)

            # Set up track handler
            @self.pc.on("track")
            async def on_track(track):
                if track.kind == "video":
                    self.video_track = track
                    print(f"Received video track: {track.id}")

                    # Process video frames
                    while True:
                        try:
                            frame = await track.recv()
                            await self.frame_queue.put(frame)
                        except Exception as e:
                            print(f"Error receiving frame: {e}")
                            break

            self.connected = True
            self.start_time = time.time()
            self.frame_count = 0
            print("WebRTC connector (native) initialized")
            return True

        except Exception as e:
            print(f"Error initializing WebRTC connector: {e}")
            return False

    def read_frame(self) -> Optional[Frame]:
        """
        Read next frame from stream.

        - In delegated mode, pull frames from RTSPConnector.
        - In native WebRTC mode, read from internal asyncio frame queue.
        """
        if not self.is_connected():
            return None

        # Delegated mode (RTSP)
        if self._use_delegate() and self.delegate_rtsp:
            try:
                return self.delegate_rtsp.read_frame()
            except Exception as e:
                print(f"Error reading delegated RTSP frame: {e}")
                return None

        # Native WebRTC mode
        if not self.frame_queue or not self.loop:
            return None

        try:
            # Get frame from queue with timeout
            async def get_frame():
                try:
                    return await asyncio.wait_for(self.frame_queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    return None

            av_frame = self.loop.run_until_complete(get_frame())
            if av_frame is None:
                return None

            # Convert av.VideoFrame to numpy array
            frame_data = av_frame.to_ndarray(format="bgr24")

            current_time = time.time()
            timestamp = current_time - self.start_time if self.start_time else 0
            self.frame_count += 1

            return Frame(
                data=frame_data,
                timestamp=timestamp,
                frame_number=self.frame_count,
                metadata={
                    "source": self.source,
                    "source_type": "webrtc",
                    "codec": self.video_codec,
                    "pts": getattr(av_frame, "pts", None),
                },
            )

        except Exception as e:
            print(f"Error reading WebRTC frame: {e}")
            return None

    async def create_offer(self) -> Dict[str, str]:
        """
        Create SDP offer for signaling (native mode only).
        Returns: {'type': ..., 'sdp': ...}
        """
        if self._use_delegate():
            raise RuntimeError("create_offer is not applicable in delegated RTSP mode")
        if not self.pc:
            raise RuntimeError("Connection not initialized")

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp,
        }

    async def set_remote_description(self, sdp_type: str, sdp: str):
        """
        Set remote SDP description from signaling (native mode only).
        """
        if self._use_delegate():
            raise RuntimeError(
                "set_remote_description is not applicable in delegated RTSP mode"
            )
        if not self.pc:
            raise RuntimeError("Connection not initialized")

        description = RTCSessionDescription(sdp=sdp, type=sdp_type)
        await self.pc.setRemoteDescription(description)

    async def create_answer(self) -> Dict[str, str]:
        """
        Create SDP answer for signaling (native mode only).
        Returns: {'type': ..., 'sdp': ...}
        """
        if self._use_delegate():
            raise RuntimeError("create_answer is not applicable in delegated RTSP mode")
        if not self.pc:
            raise RuntimeError("Connection not initialized")

        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp,
        }

    def disconnect(self) -> None:
        """Close connection (delegate or native)."""
        # Delegated RTSP path
        if self.delegate_rtsp:
            try:
                self.delegate_rtsp.disconnect()
            except Exception:
                pass
            self.delegate_rtsp = None

        # Native WebRTC path
        if self.pc:

            async def close_pc():
                await self.pc.close()

            if self.loop:
                try:
                    self.loop.run_until_complete(close_pc())
                except Exception:
                    pass

            self.pc = None

        self.video_track = None
        self.connected = False
        print("Disconnected from WebRTC stream")

    def is_connected(self) -> bool:
        """Check if connection is active."""
        if self._use_delegate() and self.delegate_rtsp:
            return self.delegate_rtsp.is_connected()
        return self.connected and self.pc is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Get connector metadata (delegate-aware)."""
        metadata = super().get_metadata()

        if self._use_delegate():
            # Reflect delegated RTSP metadata
            metadata.update(
                {
                    "mode": "delegated_rtsp",
                    "rtsp_url": self.rtsp_url,
                }
            )
            if self.delegate_rtsp:
                metadata.update(self.delegate_rtsp.get_metadata())
            return metadata

        # Native WebRTC metadata
        metadata.update(
            {
                "mode": "native_webrtc",
                "codec": self.video_codec,
                "audio_enabled": self.audio_enabled,
                "stun_servers": self.stun_servers,
                "has_video_track": self.video_track is not None,
            }
        )
        if self.pc:
            try:
                metadata["connection_state"] = self.pc.connectionState
                metadata["ice_connection_state"] = self.pc.iceConnectionState
            except Exception:
                pass

        return metadata
