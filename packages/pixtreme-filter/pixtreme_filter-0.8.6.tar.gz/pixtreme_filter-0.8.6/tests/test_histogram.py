"""Test suite for histogram equalization functions"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import equalize_hist


class TestEqualizeHist:
    """Test cases for equalize_hist() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with non-uniform histogram"""
        # Create image with low contrast (values concentrated in narrow range)
        image = cp.random.uniform(0.3, 0.5, (100, 100, 3)).astype(cp.float32)
        return image

    @pytest.fixture
    def gradient_image(self):
        """Create a smooth gradient for testing"""
        # Horizontal gradient (0 -> 1 from left to right)
        x = cp.linspace(0, 1, 100, dtype=cp.float32)
        image = cp.tile(x, (100, 1))
        # Add channel dimension
        image = cp.stack([image] * 3, axis=-1)
        return image

    @pytest.fixture
    def grayscale_image(self):
        """Create a grayscale test image"""
        image = cp.random.uniform(0.3, 0.5, (100, 100)).astype(cp.float32)
        return image

    def test_equalize_hist_basic(self, sample_image):
        """Test basic equalize_hist functionality"""
        result = equalize_hist(sample_image)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_equalize_hist_grayscale(self, grayscale_image):
        """Test equalize_hist on grayscale image"""
        result = equalize_hist(grayscale_image)

        assert result.shape == grayscale_image.shape
        assert result.dtype == cp.float32

    def test_equalize_hist_improves_contrast(self, sample_image):
        """Test that equalization improves contrast"""
        result = equalize_hist(sample_image)

        # Measure contrast using standard deviation
        original_std = float(cp.std(sample_image))
        result_std = float(cp.std(result))

        # Equalized image should have higher standard deviation (better contrast)
        assert result_std > original_std, "Histogram equalization should increase contrast"

    def test_equalize_hist_spreads_histogram(self, sample_image):
        """Test that histogram is spread across full range"""
        result = equalize_hist(sample_image)

        # Check that result uses wider range of values
        result_range = float(cp.max(result) - cp.min(result))
        original_range = float(cp.max(sample_image) - cp.min(sample_image))

        assert result_range > original_range, "Equalized image should use wider value range"

    def test_equalize_hist_output_range(self, sample_image):
        """Test that output values are in valid range"""
        result = equalize_hist(sample_image)

        # Values should be in [0, 1] range
        assert float(cp.min(result)) >= 0.0, "Output should be >= 0"
        assert float(cp.max(result)) <= 1.0, "Output should be <= 1"

    def test_equalize_hist_uniform_image(self):
        """Test behavior with uniform image"""
        # Uniform image (all pixels same value)
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.5
        result = equalize_hist(image)

        # Uniform image should remain unchanged (all same value)
        assert cp.allclose(result, image, atol=1e-6), "Uniform image should remain uniform"

    def test_equalize_hist_rejects_uint8(self):
        """Test that uint8 input is rejected"""
        image = cp.random.randint(0, 256, (100, 100, 3), dtype=cp.uint8)

        with pytest.raises(TypeError, match="float32"):
            equalize_hist(image)

    def test_equalize_hist_multichannel_independence(self, sample_image):
        """Test that channels are processed independently"""
        # Create image with different patterns per channel
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[:, :, 0] = cp.random.uniform(0.2, 0.4, (100, 100))  # Low range
        image[:, :, 1] = cp.random.uniform(0.4, 0.6, (100, 100))  # Mid range
        image[:, :, 2] = cp.random.uniform(0.6, 0.8, (100, 100))  # High range

        result = equalize_hist(image)

        # Each channel should be equalized independently
        # Check that channels still have different characteristics
        assert not cp.array_equal(result[:, :, 0], result[:, :, 1])
        assert not cp.array_equal(result[:, :, 1], result[:, :, 2])

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_equalize_hist_opencv_reference(self, gradient_image):
        """Reference test with OpenCV for grayscale image"""
        # Convert to numpy for OpenCV (use only first channel for grayscale test)
        img_gray = cp.asnumpy(gradient_image[:, :, 0])

        # Apply pixtreme equalize_hist (grayscale)
        result_px = equalize_hist(gradient_image[:, :, 0])

        # Apply OpenCV equalizeHist
        # OpenCV expects uint8, so we need to convert
        img_uint8 = (img_gray * 255).astype(np.uint8)
        result_cv_uint8 = cv2.equalizeHist(img_uint8)
        result_cv = result_cv_uint8.astype(np.float32) / 255.0

        # Convert back to CuPy
        result_cv_cp = cp.asarray(result_cv)

        # Check correlation (pixtreme may differ slightly in implementation)
        correlation = cp.corrcoef(result_px.ravel(), result_cv_cp.ravel())[0, 1]
        assert correlation > 0.95, f"Correlation with OpenCV should be high, got {float(correlation)}"

    def test_equalize_hist_preserves_shape(self):
        """Test various image shapes"""
        # Test different shapes
        shapes = [(100, 100), (100, 100, 1), (100, 100, 3), (256, 256, 3)]

        for shape in shapes:
            image = cp.random.uniform(0.2, 0.8, shape).astype(cp.float32)
            result = equalize_hist(image)
            assert result.shape == image.shape, f"Shape mismatch for {shape}"

    def test_equalize_hist_deterministic(self, sample_image):
        """Test that equalization is deterministic"""
        result1 = equalize_hist(sample_image)
        result2 = equalize_hist(sample_image)

        # Same input should produce same output
        cp.testing.assert_array_equal(result1, result2)
