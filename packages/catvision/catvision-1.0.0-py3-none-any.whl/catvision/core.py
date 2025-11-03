"""Core CatVisionFilter class implementation."""

import numpy as np
import cv2
import json
from pathlib import Path
from typing import Optional, List, Dict, Union
import warnings

from catvision.spectral import SpectralMixin
from catvision.spatial import SpatialMixin
from catvision.temporal import TemporalMixin
from catvision.motion import MotionMixin
from catvision.lowlight import LowlightMixin
from catvision.visualization import VisualizationMixin
from catvision.validation import ValidationMixin

warnings.filterwarnings('ignore')


class CatVisionFilter(
    SpectralMixin,
    SpatialMixin,
    TemporalMixin,
    MotionMixin,
    LowlightMixin,
    VisualizationMixin,
    ValidationMixin
):
    """
    Comprehensive cat vision emulation filter based on feline retinal biology.
    
    This class implements biologically accurate computational filters that emulate
    feline visual perception, based on peer-reviewed research on cat retinal
    structure and visual characteristics.
    
    Key characteristics implemented:
    - Vertical slit pupil (3:1 aspect ratio)
    - Enhanced blue-green sensitivity (~500nm peak)
    - Rod-dominated vision (25:1 rod/cone ratio)
    - Tapetum lucidum light reflection (30% enhancement)
    - Reduced color discrimination
    - Enhanced motion detection (1.8x sensitivity)
    - Wide field of view (200°×140°)
    - Reduced spatial acuity (1/6 human acuity)
    - Enhanced temporal processing (55Hz flicker fusion)
    - Horizontal motion bias (1.5x)
    
    Attributes:
        pupil_aspect_ratio (float): Vertical slit pupil aspect ratio (3:1)
        rod_cone_ratio (float): Rod to cone ratio (25:1 vs human 20:1)
        peak_wavelength (int): Peak spectral sensitivity wavelength (500nm)
        tapetum_reflectance (float): Tapetum lucidum reflection factor (0.3)
        visual_field_h (int): Horizontal field of view in degrees (200°)
        visual_field_v (int): Vertical field of view in degrees (140°)
        s_cone_peak (int): S-cone peak sensitivity wavelength (450nm)
        l_cone_peak (int): L-cone peak sensitivity wavelength (556nm)
        rod_peak (int): Rod peak sensitivity wavelength (498nm)
        spatial_acuity_factor (float): Spatial acuity reduction factor (0.167)
        foveal_acuity_cycles_per_degree (float): Peak acuity in cpd (3.0)
        flicker_fusion_threshold (int): Flicker fusion threshold in Hz (55)
        temporal_sensitivity_peak (int): Peak temporal sensitivity in Hz (10)
        motion_sensitivity (float): Motion detection enhancement (1.8)
        horizontal_motion_bias (float): Horizontal motion bias (1.5)
    
    Example:
        >>> from catvision import CatVisionFilter
        >>> import cv2
        >>> 
        >>> # Initialize the filter
        >>> cat_filter = CatVisionFilter()
        >>> 
        >>> # Load an image
        >>> image = cv2.imread('input.jpg')
        >>> 
        >>> # Apply cat vision transformation
        >>> result = cat_filter.apply_cat_vision(image, use_biological_accuracy=True)
        >>> 
        >>> # Save the result
        >>> cv2.imwrite('output.jpg', result)
        >>> 
        >>> # Visualize spectral sensitivity
        >>> cat_filter.plot_spectral_sensitivity_curves()
        >>> 
        >>> # Validate biological accuracy
        >>> validation = cat_filter.validate_biological_accuracy([image])
        >>> print(f"Overall accuracy: {validation['overall_accuracy_score']:.2%}")
    """
    
    def __init__(self):
        """
        Initialize cat vision filter with biologically accurate parameters.
        
        All parameters are based on peer-reviewed research on cat vision
        and retinal physiology.
        """
        # Basic biological parameters based on research
        self.pupil_aspect_ratio = 3.0  # vertical slit
        self.rod_cone_ratio = 25.0     # vs human 20:1
        self.peak_wavelength = 500     # nm (blue-green)
        self.tapetum_reflectance = 0.3 # light amplification factor
        self.visual_field_h = 200      # degrees horizontal
        self.visual_field_v = 140      # degrees vertical
        
        # Spectral sensitivity parameters (biological data)
        self.s_cone_peak = 450  # nm - S-cone peak sensitivity
        self.l_cone_peak = 556  # nm - L-cone peak sensitivity
        self.rod_peak = 498     # nm - Rod peak sensitivity
        
        # Spatial acuity parameters
        self.spatial_acuity_factor = 0.167  # 1/6 of human acuity (20/100-20/200 equivalent)
        self.foveal_acuity_cycles_per_degree = 3.0  # vs human ~18
        
        # Temporal processing parameters
        self.flicker_fusion_threshold = 55  # Hz (vs human ~24Hz)
        self.temporal_sensitivity_peak = 10  # Hz
        
        # Motion detection parameters
        self.motion_sensitivity = 1.8  # Enhanced motion detection
        self.horizontal_motion_bias = 1.5  # Enhanced horizontal motion sensitivity
        
        # Initialize spectral sensitivity curves
        self._init_spectral_curves()
        
        # Color sensitivity weights (legacy - will be replaced by spectral curves)
        self.color_weights = {
            'blue': 1.4,    # Enhanced blue sensitivity
            'green': 1.2,   # Enhanced green sensitivity
            'red': 0.6      # Reduced red sensitivity
        }
    
    def apply_cat_vision(
        self,
        image: np.ndarray,
        previous_frame: Optional[np.ndarray] = None,
        kernel_size: int = 15,
        use_biological_accuracy: bool = True
    ) -> np.ndarray:
        """
        Apply complete cat vision pipeline with enhanced biological accuracy.
        
        This is the main method for applying the cat vision transformation.
        It processes the input image through multiple stages to simulate
        how a cat would perceive the scene.
        
        Pipeline stages (with use_biological_accuracy=True):
        1. Spatial field transformation (wide FOV)
        2. Pupil filter (vertical slit)
        3. Spectral sensitivity correction
        4. Spatial acuity reduction
        5. Rod dominance effects
        6. Tapetum lucidum enhancement
        
        Args:
            image: Input image in BGR format (OpenCV convention)
            previous_frame: Previous frame for motion detection (optional)
            kernel_size: Size of pupil kernel (default: 15, should be odd)
            use_biological_accuracy: Use new biologically accurate methods (True)
                                    vs legacy methods (False)
            
        Returns:
            Cat vision processed image in BGR format
            
        Example:
            >>> cat_filter = CatVisionFilter()
            >>> image = cv2.imread('input.jpg')
            >>> result = cat_filter.apply_cat_vision(image, use_biological_accuracy=True)
            >>> cv2.imwrite('cat_vision.jpg', result)
        """
        if use_biological_accuracy:
            return self._apply_enhanced_cat_vision(image, previous_frame, kernel_size)
        else:
            return self._apply_legacy_cat_vision(image, previous_frame, kernel_size)
    
    def _apply_enhanced_cat_vision(
        self,
        image: np.ndarray,
        previous_frame: Optional[np.ndarray],
        kernel_size: int
    ) -> np.ndarray:
        """
        Enhanced biologically accurate cat vision pipeline.
        
        Args:
            image: Input image
            previous_frame: Previous frame (unused in single-image mode)
            kernel_size: Pupil kernel size
            
        Returns:
            Processed image
        """
        # Step 1: Apply spatial field transformation (wide FOV)
        field_transformed = self.apply_spatial_field_transformation(image)
        
        # Step 2: Apply pupil filter (vertical slit)
        pupil_filtered = self.apply_pupil_filter(field_transformed, kernel_size)
        
        # Step 3: Apply biological spectral sensitivity curves
        spectral_corrected = self.apply_spectral_sensitivity_curves(pupil_filtered)
        
        # Step 4: Simulate spatial acuity reduction
        acuity_reduced = self.simulate_spatial_acuity_reduction(spectral_corrected)
        
        # Step 5: Apply rod dominance effects
        rod_dominated = self.simulate_rod_dominance(acuity_reduced)
        
        # Step 6: Apply tapetum lucidum effect
        tapetum_enhanced = self.apply_tapetum_effect(rod_dominated)
        
        return tapetum_enhanced
    
    def _apply_legacy_cat_vision(
        self,
        image: np.ndarray,
        previous_frame: Optional[np.ndarray],
        kernel_size: int
    ) -> np.ndarray:
        """
        Legacy cat vision pipeline for comparison.
        
        Args:
            image: Input image
            previous_frame: Previous frame for motion detection
            kernel_size: Pupil kernel size
            
        Returns:
            Processed image
        """
        # Step 1: Apply pupil filter (vertical slit)
        pupil_filtered = self.apply_pupil_filter(image, kernel_size)
        
        # Step 2: Adjust color sensitivity (enhance blue-green, reduce red)
        color_adjusted = self.adjust_color_sensitivity(pupil_filtered)
        
        # Step 3: Apply rod dominance effects
        rod_dominated = self.simulate_rod_dominance(color_adjusted)
        
        # Step 4: Apply tapetum lucidum effect
        tapetum_enhanced = self.apply_tapetum_effect(rod_dominated)
        
        # Step 5: Enhance motion detection (if previous frame available)
        if previous_frame is not None:
            motion_enhanced = self.enhance_motion_detection(tapetum_enhanced, previous_frame)
        else:
            motion_enhanced = tapetum_enhanced
            
        return motion_enhanced
    
    def apply_cat_vision_to_sequence(
        self,
        frame_sequence: List[np.ndarray],
        fps: int = 30,
        use_biological_accuracy: bool = True
    ) -> List[np.ndarray]:
        """
        Apply cat vision processing to a sequence of frames with temporal processing.
        
        This method is designed for video processing and includes temporal
        and motion detection enhancements that require multiple frames.
        
        Args:
            frame_sequence: List of consecutive frames in BGR format
            fps: Frames per second of the input sequence
            use_biological_accuracy: Use enhanced biological methods
            
        Returns:
            Processed frame sequence
            
        Example:
            >>> cat_filter = CatVisionFilter()
            >>> frames = [cv2.imread(f'frame_{i:04d}.jpg') for i in range(100)]
            >>> processed = cat_filter.apply_cat_vision_to_sequence(frames, fps=30)
            >>> for i, frame in enumerate(processed):
            ...     cv2.imwrite(f'cat_frame_{i:04d}.jpg', frame)
        """
        if len(frame_sequence) == 0:
            return []
        
        # Apply spatial and spectral processing to each frame
        processed_frames = []
        for frame in frame_sequence:
            processed_frame = self.apply_cat_vision(
                frame, use_biological_accuracy=use_biological_accuracy
            )
            processed_frames.append(processed_frame)
        
        # Apply temporal processing
        if use_biological_accuracy and len(processed_frames) > 1:
            temporal_processed = self.model_temporal_processing(processed_frames, fps)
            motion_enhanced = self.enhanced_motion_detection(temporal_processed)
            return motion_enhanced
        
        return processed_frames
    
    def get_filter_parameters(self) -> Dict:
        """
        Get current filter parameters for documentation and reproducibility.
        
        Returns:
            Dictionary of all filter parameters with biological values
            
        Example:
            >>> cat_filter = CatVisionFilter()
            >>> params = cat_filter.get_filter_parameters()
            >>> print(f"Rod/cone ratio: {params['rod_cone_ratio']}")
            >>> print(f"Spatial acuity: {params['spatial_acuity_factor']}")
        """
        return {
            # Basic biological parameters
            'pupil_aspect_ratio': self.pupil_aspect_ratio,
            'rod_cone_ratio': self.rod_cone_ratio,
            'peak_wavelength': self.peak_wavelength,
            'tapetum_reflectance': self.tapetum_reflectance,
            'visual_field_horizontal': self.visual_field_h,
            'visual_field_vertical': self.visual_field_v,
            
            # Spectral sensitivity parameters
            's_cone_peak': self.s_cone_peak,
            'l_cone_peak': self.l_cone_peak,
            'rod_peak': self.rod_peak,
            
            # Spatial acuity parameters
            'spatial_acuity_factor': self.spatial_acuity_factor,
            'foveal_acuity_cycles_per_degree': self.foveal_acuity_cycles_per_degree,
            
            # Temporal processing parameters
            'flicker_fusion_threshold': self.flicker_fusion_threshold,
            'temporal_sensitivity_peak': self.temporal_sensitivity_peak,
            
            # Motion detection parameters
            'motion_sensitivity': self.motion_sensitivity,
            'horizontal_motion_bias': self.horizontal_motion_bias,
            
            # Legacy parameters (for backward compatibility)
            'color_weights': self.color_weights
        }
    
    def save_parameters(self, filepath: Union[str, Path]) -> None:
        """
        Save filter parameters to JSON file.
        
        Args:
            filepath: Path to save parameters
            
        Example:
            >>> cat_filter = CatVisionFilter()
            >>> cat_filter.save_parameters('cat_vision_params.json')
        """
        params = self.get_filter_parameters()
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(params, f, indent=2)
