"""Biological validation example for catvision package."""

import numpy as np
from pathlib import Path
from catvision import CatVisionFilter
from catvision.utils import create_test_image


def run_validation_tests():
    """Run comprehensive biological validation tests."""
    print("Cat Vision Filter - Biological Validation")
    print("=" * 60)
    
    # Initialize filter
    print("\n1. Initializing CatVisionFilter...")
    cat_filter = CatVisionFilter()
    print("   ✓ Filter initialized")
    
    # Create test images
    print("\n2. Creating test images...")
    test_images = [
        create_test_image((480, 640), 'checkerboard'),
        create_test_image((480, 640), 'gradient'),
        create_test_image((480, 640), 'color_bars')
    ]
    print(f"   ✓ Created {len(test_images)} test images")
    
    # Run validation
    print("\n3. Running biological accuracy validation...")
    print("   This validates filter behavior against published research data.")
    print()
    
    validation_results = cat_filter.validate_biological_accuracy(test_images)
    
    # Display results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    print("\n📊 Individual Component Validation:")
    print("-" * 60)
    
    # Spectral sensitivity
    spectral_score = validation_results['spectral_sensitivity_validation']
    print(f"\n1. Spectral Sensitivity Curves:")
    print(f"   Score: {spectral_score:.2%}")
    print(f"   Status: {'✓ PASS' if spectral_score > 0.8 else '✗ FAIL'}")
    print(f"   Details:")
    print(f"     • S-cone peak: {cat_filter.s_cone_peak} nm (expected: 450 nm)")
    print(f"     • L-cone peak: {cat_filter.l_cone_peak} nm (expected: 556 nm)")
    print(f"     • Rod peak: {cat_filter.rod_peak} nm (expected: 498 nm)")
    
    # Spatial acuity
    spatial_score = validation_results['spatial_acuity_validation']
    print(f"\n2. Spatial Acuity Reduction:")
    print(f"   Score: {spatial_score:.2%}")
    print(f"   Status: {'✓ PASS' if spatial_score > 0.5 else '✗ FAIL'}")
    print(f"   Details:")
    print(f"     • Acuity factor: {cat_filter.spatial_acuity_factor}")
    print(f"     • Expected: 0.167 (1/6 human acuity)")
    print(f"     • Peak acuity: {cat_filter.foveal_acuity_cycles_per_degree} cpd")
    print(f"     • Human comparison: ~18 cpd")
    
    # Temporal response
    temporal_score = validation_results['temporal_response_validation']
    print(f"\n3. Temporal Frequency Response:")
    print(f"   Score: {temporal_score:.2%}")
    print(f"   Status: {'✓ PASS' if temporal_score > 0.5 else '✗ FAIL'}")
    print(f"   Details:")
    print(f"     • Flicker fusion: {cat_filter.flicker_fusion_threshold} Hz")
    print(f"     • Human comparison: ~24 Hz")
    print(f"     • Peak sensitivity: {cat_filter.temporal_sensitivity_peak} Hz")
    
    # Motion detection
    motion_score = validation_results['motion_detection_validation']
    print(f"\n4. Motion Detection Enhancement:")
    print(f"   Score: {motion_score:.2%}")
    print(f"   Status: {'✓ PASS' if motion_score > 0.5 else '✗ FAIL'}")
    print(f"   Details:")
    print(f"     • Motion sensitivity: {cat_filter.motion_sensitivity}x")
    print(f"     • Horizontal bias: {cat_filter.horizontal_motion_bias}x")
    
    # Overall score
    overall_score = validation_results['overall_accuracy_score']
    print("\n" + "=" * 60)
    print(f"📈 OVERALL BIOLOGICAL ACCURACY: {overall_score:.2%}")
    print("=" * 60)
    
    if overall_score >= 0.8:
        grade = "A (Excellent)"
        status = "✓ HIGHLY ACCURATE"
    elif overall_score >= 0.6:
        grade = "B (Good)"
        status = "✓ ACCURATE"
    elif overall_score >= 0.4:
        grade = "C (Fair)"
        status = "⚠ NEEDS IMPROVEMENT"
    else:
        grade = "D (Poor)"
        status = "✗ INACCURATE"
    
    print(f"\nGrade: {grade}")
    print(f"Status: {status}")
    
    # Save validation results
    print("\n5. Saving validation results...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    import json
    with open(output_dir / "validation_results.json", 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"   ✓ Results saved to {output_dir}/validation_results.json")
    
    print("\n" + "=" * 60)
    print("Validation complete!")
    print("=" * 60)
    
    return validation_results


def compare_methods():
    """Compare biological vs legacy methods."""
    print("\n\nMethod Comparison: Biological vs Legacy")
    print("=" * 60)
    
    cat_filter = CatVisionFilter()
    test_image = create_test_image((480, 640), 'checkerboard')
    
    # Process with both methods
    print("\n1. Processing with biological method...")
    result_bio = cat_filter.apply_cat_vision(test_image, use_biological_accuracy=True)
    
    print("2. Processing with legacy method...")
    result_legacy = cat_filter.apply_cat_vision(test_image, use_biological_accuracy=False)
    
    # Compare results
    print("\n3. Comparison:")
    diff = np.abs(result_bio.astype(float) - result_legacy.astype(float))
    mean_diff = np.mean(diff)
    max_diff = np.max(diff)
    
    print(f"   • Mean difference: {mean_diff:.2f}")
    print(f"   • Max difference: {max_diff:.2f}")
    print(f"   • Similarity: {100 * (1 - mean_diff/255):.1f}%")
    
    print("\nKey differences:")
    print("   • Biological method includes:")
    print("     - Spectral sensitivity curves")
    print("     - Spatial field transformation")
    print("     - Frequency domain filtering")
    print("   • Legacy method is simpler but less accurate")
    
    # Save comparison
    output_dir = Path("output")
    from catvision.utils import save_image
    save_image(result_bio, output_dir / "comparison_biological.jpg")
    save_image(result_legacy, output_dir / "comparison_legacy.jpg")
    
    print(f"\n   ✓ Comparison images saved to {output_dir}/")


def main():
    """Run all validation examples."""
    # Run validation tests
    results = run_validation_tests()
    
    # Compare methods
    compare_methods()
    
    print("\n" + "=" * 60)
    print("All validation examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
