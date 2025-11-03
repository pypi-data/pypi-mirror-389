"""Visualization examples for catvision package."""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from catvision import CatVisionFilter
from catvision.utils import create_test_image


def generate_all_visualizations():
    """Generate all available visualizations."""
    print("Cat Vision Filter - Visualization Examples")
    print("=" * 60)
    
    # Initialize filter
    print("\n1. Initializing CatVisionFilter...")
    cat_filter = CatVisionFilter()
    print("   ✓ Filter initialized")
    
    # Create output directory
    output_dir = Path("output") / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n2. Output directory: {output_dir}/")
    
    # 1. Spectral Sensitivity Curves
    print("\n3. Generating spectral sensitivity curves...")
    cat_filter.plot_spectral_sensitivity_curves(
        save_path=str(output_dir / "spectral_sensitivity.png")
    )
    plt.close()
    print("   ✓ Saved: spectral_sensitivity.png")
    
    # 2. Spatial Acuity Map
    print("\n4. Generating spatial acuity map...")
    cat_filter.visualize_spatial_acuity_map(
        image_size=(480, 640),
        save_path=str(output_dir / "spatial_acuity_map.png")
    )
    plt.close()
    print("   ✓ Saved: spatial_acuity_map.png")
    
    # 3. Temporal Frequency Response
    print("\n5. Generating temporal frequency response...")
    cat_filter.demonstrate_temporal_frequency_response(
        save_path=str(output_dir / "temporal_response.png")
    )
    plt.close()
    print("   ✓ Saved: temporal_response.png")
    
    # 4. Pupil Kernel Visualization
    print("\n6. Generating pupil kernel visualization...")
    cat_filter.visualize_pupil_kernel(
        kernel_size=21,
        save_path=str(output_dir / "pupil_kernel.png")
    )
    plt.close()
    print("   ✓ Saved: pupil_kernel.png")
    
    # 5. Motion Detection Comparison
    print("\n7. Generating motion detection comparison...")
    # Create test video frames
    test_frames = []
    for i in range(10):
        frame = create_test_image((240, 320), 'checkerboard')
        # Add some variation
        import numpy as np
        noise = np.random.randint(-5, 5, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        test_frames.append(frame)
    
    cat_filter.compare_motion_detection_sensitivity(
        test_frames,
        save_path=str(output_dir / "motion_comparison.png")
    )
    plt.close()
    print("   ✓ Saved: motion_comparison.png")
    
    print("\n" + "=" * 60)
    print("All visualizations generated successfully!")
    print(f"Check the '{output_dir}' directory for results.")
    print("=" * 60)
    
    return output_dir


def create_parameter_summary():
    """Create a summary visualization of all parameters."""
    print("\n\nCreating parameter summary...")
    
    cat_filter = CatVisionFilter()
    params = cat_filter.get_filter_parameters()
    
    # Create figure with parameter summary
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.axis('off')
    
    # Title
    title = "Cat Vision Filter - Biological Parameters"
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    # Parameter categories
    categories = {
        'Basic Vision Parameters': [
            ('Pupil Aspect Ratio', f"{params['pupil_aspect_ratio']:.1f}:1 (vertical slit)"),
            ('Rod/Cone Ratio', f"{params['rod_cone_ratio']:.1f}:1 (vs human 20:1)"),
            ('Peak Wavelength', f"{params['peak_wavelength']} nm (blue-green)"),
            ('Tapetum Reflectance', f"{params['tapetum_reflectance']:.1%}"),
            ('Field of View (H)', f"{params['visual_field_horizontal']}°"),
            ('Field of View (V)', f"{params['visual_field_vertical']}°"),
        ],
        'Spectral Sensitivity': [
            ('S-cone Peak', f"{params['s_cone_peak']} nm"),
            ('L-cone Peak', f"{params['l_cone_peak']} nm"),
            ('Rod Peak', f"{params['rod_peak']} nm"),
        ],
        'Spatial Acuity': [
            ('Acuity Factor', f"{params['spatial_acuity_factor']:.3f} (1/6 human)"),
            ('Peak Acuity', f"{params['foveal_acuity_cycles_per_degree']:.1f} cpd (vs human ~18)"),
        ],
        'Temporal Processing': [
            ('Flicker Fusion', f"{params['flicker_fusion_threshold']} Hz (vs human ~24)"),
            ('Peak Sensitivity', f"{params['temporal_sensitivity_peak']} Hz"),
        ],
        'Motion Detection': [
            ('Motion Sensitivity', f"{params['motion_sensitivity']}x"),
            ('Horizontal Bias', f"{params['horizontal_motion_bias']}x"),
        ],
    }
    
    # Layout parameters
    y_pos = 0.92
    y_step = 0.045
    
    for category, items in categories.items():
        # Category header
        ax.text(0.05, y_pos, category, fontsize=13, fontweight='bold',
                transform=fig.transFigure)
        y_pos -= y_step * 0.7
        
        # Parameters
        for param_name, param_value in items:
            ax.text(0.08, y_pos, f"• {param_name}:", fontsize=11,
                    transform=fig.transFigure)
            ax.text(0.45, y_pos, param_value, fontsize=11,
                    transform=fig.transFigure, style='italic')
            y_pos -= y_step
        
        y_pos -= y_step * 0.3  # Extra space between categories
    
    # Footer
    footer_text = (
        "All parameters based on peer-reviewed research on cat retinal biology\n"
        "and visual characteristics. Values represent biological measurements\n"
        "from multiple studies on feline vision."
    )
    ax.text(0.5, 0.02, footer_text, fontsize=9, ha='center',
            transform=fig.transFigure, style='italic', color='gray')
    
    # Save
    output_dir = Path("output") / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / "parameter_summary.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"   ✓ Saved: parameter_summary.png")
    
    return str(output_dir / "parameter_summary.png")


def main():
    """Run all visualization examples."""
    # Generate all visualizations
    output_dir = generate_all_visualizations()
    
    # Create parameter summary
    create_parameter_summary()
    
    print("\n" + "=" * 60)
    print("VISUALIZATION SUMMARY")
    print("=" * 60)
    print(f"\nGenerated visualizations:")
    print("  1. spectral_sensitivity.png - Photoreceptor spectral curves")
    print("  2. spatial_acuity_map.png - Visual acuity distribution")
    print("  3. temporal_response.png - Temporal frequency response")
    print("  4. pupil_kernel.png - Vertical slit pupil kernel")
    print("  5. motion_comparison.png - Motion detection comparison")
    print("  6. parameter_summary.png - All biological parameters")
    print(f"\nAll files saved to: {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
