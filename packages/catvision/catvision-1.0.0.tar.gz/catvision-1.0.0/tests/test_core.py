"""Tests for core CatVisionFilter class."""

import pytest
import numpy as np
import cv2
import json
from pathlib import Path
from catvision import CatVisionFilter


class TestCatVisionFilterInit:
    """Test CatVisionFilter initialization."""
    
    def test_init_creates_instance(self):
        """Test that CatVisionFilter can be instantiated."""
        cat_filter = CatVisionFilter()
        assert cat_filter is not None
    
    def test_init_sets_biological_parameters(self, cat_filter):
        """Test that biological parameters are set correctly."""
        assert cat_filter.pupil_aspect_ratio == 3.0
        assert cat_filter.rod_cone_ratio == 25.0
        assert cat_filter.peak_wavelength == 500
        assert cat_filter.tapetum_reflectance == 0.3
        assert cat_filter.visual_field_h == 200
        assert cat_filter.visual_field_v == 140
    
    def test_init_sets_spectral_parameters(self, cat_filter):
        """Test that spectral parameters are set correctly."""
        assert cat_filter.s_cone_peak == 450
        assert cat_filter.l_cone_peak == 556
        assert cat_filter.rod_peak == 498
    
    def test_init_sets_spatial_parameters(self, cat_filter):
        """Test that spatial parameters are set correctly."""
        assert cat_filter.spatial_acuity_factor == 0.167
        assert cat_filter.foveal_acuity_cycles_per_degree == 3.0
    
    def test_init_sets_temporal_parameters(self, cat_filter):
        """Test that temporal parameters are set correctly."""
        assert cat_filter.flicker_fusion_threshold == 55
        assert cat_filter.temporal_sensitivity_peak == 10
    
    def test_init_sets_motion_parameters(self, cat_filter):
        """Test that motion parameters are set correctly."""
        assert cat_filter.motion_sensitivity == 1.8
        assert cat_filter.horizontal_motion_bias == 1.5
    
    def test_init_creates_spectral_curves(self, cat_filter):
        """Test that spectral curves are initialized."""
        assert hasattr(cat_filter, 'wavelengths')
        assert hasattr(cat_filter, 's_cone_sensitivity')
        assert hasattr(cat_filter, 'l_cone_sensitivity')
        assert hasattr(cat_filter, 'rod_sensitivity')
        assert len(cat_filter.wavelengths) == 321


class TestApplyCatVision:
    """Test apply_cat_vision method."""
    
    def test_apply_cat_vision_returns_image(self, cat_filter, test_image_color):
        """Test that apply_cat_vision returns an image."""
        result = cat_filter.apply_cat_vision(test_image_color)
        assert result is not None
        assert isinstance(result, np.ndarray)
    
    def test_apply_cat_vision_preserves_shape(self, cat_filter, test_image_color):
        """Test that output shape matches input shape."""
        result = cat_filter.apply_cat_vision(test_image_color)
        assert result.shape == test_image_color.shape
    
    def test_apply_cat_vision_preserves_dtype(self, cat_filter, test_image_color):
        """Test that output dtype is uint8."""
        result = cat_filter.apply_cat_vision(test_image_color)
        assert result.dtype == np.uint8
    
    def test_apply_cat_vision_biological_accuracy(self, cat_filter, test_image_color):
        """Test apply_cat_vision with biological accuracy enabled."""
        result = cat_filter.apply_cat_vision(
            test_image_color, use_biological_accuracy=True
        )
        assert result is not None
        assert result.shape == test_image_color.shape
    
    def test_apply_cat_vision_legacy_mode(self, cat_filter, test_image_color):
        """Test apply_cat_vision in legacy mode."""
        result = cat_filter.apply_cat_vision(
            test_image_color, use_biological_accuracy=False
        )
        assert result is not None
        assert result.shape == test_image_color.shape
    
    def test_apply_cat_vision_with_previous_frame(self, cat_filter, test_image_color):
        """Test apply_cat_vision with previous frame."""
        prev_frame = test_image_color.copy()
        result = cat_filter.apply_cat_vision(
            test_image_color, previous_frame=prev_frame, use_biological_accuracy=False
        )
        assert result is not None
    
    def test_apply_cat_vision_different_kernel_sizes(self, cat_filter, test_image_small):
        """Test apply_cat_vision with different kernel sizes."""
        for kernel_size in [7, 15, 21]:
            result = cat_filter.apply_cat_vision(test_image_small, kernel_size=kernel_size)
            assert result is not None
            assert result.shape == test_image_small.shape


