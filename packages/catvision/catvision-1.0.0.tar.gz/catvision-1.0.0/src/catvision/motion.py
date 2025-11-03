"""Motion detection methods for cat vision simulation."""

import numpy as np
import cv2
from typing import List, Optional, Tuple


class MotionMixin:
    """
    Mixin class for motion detection methods.
    
    Implements cat-specific motion detection characteristics:
    - Enhanced motion sensitivity (1.8x human)
    - Horizontal motion bias (1.5x)
    - Optical flow-based motion detection
    """
    
    def enhanced_motion_detection(
        self, 
        frame_sequence: List[np.ndarray],
        flow_method: str = 'lucas_kanade'
    ) -> List[np.ndarray]:
        """
        Enhanced motion detection with optical flow and directional sensitivity.
        
        Cats excel at detecting motion, particularly horizontal motion,
        which is critical for hunting prey.
        
        Args:
            frame_sequence: List of consecutive frames
            flow_method: Optical flow method ('lucas_kanade' or 'farneback')
            
        Returns:
            Motion-enhanced frame sequence
        """
        if len(frame_sequence) < 2:
            return frame_sequence
            
        enhanced_frames = []
        
        for i, frame in enumerate(frame_sequence):
            if i == 0:
                enhanced_frames.append(frame)
                continue
                
            prev_frame = frame_sequence[i-1]
            
            # Convert to grayscale for optical flow
            if len(frame.shape) == 3:
                current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            else:
                current_gray = frame
                prev_gray = prev_frame
                
            # Calculate optical flow
            if flow_method == 'lucas_kanade':
                flow = self._lucas_kanade_flow(prev_gray, current_gray)
            elif flow_method == 'farneback':
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, current_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                # Convert dense flow to sparse format for consistency
                if flow is not None:
                    h, w = flow.shape[:2]
                    y_coords, x_coords = np.mgrid[0:h:10, 0:w:10]
                    flow_vectors = flow[y_coords, x_coords]
                    flow = flow_vectors.reshape(-1, 2)
            else:
                flow = None
                
            # Calculate motion magnitude and direction
            if flow is not None:
                motion_magnitude, motion_direction = self._analyze_motion(flow)
                
                # Apply directional sensitivity (cats excel at horizontal motion)
                directional_weight = self._calculate_directional_sensitivity(motion_direction)
                
                # Enhance motion areas
                enhanced_frame = self._apply_motion_enhancement(
                    frame, motion_magnitude, directional_weight
                )
                enhanced_frames.append(enhanced_frame)
            else:
                enhanced_frames.append(frame)
                
        return enhanced_frames
    
    def _lucas_kanade_flow(
        self, 
        prev_gray: np.ndarray, 
        current_gray: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Calculate Lucas-Kanade optical flow.
        
        Args:
            prev_gray: Previous frame in grayscale
            current_gray: Current frame in grayscale
            
        Returns:
            Flow vectors or None if detection fails
        """
        try:
            # Parameters for corner detection
            feature_params = dict(
                maxCorners=100,
                qualityLevel=0.3,
                minDistance=7,
                blockSize=7
            )
            
            # Parameters for Lucas-Kanade optical flow
            lk_params = dict(
                winSize=(15, 15),
                maxLevel=2,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
            )
            
            # Find corners in previous frame
            p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, **feature_params)
            
            if p0 is not None:
                # Calculate optical flow
                p1, status, error = cv2.calcOpticalFlowPyrLK(
                    prev_gray, current_gray, p0, None, **lk_params
                )
                
                # Select good points
                if p1 is not None:
                    good_new = p1[status == 1]
                    good_old = p0[status == 1]
                    
                    # Calculate flow vectors
                    flow_vectors = good_new - good_old
                    return flow_vectors
                    
        except Exception:
            pass
            
        return None
    
    def _analyze_motion(
        self, 
        flow_vectors: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Analyze motion magnitude and direction from flow vectors.
        
        Args:
            flow_vectors: Optical flow vectors
            
        Returns:
            Tuple of (magnitude, direction) arrays
        """
        if len(flow_vectors) == 0:
            return np.array([]), np.array([])
            
        # Calculate magnitude and angle
        magnitude = np.sqrt(flow_vectors[:, 0]**2 + flow_vectors[:, 1]**2)
        direction = np.arctan2(flow_vectors[:, 1], flow_vectors[:, 0])
        
        return magnitude, direction
    
    def _calculate_directional_sensitivity(self, directions: np.ndarray) -> float:
        """
        Calculate directional sensitivity weight (cats excel at horizontal motion).
        
        Args:
            directions: Array of motion directions in radians
            
        Returns:
            Directional sensitivity weight
        """
        if len(directions) == 0:
            return 1.0
            
        # Convert angles to horizontal bias (0° and 180° are horizontal)
        horizontal_angles = np.abs(np.cos(directions))
        avg_horizontal_bias = np.mean(horizontal_angles)
        
        # Apply horizontal motion bias
        return 1.0 + (self.horizontal_motion_bias - 1.0) * avg_horizontal_bias
    
    def _apply_motion_enhancement(
        self, 
        frame: np.ndarray,
        motion_magnitude: np.ndarray,
        directional_weight: float
    ) -> np.ndarray:
        """
        Apply motion enhancement to frame.
        
        Args:
            frame: Input frame
            motion_magnitude: Motion magnitude values
            directional_weight: Directional sensitivity weight
            
        Returns:
            Motion-enhanced frame
        """
        if len(motion_magnitude) == 0:
            return frame
            
        enhanced = frame.astype(np.float32)
        
        # Create motion enhancement mask
        avg_motion = np.mean(motion_magnitude) if len(motion_magnitude) > 0 else 0
        enhancement_factor = (
            1.0 + (self.motion_sensitivity - 1.0) * 
            directional_weight * min(avg_motion / 10.0, 1.0)
        )
        
        # Apply enhancement globally (simplified approach)
        enhanced *= enhancement_factor
        
        return np.clip(enhanced, 0, 255).astype(np.uint8)
    
    def enhance_motion_detection(
        self, 
        image: np.ndarray,
        previous_frame: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Enhance motion detection capabilities (legacy method).
        
        Rod cell specialization for motion detection.
        
        Args:
            image: Current frame
            previous_frame: Previous frame for motion detection
            
        Returns:
            Motion-enhanced image
        """
        if previous_frame is None:
            return image
            
        # Convert to grayscale for motion detection
        if len(image.shape) == 3:
            current_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            prev_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        else:
            current_gray = image
            prev_gray = previous_frame
            
        # Calculate frame difference
        diff = cv2.absdiff(current_gray, prev_gray)
        
        # Enhance motion areas
        motion_mask = diff > 10  # Threshold for motion detection
        enhanced = image.copy().astype(np.float32)
        
        if len(image.shape) == 3:
            for channel in range(3):
                enhanced[:, :, channel][motion_mask] *= self.motion_sensitivity
        else:
            enhanced[motion_mask] *= self.motion_sensitivity
            
        return np.clip(enhanced, 0, 255).astype(np.uint8)
