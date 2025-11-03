"""
RT-DETR-based intelligent video frame preprocessor.

Implements all validated cost-optimization patterns:
- Temporal Redundancy (process every Nth frame)
- Object tracking across frames
- Semantic importance scoring
- Adaptive thresholds
- Frame caching
- Non-object anomaly detection
"""

from vlm.preprocessors.detector.core import DetectorPreprocessor
from vlm.preprocessors.detector.tracking import TrackedObject
from vlm.preprocessors.detector.caching import TemporalCache

__all__ = [
    'DetectorPreprocessor',
    'TrackedObject',
    'TemporalCache',
]
