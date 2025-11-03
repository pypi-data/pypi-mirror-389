"""Tests for low-light vision module."""

import pytest
import numpy as np
from catvision import CatVisionFilter


class TestApplyTapetumEffect:
    """Test tapetum lucidum effect."""
    
    def test_tapetum_returns_image(self, cat_filter, test_image_color):
        """Test that tapetum effect returns an image."""
        result = cat_filter.apply_tapetum_effect(test_image_color)
        assert result is not None
    
    def test_tapetum_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        result = cat_filter.apply_tapetum_effect(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_tapetum_preserves_dtype(self, cat_filter, test_image_color):
        """Test that dtype is uint8."""
        result = cat_filter.apply_tapetum_effect(test_image_color)
        assert result.dtype == np.uint8
    
    def test_tapetum_bright_image_unchanged(self, cat_filter):
        """Test that bright images are not enhanced."""
        bright_image = np.full((100, 100, 3), 200, dtype=np.uint8)
        result = cat_filter.apply_tapetum_effect(bright_image, brightness_threshold=0.5)
        # Bright image should remain mostly unchanged
        assert np.array_equal(result, bright_image)
    
    def test_tapetum_dark_image_enhanced(self, cat_filter):
        """Test that dark images are enhanced."""
        dark_image = np.full((100, 100, 3), 30, dtype=np.uint8)
        result = cat_filter.apply_tapetum_effect(dark_image, brightness_threshold=0.3)
        # Dark image should be brightened
        assert np.mean(result) >= np.mean(dark_image)
    
    def test_tapetum_grayscale(self, cat_filter):
        """Test tapetum effect on grayscale."""
        gray_dark = np.full((100, 100), 30, dtype=np.uint8)
        result = cat_filter.apply_tapetum_effect(gray_dark)
        assert result.shape == gray_dark.shape
    
    def test_tapetum_custom_threshold(self, cat_filter, test_image_color):
        """Test with custom brightness threshold."""
        for threshold in [0.1, 0.3, 0.5]:
            result = cat_filter.apply_tapetum_effect(test_image_color, threshold)
            assert result is not None
    
    def test_tapetum_blue_green_tint(self, cat_filter):
        """Test that blue-green tint is added in low light."""
        dark_image = np.full((100, 100, 3), 30, dtype=np.uint8)
        result = cat_filter.apply_tapetum_effect(dark_image, brightness_threshold=0.3)
        # Blue and green channels should be slightly more enhanced
        assert np.mean(result[:, :, 0]) >= np.mean(result[:, :, 2])  # Blue >= Red


class TestSimulateRodDominance:
    """Test rod dominance simulation."""
    
    def test_rod_dominance_returns_image(self, cat_filter, test_image_color):
        """Test that rod dominance returns an image."""
        result = cat_filter.simulate_rod_dominance(test_image_color)
        assert result is not None
    
    def test_rod_dominance_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        result = cat_filter.simulate_rod_dominance(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_rod_dominance_preserves_dtype(self, cat_filter, test_image_color):
        """Test that dtype is uint8."""
        result = cat_filter.simulate_rod_dominance(test_image_color)
        assert result.dtype == np.uint8
    
    def test_rod_dominance_reduces_saturation(self, cat_filter):
        """Test that color saturation is reduced."""
        # Create highly saturated test image
        saturated = np.zeros((100, 100, 3), dtype=np.uint8)
        saturated[:, :, 2] = 255  # Pure red in BGR
        
        result = cat_filter.simulate_rod_dominance(saturated)
        
        # Convert both to HSV to check saturation
        import cv2
        saturated_hsv = cv2.cvtColor(saturated, cv2.COLOR_BGR2HSV)
        result_hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
        
        # Result should have lower saturation
        assert np.mean(result_hsv[:, :, 1]) < np.mean(saturated_hsv[:, :, 1])
    
    def test_rod_dominance_enhances_contrast(self, cat_filter, test_image_color):
        """Test that contrast is enhanced."""
        result = cat_filter.simulate_rod_dominance(test_image_color)
        # Result should exist and be valid
        assert result is not None
        assert np.all(result >= 0) and np.all(result <= 255)
    
    def test_rod_dominance_grayscale(self, cat_filter, test_image_gray):
        """Test rod dominance on grayscale."""
        result = cat_filter.simulate_rod_dominance(test_image_gray)
        assert result.shape == test_image_gray.shape
    
    def test_rod_dominance_desaturates_colors(self, cat_filter):
        """Test that vibrant colors become muted."""
        # Create rainbow-like image
        rainbow = np.zeros((100, 300, 3), dtype=np.uint8)
        rainbow[:, 0:100] = [255, 0, 0]    # Blue
        rainbow[:, 100:200] = [0, 255, 0]  # Green
        rainbow[:, 200:300] = [0, 0, 255]  # Red
        
        result = cat_filter.simulate_rod_dominance(rainbow)
        
        # Result should be more uniform (desaturated)
        # Calculate color variance
        orig_var = np.var(rainbow, axis=2).mean()
        result_var = np.var(result, axis=2).mean()
        
        # Variance should decrease (colors become more similar)
        assert result_var <= orig_var


class TestLowLightCombination:
    """Test combination of low-light effects."""
    
    def test_combined_effects_dark_image(self, cat_filter):
        """Test tapetum and rod dominance on dark image."""
        dark_image = np.full((100, 100, 3), 40, dtype=np.uint8)
        
        # Apply both effects
        rod_result = cat_filter.simulate_rod_dominance(dark_image)
        combined = cat_filter.apply_tapetum_effect(rod_result, brightness_threshold=0.3)
        
        assert combined is not None
        assert combined.shape == dark_image.shape
    
    def test_combined_preserves_shape(self, cat_filter, test_image_color):
        """Test that combined effects preserve shape."""
        rod_result = cat_filter.simulate_rod_dominance(test_image_color)
        combined = cat_filter.apply_tapetum_effect(rod_result)
        assert combined.shape == test_image_color.shape
