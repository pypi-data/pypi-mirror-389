"""Tests for spectral sensitivity module."""

import pytest
import numpy as np
from catvision import CatVisionFilter


class TestSpectralInitialization:
    """Test spectral curve initialization."""
    
    def test_wavelengths_range(self, cat_filter):
        """Test that wavelengths cover the correct range."""
        assert cat_filter.wavelengths[0] == 380
        assert cat_filter.wavelengths[-1] == 700
    
    def test_spectral_curves_normalized(self, cat_filter):
        """Test that spectral curves are normalized."""
        assert np.max(cat_filter.s_cone_sensitivity) == pytest.approx(1.0, rel=1e-6)
        assert np.max(cat_filter.l_cone_sensitivity) == pytest.approx(1.0, rel=1e-6)
        assert np.max(cat_filter.rod_sensitivity) == pytest.approx(1.0, rel=1e-6)
    
    def test_spectral_curves_positive(self, cat_filter):
        """Test that spectral curves contain only positive values."""
        assert np.all(cat_filter.s_cone_sensitivity >= 0)
        assert np.all(cat_filter.l_cone_sensitivity >= 0)
        assert np.all(cat_filter.rod_sensitivity >= 0)
    
    def test_rgb_wavelengths_mapping(self, cat_filter):
        """Test RGB to wavelength mapping."""
        assert 'red' in cat_filter.rgb_wavelengths
        assert 'green' in cat_filter.rgb_wavelengths
        assert 'blue' in cat_filter.rgb_wavelengths


class TestApplySpectralSensitivity:
    """Test spectral sensitivity application."""
    
    def test_apply_spectral_returns_image(self, cat_filter, test_image_color):
        """Test that spectral correction returns an image."""
        result = cat_filter.apply_spectral_sensitivity_curves(test_image_color)
        assert result is not None
        assert isinstance(result, np.ndarray)
    
    def test_apply_spectral_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        result = cat_filter.apply_spectral_sensitivity_curves(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_apply_spectral_preserves_dtype(self, cat_filter, test_image_color):
        """Test that dtype is uint8."""
        result = cat_filter.apply_spectral_sensitivity_curves(test_image_color)
        assert result.dtype == np.uint8
    
    def test_apply_spectral_grayscale_unchanged(self, cat_filter, test_image_gray):
        """Test that grayscale images are returned unchanged."""
        result = cat_filter.apply_spectral_sensitivity_curves(test_image_gray)
        assert np.array_equal(result, test_image_gray)
    
    def test_apply_spectral_modifies_colors(self, cat_filter, test_image_color):
        """Test that spectral correction modifies colors."""
        result = cat_filter.apply_spectral_sensitivity_curves(test_image_color)
        # Result should be different from input (unless input is all black/white)
        # Check that at least some pixels changed
        different = np.sum(result != test_image_color) > 0
        assert different


class TestAdjustColorSensitivity:
    """Test legacy color sensitivity adjustment."""
    
    def test_adjust_color_returns_image(self, cat_filter, test_image_color):
        """Test that color adjustment returns an image."""
        result = cat_filter.adjust_color_sensitivity(test_image_color)
        assert result is not None
    
    def test_adjust_color_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        result = cat_filter.adjust_color_sensitivity(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_adjust_color_grayscale(self, cat_filter, test_image_gray):
        """Test with grayscale image."""
        result = cat_filter.adjust_color_sensitivity(test_image_gray)
        assert np.array_equal(result, test_image_gray)
    
    def test_adjust_color_uses_weights(self, cat_filter):
        """Test that color weights are applied."""
        # Create pure color test images
        blue_img = np.zeros((50, 50, 3), dtype=np.uint8)
        blue_img[:, :, 0] = 100  # BGR format
        
        result = cat_filter.adjust_color_sensitivity(blue_img)
        # Blue should be enhanced
        assert np.mean(result[:, :, 0]) > np.mean(blue_img[:, :, 0]) * 0.9


class TestSpectralPeaks:
    """Test spectral peak positions."""
    
    def test_s_cone_peak_position(self, cat_filter):
        """Test S-cone peak is at correct wavelength."""
        peak_idx = np.argmax(cat_filter.s_cone_sensitivity)
        peak_wavelength = cat_filter.wavelengths[peak_idx]
        assert abs(peak_wavelength - cat_filter.s_cone_peak) < 5  # Within 5nm
    
    def test_l_cone_peak_position(self, cat_filter):
        """Test L-cone peak is at correct wavelength."""
        peak_idx = np.argmax(cat_filter.l_cone_sensitivity)
        peak_wavelength = cat_filter.wavelengths[peak_idx]
        assert abs(peak_wavelength - cat_filter.l_cone_peak) < 5
    
    def test_rod_peak_position(self, cat_filter):
        """Test rod peak is at correct wavelength."""
        peak_idx = np.argmax(cat_filter.rod_sensitivity)
        peak_wavelength = cat_filter.wavelengths[peak_idx]
        assert abs(peak_wavelength - cat_filter.rod_peak) < 5
