"""Spectral sensitivity processing for cat vision simulation."""

import numpy as np
import cv2
from typing import Dict


class SpectralMixin:
    """
    Mixin class for spectral sensitivity processing methods.
    
    Implements biologically accurate spectral sensitivity curves based on
    cat photoreceptor characteristics (S-cones, L-cones, and rods).
    """
    
    def _init_spectral_curves(self) -> None:
        """
        Initialize biological spectral sensitivity curves for cat photoreceptors.
        
        Based on published research on cat retinal photoreceptor spectral sensitivities:
        - S-cone peak: ~450nm (blue)
        - L-cone peak: ~556nm (green-yellow)
        - Rod peak: ~498nm (blue-green)
        """
        # Wavelength range (nm)
        self.wavelengths = np.linspace(380, 700, 321)
        
        # Cat S-cone spectral sensitivity (peak ~450nm)
        s_sigma = 40  # nm bandwidth
        self.s_cone_sensitivity = np.exp(
            -0.5 * ((self.wavelengths - self.s_cone_peak) / s_sigma) ** 2
        )
        
        # Cat L-cone spectral sensitivity (peak ~556nm)
        l_sigma = 50  # nm bandwidth
        self.l_cone_sensitivity = np.exp(
            -0.5 * ((self.wavelengths - self.l_cone_peak) / l_sigma) ** 2
        )
        
        # Rod spectral sensitivity (peak ~498nm)
        rod_sigma = 45  # nm bandwidth
        self.rod_sensitivity = np.exp(
            -0.5 * ((self.wavelengths - self.rod_peak) / rod_sigma) ** 2
        )
        
        # Normalize curves
        self.s_cone_sensitivity /= np.max(self.s_cone_sensitivity)
        self.l_cone_sensitivity /= np.max(self.l_cone_sensitivity)
        self.rod_sensitivity /= np.max(self.rod_sensitivity)
        
        # RGB to wavelength mapping (approximate)
        self.rgb_wavelengths = {'red': 630, 'green': 530, 'blue': 470}
    
    def apply_spectral_sensitivity_curves(self, image: np.ndarray) -> np.ndarray:
        """
        Apply biological spectral sensitivity curves instead of simple RGB weights.
        
        This method maps RGB channels to the biological spectral sensitivity of
        cat photoreceptors, accounting for the rod-dominated vision (25:1 rod/cone ratio).
        
        Args:
            image: Input image in BGR format (OpenCV convention)
            
        Returns:
            Spectrally corrected image with cat-like color perception
        """
        if len(image.shape) != 3:
            return image
            
        img_float = image.astype(np.float32) / 255.0
        b, g, r = cv2.split(img_float)
        
        # Map RGB channels to spectral sensitivities
        # Blue channel (~470nm)
        blue_idx = np.argmin(np.abs(self.wavelengths - self.rgb_wavelengths['blue']))
        s_response_blue = self.s_cone_sensitivity[blue_idx]
        l_response_blue = self.l_cone_sensitivity[blue_idx]
        rod_response_blue = self.rod_sensitivity[blue_idx]
        
        # Green channel (~530nm)
        green_idx = np.argmin(np.abs(self.wavelengths - self.rgb_wavelengths['green']))
        s_response_green = self.s_cone_sensitivity[green_idx]
        l_response_green = self.l_cone_sensitivity[green_idx]
        rod_response_green = self.rod_sensitivity[green_idx]
        
        # Red channel (~630nm)
        red_idx = np.argmin(np.abs(self.wavelengths - self.rgb_wavelengths['red']))
        s_response_red = self.s_cone_sensitivity[red_idx]
        l_response_red = self.l_cone_sensitivity[red_idx]
        rod_response_red = self.rod_sensitivity[red_idx]
        
        # Apply rod dominance (25:1 ratio)
        rod_weight = self.rod_cone_ratio / (self.rod_cone_ratio + 1)
        cone_weight = 1 / (self.rod_cone_ratio + 1)
        
        # Calculate weighted responses
        b_corrected = (
            rod_weight * rod_response_blue + 
            cone_weight * (s_response_blue + l_response_blue)
        ) * b
        g_corrected = (
            rod_weight * rod_response_green + 
            cone_weight * (s_response_green + l_response_green)
        ) * g
        r_corrected = (
            rod_weight * rod_response_red + 
            cone_weight * (s_response_red + l_response_red)
        ) * r
        
        # Normalize and clip
        corrected = cv2.merge([
            np.clip(b_corrected, 0, 1),
            np.clip(g_corrected, 0, 1),
            np.clip(r_corrected, 0, 1)
        ])
        
        return (corrected * 255).astype(np.uint8)
    
    def adjust_color_sensitivity(self, image: np.ndarray) -> np.ndarray:
        """
        Adjust color sensitivity to match cat vision (legacy method).
        
        Cats have peak sensitivity around 500nm (blue-green) and reduced
        red sensitivity compared to humans. This is a simplified legacy method
        for backward compatibility.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Color-adjusted image
        """
        if len(image.shape) != 3:
            return image
            
        # Convert to float for processing
        img_float = image.astype(np.float32) / 255.0
        
        # Split channels (BGR format)
        b, g, r = cv2.split(img_float)
        
        # Apply cat-specific color weights
        b_enhanced = np.clip(b * self.color_weights['blue'], 0, 1)
        g_enhanced = np.clip(g * self.color_weights['green'], 0, 1)
        r_reduced = np.clip(r * self.color_weights['red'], 0, 1)
        
        # Merge channels
        adjusted = cv2.merge([b_enhanced, g_enhanced, r_reduced])
        
        # Convert back to uint8
        return (adjusted * 255).astype(np.uint8)
