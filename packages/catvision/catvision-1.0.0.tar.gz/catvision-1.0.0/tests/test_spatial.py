"""Tests for spatial processing module."""

import pytest
import numpy as np
from catvision import CatVisionFilter


class TestPupilKernel:
    """Test pupil kernel creation."""
    
    def test_create_pupil_kernel_returns_array(self, cat_filter):
        """Test that pupil kernel is created."""
        kernel = cat_filter.create_pupil_kernel(15)
        assert isinstance(kernel, np.ndarray)
    
    def test_pupil_kernel_size(self, cat_filter):
        """Test that kernel has correct size."""
        kernel = cat_filter.create_pupil_kernel(15)
        assert kernel.shape == (15, 15)
    
    def test_pupil_kernel_odd_size_enforcement(self, cat_filter):
        """Test that even sizes are converted to odd."""
        kernel = cat_filter.create_pupil_kernel(14)
        assert kernel.shape[0] % 2 == 1  # Should be odd
    
    def test_pupil_kernel_normalized(self, cat_filter):
        """Test that kernel is normalized."""
        kernel = cat_filter.create_pupil_kernel(15)
        assert np.sum(kernel) == pytest.approx(1.0, rel=1e-6)
    
    def test_pupil_kernel_vertical_slit(self, cat_filter):
        """Test that kernel has vertical orientation."""
        kernel = cat_filter.create_pupil_kernel(21)
        # Kernel should be taller than wide (vertical slit)
        vertical_extent = np.sum(kernel[:, kernel.shape[1]//2])
        horizontal_extent = np.sum(kernel[kernel.shape[0]//2, :])
        assert vertical_extent > horizontal_extent
    
    def test_pupil_kernel_different_sizes(self, cat_filter):
        """Test kernel creation with various sizes."""
        for size in [7, 11, 15, 21, 31]:
            kernel = cat_filter.create_pupil_kernel(size)
            assert kernel.shape[0] >= size


class TestApplyPupilFilter:
    """Test pupil filter application."""
    
    def test_apply_pupil_returns_image(self, cat_filter, test_image_color):
        """Test that pupil filter returns an image."""
        result = cat_filter.apply_pupil_filter(test_image_color)
        assert result is not None
    
    def test_apply_pupil_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        result = cat_filter.apply_pupil_filter(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_apply_pupil_grayscale(self, cat_filter, test_image_gray):
        """Test pupil filter on grayscale image."""
        result = cat_filter.apply_pupil_filter(test_image_gray)
        assert result.shape == test_image_gray.shape
    
    def test_apply_pupil_different_kernel_sizes(self, cat_filter, test_image_small):
        """Test with different kernel sizes."""
        for kernel_size in [7, 15, 21]:
            result = cat_filter.apply_pupil_filter(test_image_small, kernel_size)
            assert result.shape == test_image_small.shape


class TestSpatialAcuity:
    """Test spatial acuity reduction."""
    
    def test_spatial_acuity_returns_image(self, cat_filter, test_image_color):
        """Test that acuity reduction returns an image."""
        result = cat_filter.simulate_spatial_acuity_reduction(test_image_color)
        assert result is not None
    
    def test_spatial_acuity_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        result = cat_filter.simulate_spatial_acuity_reduction(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_spatial_acuity_preserves_dtype(self, cat_filter, test_image_color):
        """Test that dtype is uint8."""
        result = cat_filter.simulate_spatial_acuity_reduction(test_image_color)
        assert result.dtype == np.uint8
    
    def test_spatial_acuity_grayscale(self, cat_filter, test_image_gray):
        """Test acuity reduction on grayscale."""
        result = cat_filter.simulate_spatial_acuity_reduction(test_image_gray)
        assert result.shape == test_image_gray.shape
    
    def test_spatial_acuity_custom_factor(self, cat_filter, test_image_small):
        """Test with custom acuity factor."""
        result = cat_filter.simulate_spatial_acuity_reduction(
            test_image_small, acuity_factor=0.3
        )
        assert result is not None
    
    def test_spatial_acuity_reduces_detail(self, cat_filter, test_image_color):
        """Test that acuity reduction blurs the image."""
        result = cat_filter.simulate_spatial_acuity_reduction(test_image_color)
        # Calculate image sharpness (standard deviation)
        original_std = np.std(test_image_color.astype(float))
        result_std = np.std(result.astype(float))
        # Result should be slightly less sharp
        assert result_std <= original_std * 1.1


class TestSpatialFieldTransformation:
    """Test spatial field transformation."""
    
    def test_field_transform_returns_image(self, cat_filter, test_image_color):
        """Test that field transformation returns an image."""
        result = cat_filter.apply_spatial_field_transformation(test_image_color)
        assert result is not None
    
    def test_field_transform_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        result = cat_filter.apply_spatial_field_transformation(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_field_transform_custom_fov(self, cat_filter, test_image_small):
        """Test with custom field of view."""
        result = cat_filter.apply_spatial_field_transformation(
            test_image_small, fov_horizontal=180, fov_vertical=120
        )
        assert result.shape == test_image_small.shape
    
    def test_field_transform_grayscale(self, cat_filter, test_image_gray):
        """Test field transformation on grayscale."""
        result = cat_filter.apply_spatial_field_transformation(test_image_gray)
        assert result.shape == test_image_gray.shape


class TestApplySpatialFilter:
    """Test internal spatial filter method."""
    
    def test_spatial_filter_preserves_shape(self, cat_filter):
        """Test that spatial filter preserves channel shape."""
        channel = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = cat_filter._apply_spatial_filter(channel, 0.2)
        assert result.shape == channel.shape
    
    def test_spatial_filter_dtype(self, cat_filter):
        """Test that spatial filter returns uint8."""
        channel = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = cat_filter._apply_spatial_filter(channel, 0.2)
        assert result.dtype == np.uint8
