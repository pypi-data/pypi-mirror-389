"""
SDK Configuration
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class SDKConfig:
    """
    Main SDK configuration

    Attributes:
        provider: AI provider name (gemini, qwen)
        api_key: API key for the provider
        model: Model name to use
        preprocessing_enabled: Enable frame preprocessing
        motion_threshold: Motion detection sensitivity (0.0-1.0)
        scene_change_threshold: Scene change detection threshold (0.0-1.0)
        max_fps: Maximum frames per second to process
        batch_size: Number of frames to process in batch
        cache_enabled: Enable result caching
        debug: Enable debug logging
    """

    # Provider settings
    provider: str = "gemini"
    api_key: Optional[str] = None
    model: Optional[str] = None

    # Preprocessing settings
    preprocessing_enabled: bool = True
    motion_threshold: float = 0.02
    scene_change_threshold: float = 0.7
    min_processing_interval: float = 1.0  # seconds

    # Performance settings
    max_fps: int = 30
    batch_size: int = 1
    cache_enabled: bool = True

    # Advanced settings
    debug: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration"""
        if self.provider not in ["gemini", "qwen"]:
            raise ValueError(f"Unsupported provider: {self.provider}")

        if self.motion_threshold < 0 or self.motion_threshold > 1:
            raise ValueError("motion_threshold must be between 0 and 1")

        if self.scene_change_threshold < 0 or self.scene_change_threshold > 1:
            raise ValueError("scene_change_threshold must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "provider": self.provider,
            "model": self.model,
            "preprocessing_enabled": self.preprocessing_enabled,
            "motion_threshold": self.motion_threshold,
            "scene_change_threshold": self.scene_change_threshold,
            "min_processing_interval": self.min_processing_interval,
            "max_fps": self.max_fps,
            "batch_size": self.batch_size,
            "cache_enabled": self.cache_enabled,
            "debug": self.debug,
            "extra_params": self.extra_params,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SDKConfig":
        """Create config from dictionary"""
        return cls(**config_dict)
