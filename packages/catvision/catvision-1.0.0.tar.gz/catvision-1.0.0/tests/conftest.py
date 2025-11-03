"""Pytest configuration and fixtures."""

import pytest
import numpy as np
import cv2
from catvision import CatVisionFilter
from catvision.utils import create_test_image


@pytest.fixture
def cat_filter():
    """Create a CatVisionFilter instance for testing."""
    return CatVisionFilter()


@pytest.fixture
def test_image_gray():
    """Create a grayscale test image."""
    return create_test_image((480, 640), 'gradient')[:, :, 0]


@pytest.fixture
def test_image_color():
    """Create a color test image."""
    return create_test_image((480, 640), 'checkerboard')


@pytest.fixture
def test_image_small():
    """Create a small test image for quick tests."""
    return create_test_image((100, 100), 'checkerboard')


@pytest.fixture
def test_frame_sequence():
    """Create a sequence of test frames."""
    frames = []
    for i in range(5):
        # Create frames with slight variations
        img = create_test_image((240, 320), 'checkerboard')
        # Add some variation
        noise = np.random.randint(-10, 10, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        frames.append(img)
    return frames


@pytest.fixture
def test_image_list(test_image_color, test_image_small):
    """Create a list of test images."""
    return [test_image_color, test_image_small]
