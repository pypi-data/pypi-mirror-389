"""Low-light vision methods for cat vision simulation."""

import numpy as np
import cv2


class LowlightMixin:
    """
    Mixin class for low-light vision methods.
    
    Implements cat-specific low-light adaptations:
    - Tapetum lucidum light reflection (30% reflectance)
    - Rod-dominated vision (25:1 rod/cone ratio)
    - Enhanced contrast in low-light
    - Reduced color discrimination
    """
    
    def apply_tapetum_effect(
        self, 
        image: np.ndarray,
        brightness_threshold: float = 0.3
    ) -> np.ndarray:
        """
        Simulate tapetum lucidum light reflection effect.
        
        The tapetum lucidum is a reflective layer behind the retina that
        reflects light back through the retina, enhancing low-light vision
        performance by approximately 30%.
        
        Args:
            image: Input image
            brightness_threshold: Threshold for low-light enhancement (0.0-1.0)
            
        Returns:
            Image with tapetum effect applied
        """
        if len(image.shape) == 3:
            # Convert to grayscale for brightness calculation
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Calculate average brightness
        avg_brightness = np.mean(gray) / 255.0
        
        # Apply tapetum effect in low-light conditions
        if avg_brightness < brightness_threshold:
            # Create enhancement mask based on image brightness
            enhancement_factor = 1.0 + (
                self.tapetum_reflectance * 
                (brightness_threshold - avg_brightness)
            )
            
            # Apply enhancement with spatial variation
            enhanced = image.astype(np.float32) * enhancement_factor
            
            # Add slight blue-green tint (characteristic of tapetum reflection)
            if len(image.shape) == 3:
                enhanced[:, :, 0] *= 1.1   # Enhance blue channel
                enhanced[:, :, 1] *= 1.05  # Slightly enhance green
            
            # Clip values and convert back
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
            return enhanced
        
        return image
    
    def simulate_rod_dominance(self, image: np.ndarray) -> np.ndarray:
        """
        Simulate effects of rod-dominated vision (25:1 rod/cone ratio).
        
        Rod cells are responsible for:
        - Low-light vision
        - Motion detection
        - Peripheral vision
        - Reduced color discrimination
        
        Cats have a much higher rod-to-cone ratio than humans (25:1 vs 20:1),
        resulting in excellent night vision but reduced color perception.
        
        Args:
            image: Input image
            
        Returns:
            Image with rod dominance effects
        """
        # Convert to grayscale to simulate reduced color discrimination
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Create rod-dominated image with reduced color saturation
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = hsv[:, :, 1] * 0.4  # Reduce saturation significantly
            rod_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        else:
            rod_image = image.copy()
            gray = image.copy()
        
        # Enhance contrast for better low-light performance
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)
        
        # Blend enhanced grayscale with reduced-color image
        if len(image.shape) == 3:
            enhanced_gray_bgr = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
            rod_image = cv2.addWeighted(rod_image, 0.7, enhanced_gray_bgr, 0.3, 0)
        else:
            rod_image = enhanced_gray
            
        return rod_image
