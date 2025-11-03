"""
ONVIF connector for IP cameras with ONVIF support.

Supports:
- ONVIF camera discovery (WS-Discovery)
- Authentication
- PTZ control
- Camera configuration
- RTSP stream URL discovery

Note: Requires onvif-zeep package for ONVIF support
"""

from typing import Optional, Dict, Any, List
import time
from urllib.parse import urlparse, urlunparse
from vlm.connectors.rtsp import RTSPConnector

try:
    from onvif import ONVIFCamera
    from zeep.exceptions import Fault

    ONVIF_AVAILABLE = True
except ImportError:
    ONVIF_AVAILABLE = False
    ONVIFCamera = None


class ONVIFConnector(RTSPConnector):
    """
    Connector for ONVIF-compatible IP cameras.

    Requires onvif-zeep package:
        pip install onvif-zeep

    This connector extends RTSPConnector with ONVIF-specific features:
    - Automatic RTSP URL discovery
    - PTZ control
    - Camera configuration

    Example:
        connector = ONVIFConnector(
            source="192.168.1.100",
            config={
                'username': 'admin',
                'password': 'password',
                'port': 80,
                'profile_index': 0  # Use first stream profile
            }
        )
    """

    def __init__(self, source: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ONVIF connector.

        Args:
            source: Camera IP address or hostname
            config: Configuration dictionary:
                - username: ONVIF username (required)
                - password: ONVIF password (required)
                - port: ONVIF port (default: 80)
                - profile_index: Stream profile index (default: 0)
                - profile_name: Stream profile name (optional, takes precedence over index)
                - profile_token: Stream profile token (optional, highest precedence)
                - transport: RTSP transport for playback (default: 'tcp', passed to RTSPConnector)
                - wsdl_dir: Path to WSDL files (default: None, uses package default)
                - All RTSPConnector config options
        """
        if not ONVIF_AVAILABLE:
            raise ImportError(
                "onvif-zeep is required for ONVIF support. "
                "Install it with: pip install onvif-zeep"
            )

        # Don't call parent __init__ yet, we need to discover RTSP URL first
        self.camera_ip = source
        self.config = config or {}
        self.username = self.config.get("username")
        self.password = self.config.get("password")
        self.onvif_port = self.config.get("port", 80)
        self.profile_index = self.config.get("profile_index", 0)
        self.profile_name = self.config.get("profile_name")
        self.profile_token = self.config.get("profile_token")
        self.wsdl_dir = self.config.get("wsdl_dir", None)

        if not self.username or not self.password:
            raise ValueError("ONVIF requires 'username' and 'password' in config")

        self.onvif_camera: Optional[ONVIFCamera] = None
        self.media_service = None
        self.ptz_service = None
        self.media_profile = None
        self.rtsp_url: Optional[str] = None

        # Initialize ONVIF connection to discover RTSP URL
        self._initialize_onvif()

        # Now initialize parent with discovered RTSP URL
        super().__init__(self.rtsp_url, config)

    def _initialize_onvif(self):
        """Initialize ONVIF connection and discover stream URL."""
        try:
            # Create ONVIF camera client
            if self.wsdl_dir:
                self.onvif_camera = ONVIFCamera(
                    self.camera_ip,
                    self.onvif_port,
                    self.username,
                    self.password,
                    self.wsdl_dir,
                )
            else:
                self.onvif_camera = ONVIFCamera(
                    self.camera_ip, self.onvif_port, self.username, self.password
                )

            # Get media service
            self.media_service = self.onvif_camera.create_media_service()

            # Get available profiles
            profiles = self.media_service.GetProfiles()
            if not profiles:
                raise RuntimeError("No media profiles found on camera")

            # Select profile with precedence: token -> name -> index
            selected_profile = None
            if self.profile_token:
                for p in profiles:
                    if getattr(p, "token", None) == self.profile_token:
                        selected_profile = p
                        break
                if not selected_profile:
                    print(
                        f"Warning: Profile token '{self.profile_token}' not found, falling back"
                    )
            if not selected_profile and self.profile_name:
                for p in profiles:
                    if getattr(p, "Name", None) == self.profile_name:
                        selected_profile = p
                        break
                if not selected_profile:
                    print(
                        f"Warning: Profile name '{self.profile_name}' not found, falling back to index"
                    )
            if not selected_profile:
                if self.profile_index >= len(profiles):
                    print(
                        f"Warning: Profile index {self.profile_index} out of range, using profile 0"
                    )
                    self.profile_index = 0
                selected_profile = profiles[self.profile_index]

            self.media_profile = selected_profile
            print(f"Using media profile: {self.media_profile.Name}")

            # Get RTSP stream URI
            stream_setup = {"Stream": "RTP-Unicast", "Transport": {"Protocol": "RTSP"}}
            uri_response = self.media_service.GetStreamUri(
                {"StreamSetup": stream_setup, "ProfileToken": self.media_profile.token}
            )

            raw_url = uri_response.Uri

            # Inject credentials into RTSP URL if missing (common ONVIF behavior)
            try:
                parsed = urlparse(raw_url)
                netloc = parsed.netloc
                if "@" not in netloc and self.username and self.password:
                    hostport = netloc
                    netloc = f"{self.username}:{self.password}@{hostport}"
                    parsed = parsed._replace(netloc=netloc)
                    self.rtsp_url = urlunparse(parsed)
                else:
                    self.rtsp_url = raw_url
            except Exception:
                # Fallback to raw URL if parsing fails
                self.rtsp_url = raw_url

            print(f"Discovered RTSP URL: {self.rtsp_url}")

            # Try to get PTZ service (optional)
            try:
                self.ptz_service = self.onvif_camera.create_ptz_service()
            except Exception:
                self.ptz_service = None
                print("PTZ service not available on this camera")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize ONVIF camera: {e}")

    def get_profiles(self) -> List[Dict[str, Any]]:
        """
        Get available media profiles from camera.

        Returns:
            List of profile dictionaries with name, token, and configuration
        """
        if not self.media_service:
            return []

        try:
            profiles = self.media_service.GetProfiles()
            result = []
            for p in profiles:
                profile_info = {"name": p.Name, "token": p.token}

                # Add video encoder config if available
                if (
                    hasattr(p, "VideoEncoderConfiguration")
                    and p.VideoEncoderConfiguration
                ):
                    vec = p.VideoEncoderConfiguration
                    profile_info["video"] = {
                        "encoding": vec.Encoding,
                        "width": vec.Resolution.Width
                        if hasattr(vec, "Resolution")
                        else None,
                        "height": vec.Resolution.Height
                        if hasattr(vec, "Resolution")
                        else None,
                        "framerate": vec.RateControl.FrameRateLimit
                        if hasattr(vec, "RateControl")
                        else None,
                    }

                result.append(profile_info)

            return result

        except Exception as e:
            print(f"Error getting profiles: {e}")
            return []

    def ptz_move(self, pan: float, tilt: float, zoom: float, timeout: float = 1.0):
        """
        Move PTZ camera (if supported).

        Args:
            pan: Pan velocity (-1.0 to 1.0, negative = left, positive = right)
            tilt: Tilt velocity (-1.0 to 1.0, negative = down, positive = up)
            zoom: Zoom velocity (-1.0 to 1.0, negative = zoom out, positive = zoom in)
            timeout: Movement timeout in seconds
        """
        if not self.ptz_service:
            print("PTZ not supported on this camera")
            return

        try:
            request = self.ptz_service.create_type("ContinuousMove")
            request.ProfileToken = self.media_profile.token
            request.Velocity = {"PanTilt": {"x": pan, "y": tilt}, "Zoom": {"x": zoom}}
            request.Timeout = timeout

            self.ptz_service.ContinuousMove(request)

        except Exception as e:
            print(f"Error moving PTZ: {e}")

    def ptz_stop(self):
        """Stop PTZ movement."""
        if not self.ptz_service:
            return

        try:
            request = self.ptz_service.create_type("Stop")
            request.ProfileToken = self.media_profile.token
            request.PanTilt = True
            request.Zoom = True

            self.ptz_service.Stop(request)

        except Exception as e:
            print(f"Error stopping PTZ: {e}")

    def get_metadata(self) -> Dict[str, Any]:
        """Get ONVIF camera metadata."""
        metadata = super().get_metadata()
        metadata.update(
            {
                "camera_ip": self.camera_ip,
                "onvif_port": self.onvif_port,
                "rtsp_url": self.rtsp_url,
                "has_ptz": self.ptz_service is not None,
                "profile_name": self.media_profile.Name if self.media_profile else None,
                "profile_token": getattr(self.media_profile, "token", None)
                if self.media_profile
                else None,
                "transport": self.config.get("transport", "tcp"),
            }
        )

        # Add video encoder details if available on selected profile
        try:
            if self.media_profile and hasattr(
                self.media_profile, "VideoEncoderConfiguration"
            ):
                vec = self.media_profile.VideoEncoderConfiguration
                video_meta = {
                    "encoding": getattr(vec, "Encoding", None),
                    "width": getattr(getattr(vec, "Resolution", None), "Width", None)
                    if hasattr(vec, "Resolution")
                    else None,
                    "height": getattr(getattr(vec, "Resolution", None), "Height", None)
                    if hasattr(vec, "Resolution")
                    else None,
                    "framerate": getattr(
                        getattr(vec, "RateControl", None), "FrameRateLimit", None
                    )
                    if hasattr(vec, "RateControl")
                    else None,
                }
                metadata["video"] = video_meta
        except Exception:
            pass

        # Add device information
        if self.onvif_camera:
            try:
                device_info = self.onvif_camera.devicemgmt.GetDeviceInformation()
                metadata["device"] = {
                    "manufacturer": device_info.Manufacturer,
                    "model": device_info.Model,
                    "firmware_version": device_info.FirmwareVersion,
                    "serial_number": device_info.SerialNumber,
                }
            except Exception:
                pass

        return metadata

    @staticmethod
    def discover_cameras(timeout: float = 5.0) -> List[Dict[str, str]]:
        """
        Discover ONVIF cameras on the local network using WS-Discovery.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List of discovered cameras with IP and service URLs

        Note: Requires wsdiscovery package:
            pip install wsdiscovery
        """
        try:
            from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
            from wsdiscovery.scope import Scope
        except ImportError:
            print("wsdiscovery package required for camera discovery")
            print("Install with: pip install wsdiscovery")
            return []

        cameras = []
        wsd = WSDiscovery()
        wsd.start()

        try:
            services = wsd.searchServices(timeout=timeout)
            for service in services:
                # Check if it's an ONVIF device
                scopes = [str(scope) for scope in service.getScopes()]
                is_onvif = any("onvif" in scope.lower() for scope in scopes)

                if is_onvif:
                    xaddrs = service.getXAddrs()
                    if xaddrs:
                        # Extract IP from service URL
                        url = xaddrs[0]
                        # Parse IP from URL like http://192.168.1.100:80/onvif/device_service
                        import re

                        match = re.search(r"//([^:/]+)", url)
                        if match:
                            cameras.append(
                                {
                                    "ip": match.group(1),
                                    "service_url": url,
                                    "scopes": scopes,
                                }
                            )

        finally:
            wsd.stop()

        return cameras
