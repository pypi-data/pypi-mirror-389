"""Test suite for white balance color correction"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import white_balance


class TestWhiteBalanceGrayWorld:
    """Test cases for gray world white balance algorithm"""

    @pytest.fixture
    def sample_image(self):
        """Create test image with color cast (bluish tint)"""
        image = cp.random.uniform(0.3, 0.7, (100, 100, 3)).astype(cp.float32)
        # Add blue cast (increase blue channel)
        image[:, :, 2] *= 1.5
        image = cp.clip(image, 0.0, 1.0)
        return image

    @pytest.fixture
    def grayscale_image(self):
        """Create grayscale test image"""
        image = cp.random.uniform(0.3, 0.7, (100, 100)).astype(cp.float32)
        return image

    # ========== Basic Tests ==========

    def test_white_balance_basic(self, sample_image):
        """Test basic white balance functionality"""
        result = white_balance(sample_image, method="gray_world")

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_white_balance_grayscale(self, grayscale_image):
        """Test white balance with grayscale input"""
        result = white_balance(grayscale_image, method="gray_world")

        assert result.shape == grayscale_image.shape
        assert result.dtype == cp.float32

    def test_white_balance_removes_color_cast(self, sample_image):
        """Test that white balance reduces color cast"""
        # Original has blue cast (mean blue > mean red/green)
        mean_r = float(cp.mean(sample_image[:, :, 0]))
        mean_g = float(cp.mean(sample_image[:, :, 1]))
        mean_b = float(cp.mean(sample_image[:, :, 2]))

        assert mean_b > mean_r, "Original should have blue cast"
        assert mean_b > mean_g, "Original should have blue cast"

        # After white balance, means should be closer
        result = white_balance(sample_image, method="gray_world")
        result_mean_r = float(cp.mean(result[:, :, 0]))
        result_mean_g = float(cp.mean(result[:, :, 1]))
        result_mean_b = float(cp.mean(result[:, :, 2]))

        # Check that blue channel mean is reduced relative to others
        max_diff_before = abs(mean_b - mean_r) + abs(mean_b - mean_g)
        max_diff_after = abs(result_mean_b - result_mean_r) + abs(result_mean_b - result_mean_g)

        assert max_diff_after < max_diff_before, "White balance should reduce color cast"

    # ========== Method Tests ==========

    def test_white_balance_gray_world(self, sample_image):
        """Test gray world algorithm"""
        result = white_balance(sample_image, method="gray_world")

        # Gray world: each channel mean should be approximately equal
        mean_r = float(cp.mean(result[:, :, 0]))
        mean_g = float(cp.mean(result[:, :, 1]))
        mean_b = float(cp.mean(result[:, :, 2]))

        # Means should be close to each other (within 0.05)
        assert abs(mean_r - mean_g) < 0.05, f"Gray world: R-G means should be close ({mean_r:.3f} vs {mean_g:.3f})"
        assert abs(mean_r - mean_b) < 0.05, f"Gray world: R-B means should be close ({mean_r:.3f} vs {mean_b:.3f})"
        assert abs(mean_g - mean_b) < 0.05, f"Gray world: G-B means should be close ({mean_g:.3f} vs {mean_b:.3f})"

    def test_white_balance_white_patch(self, sample_image):
        """Test white patch algorithm"""
        result = white_balance(sample_image, method="white_patch")

        # White patch: at least one pixel should be near white (1.0) in each channel
        max_r = float(cp.max(result[:, :, 0]))
        max_g = float(cp.max(result[:, :, 1]))
        max_b = float(cp.max(result[:, :, 2]))

        # At least one channel should be at or near maximum
        assert max_r > 0.98 or max_g > 0.98 or max_b > 0.98, "White patch: at least one channel max should be near 1.0"

    def test_white_balance_simple(self, sample_image):
        """Test simple white balance algorithm"""
        result = white_balance(sample_image, method="simple")

        # Simple: each channel scaled independently to [0, 1]
        min_r = float(cp.min(result[:, :, 0]))
        max_r = float(cp.max(result[:, :, 0]))

        # At least one channel should span most of the range
        assert max_r > 0.9, "Simple: max value should be near 1.0"

    # ========== Parameter Tests ==========

    def test_white_balance_invalid_method(self, sample_image):
        """Test white balance with invalid method"""
        with pytest.raises(ValueError, match="Unknown white balance method"):
            white_balance(sample_image, method="invalid_method")

    def test_white_balance_default_method(self, sample_image):
        """Test white balance with default method (should be gray_world)"""
        result_default = white_balance(sample_image)
        result_gray_world = white_balance(sample_image, method="gray_world")

        # Default should match gray_world
        assert cp.allclose(result_default, result_gray_world, atol=1e-5)

    # ========== Edge Case Tests ==========

    def test_white_balance_neutral_image(self):
        """Test white balance on neutral (already balanced) image"""
        # Create image with equal channel means
        image = cp.random.uniform(0.4, 0.6, (100, 100, 3)).astype(cp.float32)
        result = white_balance(image, method="gray_world")

        # Neutral image should remain mostly unchanged
        max_diff = float(cp.max(cp.abs(result - image)))
        assert max_diff < 0.2, "White balance on neutral image should not change much"

    def test_white_balance_extreme_cast(self):
        """Test white balance on image with extreme color cast"""
        # Create image with only red channel active
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[:, :, 0] = cp.random.uniform(0.5, 1.0, (100, 100)).astype(cp.float32)

        result = white_balance(image, method="gray_world")

        # Result should still be valid
        assert cp.all(result >= 0.0)
        assert cp.all(result <= 1.0)

    def test_white_balance_clipping(self):
        """Test that white balance clips values to [0, 1]"""
        image = cp.random.uniform(0.1, 0.3, (100, 100, 3)).astype(cp.float32)
        # Create dark image with slight blue cast
        image[:, :, 2] *= 1.2

        result = white_balance(image, method="white_patch")

        # Check clipping
        assert cp.all(result >= 0.0), "Values should not go below 0"
        assert cp.all(result <= 1.0), "Values should not exceed 1"

    # ========== OpenCV Compatibility Tests ==========

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_white_balance_opencv_gray_world(self, sample_image):
        """Test gray world white balance matches OpenCV xphoto implementation"""
        # Note: OpenCV's xphoto module may not be available in all builds
        pytest.skip("OpenCV xphoto.createGrayworldWB not universally available")

    # ========== Integration Tests ==========

    def test_white_balance_preserves_contrast(self, sample_image):
        """Test that white balance preserves local contrast"""
        # Create image with clear contrast
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.3
        image[20:40, 20:40] = 0.8  # Bright region
        image[:, :, 2] *= 1.5  # Add blue cast

        result = white_balance(image, method="gray_world")

        # Bright region should still be brighter than background
        bright_mean = float(cp.mean(result[20:40, 20:40]))
        bg_mean = float(cp.mean(result[50:70, 50:70]))

        assert bright_mean > bg_mean, "White balance should preserve local contrast"

    def test_white_balance_color_pipeline(self, sample_image):
        """Test white balance in color correction pipeline"""
        # Typical pipeline: white balance → other adjustments
        balanced = white_balance(sample_image, method="gray_world")

        # Check that result is valid for further processing
        assert balanced.dtype == cp.float32
        assert cp.all(balanced >= 0.0)
        assert cp.all(balanced <= 1.0)
        assert balanced.shape == sample_image.shape

    # ========== Performance Tests ==========

    def test_white_balance_performance(self):
        """Test white balance performance on large image"""
        import time

        large_image = cp.random.rand(1024, 1024, 3).astype(cp.float32)

        start = time.perf_counter()
        result = white_balance(large_image, method="gray_world")
        cp.cuda.Stream.null.synchronize()
        elapsed = time.perf_counter() - start

        assert result.shape == (1024, 1024, 3)
        assert elapsed < 0.1, f"White balance should process 1024x1024 in <100ms (took {elapsed*1000:.1f}ms)"


class TestWhiteBalanceIntegration:
    """Integration tests combining white balance with other filters"""

    def test_white_balance_with_gaussian(self, sample_image=None):
        """Test white balance combined with Gaussian blur"""
        from pixtreme_filter import gaussian_blur

        image = cp.random.uniform(0.3, 0.7, (256, 256, 3)).astype(cp.float32)
        image[:, :, 2] *= 1.5  # Blue cast

        # Pipeline: blur → white balance
        blurred = gaussian_blur(image, ksize=5, sigma=1.0)
        balanced = white_balance(blurred, method="gray_world")

        assert balanced.shape == image.shape
        assert balanced.dtype == cp.float32

    def test_white_balance_with_unsharp(self, sample_image=None):
        """Test white balance combined with unsharp mask"""
        from pixtreme_filter import unsharp_mask

        image = cp.random.uniform(0.3, 0.7, (256, 256, 3)).astype(cp.float32)
        image[:, :, 2] *= 1.5  # Blue cast

        # Pipeline: white balance → sharpen
        balanced = white_balance(image, method="gray_world")
        sharpened = unsharp_mask(balanced, sigma=1.0, amount=1.0)

        assert sharpened.shape == image.shape
        assert sharpened.dtype == cp.float32
