"""
SURF and HOG Feature Descriptor Module
Provides functions for SURF (using SIFT as alternative) and 
HOG (Histogram of Oriented Gradients) feature descriptors.
"""

import cv2
import numpy as np
import urllib.request
import matplotlib.pyplot as plt


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


def detect_surf_features(img, nfeatures=0):
    """
    Detect SURF-like features using SIFT (SURF is patented).
    
    Args:
        img: Input image
        nfeatures: Number of features to retain (0 = all)
    
    Returns:
        Tuple of (keypoints, descriptors)
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Using SIFT as SURF alternative
    sift = cv2.SIFT_create(nfeatures=nfeatures)
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    
    return keypoints, descriptors


def compute_hog_descriptor(img, win_size=(64, 128), visualize=False):
    """
    Compute HOG (Histogram of Oriented Gradients) descriptor.
    
    Args:
        img: Input image
        win_size: Window size for HOG (width, height)
        visualize: Whether to return visualization (not supported in cv2)
    
    Returns:
        HOG descriptor array
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Resize image to standard HOG window size
    img_resized = cv2.resize(gray, win_size)
    
    # Create HOG descriptor
    hog = cv2.HOGDescriptor()
    descriptor = hog.compute(img_resized)
    
    return descriptor


def detect_people_hog(img):
    """
    Detect people in image using HOG descriptor.
    
    Args:
        img: Input image
    
    Returns:
        Tuple of (detected_boxes, img_with_detections)
    """
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # Detect people
    boxes, weights = hog.detectMultiScale(img, winStride=(8, 8), padding=(8, 8), scale=1.05)
    
    # Draw bounding boxes
    img_detected = img.copy()
    for (x, y, w, h) in boxes:
        cv2.rectangle(img_detected, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    return boxes, img_detected


def surf_hog_pipeline(img=None, save_results=False, display=True):
    """
    Complete SURF and HOG feature extraction pipeline.
    
    Args:
        img: Input image (if None, downloads sample)
        save_results: Whether to save outputs
        display: Whether to display results
    
    Returns:
        Dictionary containing SURF and HOG results
    """
    if img is None:
        print("Downloading sample image...")
        url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/box.png"
        img = load_image_from_url(url)
        
        if img is None:
            print("Error: Could not load image.")
            return None
        
        print("Image loaded successfully!")
    
    print(f"Image shape: {img.shape}")
    
    # SURF (SIFT) feature detection
    kp, des = detect_surf_features(img)
    print(f"SIFT Keypoints Detected: {len(kp)}")
    
    # Draw keypoints
    img_kp = cv2.drawKeypoints(img, kp, None, 
                               flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    
    # HOG descriptor computation
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    hog = compute_hog_descriptor(gray)
    print(f"HOG Shape: {hog.shape}")
    
    results = {
        'sift_keypoints': kp,
        'sift_descriptors': des,
        'sift_image': img_kp,
        'hog_descriptor': hog
    }
    
    if display:
        plt.figure(figsize=(6, 6))
        plt.imshow(cv2.cvtColor(img_kp, cv2.COLOR_BGR2RGB))
        plt.title("SIFT Keypoints")
        plt.axis('off')
        plt.show()
    
    if save_results:
        cv2.imwrite("sift_keypoints.jpg", img_kp)
        if des is not None:
            np.save("sift_descriptors.npy", des)
        np.save("hog_descriptor.npy", hog)
        print("\nSaved: sift_keypoints.jpg, sift_descriptors.npy, hog_descriptor.npy")
    
    return results


def demo():
    """Run a demonstration of SURF and HOG descriptors."""
    print("=== SURF and HOG Feature Descriptor Demo ===")
    surf_hog_pipeline(save_results=True, display=False)


if __name__ == "__main__":
    demo()
