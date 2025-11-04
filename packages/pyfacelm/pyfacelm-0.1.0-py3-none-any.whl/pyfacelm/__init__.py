"""
PyfaceLM: Python wrapper for OpenFace CLNF landmark detection.

Minimal dependencies wrapper around the C++ OpenFace binary (dlib-removed version).
Provides accurate facial landmark detection with 0px error and high confidence.
"""

from .detector import CLNFDetector, visualize_landmarks

__version__ = "0.1.0"
__all__ = ["CLNFDetector", "visualize_landmarks"]
