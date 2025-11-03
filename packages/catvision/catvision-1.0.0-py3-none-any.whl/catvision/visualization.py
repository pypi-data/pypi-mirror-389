"""Visualization utilities for cat vision filter."""

import matplotlib.pyplot as plt
import numpy as np
import cv2
from typing import Optional, Tuple, List


class VisualizationMixin:
    """
    Mixin class for visualization methods.
    
    Provides comprehensive visualization tools for understanding
    cat vision characteristics and filter behavior.
    """
    
    def plot_spectral_sensitivity_curves(self, save_path: Optional[str] = None) -> None:
        """
        Visualize cat photoreceptor spectral sensitivity curves.
        
        Displays the spectral sensitivity of S-cones, L-cones, and rods,
        along with RGB wavelength markers.
        
        Args:
            save_path: Optional path to save the plot
        """
        plt.figure(figsize=(12, 8))
        
        # Plot spectral sensitivity curves
        plt.plot(
            self.wavelengths, self.s_cone_sensitivity, 'b-', linewidth=2,
            label=f'S-cone (peak: {self.s_cone_peak}nm)', alpha=0.8
        )
        plt.plot(
            self.wavelengths, self.l_cone_sensitivity, 'g-', linewidth=2,
            label=f'L-cone (peak: {self.l_cone_peak}nm)', alpha=0.8
        )
        plt.plot(
            self.wavelengths, self.rod_sensitivity, 'k-', linewidth=2,
            label=f'Rod (peak: {self.rod_peak}nm)', alpha=0.8
        )
        
        # Add RGB wavelength markers
        for color, wavelength in self.rgb_wavelengths.items():
            plt.axvline(
                x=wavelength, color=color, linestyle='--', alpha=0.6,
                label=f'{color.capitalize()} (~{wavelength}nm)'
            )
        
        plt.xlabel('Wavelength (nm)', fontsize=12)
        plt.ylabel('Normalized Sensitivity', fontsize=12)
        plt.title(
            'Cat Photoreceptor Spectral Sensitivity Curves\n(Based on Biological Data)',
            fontsize=14
        )
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.xlim(380, 700)
        plt.ylim(0, 1.1)
        
        # Add annotations
        plt.annotate(
            'Enhanced blue-green\nsensitivity',
            xy=(500, 0.8), xytext=(450, 0.9),
            arrowprops=dict(arrowstyle='->', color='gray'),
            fontsize=10
        )
        plt.annotate(
            'Reduced red\nsensitivity',
            xy=(630, 0.2), xytext=(650, 0.4),
            arrowprops=dict(arrowstyle='->', color='gray'),
            fontsize=10
        )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def visualize_spatial_acuity_map(
        self, 
        image_size: Tuple[int, int],
        save_path: Optional[str] = None
    ) -> None:
        """
        Visualize spatial acuity mapping across the visual field.
        
        Shows how spatial acuity decreases from center to periphery,
        characteristic of cat vision.
        
        Args:
            image_size: (height, width) of the reference image
            save_path: Optional path to save the visualization
        """
        h, w = image_size
        y, x = np.mgrid[0:h, 0:w]
        
        # Calculate distance from center
        center_x, center_y = w//2, h//2
        max_distance = np.sqrt((w/2)**2 + (h/2)**2)
        distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Create acuity map (sharp center, blurred periphery)
        acuity_map = np.exp(-(distance_from_center / max_distance)**2 * 3)
        
        # Convert to cycles per degree (approximate)
        acuity_cpd = self.foveal_acuity_cycles_per_degree * acuity_map
        
        plt.figure(figsize=(12, 8))
        
        # Create subplot for acuity map
        plt.subplot(1, 2, 1)
        im1 = plt.imshow(acuity_map, cmap='hot', interpolation='bilinear')
        plt.colorbar(im1, label='Relative Acuity')
        plt.title('Cat Spatial Acuity Map\n(Relative to Center)', fontsize=12)
        plt.xlabel('Horizontal Position (pixels)')
        plt.ylabel('Vertical Position (pixels)')
        
        # Create subplot for cycles per degree
        plt.subplot(1, 2, 2)
        im2 = plt.imshow(acuity_cpd, cmap='viridis', interpolation='bilinear')
        plt.colorbar(im2, label='Cycles per Degree')
        plt.title('Cat Visual Acuity\n(Cycles per Degree)', fontsize=12)
        plt.xlabel('Horizontal Position (pixels)')
        plt.ylabel('Vertical Position (pixels)')
        
        plt.suptitle(
            f'Cat Visual Acuity Distribution\n'
            f'(Peak: {self.foveal_acuity_cycles_per_degree} cpd vs Human: ~18 cpd)',
            fontsize=14
        )
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def demonstrate_temporal_frequency_response(
        self, 
        save_path: Optional[str] = None
    ) -> None:
        """
        Demonstrate cat temporal frequency response characteristics.
        
        Shows the enhanced temporal sensitivity compared to humans,
        particularly the higher flicker fusion threshold.
        
        Args:
            save_path: Optional path to save the plot
        """
        frequencies = np.linspace(0, 80, 161)
        sensitivities = [self._temporal_sensitivity_function(f) for f in frequencies]
        
        plt.figure(figsize=(10, 6))
        plt.plot(
            frequencies, sensitivities, 'b-', linewidth=2,
            label='Cat Temporal Sensitivity'
        )
        
        # Add markers for key frequencies
        plt.axvline(
            x=self.temporal_sensitivity_peak, color='g', linestyle='--',
            label=f'Peak Sensitivity ({self.temporal_sensitivity_peak}Hz)'
        )
        plt.axvline(
            x=self.flicker_fusion_threshold, color='r', linestyle='--',
            label=f'Flicker Fusion Threshold ({self.flicker_fusion_threshold}Hz)'
        )
        plt.axvline(
            x=24, color='orange', linestyle=':', alpha=0.7,
            label='Human Flicker Fusion (~24Hz)'
        )
        
        plt.xlabel('Temporal Frequency (Hz)', fontsize=12)
        plt.ylabel('Sensitivity Factor', fontsize=12)
        plt.title('Cat Temporal Frequency Response\nvs Human Visual System', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 80)
        plt.ylim(0, 1.6)
        
        # Add annotations
        plt.annotate(
            'Enhanced motion\ndetection range',
            xy=(30, 1.2), xytext=(45, 1.4),
            arrowprops=dict(arrowstyle='->', color='gray'),
            fontsize=10
        )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def visualize_pupil_kernel(
        self, 
        kernel_size: int = 15,
        save_path: Optional[str] = None
    ) -> None:
        """
        Visualize the pupil kernel for validation.
        
        Shows the vertical slit pupil convolution kernel with 3:1 aspect ratio.
        
        Args:
            kernel_size: Size of kernel to visualize
            save_path: Optional path to save visualization
        """
        kernel = self.create_pupil_kernel(kernel_size)
        
        plt.figure(figsize=(8, 6))
        plt.imshow(kernel, cmap='hot', interpolation='bilinear')
        plt.colorbar(label='Kernel Weight')
        plt.title('Cat Pupil Kernel (Vertical Slit)\n3:1 Aspect Ratio')
        plt.xlabel('Horizontal Position')
        plt.ylabel('Vertical Position')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def compare_motion_detection_sensitivity(
        self,
        test_video_frames: List[np.ndarray],
        save_path: Optional[str] = None
    ) -> None:
        """
        Compare motion detection sensitivity between cat and human-like processing.
        
        Demonstrates the enhanced motion detection capabilities of cat vision.
        
        Args:
            test_video_frames: List of video frames for analysis
            save_path: Optional path to save the comparison plot
        """
        if len(test_video_frames) < 2:
            print("Need at least 2 frames for motion analysis")
            return
            
        # Analyze motion with cat-like processing
        cat_enhanced = self.enhanced_motion_detection(test_video_frames)
        
        # Analyze motion with basic frame differencing (human-like)
        human_motion_scores = []
        cat_motion_scores = []
        
        for i in range(1, len(test_video_frames)):
            # Human-like motion detection
            prev_gray = (
                cv2.cvtColor(test_video_frames[i-1], cv2.COLOR_BGR2GRAY)
                if len(test_video_frames[i-1].shape) == 3
                else test_video_frames[i-1]
            )
            curr_gray = (
                cv2.cvtColor(test_video_frames[i], cv2.COLOR_BGR2GRAY)
                if len(test_video_frames[i].shape) == 3
                else test_video_frames[i]
            )
            human_diff = cv2.absdiff(prev_gray, curr_gray)
            human_motion_scores.append(np.mean(human_diff))
            
            # Cat-like motion detection
            cat_prev_gray = (
                cv2.cvtColor(cat_enhanced[i-1], cv2.COLOR_BGR2GRAY)
                if len(cat_enhanced[i-1].shape) == 3
                else cat_enhanced[i-1]
            )
            cat_curr_gray = (
                cv2.cvtColor(cat_enhanced[i], cv2.COLOR_BGR2GRAY)
                if len(cat_enhanced[i].shape) == 3
                else cat_enhanced[i]
            )
            cat_diff = cv2.absdiff(cat_prev_gray, cat_curr_gray)
            cat_motion_scores.append(np.mean(cat_diff))
        
        # Plot comparison
        plt.figure(figsize=(12, 6))
        
        frame_indices = range(1, len(test_video_frames))
        plt.plot(
            frame_indices, human_motion_scores, 'b-', linewidth=2,
            label='Human-like Motion Detection', alpha=0.7
        )
        plt.plot(
            frame_indices, cat_motion_scores, 'r-', linewidth=2,
            label='Cat-like Motion Detection', alpha=0.7
        )
        
        plt.xlabel('Frame Number', fontsize=12)
        plt.ylabel('Motion Score (Mean Pixel Difference)', fontsize=12)
        plt.title(
            'Motion Detection Sensitivity Comparison\nCat vs Human Visual Processing',
            fontsize=14
        )
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Calculate enhancement ratio
        avg_enhancement = np.mean(
            np.array(cat_motion_scores) / (np.array(human_motion_scores) + 1e-6)
        )
        plt.text(
            0.02, 0.98, f'Average Cat Enhancement: {avg_enhancement:.2f}x',
            transform=plt.gca().transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
