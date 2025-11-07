"""
SIFT Feature Descriptor Module
Provides functions for SIFT (Scale-Invariant Feature Transform) 
feature detection and description.
"""

import cv2
import numpy as np
import urllib.request


def load_image_from_url(url):
    """Load image from URL."""
    try:
        resp = urllib.request.urlopen(url)
        img_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


def detect_sift_features(img, nfeatures=0):
    """
    Detect SIFT keypoints and compute descriptors.
    
    Args:
        img: Input image
        nfeatures: Number of best features to retain (0 = all)
    
    Returns:
        Tuple of (keypoints, descriptors)
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    sift = cv2.SIFT_create(nfeatures=nfeatures)
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    
    return keypoints, descriptors


def draw_sift_keypoints(img, keypoints, flags=None):
    """
    Draw SIFT keypoints on image.
    
    Args:
        img: Input image
        keypoints: Detected keypoints
        flags: Drawing flags
    
    Returns:
        Image with keypoints drawn
    """
    if flags is None:
        flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
    
    img_keypoints = cv2.drawKeypoints(img, keypoints, None, flags=flags)
    return img_keypoints


def sift_pipeline(img=None, nfeatures=0, save_results=False):
    """
    Complete SIFT feature detection pipeline.
    
    Args:
        img: Input image (if None, downloads sample)
        nfeatures: Number of features to detect (0 = all)
        save_results: Whether to save output
    
    Returns:
        Tuple of (keypoints, descriptors, img_with_keypoints)
    """
    if img is None:
        print("Downloading sample image...")
        url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/box.png"
        img = load_image_from_url(url)
        
        if img is None:
            print("Error: Could not load image.")
            return None, None, None
        
        print("Image downloaded successfully!")
    
    # Detect SIFT features
    keypoints, descriptors = detect_sift_features(img, nfeatures)
    
    print(f"Keypoints detected: {len(keypoints)}")
    if descriptors is not None:
        print(f"Descriptor shape: {descriptors.shape}")  # (N x 128)
    
    # Draw keypoints
    img_keypoints = draw_sift_keypoints(img, keypoints)
    
    if save_results:
        cv2.imwrite("sift_keypoints.jpg", img_keypoints)
        if descriptors is not None:
            np.save("sift_descriptors.npy", descriptors)
        print("\nSaved: sift_keypoints.jpg, sift_descriptors.npy")
    
    return keypoints, descriptors, img_keypoints


def match_sift_features(img1, img2, ratio_threshold=0.75):
    """
    Match SIFT features between two images.
    
    Args:
        img1: First image
        img2: Second image
        ratio_threshold: Lowe's ratio test threshold
    
    Returns:
        Tuple of (good_matches, keypoints1, keypoints2)
    """
    # Detect features
    kp1, des1 = detect_sift_features(img1)
    kp2, des2 = detect_sift_features(img2)
    
    # Match features
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    
    # Apply Lowe's ratio test
    good = []
    for m, n in matches:
        if m.distance < ratio_threshold * n.distance:
            good.append(m)
    
    print(f"Found {len(good)} good matches out of {len(matches)} total matches")
    
    return good, kp1, kp2


def demo():
    """Run a demonstration of SIFT feature detection."""
    print("=== SIFT Feature Descriptor Demo ===")
    sift_pipeline(save_results=True)


if __name__ == "__main__":
    demo()
