"""Validation methods for biological accuracy verification."""

import numpy as np
import cv2
from typing import List, Dict, Optional


class ValidationMixin:
    """
    Mixin class for validation methods.
    
    Validates filter outputs against published biological data
    on cat vision characteristics.
    """
    
    def validate_biological_accuracy(
        self,
        test_images: List[np.ndarray],
        ground_truth_data: Optional[Dict] = None
    ) -> Dict:
        """
        Validate biological accuracy against published cat vision characteristics.
        
        Compares filter behavior with peer-reviewed research on:
        - Spectral sensitivity curves
        - Spatial acuity measurements
        - Temporal response characteristics
        - Motion detection capabilities
        
        Args:
            test_images: List of test images for validation
            ground_truth_data: Optional ground truth data for comparison
            
        Returns:
            Validation results dictionary with accuracy scores
        """
        results = {
            'spectral_sensitivity_validation': self._validate_spectral_sensitivity(),
            'spatial_acuity_validation': self._validate_spatial_acuity(test_images),
            'temporal_response_validation': self._validate_temporal_response(),
            'motion_detection_validation': self._validate_motion_detection(test_images),
            'overall_accuracy_score': 0.0
        }
        
        # Calculate overall accuracy score (exclude overall_accuracy_score itself)
        scores = [v for k, v in results.items() 
                  if isinstance(v, (int, float)) and k != 'overall_accuracy_score']
        if scores:
            results['overall_accuracy_score'] = np.mean(scores)
        
        return results
    
    def _validate_spectral_sensitivity(self) -> float:
        """
        Validate spectral sensitivity curves against biological data.
        
        Compares peak wavelengths against published values:
        - S-cone peak: 450nm (±10nm tolerance)
        - L-cone peak: 556nm (±15nm tolerance)
        - Rod peak: 498nm (±10nm tolerance)
        
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        # Expected peak wavelengths from literature
        expected_s_peak = 450  # ±10nm
        expected_l_peak = 556  # ±15nm
        expected_rod_peak = 498  # ±10nm
        
        # Calculate accuracy based on peak positions
        s_accuracy = 1.0 - min(abs(self.s_cone_peak - expected_s_peak) / 10.0, 1.0)
        l_accuracy = 1.0 - min(abs(self.l_cone_peak - expected_l_peak) / 15.0, 1.0)
        rod_accuracy = 1.0 - min(abs(self.rod_peak - expected_rod_peak) / 10.0, 1.0)
        
        return np.mean([s_accuracy, l_accuracy, rod_accuracy])
    
    def _validate_spatial_acuity(self, test_images: List[np.ndarray]) -> float:
        """
        Validate spatial acuity reduction against behavioral measurements.
        
        Validates that spatial acuity reduction matches the expected
        1/6 ratio compared to human vision.
        
        Args:
            test_images: List of test images
            
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        if not test_images:
            return 0.0
            
        # Test acuity reduction on a sample image
        test_image = test_images[0]
        gray_test = (
            cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
            if len(test_image.shape) == 3
            else test_image
        )
        original_fft = np.fft.fft2(gray_test)
        
        # Apply acuity reduction
        acuity_reduced = self.simulate_spatial_acuity_reduction(test_image)
        gray_reduced = (
            cv2.cvtColor(acuity_reduced, cv2.COLOR_BGR2GRAY)
            if len(acuity_reduced.shape) == 3
            else acuity_reduced
        )
        reduced_fft = np.fft.fft2(gray_reduced)
        
        # Calculate frequency content reduction
        original_power = np.mean(np.abs(original_fft))
        reduced_power = np.mean(np.abs(reduced_fft))
        reduction_ratio = reduced_power / original_power
        
        # Expected reduction should be around 0.167 (1/6 of human acuity)
        expected_ratio = self.spatial_acuity_factor
        accuracy = 1.0 - min(abs(reduction_ratio - expected_ratio) / expected_ratio, 1.0)
        
        return accuracy
    
    def _validate_temporal_response(self) -> float:
        """
        Validate temporal frequency response characteristics.
        
        Tests the temporal sensitivity function at key frequency points
        to ensure it matches expected cat vision behavior.
        
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        # Test key frequency points
        test_frequencies = [10, 24, 55, 80]  # Hz
        expected_responses = [1.5, 1.2, 1.0, 0.1]  # Approximate expected values
        
        actual_responses = [
            self._temporal_sensitivity_function(f) for f in test_frequencies
        ]
        
        # Calculate accuracy based on response matching
        accuracies = []
        for actual, expected in zip(actual_responses, expected_responses):
            accuracy = 1.0 - min(abs(actual - expected) / expected, 1.0)
            accuracies.append(accuracy)
        
        return np.mean(accuracies)
    
    def _validate_motion_detection(self, test_images: List[np.ndarray]) -> float:
        """
        Validate motion detection enhancement.
        
        Verifies that motion detection enhancement matches the expected
        sensitivity factor (1.8x human).
        
        Args:
            test_images: List of test images
            
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        if len(test_images) < 2:
            return 0.0
            
        # Create simple motion test
        frame1 = test_images[0]
        frame2 = test_images[1] if len(test_images) > 1 else test_images[0]
        
        # Ensure frames have same size
        if frame1.shape != frame2.shape:
            frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
        
        # Test enhanced motion detection
        enhanced_frames = self.enhanced_motion_detection([frame1, frame2])
        
        # Calculate motion enhancement factor
        gray1 = (
            cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            if len(frame1.shape) == 3
            else frame1
        )
        gray2 = (
            cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            if len(frame2.shape) == 3
            else frame2
        )
        original_diff = cv2.absdiff(gray1, gray2)
        
        enh_gray1 = (
            cv2.cvtColor(enhanced_frames[0], cv2.COLOR_BGR2GRAY)
            if len(enhanced_frames[0].shape) == 3
            else enhanced_frames[0]
        )
        enh_gray2 = (
            cv2.cvtColor(enhanced_frames[1], cv2.COLOR_BGR2GRAY)
            if len(enhanced_frames[1].shape) == 3
            else enhanced_frames[1]
        )
        enhanced_diff = cv2.absdiff(enh_gray1, enh_gray2)
        
        enhancement_ratio = np.mean(enhanced_diff) / (np.mean(original_diff) + 1e-6)
        
        # Expected enhancement should be around motion_sensitivity factor
        expected_enhancement = self.motion_sensitivity
        accuracy = 1.0 - min(
            abs(enhancement_ratio - expected_enhancement) / expected_enhancement, 1.0
        )
        
        return accuracy
