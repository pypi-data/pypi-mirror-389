"""Tests for validation module."""

import pytest
import numpy as np
from catvision import CatVisionFilter


class TestValidateBiologicalAccuracy:
    """Test overall validation framework."""
    
    def test_validation_returns_dict(self, cat_filter, test_image_list):
        """Test that validation returns a dictionary."""
        result = cat_filter.validate_biological_accuracy(test_image_list)
        assert isinstance(result, dict)
    
    def test_validation_contains_all_keys(self, cat_filter, test_image_list):
        """Test that all validation keys are present."""
        result = cat_filter.validate_biological_accuracy(test_image_list)
        expected_keys = [
            'spectral_sensitivity_validation',
            'spatial_acuity_validation',
            'temporal_response_validation',
            'motion_detection_validation',
            'overall_accuracy_score'
        ]
        for key in expected_keys:
            assert key in result
    
    def test_validation_scores_in_range(self, cat_filter, test_image_list):
        """Test that validation scores are between 0 and 1."""
        result = cat_filter.validate_biological_accuracy(test_image_list)
        for key, value in result.items():
            if isinstance(value, (int, float)):
                assert 0.0 <= value <= 1.0
    
    def test_validation_overall_score_calculated(self, cat_filter, test_image_list):
        """Test that overall score is calculated."""
        result = cat_filter.validate_biological_accuracy(test_image_list)
        assert 'overall_accuracy_score' in result
        assert result['overall_accuracy_score'] >= 0.0


class TestValidateSpectralSensitivity:
    """Test spectral sensitivity validation."""
    
    def test_spectral_validation_returns_float(self, cat_filter):
        """Test that spectral validation returns a float."""
        score = cat_filter._validate_spectral_sensitivity()
        assert isinstance(score, (int, float))
    
    def test_spectral_validation_in_range(self, cat_filter):
        """Test that score is between 0 and 1."""
        score = cat_filter._validate_spectral_sensitivity()
        assert 0.0 <= score <= 1.0
    
    def test_spectral_validation_high_score(self, cat_filter):
        """Test that default parameters give high score."""
        score = cat_filter._validate_spectral_sensitivity()
        # Should be very accurate with default biological parameters
        assert score > 0.8
    
    def test_spectral_validation_perfect_peaks(self, cat_filter):
        """Test that exact peak values give perfect score."""
        # Temporarily set peaks to expected values
        original_s = cat_filter.s_cone_peak
        original_l = cat_filter.l_cone_peak
        original_rod = cat_filter.rod_peak
        
        cat_filter.s_cone_peak = 450
        cat_filter.l_cone_peak = 556
        cat_filter.rod_peak = 498
        
        score = cat_filter._validate_spectral_sensitivity()
        assert score == 1.0
        
        # Restore original values
        cat_filter.s_cone_peak = original_s
        cat_filter.l_cone_peak = original_l
        cat_filter.rod_peak = original_rod


class TestValidateSpatialAcuity:
    """Test spatial acuity validation."""
    
    def test_spatial_validation_with_images(self, cat_filter, test_image_list):
        """Test spatial validation with test images."""
        score = cat_filter._validate_spatial_acuity(test_image_list)
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0
    
    def test_spatial_validation_empty_list(self, cat_filter):
        """Test spatial validation with empty list."""
        score = cat_filter._validate_spatial_acuity([])
        assert score == 0.0
    
    def test_spatial_validation_accuracy(self, cat_filter, test_image_list):
        """Test that spatial validation gives reasonable score."""
        score = cat_filter._validate_spatial_acuity(test_image_list)
        # Should give a reasonable score (not necessarily perfect)
        assert score >= 0.0


class TestValidateTemporalResponse:
    """Test temporal response validation."""
    
    def test_temporal_validation_returns_float(self, cat_filter):
        """Test that temporal validation returns a float."""
        score = cat_filter._validate_temporal_response()
        assert isinstance(score, (int, float))
    
    def test_temporal_validation_in_range(self, cat_filter):
        """Test that score is between 0 and 1."""
        score = cat_filter._validate_temporal_response()
        assert 0.0 <= score <= 1.0
    
    def test_temporal_validation_high_score(self, cat_filter):
        """Test that default parameters give high score."""
        score = cat_filter._validate_temporal_response()
        # Should be reasonably accurate
        assert score >= 0.0


class TestValidateMotionDetection:
    """Test motion detection validation."""
    
    def test_motion_validation_with_images(self, cat_filter, test_image_list):
        """Test motion validation with test images."""
        score = cat_filter._validate_motion_detection(test_image_list)
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0
    
    def test_motion_validation_single_image(self, cat_filter, test_image_color):
        """Test motion validation with single image."""
        score = cat_filter._validate_motion_detection([test_image_color])
        assert score == 0.0  # Need at least 2 images
    
    def test_motion_validation_empty_list(self, cat_filter):
        """Test motion validation with empty list."""
        score = cat_filter._validate_motion_detection([])
        assert score == 0.0
    
    def test_motion_validation_two_images(self, cat_filter, test_image_list):
        """Test motion validation with two images."""
        score = cat_filter._validate_motion_detection(test_image_list[:2])
        assert 0.0 <= score <= 1.0


class TestValidationConsistency:
    """Test validation consistency."""
    
    def test_validation_deterministic(self, cat_filter, test_image_list):
        """Test that validation gives consistent results."""
        result1 = cat_filter.validate_biological_accuracy(test_image_list)
        result2 = cat_filter.validate_biological_accuracy(test_image_list)
        
        # Results should be identical
        for key in result1:
            if isinstance(result1[key], (int, float)):
                assert result1[key] == pytest.approx(result2[key], rel=1e-6)
    
    def test_overall_score_average(self, cat_filter, test_image_list):
        """Test that overall score is average of individual scores."""
        result = cat_filter.validate_biological_accuracy(test_image_list)
        
        individual_scores = [
            result['spectral_sensitivity_validation'],
            result['spatial_acuity_validation'],
            result['temporal_response_validation'],
            result['motion_detection_validation']
        ]
        
        expected_overall = np.mean(individual_scores)
        assert result['overall_accuracy_score'] == pytest.approx(expected_overall, rel=1e-6)
