"""Tests for temporal processing module."""

import pytest
import numpy as np
from catvision import CatVisionFilter


class TestModelTemporalProcessing:
    """Test temporal processing."""
    
    def test_temporal_returns_list(self, cat_filter, test_frame_sequence):
        """Test that temporal processing returns a list."""
        result = cat_filter.model_temporal_processing(test_frame_sequence)
        assert isinstance(result, list)
    
    def test_temporal_preserves_length(self, cat_filter, test_frame_sequence):
        """Test that sequence length is preserved."""
        result = cat_filter.model_temporal_processing(test_frame_sequence)
        assert len(result) == len(test_frame_sequence)
    
    def test_temporal_single_frame(self, cat_filter, test_image_color):
        """Test with single frame."""
        result = cat_filter.model_temporal_processing([test_image_color])
        assert len(result) == 1
    
    def test_temporal_empty_sequence(self, cat_filter):
        """Test with empty sequence."""
        result = cat_filter.model_temporal_processing([])
        assert result == []
    
    def test_temporal_preserves_shape(self, cat_filter, test_frame_sequence):
        """Test that frame shapes are preserved."""
        result = cat_filter.model_temporal_processing(test_frame_sequence)
        for orig, proc in zip(test_frame_sequence, result):
            assert proc.shape == orig.shape
    
    def test_temporal_different_fps(self, cat_filter, test_frame_sequence):
        """Test with different FPS values."""
        for fps in [24, 30, 60]:
            result = cat_filter.model_temporal_processing(test_frame_sequence, fps=fps)
            assert len(result) == len(test_frame_sequence)
    
    def test_temporal_grayscale_sequence(self, cat_filter):
        """Test with grayscale frames."""
        gray_sequence = [np.random.randint(0, 255, (100, 100), dtype=np.uint8) for _ in range(3)]
        result = cat_filter.model_temporal_processing(gray_sequence)
        assert len(result) == len(gray_sequence)


class TestTemporalSensitivityFunction:
    """Test temporal sensitivity function."""
    
    def test_sensitivity_at_zero(self, cat_filter):
        """Test sensitivity at 0 Hz."""
        sensitivity = cat_filter._temporal_sensitivity_function(0)
        assert sensitivity == 1.0
    
    def test_sensitivity_at_peak(self, cat_filter):
        """Test sensitivity at peak frequency."""
        sensitivity = cat_filter._temporal_sensitivity_function(10)
        assert sensitivity == 1.5
    
    def test_sensitivity_at_threshold(self, cat_filter):
        """Test sensitivity at flicker fusion threshold."""
        sensitivity = cat_filter._temporal_sensitivity_function(55)
        assert sensitivity == pytest.approx(1.0, rel=0.1)
    
    def test_sensitivity_above_threshold(self, cat_filter):
        """Test sensitivity above flicker fusion threshold."""
        sensitivity = cat_filter._temporal_sensitivity_function(80)
        assert sensitivity == 0.1
    
    def test_sensitivity_increasing_phase(self, cat_filter):
        """Test that sensitivity increases before peak."""
        s1 = cat_filter._temporal_sensitivity_function(2)
        s2 = cat_filter._temporal_sensitivity_function(5)
        s3 = cat_filter._temporal_sensitivity_function(10)
        assert s1 < s2 < s3
    
    def test_sensitivity_decreasing_phase(self, cat_filter):
        """Test that sensitivity decreases after peak."""
        s1 = cat_filter._temporal_sensitivity_function(10)
        s2 = cat_filter._temporal_sensitivity_function(30)
        s3 = cat_filter._temporal_sensitivity_function(55)
        assert s1 > s2 > s3
    
    def test_sensitivity_positive(self, cat_filter):
        """Test that sensitivity is always positive."""
        for freq in [0, 5, 10, 24, 55, 80, 100]:
            sensitivity = cat_filter._temporal_sensitivity_function(freq)
            assert sensitivity > 0
    
    def test_sensitivity_negative_frequency(self, cat_filter):
        """Test with negative frequency (edge case)."""
        sensitivity = cat_filter._temporal_sensitivity_function(-1)
        assert sensitivity == 1.0
