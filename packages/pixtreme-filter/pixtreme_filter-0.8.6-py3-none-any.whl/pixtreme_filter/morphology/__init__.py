"""Morphological operations for image processing

This module provides GPU-accelerated morphological operations including:
- Erosion: Shrinks white regions
- Dilation: Expands white regions
- Opening: Removes noise
- Closing: Fills holes
- Gradient: Detects edges
- Top Hat: Extracts bright features
- Black Hat: Extracts dark features
"""

from .dilate import create_dilate_kernel, dilate
from .erode import create_erode_kernel, erode
from .operations import (
    morphology_blackhat,
    morphology_close,
    morphology_gradient,
    morphology_open,
    morphology_tophat,
)

__all__ = [
    "erode",
    "create_erode_kernel",
    "dilate",
    "create_dilate_kernel",
    "morphology_open",
    "morphology_close",
    "morphology_gradient",
    "morphology_tophat",
    "morphology_blackhat",
]
