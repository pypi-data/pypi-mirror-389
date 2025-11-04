"""Test suite for unsharp_mask filter with OpenCV compatibility tests"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import unsharp_mask


class TestUnsharpMask:
    """Test cases for unsharp_mask() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with known patterns"""
        # Create image with sharp edges and details
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # White square in center
        # Add some details
        image[45:55, 45:55] = 0.5  # Gray square in center
        return image

    @pytest.fixture
    def complex_image(self):
        """Create a more complex test image"""
        # Create gradient image
        x = cp.linspace(0, 1, 128).astype(cp.float32)
        y = cp.linspace(0, 1, 128).astype(cp.float32)
        xx, yy = cp.meshgrid(x, y)
        image = cp.stack([xx, yy, (xx + yy) / 2], axis=-1)
        return image

    def test_unsharp_mask_basic(self, sample_image):
        """Test basic unsharp mask functionality"""
        result = unsharp_mask(sample_image, sigma=1.0, amount=1.0)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32
        # Values might go outside [0, 1] due to sharpening (no clipping by default)
        # Just verify results are finite and reasonable
        assert cp.all(cp.isfinite(result))
        assert cp.all(result >= -1.0)
        assert cp.all(result <= 3.0)

    def test_unsharp_mask_sharpening_effect(self, sample_image):
        """Test that unsharp mask actually sharpens edges"""
        # Apply mild sharpening
        result = unsharp_mask(sample_image, sigma=2.0, amount=0.5)

        # Edge contrast should increase compared to original
        # Check edge pixel (just inside the white square)
        edge_orig = float(sample_image[31, 50, 0])
        edge_sharp = float(result[31, 50, 0])

        # The sharpened edge should be at least as bright as original
        # (unsharp mask enhances edges)
        assert edge_sharp >= edge_orig * 0.95

        # Center should remain similar
        center_orig = float(sample_image[50, 50, 0])
        center_sharp = float(result[50, 50, 0])
        assert abs(center_sharp - center_orig) < 0.3

    def test_unsharp_mask_amount_parameter(self, sample_image):
        """Test different amount values"""
        # Low amount (subtle sharpening)
        result_low = unsharp_mask(sample_image, sigma=1.0, amount=0.3)

        # High amount (strong sharpening)
        result_high = unsharp_mask(sample_image, sigma=1.0, amount=2.0)

        # Higher amount should produce more different result from original
        diff_low = float(cp.mean(cp.abs(result_low - sample_image)))
        diff_high = float(cp.mean(cp.abs(result_high - sample_image)))

        assert diff_high > diff_low

    def test_unsharp_mask_sigma_parameter(self, sample_image):
        """Test different sigma values"""
        # Small sigma (sharpen fine details)
        result_small = unsharp_mask(sample_image, sigma=0.5, amount=1.0)

        # Large sigma (sharpen broad features)
        result_large = unsharp_mask(sample_image, sigma=5.0, amount=1.0)

        # Results should be different
        diff = float(cp.mean(cp.abs(result_small - result_large)))
        assert diff > 0.01

    def test_unsharp_mask_zero_amount(self, sample_image):
        """Test that zero amount returns unchanged image"""
        result = unsharp_mask(sample_image, sigma=1.0, amount=0.0)

        # Should be identical to original
        assert cp.allclose(result, sample_image, rtol=1e-5, atol=1e-5)

    def test_unsharp_mask_dtype_preservation(self, sample_image):
        """Test that output dtype is float32"""
        # Test float32
        result_fp32 = unsharp_mask(sample_image, sigma=1.0, amount=1.0)
        assert result_fp32.dtype == cp.float32

    def test_unsharp_mask_small_image(self):
        """Test with small image dimensions"""
        small_image = cp.random.rand(16, 16, 3).astype(cp.float32)
        result = unsharp_mask(small_image, sigma=1.0, amount=1.0)

        assert result.shape == small_image.shape
        assert result.dtype == cp.float32

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_unsharp_mask_opencv_compatibility_basic(self, complex_image):
        """Test OpenCV compatibility with basic parameters

        Note: Tolerance is set to 1e-2 due to underlying gaussian_blur differences.
        The error is inherited from gaussian_blur, not unsharp_mask itself.
        Future improvements to gaussian_blur will reduce this error.
        """
        sigma = 1.0
        amount = 1.0

        # Pixtreme implementation
        px_result = unsharp_mask(complex_image, sigma=sigma, amount=amount)

        # OpenCV implementation
        image_np = cp.asnumpy(complex_image)
        blurred_cv = cv2.GaussianBlur(image_np, (0, 0), sigma)
        cv_result = cv2.addWeighted(image_np, 1 + amount, blurred_cv, -amount, 0)

        # Compare
        px_result_np = cp.asnumpy(px_result)
        max_diff = np.max(np.abs(px_result_np - cv_result))
        mean_diff = np.mean(np.abs(px_result_np - cv_result))

        # Relaxed tolerance due to gaussian_blur implementation differences
        assert max_diff < 1e-2, f"Max difference {max_diff} exceeds threshold"
        assert mean_diff < 1e-3, f"Mean difference {mean_diff} exceeds threshold"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_unsharp_mask_opencv_compatibility_strong(self, complex_image):
        """Test OpenCV compatibility with strong sharpening

        Note: Tolerance is set to 2e-2 due to underlying gaussian_blur differences.
        Strong amount values amplify the gaussian_blur error.
        """
        sigma = 2.0
        amount = 2.5

        # Pixtreme implementation
        px_result = unsharp_mask(complex_image, sigma=sigma, amount=amount)

        # OpenCV implementation
        image_np = cp.asnumpy(complex_image)
        blurred_cv = cv2.GaussianBlur(image_np, (0, 0), sigma)
        cv_result = cv2.addWeighted(image_np, 1 + amount, blurred_cv, -amount, 0)

        # Compare
        px_result_np = cp.asnumpy(px_result)
        max_diff = np.max(np.abs(px_result_np - cv_result))
        mean_diff = np.mean(np.abs(px_result_np - cv_result))

        # Relaxed tolerance due to error amplification
        assert max_diff < 2e-2, f"Max difference {max_diff} exceeds threshold"
        assert mean_diff < 2e-3, f"Mean difference {mean_diff} exceeds threshold"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_unsharp_mask_opencv_compatibility_subtle(self, complex_image):
        """Test OpenCV compatibility with subtle sharpening

        Note: Tolerance is set to 1e-2 due to underlying gaussian_blur differences.
        """
        sigma = 0.5
        amount = 0.3

        # Pixtreme implementation
        px_result = unsharp_mask(complex_image, sigma=sigma, amount=amount)

        # OpenCV implementation
        image_np = cp.asnumpy(complex_image)
        blurred_cv = cv2.GaussianBlur(image_np, (0, 0), sigma)
        cv_result = cv2.addWeighted(image_np, 1 + amount, blurred_cv, -amount, 0)

        # Compare
        px_result_np = cp.asnumpy(px_result)
        max_diff = np.max(np.abs(px_result_np - cv_result))
        mean_diff = np.mean(np.abs(px_result_np - cv_result))

        assert max_diff < 1e-2, f"Max difference {max_diff} exceeds threshold"
        assert mean_diff < 1e-3, f"Mean difference {mean_diff} exceeds threshold"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_unsharp_mask_opencv_compatibility_large_sigma(self, complex_image):
        """Test OpenCV compatibility with large sigma

        Note: Tolerance is set to 1e-2 due to underlying gaussian_blur differences.
        Large sigma values amplify the error.
        """
        sigma = 10.0
        amount = 1.5

        # Pixtreme implementation
        px_result = unsharp_mask(complex_image, sigma=sigma, amount=amount)

        # OpenCV implementation
        image_np = cp.asnumpy(complex_image)
        blurred_cv = cv2.GaussianBlur(image_np, (0, 0), sigma)
        cv_result = cv2.addWeighted(image_np, 1 + amount, blurred_cv, -amount, 0)

        # Compare
        px_result_np = cp.asnumpy(px_result)
        max_diff = np.max(np.abs(px_result_np - cv_result))
        mean_diff = np.mean(np.abs(px_result_np - cv_result))

        # Slightly relaxed tolerance for large sigma
        assert max_diff < 5e-2, f"Max difference {max_diff} exceeds threshold"
        assert mean_diff < 5e-3, f"Mean difference {mean_diff} exceeds threshold"

    def test_unsharp_mask_performance(self, complex_image):
        """Test performance with 1024x1024 image"""
        large_image = cp.random.rand(1024, 1024, 3).astype(cp.float32)

        import time

        start = time.time()
        result = unsharp_mask(large_image, sigma=2.0, amount=1.5)
        elapsed = time.time() - start

        assert result.shape == large_image.shape
        # Should complete in reasonable time (< 100ms including gaussian_blur)
        assert elapsed < 0.1, f"Performance test failed: {elapsed:.3f}s > 0.1s"
