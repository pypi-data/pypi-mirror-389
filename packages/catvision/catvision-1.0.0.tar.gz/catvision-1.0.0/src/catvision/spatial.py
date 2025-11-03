"""Spatial processing methods for cat vision simulation."""

import numpy as np
import cv2
from scipy.ndimage import gaussian_filter
from typing import Optional


class SpatialMixin:
    """
    Mixin class for spatial processing methods.
    
    Implements cat-specific spatial characteristics including:
    - Vertical slit pupil (3:1 aspect ratio)
    - Reduced spatial acuity (1/6 human acuity)
    - Wide-angle field of view (200°×140°)
    - Center-surround acuity mapping
    """
    
    def create_pupil_kernel(self, kernel_size: int = 15) -> np.ndarray:
        """
        Create vertical slit pupil convolution kernel.
        
        Cats have a distinctive vertical slit pupil with a 3:1 aspect ratio,
        which affects light distribution and depth of field.
        
        Args:
            kernel_size: Size of the kernel (should be odd)
            
        Returns:
            Normalized convolution kernel representing cat pupil
        """
        if kernel_size % 2 == 0:
            kernel_size += 1  # Ensure odd size
            
        # Create elliptical Gaussian with 3:1 aspect ratio (vertical slit)
        center = kernel_size // 2
        y, x = np.ogrid[:kernel_size, :kernel_size]
        
        # Elliptical parameters
        sigma_x = kernel_size / 8.0  # Narrow horizontal spread
        sigma_y = sigma_x * self.pupil_aspect_ratio  # Wider vertical spread
        
        # Create elliptical Gaussian
        kernel = np.exp(
            -((x - center)**2 / (2 * sigma_x**2) + 
              (y - center)**2 / (2 * sigma_y**2))
        )
        
        # Normalize kernel
        kernel = kernel / np.sum(kernel)
        
        return kernel
    
    def apply_pupil_filter(self, image: np.ndarray, kernel_size: int = 15) -> np.ndarray:
        """
        Apply vertical slit pupil convolution filter.
        
        Args:
            image: Input image
            kernel_size: Size of pupil kernel
            
        Returns:
            Pupil-filtered image
        """
        kernel = self.create_pupil_kernel(kernel_size)
        
        if len(image.shape) == 3:
            # Apply to each channel
            filtered_channels = []
            for i in range(3):
                filtered_channel = cv2.filter2D(image[:, :, i], -1, kernel)
                filtered_channels.append(filtered_channel)
            filtered_image = cv2.merge(filtered_channels)
        else:
            filtered_image = cv2.filter2D(image, -1, kernel)
            
        return filtered_image
    
    def simulate_spatial_acuity_reduction(
        self, 
        image: np.ndarray, 
        acuity_factor: Optional[float] = None
    ) -> np.ndarray:
        """
        Simulate cat spatial acuity reduction using frequency domain filtering.
        
        Cats have approximately 1/6 the spatial acuity of humans, corresponding
        to visual acuity of about 20/100 to 20/200 in human terms.
        
        Args:
            image: Input image
            acuity_factor: Acuity reduction factor (default: 0.167 = 1/6 human acuity)
            
        Returns:
            Spatially filtered image
        """
        if acuity_factor is None:
            acuity_factor = self.spatial_acuity_factor
            
        if len(image.shape) == 3:
            # Process each channel separately
            filtered_channels = []
            for i in range(3):
                filtered_channel = self._apply_spatial_filter(image[:, :, i], acuity_factor)
                filtered_channels.append(filtered_channel)
            return cv2.merge(filtered_channels)
        else:
            return self._apply_spatial_filter(image, acuity_factor)
    
    def _apply_spatial_filter(self, channel: np.ndarray, acuity_factor: float) -> np.ndarray:
        """
        Apply spatial frequency filtering to simulate reduced acuity.
        
        Args:
            channel: Single channel image
            acuity_factor: Acuity reduction factor
            
        Returns:
            Filtered channel
        """
        # Convert to frequency domain
        f_transform = np.fft.fft2(channel)
        f_shifted = np.fft.fftshift(f_transform)
        
        # Create frequency coordinates
        rows, cols = channel.shape
        crow, ccol = rows // 2, cols // 2
        
        # Create distance matrix from center
        y, x = np.ogrid[:rows, :cols]
        distance = np.sqrt((x - ccol)**2 + (y - crow)**2)
        
        # Create low-pass filter based on acuity factor
        # Higher acuity_factor = more high frequencies preserved
        cutoff_freq = acuity_factor * min(rows, cols) / 4
        filter_mask = np.exp(-(distance**2) / (2 * cutoff_freq**2))
        
        # Apply filter
        f_filtered = f_shifted * filter_mask
        
        # Convert back to spatial domain
        f_ishifted = np.fft.ifftshift(f_filtered)
        filtered = np.fft.ifft2(f_ishifted)
        filtered = np.real(filtered)
        
        return np.clip(filtered, 0, 255).astype(np.uint8)
    
    def apply_spatial_field_transformation(
        self, 
        image: np.ndarray,
        fov_horizontal: int = 200,
        fov_vertical: int = 140
    ) -> np.ndarray:
        """
        Apply wide-angle peripheral vision transformation.
        
        Cats have a wider field of view than humans (200°×140° vs 180°×120°),
        with enhanced peripheral vision but reduced central acuity.
        
        Args:
            image: Input image
            fov_horizontal: Horizontal field of view in degrees (default: 200°)
            fov_vertical: Vertical field of view in degrees (default: 140°)
            
        Returns:
            Transformed image with cat-like field of view
        """
        h, w = image.shape[:2]
        
        # Create coordinate grids
        y, x = np.mgrid[0:h, 0:w]
        
        # Normalize coordinates to [-1, 1]
        x_norm = (x - w/2) / (w/2)
        y_norm = (y - h/2) / (h/2)
        
        # Apply barrel distortion for wider field of view
        # Cat FOV is wider than human, so we need to compress the image
        fov_ratio_h = fov_horizontal / 180  # Human ~180°
        fov_ratio_v = fov_vertical / 120    # Human ~120°
        
        # Barrel distortion parameters
        k1 = 0.1 * (fov_ratio_h - 1)  # Horizontal distortion
        k2 = 0.1 * (fov_ratio_v - 1)  # Vertical distortion
        
        # Apply distortion
        r_squared = x_norm**2 + y_norm**2
        x_distorted = x_norm * (1 + k1 * r_squared)
        y_distorted = y_norm * (1 + k2 * r_squared)
        
        # Convert back to image coordinates
        x_new = (x_distorted * w/2 + w/2).astype(np.float32)
        y_new = (y_distorted * h/2 + h/2).astype(np.float32)
        
        # Apply remapping
        transformed = cv2.remap(
            image, x_new, y_new, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT
        )
        
        # Apply center-surround acuity mapping
        center_x, center_y = w//2, h//2
        max_distance = np.sqrt((w/2)**2 + (h/2)**2)
        
        # Create acuity mask (sharp center, blurred periphery)
        distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        acuity_mask = np.exp(-(distance_from_center / max_distance)**2 * 3)
        
        # Apply variable blur based on distance from center
        if len(image.shape) == 3:
            for i in range(3):
                # Create peripheral blur
                blurred = gaussian_filter(transformed[:, :, i], sigma=3)
                # Blend based on acuity mask
                transformed[:, :, i] = (
                    acuity_mask * transformed[:, :, i] + 
                    (1 - acuity_mask) * blurred
                ).astype(np.uint8)
        else:
            blurred = gaussian_filter(transformed, sigma=3)
            transformed = (
                acuity_mask * transformed + (1 - acuity_mask) * blurred
            ).astype(np.uint8)
        
        return transformed
