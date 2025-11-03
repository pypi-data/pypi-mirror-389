"""Basic usage example for catvision package."""

import cv2
import numpy as np
from pathlib import Path
from catvision import CatVisionFilter
from catvision.utils import create_test_image, save_image


def main():
    """Demonstrate basic usage of the cat vision filter."""
    print("Cat Vision Filter - Basic Usage Example")
    print("=" * 60)
    
    # Initialize the filter
    print("\n1. Initializing CatVisionFilter...")
    cat_filter = CatVisionFilter()
    print("   ✓ Filter initialized successfully")
    
    # Create or load a test image
    print("\n2. Loading test image...")
    # For this example, we'll create a test image
    # In practice, you would use: image = cv2.imread('your_image.jpg')
    image = create_test_image((480, 640), 'color_bars')
    print(f"   ✓ Image loaded: {image.shape}")
    
    # Apply cat vision transformation (biologically accurate mode)
    print("\n3. Applying cat vision transformation (biological mode)...")
    result_biological = cat_filter.apply_cat_vision(
        image, 
        use_biological_accuracy=True
    )
    print("   ✓ Biological transformation complete")
    
    # Apply cat vision transformation (legacy mode for comparison)
    print("\n4. Applying cat vision transformation (legacy mode)...")
    result_legacy = cat_filter.apply_cat_vision(
        image,
        use_biological_accuracy=False
    )
    print("   ✓ Legacy transformation complete")
    
    # Save results
    print("\n5. Saving results...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    save_image(image, output_dir / "original.jpg")
    save_image(result_biological, output_dir / "cat_vision_biological.jpg")
    save_image(result_legacy, output_dir / "cat_vision_legacy.jpg")
    print(f"   ✓ Results saved to {output_dir}/")
    
    # Get filter parameters
    print("\n6. Filter parameters:")
    params = cat_filter.get_filter_parameters()
    print(f"   • Rod/cone ratio: {params['rod_cone_ratio']}")
    print(f"   • Spatial acuity factor: {params['spatial_acuity_factor']}")
    print(f"   • Flicker fusion threshold: {params['flicker_fusion_threshold']} Hz")
    print(f"   • Motion sensitivity: {params['motion_sensitivity']}")
    
    # Save parameters to file
    cat_filter.save_parameters(output_dir / "parameters.json")
    print(f"   ✓ Parameters saved to {output_dir}/parameters.json")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print(f"Check the '{output_dir}' directory for results.")
    print("=" * 60)


if __name__ == "__main__":
    main()
