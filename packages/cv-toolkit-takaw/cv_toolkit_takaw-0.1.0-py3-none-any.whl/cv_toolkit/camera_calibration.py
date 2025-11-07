"""
Camera Calibration Module
Provides functions for camera calibration and image undistortion.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import data, img_as_ubyte


def prepare_calibration_points(pattern_size=(6, 6)):
    """
    Prepare object points for calibration.
    
    Args:
        pattern_size: Tuple of (rows, cols) of inner corners in checkerboard
    
    Returns:
        Object points array
    """
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    return objp


def calibrate_camera(objpoints, imgpoints, image_size):
    """
    Perform camera calibration.
    
    Args:
        objpoints: List of object points
        imgpoints: List of image points
        image_size: Tuple of (width, height)
    
    Returns:
        Tuple of (ret, camera_matrix, distortion_coeffs, rvecs, tvecs)
    """
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, image_size, None, None
    )
    return ret, mtx, dist, rvecs, tvecs


def undistort_image(img, camera_matrix, dist_coeffs):
    """
    Undistort an image using camera calibration parameters.
    
    Args:
        img: Input image
        camera_matrix: Camera matrix from calibration
        dist_coeffs: Distortion coefficients from calibration
    
    Returns:
        Undistorted image
    """
    h, w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), 1, (w, h)
    )
    dst = cv2.undistort(img, camera_matrix, dist_coeffs, None, newcameramtx)
    return dst


def camera_calibration_demo(display=True):
    """
    Complete camera calibration demonstration using checkerboard image.
    
    Args:
        display: Whether to display results
    
    Returns:
        Tuple of (camera_matrix, dist_coeffs, undistorted_image)
    """
    # Load checkerboard image
    img = img_as_ubyte(data.checkerboard())
    h, w = img.shape
    
    # Prepare object points
    objp = prepare_calibration_points()
    
    # Simulate detected image points (scaled to image size)
    imgpoints = objp[:, :2] * (w / 6)
    imgpoints = imgpoints.reshape(-1, 1, 2).astype(np.float32)
    
    objpoints = [objp]
    imgpoints = [imgpoints]
    
    # Perform calibration
    ret, mtx, dist, rvecs, tvecs = calibrate_camera(objpoints, imgpoints, (w, h))
    
    # Undistort image
    dst = undistort_image(img, mtx, dist)
    
    if display:
        print("Camera Matrix:")
        print(mtx)
        print("\nDistortion Coefficients:")
        print(dist)
        
        plt.figure(figsize=(10, 5))
        
        plt.subplot(1, 2, 1)
        plt.imshow(img, cmap='gray')
        plt.title("Original")
        plt.axis('off')
        
        plt.subplot(1, 2, 2)
        plt.imshow(dst, cmap='gray')
        plt.title("Undistorted")
        plt.axis('off')
        
        plt.tight_layout()
        plt.show()
    
    return mtx, dist, dst


def demo():
    """Run a demonstration of camera calibration."""
    print("=== Camera Calibration Demo ===")
    camera_calibration_demo()


if __name__ == "__main__":
    demo()