class TestApplyCatVisionToSequence:
    """Test apply_cat_vision_to_sequence method."""
    
    def test_sequence_returns_list(self, cat_filter, test_frame_sequence):
        """Test that sequence processing returns a list."""
        result = cat_filter.apply_cat_vision_to_sequence(test_frame_sequence)
        assert isinstance(result, list)
    
    def test_sequence_preserves_length(self, cat_filter, test_frame_sequence):
        """Test that output sequence length matches input."""
        result = cat_filter.apply_cat_vision_to_sequence(test_frame_sequence)
        assert len(result) == len(test_frame_sequence)
    
    def test_sequence_empty_input(self, cat_filter):
        """Test sequence processing with empty input."""
        result = cat_filter.apply_cat_vision_to_sequence([])
        assert result == []
    
    def test_sequence_single_frame(self, cat_filter, test_image_color):
        """Test sequence processing with single frame."""
        result = cat_filter.apply_cat_vision_to_sequence([test_image_color])
        assert len(result) == 1
    
    def test_sequence_with_fps(self, cat_filter, test_frame_sequence):
        """Test sequence processing with different FPS."""
        result = cat_filter.apply_cat_vision_to_sequence(test_frame_sequence, fps=60)
        assert len(result) == len(test_frame_sequence)
    
    def test_sequence_biological_accuracy(self, cat_filter, test_frame_sequence):
        """Test sequence with biological accuracy."""
        result = cat_filter.apply_cat_vision_to_sequence(
            test_frame_sequence, use_biological_accuracy=True
        )
        assert len(result) == len(test_frame_sequence)


class TestParameterManagement:
    """Test parameter management methods."""
    
    def test_get_filter_parameters_returns_dict(self, cat_filter):
        """Test that get_filter_parameters returns a dictionary."""
        params = cat_filter.get_filter_parameters()
        assert isinstance(params, dict)
    
    def test_get_filter_parameters_contains_all_params(self, cat_filter):
        """Test that all parameters are included."""
        params = cat_filter.get_filter_parameters()
        expected_keys = [
            'pupil_aspect_ratio', 'rod_cone_ratio', 'peak_wavelength',
            'tapetum_reflectance', 'visual_field_horizontal', 'visual_field_vertical',
            's_cone_peak', 'l_cone_peak', 'rod_peak',
            'spatial_acuity_factor', 'foveal_acuity_cycles_per_degree',
            'flicker_fusion_threshold', 'temporal_sensitivity_peak',
            'motion_sensitivity', 'horizontal_motion_bias', 'color_weights'
        ]
        for key in expected_keys:
            assert key in params
    
    def test_save_parameters_creates_file(self, cat_filter, tmp_path):
        """Test that save_parameters creates a JSON file."""
        filepath = tmp_path / "params.json"
        cat_filter.save_parameters(filepath)
        assert filepath.exists()
    
    def test_save_parameters_valid_json(self, cat_filter, tmp_path):
        """Test that saved parameters are valid JSON."""
        filepath = tmp_path / "params.json"
        cat_filter.save_parameters(filepath)
        
        with open(filepath, 'r') as f:
            params = json.load(f)
        
        assert isinstance(params, dict)
        assert 'rod_cone_ratio' in params
    
    def test_save_parameters_creates_directory(self, cat_filter, tmp_path):
        """Test that save_parameters creates parent directories."""
        filepath = tmp_path / "subdir" / "params.json"
        cat_filter.save_parameters(filepath)
        assert filepath.exists()


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_grayscale_image_processing(self, cat_filter, test_image_gray):
        """Test processing of grayscale images."""
        result = cat_filter.apply_cat_vision(test_image_gray)
        assert result is not None
    
    def test_very_small_image(self, cat_filter):
        """Test processing of very small images."""
        small_img = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        result = cat_filter.apply_cat_vision(small_img)
        assert result is not None
        assert result.shape == small_img.shape
    
    def test_large_kernel_size(self, cat_filter, test_image_small):
        """Test with large kernel size."""
        result = cat_filter.apply_cat_vision(test_image_small, kernel_size=31)
        assert result is not None
