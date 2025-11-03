"""
UDP connector for receiving video streams over UDP.

Supports:
- Raw UDP video streams
- Frame reassembly from chunks
- Multiple encoding formats (JPEG, H.264, etc.)
"""

from typing import Optional, Dict, Any, Iterator
import socket
import cv2
import numpy as np
import time
from vlm.connectors.base import BaseConnector
from vlm.core.types import Frame


class UDPConnector(BaseConnector):
    """
    Connector for UDP video streams.

    Receives video frames over UDP and handles chunk reassembly.
    """

    def __init__(self, source: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize UDP connector.

        Args:
            source: UDP URL in format "udp://host:port" or just port number
            config: Optional configuration:
                - buffer_size: Socket buffer size in bytes (default: 65536)
                - timeout: Socket timeout in seconds (default: 5)
                - encoding: Expected frame encoding 'jpeg', 'h264', 'raw' (default: 'jpeg')
                - max_chunk_wait: Max time to wait for all chunks in seconds (default: 1.0)
        """
        super().__init__(source, config)
        self.buffer_size = self.config.get("buffer_size", 65536)
        self.timeout = self.config.get(
            "timeout", 1
        )  # Shorter timeout for better responsiveness
        self.encoding = self.config.get("encoding", "jpeg")
        self.max_chunk_wait = self.config.get("max_chunk_wait", 1.0)
        self.raw_mode = self.config.get(
            "raw_mode", True
        )  # Auto-detect raw streams from FFmpeg

        # Parse source
        self.host, self.port = self._parse_source(source)

        self.sock: Optional[socket.socket] = None
        self.chunk_buffer: Dict[
            int, Dict[int, bytes]
        ] = {}  # frame_id -> {chunk_id: data}
        self.chunk_metadata: Dict[
            int, Dict[str, Any]
        ] = {}  # frame_id -> {total_chunks, first_chunk_time}

        # MJPEG frame assembly buffer for FFmpeg streams
        self.mjpeg_buffer = bytearray()
        self.last_packet_time = 0
        self.video_pid: Optional[int] = None
        self.ts_buffer = bytearray()

    def _parse_source(self, source: str) -> tuple[str, int]:
        """Parse UDP source into host and port."""
        if source.startswith("udp://"):
            source = source[6:]  # Remove 'udp://'

        if ":" in source:
            host, port_str = source.rsplit(":", 1)
            return host or "0.0.0.0", int(port_str)
        else:
            # Just port number
            return "0.0.0.0", int(source)

    def connect(self) -> bool:
        """Start UDP socket listener."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.settimeout(self.timeout)

            self.connected = True
            self.start_time = time.time()
            self.frame_count = 0
            print(f"UDP connector listening on {self.host}:{self.port}")
            return True

        except Exception as e:
            print(f"Error starting UDP connector: {e}")
            return False

    def stream_frames(self) -> Iterator[Frame]:
        """
        Override stream_frames for UDP to handle timeouts gracefully.
        UDP should continue waiting for frames even on timeout.
        """
        if not self.connected:
            if not self.connect():
                raise ConnectionError(f"Failed to connect to {self.source}")

        if self.start_time is None:
            self.start_time = time.time()

        try:
            while self.is_connected():
                frame = self.read_frame()
                if frame is not None:
                    yield frame
                # For UDP, continue waiting even if no frame (timeout)
                # This is different from other connectors that would break
        finally:
            self.disconnect()

    def read_frame(self) -> Optional[Frame]:
        """Read next frame from UDP stream.

        This method receives UDP packets and returns when a complete frame
        has been assembled OR on timeout to prevent blocking the event loop.
        """
        if not self.is_connected():
            return None

        try:
            # Try to receive ONE packet (with timeout)
            try:
                packet, addr = self.sock.recvfrom(self.buffer_size)
                # Debug: Log first packet received
                if self.frame_count == 0 and len(packet) > 0:
                    print(f"UDP: First packet received! Size: {len(packet)} bytes from {addr}")
                    print(f"UDP: Packet starts with: {packet[:20].hex() if len(packet) >= 20 else packet.hex()}")
            except socket.timeout:
                # Return None on timeout to yield control back
                # The stream_frames generator will call us again
                return None

            if not packet:
                return None

            # Chunked mode (custom header): assemble until full frame is ready
            if not self.raw_mode and len(packet) >= 4:
                frame = self._handle_chunked_packet(packet)
                return frame  # May be None if not complete yet

            # Raw mode (best-effort single-packet decode)
            frame = self._handle_raw_packet(packet)
            if frame is not None and self.frame_count % 30 == 0:
                print(f"UDP: Decoded frame #{self.frame_count}")
            return frame  # May be None if not decodable

        except Exception as e:
            print(f"Error reading UDP frame: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _handle_raw_packet(self, packet: bytes) -> Optional[Frame]:
        """Handle raw UDP packets (e.g., from FFmpeg MPEG-TS with MJPEG)."""
        try:
            current_time = time.time()

            # For MPEG-TS streams, we need to extract JPEG frames
            # First, extract payload from MPEG-TS packets
            if self.encoding in ["jpeg", "mjpeg", "mpegts"]:
                # Parse MPEG-TS packets and extract payload
                payload = self._extract_mpegts_payload(packet)
                if payload:
                    self.mjpeg_buffer.extend(payload)

                # Look for JPEG markers in the accumulated buffer
                jpeg_start = b'\xff\xd8'  # JPEG Start of Image
                jpeg_end = b'\xff\xd9'    # JPEG End of Image

                # Debug: Log buffer state for first frame only
                if len(self.mjpeg_buffer) > 0 and self.frame_count == 0:
                    has_start = jpeg_start in self.mjpeg_buffer
                    has_end = jpeg_end in self.mjpeg_buffer
                    if has_start or has_end:
                        print(f"UDP: Buffer size: {len(self.mjpeg_buffer)} bytes, JPEG start: {has_start}, end: {has_end}")

                # Check if we have a complete JPEG frame
                if jpeg_start in self.mjpeg_buffer and jpeg_end in self.mjpeg_buffer:
                    # Find the start and end positions
                    start_idx = self.mjpeg_buffer.find(jpeg_start)
                    end_idx = self.mjpeg_buffer.find(jpeg_end, start_idx)

                    if start_idx != -1 and end_idx != -1:
                        # Extract the complete JPEG frame (including end marker)
                        frame_data = bytes(self.mjpeg_buffer[start_idx:end_idx + 2])

                        # Remove processed data from buffer
                        self.mjpeg_buffer = self.mjpeg_buffer[end_idx + 2:]

                        # Try to decode the frame
                        decoded_frame = self._decode_frame(frame_data)
                        if decoded_frame is not None:
                            timestamp = current_time - self.start_time if self.start_time else 0
                            self.frame_count += 1

                            if self.frame_count == 1 or self.frame_count % 30 == 0:
                                print(f"UDP: Decoded frame #{self.frame_count}, shape: {decoded_frame.shape}")

                            return Frame(
                                data=decoded_frame,
                                timestamp=timestamp,
                                frame_number=self.frame_count,
                                metadata={
                                    "source": self.source,
                                    "source_type": "udp",
                                    "encoding": self.encoding,
                                    "raw_mode": True,
                                },
                            )

                # Prevent buffer from growing too large
                if len(self.mjpeg_buffer) > 1024 * 1024:  # 1MB limit
                    # Keep only the last portion that might contain partial frame
                    self.mjpeg_buffer = self.mjpeg_buffer[-65536:]

            # For other encodings, skip for now
            return None

        except Exception as e:
            print(f"Error handling raw packet: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_mpegts_payload(self, packet: bytes) -> bytes:
        """Extract payload from MPEG-TS packets, skipping headers and PSI tables."""
        payload = bytearray()
        # Accumulate incoming data in case TS packets cross UDP datagrams
        self.ts_buffer.extend(packet)
        data = self.ts_buffer
        pos = 0

        while pos + 188 <= len(data):
            if data[pos] != 0x47:
                # Not aligned on sync byte, seek to the next one
                next_sync = data.find(b"\x47", pos + 1)
                if next_sync == -1:
                    break
                pos = next_sync
                continue

            ts_packet = data[pos : pos + 188]

            # Extract header fields
            header = (ts_packet[1] << 8) | ts_packet[2]
            payload_start = (header >> 14) & 0x01
            pid = header & 0x1FFF

            # Skip null packets and PAT
            if pid in (0x1FFF, 0x0000):
                pos += 188
                continue

            adaptation_field = (ts_packet[3] >> 4) & 0x03

            header_size = 4
            if adaptation_field in (0x02, 0x03):
                adaptation_length = ts_packet[4]
                header_size += 1 + adaptation_length
                if header_size >= 188:
                    pos += 188
                    continue

            if adaptation_field in (0x01, 0x03):
                payload_bytes = ts_packet[header_size:188]
                if not payload_bytes:
                    pos += 188
                    continue

                if payload_start and payload_bytes[:3] == b"\x00\x00\x01":
                    # PES start - skip PES header
                    if self.video_pid is None:
                        self.video_pid = pid
                    elif pid != self.video_pid:
                        pos += 188
                        continue

                    if len(payload_bytes) >= 9:
                        pes_header_length = payload_bytes[8]
                        pes_payload_start = 9 + pes_header_length
                        if pes_payload_start <= len(payload_bytes):
                            payload_bytes = payload_bytes[pes_payload_start:]
                        else:
                            payload_bytes = b""
                else:
                    # Ignore PSI/other streams once we know the video PID
                    if self.video_pid is not None and pid != self.video_pid:
                        pos += 188
                        continue
                    # Until we discover the video PID, skip non-PES payloads
                    if self.video_pid is None:
                        pos += 188
                        continue

                if payload_bytes:
                    payload.extend(payload_bytes)

            pos += 188

        # Keep leftover bytes (less than 188) for next call
        if pos < len(data):
            self.ts_buffer = bytearray(data[pos:])
        else:
            self.ts_buffer.clear()

        return bytes(payload)

    def _handle_chunked_packet(self, packet: bytes) -> Optional[Frame]:
        """Handle chunked packets with custom header format."""
        try:
            if len(packet) < 4:
                return None

            # Parse header (4 bytes: frame_id + chunk_id + total_chunks + reserved)
            frame_id = int.from_bytes(packet[0:2], "big")
            chunk_id = packet[2]
            total_chunks = packet[3]
            chunk_data = packet[4:]

            # Initialize frame buffer if needed
            if frame_id not in self.chunk_buffer:
                self.chunk_buffer[frame_id] = {}
                self.chunk_metadata[frame_id] = {
                    "total_chunks": total_chunks,
                    "first_chunk_time": time.time(),
                }

            # Store chunk
            self.chunk_buffer[frame_id][chunk_id] = chunk_data

            # Check if we have all chunks
            if len(self.chunk_buffer[frame_id]) == total_chunks:
                # Reassemble frame
                frame_data = b"".join(
                    [self.chunk_buffer[frame_id][i] for i in range(total_chunks)]
                )

                # Clean up old frames
                self._cleanup_old_frames(frame_id)

                # Decode frame
                decoded_frame = self._decode_frame(frame_data)
                if decoded_frame is not None:
                    current_time = time.time()
                    timestamp = current_time - self.start_time if self.start_time else 0
                    self.frame_count += 1

                    return Frame(
                        data=decoded_frame,
                        timestamp=timestamp,
                        frame_number=self.frame_count,
                        metadata={
                            "source": self.source,
                            "source_type": "udp",
                            "encoding": self.encoding,
                            "chunks": total_chunks,
                        },
                    )

            # Clean up stale incomplete frames
            self._cleanup_stale_frames()
            return None

        except Exception as e:
            print(f"Error handling chunked packet: {e}")
            return None

    def _decode_frame(self, frame_data: bytes) -> Optional[np.ndarray]:
        """Decode frame data based on encoding."""
        try:
            if self.encoding in ["jpeg", "mjpeg"]:
                # Decode JPEG/MJPEG
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return frame
            elif self.encoding == "raw":
                # Assume raw BGR format - would need width/height from config
                return np.frombuffer(frame_data, np.uint8)
            else:
                # Try to decode as JPEG anyway (common fallback)
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is not None:
                    return frame
                print(f"Unsupported encoding: {self.encoding}")
                return None
        except Exception as e:
            # Silently skip decode errors for raw streams
            return None

    def _cleanup_old_frames(self, current_frame_id: int):
        """Remove processed frames from buffer."""
        frames_to_remove = [
            fid for fid in self.chunk_buffer.keys() if fid <= current_frame_id
        ]
        for fid in frames_to_remove:
            del self.chunk_buffer[fid]
            if fid in self.chunk_metadata:
                del self.chunk_metadata[fid]

    def _cleanup_stale_frames(self):
        """Remove incomplete frames that are too old."""
        current_time = time.time()
        stale_frames = []

        for frame_id, metadata in self.chunk_metadata.items():
            if current_time - metadata["first_chunk_time"] > self.max_chunk_wait:
                stale_frames.append(frame_id)

        for frame_id in stale_frames:
            if frame_id in self.chunk_buffer:
                del self.chunk_buffer[frame_id]
            if frame_id in self.chunk_metadata:
                del self.chunk_metadata[frame_id]

    def disconnect(self) -> None:
        """Close UDP socket."""
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        self.connected = False
        self.chunk_buffer.clear()
        self.chunk_metadata.clear()
        self.mjpeg_buffer.clear()  # Clear MJPEG buffer
        self.video_pid = None
        self.ts_buffer.clear()
        print(f"Disconnected from UDP stream: {self.source}")

    def is_connected(self) -> bool:
        """Check if UDP socket is active."""
        return self.connected and self.sock is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Get UDP stream metadata."""
        metadata = super().get_metadata()
        metadata.update(
            {
                "host": self.host,
                "port": self.port,
                "encoding": self.encoding,
                "buffer_size": self.buffer_size,
                "pending_frames": len(self.chunk_buffer),
            }
        )
        return metadata
