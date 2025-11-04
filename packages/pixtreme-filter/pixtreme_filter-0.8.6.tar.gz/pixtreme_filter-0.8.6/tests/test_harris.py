"""Tests for Harris Corner Detection"""

import cupy as cp
import numpy as np
import pytest


class TestHarrisCorner:
    """Test suite for Harris Corner Detection"""

    def test_corner_harris_basic(self):
        """Test basic corner detection with synthetic corner"""
        # Create simple L-shaped corner
        image = cp.zeros((50, 50), dtype=cp.float32)
        image[20:30, 20:50] = 1.0  # Horizontal bar
        image[20:50, 20:30] = 1.0  # Vertical bar

        from pixtreme_filter import corner_harris

        # Compute corner response
        response = corner_harris(image, blockSize=3, ksize=3, k=0.04)

        # Response should be 2D array
        assert response.ndim == 2
        assert response.shape == image.shape
        assert response.dtype == cp.float32

    def test_corner_harris_grayscale_input(self):
        """Test with grayscale image"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.float32)
        response = corner_harris(image, blockSize=3, ksize=3, k=0.04)

        assert response.shape == (64, 64)
        assert response.dtype == cp.float32

    def test_corner_harris_color_input(self):
        """Test with color image (should convert to grayscale)"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64, 3).astype(cp.float32)
        response = corner_harris(image, blockSize=3, ksize=3, k=0.04)

        # Output should be 2D (grayscale response map)
        assert response.ndim == 2
        assert response.shape == (64, 64)
        assert response.dtype == cp.float32

    def test_corner_harris_different_block_sizes(self):
        """Test with different block sizes"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.float32)

        # Different block sizes should work
        response_3 = corner_harris(image, blockSize=3, ksize=3, k=0.04)
        response_5 = corner_harris(image, blockSize=5, ksize=3, k=0.04)
        response_7 = corner_harris(image, blockSize=7, ksize=3, k=0.04)

        assert response_3.shape == (64, 64)
        assert response_5.shape == (64, 64)
        assert response_7.shape == (64, 64)

        # Different block sizes should produce different responses
        assert not cp.allclose(response_3, response_5)

    def test_corner_harris_different_ksize(self):
        """Test with different Sobel kernel sizes"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.float32)

        # Different Sobel kernel sizes
        response_3 = corner_harris(image, blockSize=3, ksize=3, k=0.04)
        response_5 = corner_harris(image, blockSize=3, ksize=5, k=0.04)

        assert response_3.shape == (64, 64)
        assert response_5.shape == (64, 64)

        # Different ksize should produce different responses
        assert not cp.allclose(response_3, response_5)

    def test_corner_harris_different_k_values(self):
        """Test with different k parameter values"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.float32)

        # Different k values (Harris free parameter)
        response_k_small = corner_harris(image, blockSize=3, ksize=3, k=0.01)
        response_k_medium = corner_harris(image, blockSize=3, ksize=3, k=0.04)
        response_k_large = corner_harris(image, blockSize=3, ksize=3, k=0.15)

        assert response_k_small.shape == (64, 64)
        assert response_k_medium.shape == (64, 64)
        assert response_k_large.shape == (64, 64)

        # Different k values should produce different responses
        assert not cp.allclose(response_k_small, response_k_medium)
        assert not cp.allclose(response_k_medium, response_k_large)

    def test_corner_harris_checkerboard_pattern(self):
        """Test corner detection on checkerboard (many corners)"""
        from pixtreme_filter import corner_harris

        # Create checkerboard pattern (8x8 squares)
        image = cp.zeros((64, 64), dtype=cp.float32)
        for i in range(8):
            for j in range(8):
                if (i + j) % 2 == 0:
                    image[i * 8 : (i + 1) * 8, j * 8 : (j + 1) * 8] = 1.0

        response = corner_harris(image, blockSize=3, ksize=3, k=0.04)

        # Checkerboard should have strong corner responses at intersections
        # (qualitative check - max response should be significantly positive)
        max_response = float(cp.max(response))
        assert max_response > 0.01, f"Expected strong corners, got max response {max_response}"

    def test_corner_harris_uniform_image(self):
        """Test with uniform image (no corners)"""
        from pixtreme_filter import corner_harris

        # Uniform image - no features
        image = cp.ones((64, 64), dtype=cp.float32) * 0.5

        response = corner_harris(image, blockSize=3, ksize=3, k=0.04)

        # Uniform image should have near-zero response everywhere
        max_abs_response = float(cp.max(cp.abs(response)))
        assert max_abs_response < 1e-5, f"Expected near-zero response, got {max_abs_response}"

    def test_corner_harris_horizontal_edge(self):
        """Test with horizontal edge (no corners)"""
        from pixtreme_filter import corner_harris

        # Horizontal edge - should not produce corner response
        image = cp.zeros((64, 64), dtype=cp.float32)
        image[32:, :] = 1.0

        response = corner_harris(image, blockSize=3, ksize=3, k=0.04)

        # Edge should have lower response than corners
        # (this is qualitative - we just check it doesn't crash)
        assert response.shape == (64, 64)
        assert response.dtype == cp.float32

    def test_corner_harris_opencv_compatibility_synthetic(self):
        """Test OpenCV compatibility with synthetic L-corner"""
        try:
            import cv2
        except ImportError:
            pytest.skip("OpenCV not available")

        from pixtreme_filter import corner_harris

        # Create synthetic L-shaped corner (uint8 for OpenCV)
        image_np = np.zeros((50, 50), dtype=np.uint8)
        image_np[20:30, 20:50] = 255  # Horizontal bar
        image_np[20:50, 20:30] = 255  # Vertical bar

        # OpenCV processing (uint8 input)
        response_cv = cv2.cornerHarris(image_np, blockSize=3, ksize=3, k=0.04)

        # Pixtreme processing (float32 input)
        image_cp_float32 = cp.asarray(image_np).astype(cp.float32) / 255.0
        response_px = corner_harris(image_cp_float32, blockSize=3, ksize=3, k=0.04)
        response_px_np = cp.asnumpy(response_px)

        # Compare response maps (deterministic part)
        max_diff = np.max(np.abs(response_cv - response_px_np))
        mean_diff = np.mean(np.abs(response_cv - response_px_np))

        print(f"\nHarris OpenCV compatibility (synthetic):")
        print(f"  Max diff: {max_diff:.6f}")
        print(f"  Mean diff: {mean_diff:.6f}")
        print(f"  OpenCV range: [{response_cv.min():.6f}, {response_cv.max():.6f}]")
        print(f"  Pixtreme range: [{response_px_np.min():.6f}, {response_px_np.max():.6f}]")

        # Response maps should be similar (relaxed tolerance for gradient computation differences)
        assert max_diff < 1e-3, f"Max difference {max_diff} exceeds tolerance"
        assert mean_diff < 1e-4, f"Mean difference {mean_diff} exceeds tolerance"

    def test_corner_harris_opencv_compatibility_random(self):
        """Test OpenCV compatibility with random image"""
        try:
            import cv2
        except ImportError:
            pytest.skip("OpenCV not available")

        from pixtreme_filter import corner_harris

        # Random image for general comparison (uint8 for OpenCV)
        np.random.seed(42)
        image_np = (np.random.rand(64, 64) * 255).astype(np.uint8)

        # OpenCV processing (uint8 input)
        response_cv = cv2.cornerHarris(image_np, blockSize=3, ksize=3, k=0.04)

        # Pixtreme processing (float32 input)
        image_cp_float32 = cp.asarray(image_np).astype(cp.float32) / 255.0
        response_px = corner_harris(image_cp_float32, blockSize=3, ksize=3, k=0.04)
        response_px_np = cp.asnumpy(response_px)

        # Compare response maps
        max_diff = np.max(np.abs(response_cv - response_px_np))
        mean_diff = np.mean(np.abs(response_cv - response_px_np))

        print(f"\nHarris OpenCV compatibility (random):")
        print(f"  Max diff: {max_diff:.6f}")
        print(f"  Mean diff: {mean_diff:.6f}")

        # Response maps should be similar
        assert max_diff < 1e-3, f"Max difference {max_diff} exceeds tolerance"
        assert mean_diff < 1e-4, f"Mean difference {mean_diff} exceeds tolerance"

    def test_corner_harris_opencv_compatibility_ksize5(self):
        """Test OpenCV compatibility with ksize=5"""
        try:
            import cv2
        except ImportError:
            pytest.skip("OpenCV not available")

        from pixtreme_filter import corner_harris

        # Random image (uint8 for OpenCV)
        np.random.seed(42)
        image_np = (np.random.rand(64, 64) * 255).astype(np.uint8)

        # OpenCV processing (uint8 input)
        response_cv = cv2.cornerHarris(image_np, blockSize=3, ksize=5, k=0.04)

        # Pixtreme processing (float32 input)
        image_cp_float32 = cp.asarray(image_np).astype(cp.float32) / 255.0
        response_px = corner_harris(image_cp_float32, blockSize=3, ksize=5, k=0.04)
        response_px_np = cp.asnumpy(response_px)

        max_diff = np.max(np.abs(response_cv - response_px_np))
        mean_diff = np.mean(np.abs(response_cv - response_px_np))

        print(f"\nHarris OpenCV compatibility (ksize=5):")
        print(f"  Max diff: {max_diff:.6f}")
        print(f"  Mean diff: {mean_diff:.6f}")

        assert max_diff < 1e-3, f"Max difference {max_diff} exceeds tolerance"
        assert mean_diff < 1e-4, f"Mean difference {mean_diff} exceeds tolerance"

    def test_corner_harris_invalid_dtype(self):
        """Test error handling for invalid dtype"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.uint8)

        with pytest.raises(ValueError, match="must be float32"):
            corner_harris(image, blockSize=3, ksize=3, k=0.04)

    def test_corner_harris_invalid_ksize(self):
        """Test error handling for invalid ksize"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.float32)

        # Even ksize should raise error
        with pytest.raises(ValueError, match="ksize must be odd"):
            corner_harris(image, blockSize=3, ksize=4, k=0.04)

        # ksize < 3 should raise error
        with pytest.raises(ValueError, match="ksize must be at least 3"):
            corner_harris(image, blockSize=3, ksize=1, k=0.04)

    def test_corner_harris_invalid_blocksize(self):
        """Test error handling for invalid blockSize"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.float32)

        # Even blockSize should raise error
        with pytest.raises(ValueError, match="blockSize must be odd"):
            corner_harris(image, blockSize=4, ksize=3, k=0.04)

        # blockSize < 3 should raise error
        with pytest.raises(ValueError, match="blockSize must be at least 3"):
            corner_harris(image, blockSize=1, ksize=3, k=0.04)

    def test_corner_harris_negative_k(self):
        """Test error handling for negative k parameter"""
        from pixtreme_filter import corner_harris

        image = cp.random.rand(64, 64).astype(cp.float32)

        # Negative k is technically allowed but not recommended
        # (some implementations use it for Shi-Tomasi detector)
        # We'll just verify it doesn't crash
        response = corner_harris(image, blockSize=3, ksize=3, k=-0.04)
        assert response.shape == (64, 64)

    def test_corner_harris_performance(self):
        """Test performance with large image"""
        from pixtreme_filter import corner_harris
        import time

        # Large image
        image = cp.random.rand(1024, 1024).astype(cp.float32)

        start = time.time()
        response = corner_harris(image, blockSize=3, ksize=3, k=0.04)
        cp.cuda.Device().synchronize()  # Wait for GPU completion
        elapsed = time.time() - start

        print(f"\nHarris Corner performance (1024x1024): {elapsed:.3f}s")

        assert response.shape == (1024, 1024)
        assert elapsed < 2.0, f"Performance too slow: {elapsed:.3f}s"
