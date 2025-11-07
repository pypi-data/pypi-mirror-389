"""
Fundamental Matrix Computation Module
Provides functions to compute fundamental matrix from stereo images
and draw epipolar lines.
"""

import cv2
import numpy as np
import urllib.request


def load_image_from_url(url):
    """
    Load image from URL.
    
    Args:
        url: Image URL
    
    Returns:
        Loaded image or None if failed
    """
    try:
        resp = urllib.request.urlopen(url)
        img_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


def detect_and_match_features(img1, img2, ratio_threshold=0.75):
    """
    Detect SIFT features and match them between two images.
    
    Args:
        img1: First image
        img2: Second image
        ratio_threshold: Lowe's ratio test threshold
    
    Returns:
        Tuple of (good_matches, pts1, pts2, kp1, kp2)
    """
    # Convert to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Detect SIFT keypoints and descriptors
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)
    
    # Match features
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    
    # Apply Lowe's ratio test
    good = []
    pts1 = []
    pts2 = []
    for m, n in matches:
        if m.distance < ratio_threshold * n.distance:
            good.append(m)
            pts1.append(kp1[m.queryIdx].pt)
            pts2.append(kp2[m.trainIdx].pt)
    
    pts1 = np.int32(pts1)
    pts2 = np.int32(pts2)
    
    return good, pts1, pts2, kp1, kp2


def compute_fundamental_matrix(pts1, pts2):
    """
    Compute fundamental matrix from matched points.
    
    Args:
        pts1: Points in first image
        pts2: Points in second image
    
    Returns:
        Tuple of (fundamental_matrix, mask)
    """
    F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC)
    return F, mask


def draw_epipolar_lines(img1, img2, lines, pts1, pts2):
    """
    Draw epipolar lines on images.
    
    Args:
        img1: First image
        img2: Second image
        lines: Epipolar lines
        pts1: Points in first image
        pts2: Points in second image
    
    Returns:
        Tuple of (img1_with_lines, img2_with_lines)
    """
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    img1_color = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
    img2_color = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)
    r, c = img1.shape[:2]
    
    for rline, pt1, pt2 in zip(lines, pts1, pts2):
        color = tuple(np.random.randint(0, 255, 3).tolist())
        x0, y0 = map(int, [0, -rline[2] / rline[1]])
        x1, y1 = map(int, [c, -(rline[2] + rline[0] * c) / rline[1]])
        cv2.line(img2_color, (x0, y0), (x1, y1), color, 1)
        cv2.circle(img1_color, tuple(pt1), 5, color, -1)
        cv2.circle(img2_color, tuple(pt2), 5, color, -1)
    
    return img1_color, img2_color


def fundamental_matrix_pipeline(img1=None, img2=None, save_results=False):
    """
    Complete fundamental matrix computation pipeline.
    
    Args:
        img1: First image (if None, downloads sample)
        img2: Second image (if None, downloads sample)
        save_results: Whether to save output images
    
    Returns:
        Tuple of (fundamental_matrix, matches_img, epilines_img1, epilines_img2)
    """
    # Load sample images if not provided
    if img1 is None or img2 is None:
        print("Downloading sample stereo images...")
        url_left = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/left01.jpg"
        url_right = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/right01.jpg"
        
        img1 = load_image_from_url(url_left)
        img2 = load_image_from_url(url_right)
        
        if img1 is None or img2 is None:
            print("Error: Couldn't load images.")
            return None, None, None, None
        
        print("Images loaded successfully.")
    
    # Detect and match features
    good, pts1, pts2, kp1, kp2 = detect_and_match_features(img1, img2)
    
    if len(good) < 8:
        print(f"Not enough matches found: {len(good)}")
        return None, None, None, None
    
    print(f"Found {len(good)} good matches")
    
    # Compute fundamental matrix
    F, mask = compute_fundamental_matrix(pts1, pts2)
    print("\nFundamental Matrix:")
    print(F)
    
    # Filter inliers
    pts1_in = pts1[mask.ravel() == 1]
    pts2_in = pts2[mask.ravel() == 1]
    
    # Compute epipolar lines
    lines1 = cv2.computeCorrespondEpilines(pts2_in.reshape(-1, 1, 2), 2, F)
    lines1 = lines1.reshape(-1, 3)
    
    # Draw epipolar lines
    img_epi1, img_epi2 = draw_epipolar_lines(img1, img2, lines1, pts1_in, pts2_in)
    
    # Draw matches
    matches_img = cv2.drawMatches(img1, kp1, img2, kp2, good, None, flags=2)
    
    if save_results:
        cv2.imwrite("matches.jpg", matches_img)
        cv2.imwrite("epilines_left.jpg", img_epi1)
        cv2.imwrite("epilines_right.jpg", img_epi2)
        np.save("fundamental_matrix.npy", F)
        print("\nSaved: matches.jpg, epilines_left.jpg, epilines_right.jpg, fundamental_matrix.npy")
    
    return F, matches_img, img_epi1, img_epi2


def demo():
    """Run a demonstration of fundamental matrix computation."""
    print("=== Fundamental Matrix Computation Demo ===")
    fundamental_matrix_pipeline(save_results=True)


if __name__ == "__main__":
    demo()
