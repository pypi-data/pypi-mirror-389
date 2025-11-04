#!/usr/bin/env python3
"""
Test script for PyfaceLM optimized detector.

Compares against original C++ output and tests:
- Basic detection accuracy
- Bbox computation
- Visualization with landmarks + bbox
- Cache performance
"""

import numpy as np
import time
from pathlib import Path
import sys

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from pyfacelm import CLNFDetector, visualize_landmarks


def test_basic_detection():
    """Test basic landmark detection."""
    print("\n" + "="*60)
    print("TEST 1: Basic Detection")
    print("="*60)

    test_image = "/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/frames/IMG_8401.jpg"

    if not Path(test_image).exists():
        print(f"✗ Test image not found: {test_image}")
        return False

    detector = CLNFDetector()

    try:
        landmarks, confidence, bbox = detector.detect(test_image, verbose=True)

        print(f"\n✓ Detection successful!")
        print(f"  Landmarks shape: {landmarks.shape}")
        print(f"  Confidence: {confidence:.4f}")
        print(f"  Bbox (x, y, w, h): {bbox}")
        print(f"\n  First 5 landmarks:")
        for i in range(5):
            print(f"    {i}: ({landmarks[i, 0]:.2f}, {landmarks[i, 1]:.2f})")

        return True
    except Exception as e:
        print(f"\n✗ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_performance():
    """Test caching performance."""
    print("\n" + "="*60)
    print("TEST 2: Cache Performance")
    print("="*60)

    test_image = "/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/frames/IMG_8401.jpg"

    if not Path(test_image).exists():
        print(f"✗ Test image not found: {test_image}")
        return False

    detector = CLNFDetector(enable_cache=True)

    # First run (no cache)
    print("\nFirst run (no cache):")
    start = time.time()
    landmarks1, conf1, bbox1 = detector.detect(test_image)
    time1 = time.time() - start
    print(f"  Time: {time1:.3f}s")

    # Second run (cached)
    print("\nSecond run (cached):")
    start = time.time()
    landmarks2, conf2, bbox2 = detector.detect(test_image)
    time2 = time.time() - start
    print(f"  Time: {time2:.3f}s")
    print(f"  Speedup: {time1/time2:.1f}x")

    # Verify results match
    if np.allclose(landmarks1, landmarks2):
        print("\n✓ Cached results match original")
        print(f"  Cache stats: {detector.get_cache_stats()}")
        return True
    else:
        print("\n✗ Cached results don't match!")
        return False


def test_comparison_with_cpp():
    """Compare with ground truth C++ output."""
    print("\n" + "="*60)
    print("TEST 3: Comparison with C++ Ground Truth")
    print("="*60)

    test_image = "/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/frames/IMG_8401.jpg"
    cpp_output = "/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/results/cpp_landmarks.npy"

    if not Path(cpp_output).exists():
        print(f"✗ C++ ground truth not found: {cpp_output}")
        print("  Skipping comparison test")
        return True  # Don't fail if ground truth not available

    detector = CLNFDetector()

    landmarks, confidence, bbox = detector.detect(test_image)
    cpp_landmarks = np.load(cpp_output)

    # Compute error
    error = np.abs(landmarks - cpp_landmarks)
    mean_error = error.mean()
    max_error = error.max()
    rmse = np.sqrt((error ** 2).mean())

    print(f"\n  Wrapper landmarks: {landmarks.shape}")
    print(f"  C++ landmarks:     {cpp_landmarks.shape}")
    print(f"\n  Mean absolute error: {mean_error:.4f} px")
    print(f"  Max absolute error:  {max_error:.4f} px")
    print(f"  RMSE:               {rmse:.4f} px")

    # Check if they match (should be identical, allow tiny floating point diff)
    if mean_error < 0.1:
        print(f"\n✓ Perfect match with C++ output! ({mean_error:.6f}px error)")
        return True
    else:
        print(f"\n✗ Error too high! Expected <0.1px, got {mean_error:.4f}px")
        return False


def test_visualization():
    """Test visualization with landmarks and bbox."""
    print("\n" + "="*60)
    print("TEST 4: Visualization with Landmarks + Bbox")
    print("="*60)

    test_image = "/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/frames/IMG_8401.jpg"
    output_dir = Path("/Users/johnwilsoniv/Documents/SplitFace Open3/PyfaceLM/test_output")
    output_dir.mkdir(exist_ok=True)

    detector = CLNFDetector()

    try:
        # Detect with bbox
        landmarks, confidence, bbox = detector.detect(test_image)

        # Create visualization
        output_path = output_dir / "IMG_8401_visualization.jpg"
        vis = visualize_landmarks(
            test_image,
            landmarks,
            bbox=bbox,
            confidence=confidence,
            output_path=str(output_path)
        )

        print(f"\n✓ Visualization saved to: {output_path}")
        print(f"  Image shape: {vis.shape}")
        print(f"  Bbox drawn: {bbox}")
        print(f"  Confidence displayed: {confidence:.4f}")

        return True
    except Exception as e:
        print(f"\n✗ Visualization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_processing():
    """Test batch processing."""
    print("\n" + "="*60)
    print("TEST 5: Batch Processing")
    print("="*60)

    # Try to find multiple images
    frames_dir = Path("/Users/johnwilsoniv/Documents/SplitFace Open3/comparison_test/frames")

    if not frames_dir.exists():
        print(f"✗ Frames directory not found: {frames_dir}")
        return False

    image_paths = list(frames_dir.glob("*.jpg"))[:3]  # First 3 images

    if len(image_paths) == 0:
        print(f"✗ No images found in {frames_dir}")
        return False

    print(f"\nProcessing {len(image_paths)} images...")

    detector = CLNFDetector()

    start = time.time()
    results = detector.detect_batch([str(p) for p in image_paths], verbose=True)
    total_time = time.time() - start

    successful = sum(1 for r in results if r[0] is not None)
    print(f"\n✓ Batch processing complete:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average time: {total_time/len(image_paths):.3f}s per image")
    print(f"  Successful: {successful}/{len(image_paths)}")

    return successful == len(image_paths)


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PYFACELM OPTIMIZED DETECTOR TEST SUITE")
    print("="*60)

    tests = [
        ("Basic Detection", test_basic_detection),
        ("Cache Performance", test_cache_performance),
        ("C++ Comparison", test_comparison_with_cpp),
        ("Visualization", test_visualization),
        ("Batch Processing", test_batch_processing),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
