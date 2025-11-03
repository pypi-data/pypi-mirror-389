"""
Preprocessors for intelligent frame selection and filtering.

Preprocessors determine which video frames should be sent to expensive cloud
VLM processing based on various criteria (motion, objects, scene changes, etc).
"""

from vlm.preprocessors.base import BasePreprocessor, CompositePreprocessor
from vlm.preprocessors.detector.core import DetectorPreprocessor

__all__ = [
    'BasePreprocessor',
    'CompositePreprocessor',
    'DetectorPreprocessor',
]
