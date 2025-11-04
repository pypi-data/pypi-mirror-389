"""Utility functions for Terminal Media Player"""

import os
import sys

def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import PIL
    except ImportError:
        missing.append("Pillow")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print("Error: Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install " + " ".join(missing))
        return False
    
    return True

def get_supported_formats():
    """Get list of supported file formats"""
    video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    return {
        'video': video_formats,
        'image': image_formats
    }