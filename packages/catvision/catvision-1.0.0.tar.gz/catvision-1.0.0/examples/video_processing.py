"""Video processing example for catvision package."""

import cv2
import numpy as np
from pathlib import Path
from catvision import CatVisionFilter
from catvision.utils import create_test_image


def create_test_video_frames(num_frames=30, size=(480, 640)):
    """
    Create a simple test video with moving objects.
    
    Args:
        num_frames: Number of frames to generate
        size: Frame size as (height, width)
        
    Returns:
        List of frames
    """
    frames = []
    h, w = size
    
    for i in range(num_frames):
        # Create base frame
        frame = np.full((h, w, 3), 50, dtype=np.uint8)
        
        # Add moving circle (simulates prey)
        center_x = int(w * 0.2 + (w * 0.6 * i / num_frames))
        center_y = h // 2
        cv2.circle(frame, (center_x, center_y), 30, (200, 200, 200), -1)
        
        # Add static background elements
        cv2.rectangle(frame, (10, 10), (100, 100), (100, 100, 100), -1)
        cv2.rectangle(frame, (w-100, 10), (w-10, 100), (100, 100, 100), -1)
        
        frames.append(frame)
    
    return frames


def process_video_sequence():
    """Demonstrate video sequence processing with cat vision."""
    print("Cat Vision Filter - Video Processing Example")
    print("=" * 60)
    
    # Initialize filter
    print("\n1. Initializing CatVisionFilter...")
    cat_filter = CatVisionFilter()
    print("   ✓ Filter initialized")
    
    # Create test video frames
    print("\n2. Creating test video sequence...")
    num_frames = 30
    frames = create_test_video_frames(num_frames, size=(360, 480))
    print(f"   ✓ Created {len(frames)} frames")
    
    # Process video sequence
    print("\n3. Processing video with cat vision...")
    print("   - Applying spatial transformations...")
    print("   - Applying spectral corrections...")
    print("   - Applying temporal processing...")
    print("   - Applying motion enhancement...")
    
    processed_frames = cat_filter.apply_cat_vision_to_sequence(
        frames,
        fps=30,
        use_biological_accuracy=True
    )
    print("   ✓ Video processing complete")
    
    # Save a few sample frames
    print("\n4. Saving sample frames...")
    output_dir = Path("output") / "video_frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save every 5th frame
    for i in range(0, num_frames, 5):
        cv2.imwrite(str(output_dir / f"original_frame_{i:03d}.jpg"), frames[i])
        cv2.imwrite(str(output_dir / f"cat_vision_frame_{i:03d}.jpg"), processed_frames[i])
    
    print(f"   ✓ Sample frames saved to {output_dir}/")
    
    # Display statistics
    print("\n5. Processing statistics:")
    print(f"   • Total frames processed: {len(processed_frames)}")
    print(f"   • Frame size: {frames[0].shape}")
    print(f"   • Processing mode: Biological accuracy enabled")
    print(f"   • Temporal processing: {cat_filter.flicker_fusion_threshold} Hz threshold")
    print(f"   • Motion sensitivity: {cat_filter.motion_sensitivity}x")
    
    print("\n" + "=" * 60)
    print("Video processing example completed!")
    print("=" * 60)


def process_video_file(input_path, output_path):
    """
    Process a video file with cat vision filter.
    
    This is a template function showing how to process real video files.
    
    Args:
        input_path: Path to input video file
        output_path: Path to output video file
    """
    print(f"\nProcessing video file: {input_path}")
    
    # Open video file
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {input_path}")
        return
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video properties: {width}x{height} @ {fps} FPS, {total_frames} frames")
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Initialize filter
    cat_filter = CatVisionFilter()
    
    # Process frames in batches for temporal processing
    batch_size = 10
    frame_buffer = []
    
    print("Processing frames...")
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_buffer.append(frame)
        
        # Process batch when buffer is full
        if len(frame_buffer) >= batch_size:
            processed = cat_filter.apply_cat_vision_to_sequence(
                frame_buffer,
                fps=fps,
                use_biological_accuracy=True
            )
            
            # Write processed frames
            for processed_frame in processed:
                out.write(processed_frame)
            
            frame_count += len(processed)
            print(f"  Processed {frame_count}/{total_frames} frames", end='\r')
            
            frame_buffer = []
    
    # Process remaining frames
    if frame_buffer:
        processed = cat_filter.apply_cat_vision_to_sequence(
            frame_buffer,
            fps=fps,
            use_biological_accuracy=True
        )
        for processed_frame in processed:
            out.write(processed_frame)
    
    # Cleanup
    cap.release()
    out.release()
    
    print(f"\n✓ Video saved to {output_path}")


def main():
    """Run video processing examples."""
    # Run sequence processing example
    process_video_sequence()
    
    # Uncomment to process a real video file:
    # process_video_file('input_video.mp4', 'output/cat_vision_video.mp4')
    
    print("\nNote: To process your own video files, uncomment and modify")
    print("      the process_video_file() call at the end of this script.")


if __name__ == "__main__":
    main()
