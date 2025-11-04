"""Test suite for median blur filter with OpenCV compatibility tests"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import median_blur


class TestMedianBlur:
    """Test cases for median_blur() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with salt-and-pepper noise"""
        # Create clean image
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.5

        # Add salt-and-pepper noise (random white and black pixels)
        noise_mask = cp.random.rand(100, 100, 3) < 0.05  # 5% noise
        noise_count = int(cp.sum(noise_mask))  # Convert CuPy scalar to Python int
        image[noise_mask] = cp.random.choice([0.0, 1.0], size=noise_count)

        return image

    @pytest.fixture
    def clean_image(self):
        """Create a clean test image with sharp edges"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # White square in center
        return image

    def test_median_blur_basic(self, sample_image):
        """Test basic median blur functionality"""
        result = median_blur(sample_image, ksize=3)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32
        assert cp.all(result >= 0.0)
        assert cp.all(result <= 1.0)

    def test_median_blur_removes_noise(self, sample_image):
        """Test that median blur removes salt-and-pepper noise"""
        # Apply median blur
        result = median_blur(sample_image, ksize=5)

        # Result should be smoother than input
        # Count pixels that are pure black (0.0) or pure white (1.0)
        extreme_input = cp.sum((sample_image == 0.0) | (sample_image == 1.0))
        extreme_output = cp.sum((result == 0.0) | (result == 1.0))

        # Median filter should reduce number of extreme values
        assert extreme_output < extreme_input, "Median blur should reduce noise"

    def test_median_blur_preserves_edges(self, clean_image):
        """Test that median blur preserves edges better than averaging"""
        result = median_blur(clean_image, ksize=3)

        # Check that edges are preserved (center should still be bright)
        center_region = result[40:60, 40:60, 0]
        assert cp.mean(center_region) > 0.9, "Center should remain bright after median blur"

        # Edges should be relatively sharp (not heavily blurred)
        edge_region = result[29:31, 40:60, 0]  # Top edge
        edge_variation = cp.std(edge_region)
        assert edge_variation > 0.1, "Edges should maintain some sharpness"

    def test_median_blur_different_ksizes(self):
        """Test different kernel sizes with structured noise"""
        # Create image with more structured pattern (not just random noise)
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.5
        # Add checkerboard pattern of varying intensity
        image[::5, ::5] = 0.0  # Dark spots
        image[2::5, 2::5] = 1.0  # Bright spots

        result_3 = median_blur(image, ksize=3)
        result_5 = median_blur(image, ksize=5)
        result_7 = median_blur(image, ksize=7)

        # All should have same shape
        assert result_3.shape == result_5.shape == result_7.shape

        # Larger kernels should produce smoother results (lower std dev)
        std_3 = cp.std(result_3)
        std_5 = cp.std(result_5)
        std_7 = cp.std(result_7)

        # Standard deviation should decrease with larger kernels
        assert std_5 <= std_3, "ksize=5 should be smoother than ksize=3"
        assert std_7 <= std_5, "ksize=7 should be smoother than ksize=5"

    def test_median_blur_single_channel(self):
        """Test median blur on single-channel (grayscale) image"""
        # Create grayscale image with noise
        image = cp.ones((100, 100), dtype=cp.float32) * 0.5
        noise_mask = cp.random.rand(100, 100) < 0.05
        noise_count = int(cp.sum(noise_mask))  # Convert CuPy scalar to Python int
        image[noise_mask] = cp.random.choice([0.0, 1.0], size=noise_count)

        result = median_blur(image, ksize=3)

        # Result will be 3D (H, W, 1) due to prepare_image_for_filter
        assert result.shape == (100, 100, 1)
        assert result.dtype == cp.float32

    def test_median_blur_uniform_image(self):
        """Test median blur on uniform image (should be unchanged)"""
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.7
        result = median_blur(image, ksize=5)

        # Uniform image should remain unchanged
        assert cp.allclose(result, image, atol=1e-6)

    def test_median_blur_odd_ksize_only(self, sample_image):
        """Test that only odd kernel sizes are accepted"""
        # Odd sizes should work
        _ = median_blur(sample_image, ksize=3)
        _ = median_blur(sample_image, ksize=5)

        # Even sizes should raise error
        with pytest.raises(ValueError, match="must be odd"):
            median_blur(sample_image, ksize=4)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_median_blur_opencv_compatibility_ksize3(self, clean_image):
        """Test median blur OpenCV compatibility with ksize=3"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(clean_image)

        # Apply median blur using both implementations
        result_px = median_blur(clean_image, ksize=3)
        result_cv = cv2.medianBlur(image_np.astype(np.float32), ksize=3)

        # Convert back to CuPy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Calculate difference
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nMedian blur ksize=3: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # OpenCV compatibility check
        assert max_diff < 1e-5, f"Max difference {max_diff} exceeds threshold 1e-5"
        assert mean_diff < 1e-6, f"Mean difference {mean_diff} exceeds threshold 1e-6"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_median_blur_opencv_compatibility_ksize5(self, clean_image):
        """Test median blur OpenCV compatibility with ksize=5"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(clean_image)

        # Apply median blur using both implementations
        result_px = median_blur(clean_image, ksize=5)
        result_cv = cv2.medianBlur(image_np.astype(np.float32), ksize=5)

        # Convert back to CuPy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Calculate difference
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nMedian blur ksize=5: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # OpenCV compatibility check
        assert max_diff < 1e-5, f"Max difference {max_diff} exceeds threshold 1e-5"
        assert mean_diff < 1e-6, f"Mean difference {mean_diff} exceeds threshold 1e-6"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_median_blur_opencv_compatibility_noisy_image(self, sample_image):
        """Test median blur OpenCV compatibility with noisy image"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)

        # Apply median blur using both implementations
        result_px = median_blur(sample_image, ksize=3)
        result_cv = cv2.medianBlur(image_np.astype(np.float32), ksize=3)

        # Convert back to CuPy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Calculate difference
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nMedian blur noisy image: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # OpenCV compatibility check
        assert max_diff < 1e-5, f"Max difference {max_diff} exceeds threshold 1e-5"
        assert mean_diff < 1e-6, f"Mean difference {mean_diff} exceeds threshold 1e-6"

    def test_median_blur_performance(self):
        """Test median blur performance on large image"""
        import time

        # Create large test image
        image = cp.random.rand(1024, 1024, 3).astype(cp.float32)

        # Warm-up
        _ = median_blur(image, ksize=3)

        # Measure performance
        start = time.time()
        _ = median_blur(image, ksize=3)
        cp.cuda.Stream.null.synchronize()  # Wait for GPU to finish
        elapsed = time.time() - start

        print(f"\nMedian blur performance: {elapsed * 1000:.2f}ms for 1024x1024 image")

        # Should complete in reasonable time (<200ms for median filter)
        assert elapsed < 0.2, f"Median blur took {elapsed * 1000:.2f}ms (expected <200ms)"
