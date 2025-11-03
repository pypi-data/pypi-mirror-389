# CatVision - Biologically Accurate Cat Vision Filter

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package that replicates the biologically accurate vision of cats based on peer-reviewed research on feline retinal structure and visual characteristics.

## Features

### Biologically Accurate Cat Vision Simulation

- **🔵 Spectral Sensitivity**: Dichromatic vision with S-cone (450nm) and L-cone (556nm) peaks
- **👁️ Vertical Slit Pupil**: 3:1 aspect ratio for enhanced depth of field
- **🌙 Rod-Dominated Vision**: 25:1 rod/cone ratio for superior night vision
- **✨ Tapetum Lucidum**: 30% light reflection enhancement for low-light conditions
- **📐 Reduced Spatial Acuity**: 1/6 human acuity (3 vs 18 cycles per degree)
- **🎬 Enhanced Temporal Processing**: 55Hz flicker fusion threshold
- **🏃 Motion Detection**: 1.8x human sensitivity with horizontal bias
- **👀 Wide Field of View**: 200° horizontal × 140° vertical

## Installation

### From PyPI

```bash
pip install catvision
```

### From Source

```bash
git clone https://github.com/aryashah2k/catvision.git
cd catvision
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from catvision import CatVisionFilter
import cv2

# Initialize the filter
cat_filter = CatVisionFilter()

# Load an image
image = cv2.imread('input.jpg')

# Apply cat vision transformation
result = cat_filter.apply_cat_vision(image, use_biological_accuracy=True)

# Save the result
cv2.imwrite('cat_vision_output.jpg', result)
```

## Usage Examples

### Basic Image Processing

```python
from catvision import CatVisionFilter
import cv2

# Create filter instance
cat_filter = CatVisionFilter()

# Process single image
image = cv2.imread('photo.jpg')
cat_view = cat_filter.apply_cat_vision(image)
cv2.imwrite('cat_perspective.jpg', cat_view)
```

### Video Processing

```python
from catvision import CatVisionFilter
import cv2

cat_filter = CatVisionFilter()

# Process video sequence
frames = []  # Your video frames
processed_frames = cat_filter.apply_cat_vision_to_sequence(
    frames, 
    fps=30,
    use_biological_accuracy=True
)
```

### Biological Validation

```python
from catvision import CatVisionFilter

cat_filter = CatVisionFilter()

# Validate against biological data
test_images = [...]  # Your test images
validation = cat_filter.validate_biological_accuracy(test_images)

print(f"Overall Accuracy: {validation['overall_accuracy_score']:.2%}")
print(f"Spectral Sensitivity: {validation['spectral_sensitivity_validation']:.2%}")
print(f"Spatial Acuity: {validation['spatial_acuity_validation']:.2%}")
```

### Visualizations

```python
from catvision import CatVisionFilter

cat_filter = CatVisionFilter()

# Generate spectral sensitivity curves
cat_filter.plot_spectral_sensitivity_curves(save_path='spectral_curves.png')

# Visualize spatial acuity map
cat_filter.visualize_spatial_acuity_map(
    image_size=(480, 640),
    save_path='acuity_map.png'
)

# Show temporal frequency response
cat_filter.demonstrate_temporal_frequency_response(save_path='temporal_response.png')
```

## Biological Parameters

All parameters are based on peer-reviewed research:

| Parameter | Value | Human Comparison |
|-----------|-------|------------------|
| **Pupil Shape** | 3:1 vertical slit | Circular |
| **Rod/Cone Ratio** | 25:1 | 20:1 |
| **S-cone Peak** | 450nm (blue) | 420nm |
| **L-cone Peak** | 556nm (green-yellow) | 534nm (M), 564nm (L) |
| **Rod Peak** | 498nm (blue-green) | 498nm |
| **Spatial Acuity** | 3 cpd | ~18 cpd |
| **Flicker Fusion** | 55 Hz | ~24 Hz |
| **Field of View** | 200°×140° | 180°×135° |
| **Tapetum Reflectance** | 30% enhancement | None |

## Architecture

The package uses a modular mixin architecture:

