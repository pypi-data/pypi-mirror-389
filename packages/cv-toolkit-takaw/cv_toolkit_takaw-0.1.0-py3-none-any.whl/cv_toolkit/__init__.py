"""
CV Toolkit - A Computer Vision Library
=======================================

A comprehensive computer vision toolkit providing functionalities for:
- Image handling and processing
- Geometric transformations
- Homography and perspective transformations
- Camera calibration
- Fundamental matrix computation
- Edge, line, and corner detection
- Feature descriptors (SIFT, SURF, HOG)

Usage:
    from cv_toolkit import image_processing, geometric_transforms, feature_descriptors
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Import main modules
from . import image_processing
from . import geometric_transforms
from . import homography
from . import perspective_transform
from . import camera_calibration
from . import fundamental_matrix
from . import edge_line_corner_detection
from . import sift_descriptor
from . import surf_hog_descriptor

__all__ = [
    'image_processing',
    'geometric_transforms',
    'homography',
    'perspective_transform',
    'camera_calibration',
    'fundamental_matrix',
    'edge_line_corner_detection',
    'sift_descriptor',
    'surf_hog_descriptor'
]
