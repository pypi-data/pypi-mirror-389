"""Test suite for Difference of Gaussians (DoG) filter with OpenCV compatibility tests"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import dog


class TestDoG:
    """Test cases for dog() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with blobs"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        # Create circular blobs of different sizes
        y, x = cp.ogrid[:100, :100]
        # Large blob
        mask1 = ((x - 30) ** 2 + (y - 30) ** 2) <= 10**2
        image[mask1] = 1.0
        # Small blob
        mask2 = ((x - 70) ** 2 + (y - 70) ** 2) <= 5**2
        image[mask2] = 0.8
        return image

    @pytest.fixture
    def grayscale_image(self):
        """Create a grayscale test image"""
        image = cp.zeros((100, 100), dtype=cp.float32)
        y, x = cp.ogrid[:100, :100]
        mask = ((x - 50) ** 2 + (y - 50) ** 2) <= 15**2
        image[mask] = 1.0
        return image

    # ========== Basic Tests ==========

    def test_dog_basic(self, sample_image):
        """Test basic DoG functionality"""
        result = dog(sample_image, sigma1=1.0, sigma2=2.0)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_dog_grayscale(self, grayscale_image):
        """Test DoG with grayscale input"""
        result = dog(grayscale_image, sigma1=1.0, sigma2=2.0)

        assert result.shape == grayscale_image.shape
        assert result.dtype == cp.float32

    def test_dog_detects_blobs(self, sample_image):
        """Test that DoG detects blob boundaries"""
        result = dog(sample_image, sigma1=1.0, sigma2=3.0)

        # DoG should produce positive and negative values at blob edges
        assert cp.any(result > 0.01), "DoG should have positive responses"
        assert cp.any(result < -0.01), "DoG should have negative responses"

    # ========== Parameter Tests ==========

    def test_dog_different_sigma_ratios(self, sample_image):
        """Test DoG with different sigma ratios"""
        # Small ratio (fine details)
        result_small = dog(sample_image, sigma1=1.0, sigma2=1.6)

        # Large ratio (coarse features)
        result_large = dog(sample_image, sigma1=1.0, sigma2=5.0)

        assert result_small.shape == result_large.shape
        # Different ratios should produce different results
        assert not cp.allclose(result_small, result_large)

    def test_dog_with_ksize(self, sample_image):
        """Test DoG with explicit kernel sizes"""
        # Auto ksize
        result_auto = dog(sample_image, sigma1=2.0, sigma2=4.0)

        # Explicit ksize
        result_explicit = dog(sample_image, sigma1=2.0, sigma2=4.0, ksize1=11, ksize2=21)

        assert result_auto.shape == result_explicit.shape
        # Should be similar but not identical
        assert cp.corrcoef(result_auto.flatten(), result_explicit.flatten())[0, 1] > 0.9

    def test_dog_sigma_order(self, sample_image):
        """Test that sigma order affects result polarity"""
        # Normal order (sigma2 > sigma1)
        result_normal = dog(sample_image, sigma1=1.0, sigma2=3.0)

        # Reversed order (sigma1 > sigma2)
        result_reversed = dog(sample_image, sigma1=3.0, sigma2=1.0)

        # Results should be negatives of each other
        assert cp.allclose(result_normal, -result_reversed, atol=1e-5)

    # ========== Edge Case Tests ==========

    def test_dog_equal_sigmas(self, sample_image):
        """Test DoG with equal sigmas (should be near zero)"""
        result = dog(sample_image, sigma1=2.0, sigma2=2.0)

        # Should be approximately zero everywhere
        assert cp.abs(result).max() < 1e-3, "DoG with equal sigmas should be near zero"

    def test_dog_uniform_image(self):
        """Test DoG on uniform image (no features)"""
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.5
        result = dog(image, sigma1=1.0, sigma2=3.0)

        # Uniform image should produce near-zero result
        assert cp.abs(result).max() < 1e-5, "DoG of uniform image should be zero"

    def test_dog_small_sigmas(self, sample_image):
        """Test DoG with very small sigmas"""
        result = dog(sample_image, sigma1=0.3, sigma2=0.6)

        assert result.shape == sample_image.shape
        assert cp.isfinite(result).all(), "DoG with small sigmas should produce finite values"

    # ========== OpenCV Compatibility Tests ==========

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_dog_opencv_compatibility_basic(self, sample_image):
        """Test DoG OpenCV compatibility with basic parameters"""
        sigma1, sigma2 = 1.0, 3.0

        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)

        # OpenCV DoG (manual implementation)
        # OpenCV uses ksize = round(sigma*4)*2 + 1 formula
        ksize1 = round(sigma1 * 4) * 2 + 1
        ksize2 = round(sigma2 * 4) * 2 + 1

        blur1_cv = cv2.GaussianBlur(image_np, (ksize1, ksize1), sigma1)
        blur2_cv = cv2.GaussianBlur(image_np, (ksize2, ksize2), sigma2)
        dog_cv = blur1_cv - blur2_cv

        # Pixtreme DoG
        dog_px = dog(sample_image, sigma1=sigma1, sigma2=sigma2)
        dog_px_np = cp.asnumpy(dog_px)

        # Compare
        max_diff = np.abs(dog_cv - dog_px_np).max()
        assert max_diff < 1e-4, f"DoG should match OpenCV (max_diff={max_diff:.6f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_dog_opencv_compatibility_grayscale(self, grayscale_image):
        """Test DoG OpenCV compatibility with grayscale"""
        sigma1, sigma2 = 0.8, 2.5

        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(grayscale_image)

        # OpenCV DoG
        ksize1 = round(sigma1 * 4) * 2 + 1
        ksize2 = round(sigma2 * 4) * 2 + 1

        blur1_cv = cv2.GaussianBlur(image_np, (ksize1, ksize1), sigma1)
        blur2_cv = cv2.GaussianBlur(image_np, (ksize2, ksize2), sigma2)
        dog_cv = blur1_cv - blur2_cv

        # Pixtreme DoG
        dog_px = dog(grayscale_image, sigma1=sigma1, sigma2=sigma2)
        dog_px_np = cp.asnumpy(dog_px)

        # Compare
        max_diff = np.abs(dog_cv - dog_px_np).max()
        assert max_diff < 1e-4, f"DoG grayscale should match OpenCV (max_diff={max_diff:.6f})"

    # ========== Performance Tests ==========

    def test_dog_performance(self):
        """Test DoG performance on large image"""
        import time

        large_image = cp.random.rand(1024, 1024, 3).astype(cp.float32)

        start = time.perf_counter()
        result = dog(large_image, sigma1=1.0, sigma2=3.0)
        cp.cuda.Stream.null.synchronize()  # Wait for GPU
        elapsed = time.perf_counter() - start

        assert result.shape == (1024, 1024, 3)
        assert elapsed < 0.1, f"DoG should process 1024x1024 in <100ms (took {elapsed*1000:.1f}ms)"

    # ========== Integration Tests ==========

    def test_dog_pipeline_blob_detection(self):
        """Test DoG in blob detection pipeline"""
        # Create image with multiple blobs at different scales
        image = cp.zeros((200, 200, 3), dtype=cp.float32)
        y, x = cp.ogrid[:200, :200]

        # Small blob
        mask1 = ((x - 50) ** 2 + (y - 50) ** 2) <= 5**2
        image[mask1] = 1.0

        # Medium blob
        mask2 = ((x - 150) ** 2 + (y - 150) ** 2) <= 15**2
        image[mask2] = 0.8

        # Large blob
        mask3 = ((x - 100) ** 2 + (y - 100) ** 2) <= 25**2
        image[mask3] = 0.6

        # Apply DoG at multiple scales
        dog_small = dog(image, sigma1=1.0, sigma2=1.6)
        dog_medium = dog(image, sigma1=3.0, sigma2=4.8)
        dog_large = dog(image, sigma1=5.0, sigma2=8.0)

        # Each scale should detect different blobs
        assert cp.abs(dog_small).max() > 0.01
        assert cp.abs(dog_medium).max() > 0.01
        assert cp.abs(dog_large).max() > 0.01
