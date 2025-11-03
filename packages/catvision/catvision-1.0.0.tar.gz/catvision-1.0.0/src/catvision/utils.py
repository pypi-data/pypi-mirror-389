"""Utility functions for cat vision filter."""

import numpy as np
import cv2
from pathlib import Path
from typing import Union, Optional


def load_image(image_path: Union[str, Path]) -> Optional[np.ndarray]:
    """
    Load an image from file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Image as numpy array in BGR format, or None if loading fails
    """
    try:
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return None
        return image
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


def save_image(image: np.ndarray, output_path: Union[str, Path]) -> bool:
    """
    Save an image to file.
    
    Args:
        image: Image as numpy array
        output_path: Path to save the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = cv2.imwrite(str(output_path), image)
        if not success:
            print(f"Error: Could not save image to {output_path}")
        return success
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def validate_image(image: np.ndarray) -> bool:
    """
    Validate that an image is in the correct format.
    
    Args:
        image: Image to validate
        
    Returns:
        True if valid, False otherwise
    """
    if image is None:
        return False
    
    if not isinstance(image, np.ndarray):
        return False
    
    if image.size == 0:
        return False
    
    if len(image.shape) not in [2, 3]:
        return False
    
    if len(image.shape) == 3 and image.shape[2] not in [1, 3, 4]:
        return False
    
    return True


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image to 0-255 range as uint8.
    
    Args:
        image: Input image
        
    Returns:
        Normalized image
    """
    if image.dtype == np.uint8:
        return image
    
    # Normalize to 0-255
    img_min = np.min(image)
    img_max = np.max(image)
    
    if img_max - img_min < 1e-6:
        return np.zeros_like(image, dtype=np.uint8)
    
    normalized = ((image - img_min) / (img_max - img_min) * 255)
    return normalized.astype(np.uint8)


def create_test_image(size: tuple = (480, 640), pattern: str = 'checkerboard') -> np.ndarray:
    """
    Create a test image for validation and testing.
    
    Args:
        size: Image size as (height, width)
        pattern: Pattern type ('checkerboard', 'gradient', 'color_bars')
        
    Returns:
        Test image as numpy array
    """
    h, w = size
    
    if pattern == 'checkerboard':
        # Create checkerboard pattern
        image = np.zeros((h, w, 3), dtype=np.uint8)
        square_size = 40
        for i in range(0, h, square_size):
            for j in range(0, w, square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    image[i:i+square_size, j:j+square_size] = 255
        return image
    
    elif pattern == 'gradient':
        # Create horizontal gradient
        gradient = np.linspace(0, 255, w, dtype=np.uint8)
        image = np.tile(gradient, (h, 1))
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    elif pattern == 'color_bars':
        # Create RGB color bars
        image = np.zeros((h, w, 3), dtype=np.uint8)
        bar_width = w // 7
        
        # Colors: Black, Blue, Green, Cyan, Red, Magenta, Yellow, White
        colors = [
            (0, 0, 0), (255, 0, 0), (0, 255, 0), (255, 255, 0),
            (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)
        ]
        
        for i, color in enumerate(colors):
            start_x = i * bar_width
            end_x = min((i + 1) * bar_width, w)
            image[:, start_x:end_x] = color
        
        return image
    
    else:
        # Default: solid gray
        return np.full((h, w, 3), 128, dtype=np.uint8)
