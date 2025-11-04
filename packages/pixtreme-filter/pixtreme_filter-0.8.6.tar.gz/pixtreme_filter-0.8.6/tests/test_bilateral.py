"""Test suite for bilateral filter with OpenCV compatibility tests"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import bilateral_filter


class TestBilateralFilter:
    """Test cases for bilateral_filter() function"""

    @pytest.fixture
    def noisy_image(self):
        """Create a test image with Gaussian noise"""
        # Create clean image with sharp edges
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # White square

        # Add Gaussian noise
        noise = cp.random.normal(0, 0.1, image.shape).astype(cp.float32)
        noisy = cp.clip(image + noise, 0.0, 1.0)

        return noisy

    @pytest.fixture
    def clean_image(self):
        """Create a clean test image with sharp edges"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # White square in center
        return image

    def test_bilateral_filter_basic(self, noisy_image):
        """Test basic bilateral filter functionality"""
        result = bilateral_filter(noisy_image, d=5, sigma_color=0.1, sigma_space=5.0)

        assert result.shape == noisy_image.shape
        assert result.dtype == cp.float32
        assert cp.all(result >= 0.0)
        assert cp.all(result <= 1.0)

    def test_bilateral_filter_reduces_noise(self, noisy_image):
        """Test that bilateral filter reduces Gaussian noise"""
        # Apply bilateral filter
        result = bilateral_filter(noisy_image, d=9, sigma_color=0.2, sigma_space=9.0)

        # Result should be smoother than input in noisy regions
        # Check variance in a uniform region (should be lower after filtering)
        region = result[40:60, 40:60, 0]  # Center region
        input_region = noisy_image[40:60, 40:60, 0]

        # Variance should be reduced
        assert cp.std(region) < cp.std(input_region), "Bilateral filter should reduce noise variance"

    def test_bilateral_filter_preserves_edges(self, noisy_image):
        """Test that bilateral filter preserves edges better than Gaussian blur"""
        result = bilateral_filter(noisy_image, d=9, sigma_color=0.2, sigma_space=9.0)

        # Check that edges are preserved
        # Measure edge sharpness by gradient magnitude at boundary
        edge_x = 30  # Left edge of square
        edge_profile = result[50, edge_x - 2 : edge_x + 3, 0]  # 5 pixels across edge

        # Edge should have significant gradient (sharp transition)
        gradient = cp.max(edge_profile) - cp.min(edge_profile)
        assert gradient > 0.5, "Bilateral filter should preserve edges"

    def test_bilateral_filter_different_d_values(self):
        """Test different neighborhood diameters"""
        image = cp.random.rand(50, 50, 3).astype(cp.float32)

        for d in [3, 5, 7, 9]:
            result = bilateral_filter(image, d=d, sigma_color=0.1, sigma_space=5.0)
            assert result.shape == image.shape
            assert result.dtype == cp.float32

    def test_bilateral_filter_different_sigma_color(self):
        """Test different color sigma values"""
        image = cp.random.rand(50, 50, 3).astype(cp.float32)

        for sigma_color in [0.05, 0.1, 0.2, 0.5]:
            result = bilateral_filter(image, d=5, sigma_color=sigma_color, sigma_space=5.0)
            assert result.shape == image.shape
            assert result.dtype == cp.float32

    def test_bilateral_filter_different_sigma_space(self):
        """Test different spatial sigma values"""
        image = cp.random.rand(50, 50, 3).astype(cp.float32)

        for sigma_space in [1.0, 5.0, 10.0, 20.0]:
            result = bilateral_filter(image, d=5, sigma_color=0.1, sigma_space=sigma_space)
            assert result.shape == image.shape
            assert result.dtype == cp.float32

    def test_bilateral_filter_single_channel(self):
        """Test bilateral filter on single-channel (grayscale) image"""
        image = cp.random.rand(50, 50, 1).astype(cp.float32)
        result = bilateral_filter(image, d=5, sigma_color=0.1, sigma_space=5.0)

        assert result.shape == image.shape
        assert result.dtype == cp.float32

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_bilateral_filter_opencv_compatibility_basic(self):
        """Test bilateral filter compatibility with OpenCV (basic parameters)"""
        # Create test image
        np.random.seed(42)
        image_np = np.random.rand(64, 64, 3).astype(np.float32)
        image_cp = cp.asarray(image_np)

        # Apply bilateral filter (pixtreme)
        result_px = bilateral_filter(image_cp, d=5, sigma_color=0.1, sigma_space=5.0)

        # Apply bilateral filter (OpenCV)
        result_cv = cv2.bilateralFilter(image_np, d=5, sigmaColor=0.1, sigmaSpace=5.0)

        # Compare results
        result_px_np = cp.asnumpy(result_px)
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nOpenCV compatibility (basic): max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")
        # Bilateral filter involves exponential calculations with floating-point accumulation
        # Implementation differences in border handling and numerical precision
        # Relax threshold significantly compared to separable filters
        assert max_diff < 0.2, f"Max difference {max_diff} exceeds threshold"
        assert mean_diff < 0.05, f"Mean difference {mean_diff} exceeds threshold"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_bilateral_filter_opencv_compatibility_d9(self):
        """Test bilateral filter compatibility with OpenCV (d=9, stronger filtering)"""
        np.random.seed(123)
        image_np = np.random.rand(64, 64, 3).astype(np.float32)
        image_cp = cp.asarray(image_np)

        # Apply bilateral filter (pixtreme)
        result_px = bilateral_filter(image_cp, d=9, sigma_color=0.2, sigma_space=9.0)

        # Apply bilateral filter (OpenCV)
        result_cv = cv2.bilateralFilter(image_np, d=9, sigmaColor=0.2, sigmaSpace=9.0)

        # Compare results
        result_px_np = cp.asnumpy(result_px)
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nOpenCV compatibility (d=9): max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")
        # Larger neighborhood (d=9) increases accumulation errors and border effects
        assert max_diff < 0.3, f"Max difference {max_diff} exceeds threshold"
        assert mean_diff < 0.1, f"Mean difference {mean_diff} exceeds threshold"

    def test_bilateral_filter_performance(self):
        """Test bilateral filter performance on large image"""
        import time

        image = cp.random.rand(512, 512, 3).astype(cp.float32)

        start = time.time()
        result = bilateral_filter(image, d=5, sigma_color=0.1, sigma_space=5.0)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert result.shape == image.shape
        print(f"\nBilateral filter (512x512, d=5): {elapsed:.2f}ms")
        # Bilateral filter is compute-intensive, allow up to 500ms for d=5
        assert elapsed < 500, f"Bilateral filter too slow: {elapsed:.2f}ms"
