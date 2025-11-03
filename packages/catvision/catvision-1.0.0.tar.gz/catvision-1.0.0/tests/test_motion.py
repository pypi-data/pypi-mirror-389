"""Tests for motion detection module."""

import pytest
import numpy as np
from catvision import CatVisionFilter


class TestEnhancedMotionDetection:
    """Test enhanced motion detection."""
    
    def test_motion_returns_list(self, cat_filter, test_frame_sequence):
        """Test that motion detection returns a list."""
        result = cat_filter.enhanced_motion_detection(test_frame_sequence)
        assert isinstance(result, list)
    
    def test_motion_preserves_length(self, cat_filter, test_frame_sequence):
        """Test that sequence length is preserved."""
        result = cat_filter.enhanced_motion_detection(test_frame_sequence)
        assert len(result) == len(test_frame_sequence)
    
    def test_motion_single_frame(self, cat_filter, test_image_color):
        """Test with single frame."""
        result = cat_filter.enhanced_motion_detection([test_image_color])
        assert len(result) == 1
    
    def test_motion_empty_sequence(self, cat_filter):
        """Test with empty sequence."""
        result = cat_filter.enhanced_motion_detection([])
        assert result == []
    
    def test_motion_preserves_shape(self, cat_filter, test_frame_sequence):
        """Test that frame shapes are preserved."""
        result = cat_filter.enhanced_motion_detection(test_frame_sequence)
        for orig, proc in zip(test_frame_sequence, result):
            assert proc.shape == orig.shape
    
    def test_motion_different_flow_methods(self, cat_filter, test_frame_sequence):
        """Test with different optical flow methods."""
        for method in ['lucas_kanade', 'farneback']:
            result = cat_filter.enhanced_motion_detection(test_frame_sequence, flow_method=method)
            assert len(result) == len(test_frame_sequence)
    
    def test_motion_grayscale_sequence(self, cat_filter):
        """Test with grayscale frames."""
        gray_sequence = [np.random.randint(0, 255, (100, 100), dtype=np.uint8) for _ in range(3)]
        result = cat_filter.enhanced_motion_detection(gray_sequence)
        assert len(result) == len(gray_sequence)


class TestLucasKanadeFlow:
    """Test Lucas-Kanade optical flow."""
    
    def test_lucas_kanade_returns_array_or_none(self, cat_filter):
        """Test that Lucas-Kanade returns array or None."""
        frame1 = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        frame2 = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = cat_filter._lucas_kanade_flow(frame1, frame2)
        assert result is None or isinstance(result, np.ndarray)
    
    def test_lucas_kanade_with_features(self, cat_filter, test_image_color):
        """Test Lucas-Kanade with image containing features."""
        gray = test_image_color[:, :, 0]
        frame1 = gray.copy()
        # Create shifted version
        frame2 = np.roll(gray, 5, axis=1)
        result = cat_filter._lucas_kanade_flow(frame1, frame2)
        # May return None if no features detected, which is acceptable
        if result is not None:
            assert isinstance(result, np.ndarray)


class TestAnalyzeMotion:
    """Test motion analysis."""
    
    def test_analyze_empty_vectors(self, cat_filter):
        """Test with empty flow vectors."""
        magnitude, direction = cat_filter._analyze_motion(np.array([]))
        assert len(magnitude) == 0
        assert len(direction) == 0
    
    def test_analyze_motion_shape(self, cat_filter):
        """Test that output shapes match."""
        flow_vectors = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        magnitude, direction = cat_filter._analyze_motion(flow_vectors)
        assert len(magnitude) == len(flow_vectors)
        assert len(direction) == len(flow_vectors)
    
    def test_analyze_motion_magnitude_positive(self, cat_filter):
        """Test that magnitudes are positive."""
        flow_vectors = np.array([[1.0, 2.0], [-3.0, 4.0]])
        magnitude, direction = cat_filter._analyze_motion(flow_vectors)
        assert np.all(magnitude >= 0)
    
    def test_analyze_motion_direction_range(self, cat_filter):
        """Test that directions are in valid range."""
        flow_vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
        magnitude, direction = cat_filter._analyze_motion(flow_vectors)
        assert np.all(direction >= -np.pi)
        assert np.all(direction <= np.pi)


class TestDirectionalSensitivity:
    """Test directional sensitivity calculation."""
    
    def test_directional_empty_array(self, cat_filter):
        """Test with empty directions."""
        weight = cat_filter._calculate_directional_sensitivity(np.array([]))
        assert weight == 1.0
    
    def test_directional_horizontal_motion(self, cat_filter):
        """Test with horizontal motion (0° and 180°)."""
        directions = np.array([0.0, np.pi])  # Horizontal
        weight = cat_filter._calculate_directional_sensitivity(directions)
        # Should be enhanced
        assert weight > 1.0
    
    def test_directional_vertical_motion(self, cat_filter):
        """Test with vertical motion (90° and 270°)."""
        directions = np.array([np.pi/2, -np.pi/2])  # Vertical
        weight = cat_filter._calculate_directional_sensitivity(directions)
        # Should be less enhanced
        assert weight >= 1.0
    
    def test_directional_weight_bounds(self, cat_filter):
        """Test that weight is within reasonable bounds."""
        for angle in np.linspace(-np.pi, np.pi, 20):
            directions = np.array([angle])
            weight = cat_filter._calculate_directional_sensitivity(directions)
            assert 1.0 <= weight <= cat_filter.horizontal_motion_bias


class TestApplyMotionEnhancement:
    """Test motion enhancement application."""
    
    def test_enhancement_empty_magnitude(self, cat_filter, test_image_color):
        """Test with empty motion magnitude."""
        result = cat_filter._apply_motion_enhancement(test_image_color, np.array([]), 1.0)
        assert np.array_equal(result, test_image_color)
    
    def test_enhancement_preserves_shape(self, cat_filter, test_image_color):
        """Test that shape is preserved."""
        magnitude = np.array([1.0, 2.0, 3.0])
        result = cat_filter._apply_motion_enhancement(test_image_color, magnitude, 1.5)
        assert result.shape == test_image_color.shape
    
    def test_enhancement_dtype(self, cat_filter, test_image_color):
        """Test that dtype is uint8."""
        magnitude = np.array([1.0, 2.0, 3.0])
        result = cat_filter._apply_motion_enhancement(test_image_color, magnitude, 1.5)
        assert result.dtype == np.uint8


class TestEnhanceMotionLegacy:
    """Test legacy motion enhancement."""
    
    def test_legacy_without_previous_frame(self, cat_filter, test_image_color):
        """Test legacy method without previous frame."""
        result = cat_filter.enhance_motion_detection(test_image_color, None)
        assert np.array_equal(result, test_image_color)
    
    def test_legacy_with_previous_frame(self, cat_filter, test_image_color):
        """Test legacy method with previous frame."""
        prev_frame = test_image_color.copy()
        result = cat_filter.enhance_motion_detection(test_image_color, prev_frame)
        assert result.shape == test_image_color.shape
    
    def test_legacy_grayscale(self, cat_filter, test_image_gray):
        """Test legacy method with grayscale."""
        prev_frame = test_image_gray.copy()
        result = cat_filter.enhance_motion_detection(test_image_gray, prev_frame)
        assert result.shape == test_image_gray.shape
