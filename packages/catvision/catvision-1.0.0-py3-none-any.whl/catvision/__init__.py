"""
catvision - Biologically Accurate Cat Vision Filter

A Python package that replicates the biologically accurate vision of cats
based on peer-reviewed research on feline retinal structure and visual characteristics.

Key Features:
- Vertical slit pupil (3:1 aspect ratio)
- Enhanced blue-green sensitivity (~500nm peak)
- Rod-dominated vision (25:1 rod/cone ratio)
- Tapetum lucidum light reflection
- Reduced color discrimination
- Enhanced motion detection
- Wide field of view (200°×140°)
- Reduced spatial acuity (1/6 human)
- Enhanced temporal processing (55Hz flicker fusion)

Example:
    >>> from catvision import CatVisionFilter
    >>> import cv2
    >>> 
    >>> # Load an image
    >>> image = cv2.imread('input.jpg')
    >>> 
    >>> # Initialize the filter
    >>> cat_filter = CatVisionFilter()
    >>> 
    >>> # Apply cat vision transformation
    >>> result = cat_filter.apply_cat_vision(image, use_biological_accuracy=True)
    >>> 
    >>> # Save the result
    >>> cv2.imwrite('cat_vision_output.jpg', result)
"""

from catvision.__version__ import __version__, __author__, __email__
from catvision.core import CatVisionFilter

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "CatVisionFilter",
]
