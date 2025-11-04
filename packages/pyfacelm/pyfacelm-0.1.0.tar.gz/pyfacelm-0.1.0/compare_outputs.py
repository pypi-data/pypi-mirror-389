#!/usr/bin/env python3
"""
Create side-by-side comparison of PyfaceLM wrapper vs original C++ output.
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyfacelm import CLNFDetector, visualize_landmarks

try:
    import cv2
except ImportError:
    print("opencv-python required for this comparison script")
    sys.exit(1)


def main():
    test_image = "/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/frames/IMG_8401.jpg"
    cpp_landmarks_path = "/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/results/cpp_landmarks.npy"
    output_dir = Path("/Users/johnwilsoniv/Documents/SplitFace Open3/PyfaceLM/test_output")
    output_dir.mkdir(exist_ok=True)

    print("Creating side-by-side comparison...")

    # Load image
    img = cv2.imread(test_image)
    h, w = img.shape[:2]

    # Get wrapper results
    print("\n1. Running PyfaceLM wrapper...")
    detector = CLNFDetector()
    wrapper_landmarks, wrapper_conf, wrapper_bbox = detector.detect(test_image)

    # Load C++ ground truth
    print("2. Loading C++ ground truth...")
    cpp_landmarks = np.load(cpp_landmarks_path)
    cpp_bbox = CLNFDetector.compute_bbox(cpp_landmarks)

    # Create visualizations
    print("3. Creating visualizations...")

    # Wrapper visualization
    wrapper_vis = visualize_landmarks(
        test_image,
        wrapper_landmarks,
        bbox=wrapper_bbox,
        confidence=wrapper_conf
    )

    # C++ visualization (no confidence since not in .npy file)
    cpp_vis = visualize_landmarks(
        test_image,
        cpp_landmarks,
        bbox=cpp_bbox,
        confidence=None
    )

    # Add labels
    cv2.putText(
        wrapper_vis,
        "PyfaceLM Wrapper",
        (10, h - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 255, 0),
        3
    )

    cv2.putText(
        cpp_vis,
        "C++ Ground Truth",
        (10, h - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 255, 0),
        3
    )

    # Compute error metrics
    error = np.abs(wrapper_landmarks - cpp_landmarks)
    mean_error = error.mean()
    max_error = error.max()
    rmse = np.sqrt((error ** 2).mean())

    # Create difference visualization
    diff_vis = img.copy()
    for i in range(68):
        wx, wy = wrapper_landmarks[i]
        cx, cy = cpp_landmarks[i]

        # Draw line between wrapper and C++ landmarks
        cv2.line(
            diff_vis,
            (int(wx), int(wy)),
            (int(cx), int(cy)),
            (0, 0, 255),
            2
        )

        # Draw wrapper landmarks (green)
        cv2.circle(diff_vis, (int(wx), int(wy)), 3, (0, 255, 0), -1)

        # Draw C++ landmarks (blue)
        cv2.circle(diff_vis, (int(cx), int(cy)), 3, (255, 0, 0), -1)

    # Add error metrics
    cv2.putText(
        diff_vis,
        f"Mean Error: {mean_error:.4f}px",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2
    )
    cv2.putText(
        diff_vis,
        f"Max Error: {max_error:.4f}px",
        (10, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2
    )
    cv2.putText(
        diff_vis,
        f"RMSE: {rmse:.4f}px",
        (10, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2
    )
    cv2.putText(
        diff_vis,
        "Difference (Green=Wrapper, Blue=C++)",
        (10, h - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (0, 255, 255),
        3
    )

    # Create side-by-side comparison
    comparison = np.hstack([wrapper_vis, cpp_vis, diff_vis])

    # Save outputs
    output_path = output_dir / "comparison_wrapper_vs_cpp.jpg"
    cv2.imwrite(str(output_path), comparison)

    print(f"\n✓ Comparison saved to: {output_path}")
    print(f"\n  Wrapper landmarks: {wrapper_landmarks.shape}")
    print(f"  C++ landmarks:     {cpp_landmarks.shape}")
    print(f"  Wrapper bbox:      {wrapper_bbox}")
    print(f"  C++ bbox:          {cpp_bbox}")
    print(f"\n  Mean error:  {mean_error:.6f} px")
    print(f"  Max error:   {max_error:.6f} px")
    print(f"  RMSE:        {rmse:.6f} px")
    print(f"\n✓ Perfect match!" if mean_error < 0.01 else f"✗ Error too high!")


if __name__ == "__main__":
    main()