```
CatVisionFilter
├── SpectralMixin (spectral.py)
│   ├── Spectral sensitivity curves
│   └── Color perception adjustments
├── SpatialMixin (spatial.py)
│   ├── Pupil kernel (vertical slit)
│   ├── Spatial acuity reduction
│   └── Field of view transformation
├── TemporalMixin (temporal.py)
│   ├── Temporal frequency processing
│   └── Flicker fusion modeling
├── MotionMixin (motion.py)
│   ├── Optical flow (Lucas-Kanade/Farneback)
│   ├── Motion enhancement
│   └── Directional sensitivity
├── LowlightMixin (lowlight.py)
│   ├── Tapetum lucidum effect
│   └── Rod dominance simulation
├── VisualizationMixin (visualization.py)
│   └── Scientific visualizations
└── ValidationMixin (validation.py)
    └── Biological accuracy validation
```

## API Reference

### Core Class

#### `CatVisionFilter()`

Main filter class that combines all cat vision characteristics.

**Methods:**

- `apply_cat_vision(image, previous_frame=None, kernel_size=15, use_biological_accuracy=True)` - Apply complete cat vision pipeline
- `apply_cat_vision_to_sequence(frame_sequence, fps=30, use_biological_accuracy=True)` - Process video sequence
- `get_filter_parameters()` - Get current biological parameters
- `save_parameters(filepath)` - Save parameters to JSON file
- `validate_biological_accuracy(test_images, ground_truth_data=None)` - Validate filter accuracy

**Visualization Methods:**

- `plot_spectral_sensitivity_curves(save_path=None)` - Plot photoreceptor spectral curves
- `visualize_spatial_acuity_map(image_size, save_path=None)` - Show acuity distribution
- `demonstrate_temporal_frequency_response(save_path=None)` - Display temporal sensitivity
- `visualize_pupil_kernel(kernel_size=15, save_path=None)` - Show pupil convolution kernel

## Examples

The package includes comprehensive examples in the `examples/` directory:

- `basic_usage.py` - Simple image processing
- `video_processing.py` - Video sequence processing
- `biological_validation.py` - Accuracy validation
- `visualizations.py` - Generate all visualizations

Run examples:

```bash
python examples/basic_usage.py
python examples/biological_validation.py
python examples/visualizations.py
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=catvision --cov-report=term-missing

# Run specific test module
pytest tests/test_spectral.py -v
```

## Scientific Background

This implementation is based on published research on cat vision:

### Key References

1. **Spectral Sensitivity**: Loop et al. (1987) - "Spectral characteristics of cat retinal ganglion cells"
2. **Spatial Acuity**: Blake (1979) - "The visual acuity of the cat"
3. **Temporal Processing**: Pasternak & Merigan (1981) - "The luminance dependence of spatial vision in the cat"
4. **Motion Detection**: Orban et al. (1986) - "Velocity selectivity in the cat visual system"
5. **Tapetum Lucidum**: Ollivier et al. (2004) - "Retinal structure and light intensification"

### Biological Accuracy

The filter achieves **high biological accuracy** through:

- Direct implementation of measured spectral sensitivity curves
- Frequency-domain spatial filtering based on contrast sensitivity functions
- Temporal processing matching measured flicker fusion thresholds
- Motion detection calibrated to behavioral measurements

## Performance

- **Single Image (640×480)**: ~100ms (biological mode)
- **Video Frame (1080p)**: ~200ms per frame
- **Memory Usage**: <500MB for typical workloads

## Requirements

- Python 3.8+
- opencv-python-headless >= 4.8.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- matplotlib >= 3.7.0
- Pillow >= 10.0.0

## Contributing

Contributions are welcome! Please fork the Repository, create a feature branch, and submit a pull request!

### Development Setup

```bash
git clone https://github.com/aryashah2k/catvision.git
cd catvision
pip install -e ".[dev]"
pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this package in your research, please cite:

```bibtex
@software{catvision2025,
  title={CatVision: Biologically Accurate Cat Vision Filter},
  author={Arya Shah and Vaibhav Tripathi},
  year={2025},
  url={https://github.com/aryashah2k/catvision}
}
```

## Acknowledgments

- Based on decades of cat vision research by neuroscientists worldwide
- Inspired by the need for accurate animal vision simulation in research
- Built with modern Python best practices and scientific computing tools

## Contact

- **Issues**: [GitHub Issues](https://github.com/aryashah2k/catvision/issues)
- **Email**: {arya[dot]shah, vaibhav[dot]tripathi}[at]iitgn[dot]ac[dot]in

---

**Note**: This package is designed for scientific and educational purposes. For neuroscience research applications, please validate results against your specific requirements.
