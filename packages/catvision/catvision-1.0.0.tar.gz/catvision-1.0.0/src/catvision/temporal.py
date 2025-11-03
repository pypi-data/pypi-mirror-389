"""Temporal processing methods for cat vision simulation."""

import numpy as np
import cv2
from typing import List


class TemporalMixin:
    """
    Mixin class for temporal processing methods.
    
    Implements cat temporal characteristics:
    - Enhanced flicker fusion threshold (55Hz vs human 24Hz)
    - Peak temporal sensitivity at 10Hz
    - Enhanced temporal frequency response
    """
    
    def model_temporal_processing(
        self, 
        frame_sequence: List[np.ndarray], 
        fps: int = 30
    ) -> List[np.ndarray]:
        """
        Model cat temporal processing with enhanced flicker fusion threshold.
        
        Cats can detect flicker up to 55Hz compared to humans at ~24Hz,
        making them more sensitive to rapid changes and motion.
        
        Args:
            frame_sequence: List of consecutive frames
            fps: Frames per second of the input sequence
            
        Returns:
            Temporally processed frame sequence
        """
        if len(frame_sequence) < 2:
            return frame_sequence
            
        processed_frames = []
        
        for i, frame in enumerate(frame_sequence):
            if i == 0:
                processed_frames.append(frame)
                continue
                
            # Calculate temporal frequency based on frame differences
            prev_frame = frame_sequence[i-1]
            
            # Convert to grayscale for temporal analysis
            if len(frame.shape) == 3:
                current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            else:
                current_gray = frame
                prev_gray = prev_frame
                
            # Calculate frame difference (motion/flicker detection)
            frame_diff = cv2.absdiff(current_gray, prev_gray)
            
            # Apply temporal sensitivity curve (peak at ~10Hz for cats)
            temporal_freq = fps / max(1, i)  # Approximate frequency
            sensitivity = self._temporal_sensitivity_function(temporal_freq)
            
            # Enhance or suppress based on temporal frequency
            if len(frame.shape) == 3:
                enhanced_frame = frame.astype(np.float32)
                motion_mask = frame_diff > 5  # Motion threshold
                
                for channel in range(3):
                    enhanced_frame[:, :, channel][motion_mask] *= sensitivity
                    
                processed_frame = np.clip(enhanced_frame, 0, 255).astype(np.uint8)
            else:
                enhanced_frame = frame.astype(np.float32)
                motion_mask = frame_diff > 5
                enhanced_frame[motion_mask] *= sensitivity
                processed_frame = np.clip(enhanced_frame, 0, 255).astype(np.uint8)
                
            processed_frames.append(processed_frame)
            
        return processed_frames
    
    def _temporal_sensitivity_function(self, frequency: float) -> float:
        """
        Calculate temporal sensitivity based on cat visual system.
        
        Cat temporal sensitivity:
        - Peaks around 10Hz
        - Remains responsive up to 55Hz (flicker fusion threshold)
        - Drops off sharply above 55Hz
        
        Args:
            frequency: Temporal frequency in Hz
            
        Returns:
            Sensitivity factor (multiplier)
        """
        # Cat temporal sensitivity peaks around 10Hz, drops off after 55Hz
        if frequency <= 0:
            return 1.0
        elif frequency <= self.temporal_sensitivity_peak:
            # Increasing sensitivity up to peak
            return 1.0 + 0.5 * (frequency / self.temporal_sensitivity_peak)
        elif frequency <= self.flicker_fusion_threshold:
            # Decreasing sensitivity after peak
            decay_factor = (
                (frequency - self.temporal_sensitivity_peak) / 
                (self.flicker_fusion_threshold - self.temporal_sensitivity_peak)
            )
            return 1.5 - 0.5 * decay_factor
        else:
            # Above flicker fusion threshold - minimal sensitivity
            return 0.1
