"""
Base preprocessor abstract class for all frame preprocessors
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import time
import numpy as np
from vlm.core.types import Frame, PreprocessingResult, FrameSelectionReason


class BasePreprocessor(ABC):
    """
    Abstract base class for all video frame preprocessors.

    Preprocessors are responsible for determining which frames should be
    sent to expensive cloud VLM processing and which can be skipped.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the preprocessor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.name = self.__class__.__name__
        self.stats = {
            'frames_processed': 0,
            'frames_selected': 0,
            'frames_skipped': 0,
            'total_processing_time': 0.0,
            'last_processing_time': 0.0,
        }
        self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize any resources needed by the preprocessor.
        This is called once during __init__.
        """
        pass

    @abstractmethod
    def process_frame(self, frame: Frame) -> PreprocessingResult:
        """
        Process a single frame and determine if it should be sent to cloud VLM.

        Args:
            frame: The frame to process

        Returns:
            PreprocessingResult indicating whether to process the frame
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up any resources used by the preprocessor.
        """
        pass

    def __call__(self, frame: Frame) -> PreprocessingResult:
        """
        Process a frame through this preprocessor.

        Args:
            frame: The frame to process

        Returns:
            PreprocessingResult with processing decision
        """
        if not self.enabled:
            return PreprocessingResult(
                should_process=False,
                reason=FrameSelectionReason.SKIPPED,
                confidence=1.0,
                metadata={'preprocessor': self.name, 'enabled': False}
            )

        # Time the processing
        start_time = time.time()
        result = self.process_frame(frame)
        processing_time = time.time() - start_time

        # Update statistics
        self.stats['frames_processed'] += 1
        if result.should_process:
            self.stats['frames_selected'] += 1
        else:
            self.stats['frames_skipped'] += 1
        self.stats['total_processing_time'] += processing_time
        self.stats['last_processing_time'] = processing_time

        # Add metadata
        result.metadata = result.metadata or {}
        result.metadata.update({
            'preprocessor': self.name,
            'processing_time': processing_time,
        })

        return result

    def get_stats(self) -> Dict[str, Any]:
        """
        Get preprocessing statistics.

        Returns:
            Dictionary of statistics
        """
        stats = self.stats.copy()
        if stats['frames_processed'] > 0:
            stats['selection_rate'] = stats['frames_selected'] / stats['frames_processed']
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['frames_processed']
        else:
            stats['selection_rate'] = 0
            stats['avg_processing_time'] = 0
        return stats

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            'frames_processed': 0,
            'frames_selected': 0,
            'frames_skipped': 0,
            'total_processing_time': 0.0,
            'last_processing_time': 0.0,
        }

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update preprocessor configuration.

        Args:
            config: New configuration dictionary
        """
        self.config.update(config)
        self.enabled = self.config.get('enabled', True)


class CompositePreprocessor(BasePreprocessor):
    """
    Composite preprocessor that chains multiple preprocessors together.
    Implements hierarchical filtering (L1 -> L2 -> L3 -> L4).
    """

    def __init__(self, preprocessors: List[BasePreprocessor], config: Optional[Dict[str, Any]] = None):
        """
        Initialize composite preprocessor.

        Args:
            preprocessors: List of preprocessors to chain
            config: Optional configuration
        """
        self.preprocessors = preprocessors
        super().__init__(config)

    def initialize(self) -> None:
        """Initialize all child preprocessors."""
        for preprocessor in self.preprocessors:
            preprocessor.initialize()

    def process_frame(self, frame: Frame) -> PreprocessingResult:
        """
        Process frame through all preprocessors in sequence.

        Uses OR logic: if ANY preprocessor says process, we process.
        Stops at first preprocessor that says to process (optimization).

        Args:
            frame: The frame to process

        Returns:
            Combined preprocessing result
        """
        combined_metadata = {}
        highest_confidence = 0.0
        selected_reason = FrameSelectionReason.SKIPPED

        for preprocessor in self.preprocessors:
            result = preprocessor(frame)

            # Collect metadata from all preprocessors
            combined_metadata[preprocessor.name] = result.metadata

            if result.should_process:
                # Found a reason to process, return early
                result.metadata = combined_metadata
                return result

            # Track highest confidence even for skipped frames
            if result.confidence > highest_confidence:
                highest_confidence = result.confidence
                selected_reason = result.reason

        # No preprocessor selected the frame
        return PreprocessingResult(
            should_process=False,
            reason=selected_reason,
            confidence=highest_confidence,
            metadata=combined_metadata
        )

    def cleanup(self) -> None:
        """Clean up all child preprocessors."""
        for preprocessor in self.preprocessors:
            preprocessor.cleanup()

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics from all preprocessors."""
        stats = super().get_stats()
        stats['preprocessor_stats'] = {}
        for preprocessor in self.preprocessors:
            stats['preprocessor_stats'][preprocessor.name] = preprocessor.get_stats()
        return stats