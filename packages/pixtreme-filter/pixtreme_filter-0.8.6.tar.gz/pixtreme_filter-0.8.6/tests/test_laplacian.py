"""Test suite for Laplacian edge detection filter"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import laplacian


class TestLaplacian:
    """Test cases for laplacian() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with known edges"""
        # Create image with sharp edges (square in center)
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # White square in center
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
        image = cp.zeros((100, 100), dtype=cp.float32)
        image[30:70, 30:70] = 1.0
        return image

    def test_laplacian_basic(self, sample_image):
        """Test basic Laplacian functionality"""
        result = laplacian(sample_image, ksize=1)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_laplacian_grayscale(self, grayscale_image):
        """Test Laplacian on grayscale image"""
        result = laplacian(grayscale_image, ksize=1)

        assert result.shape == grayscale_image.shape
        assert result.dtype == cp.float32

    def test_laplacian_detects_edges(self, sample_image):
        """Test that Laplacian detects all edges of square"""
        result = laplacian(sample_image, ksize=1)

        # Laplacian should detect all 4 edges
        # Top edge
        top_edge_response = cp.abs(result[30:32, 50, 0])
        assert cp.mean(top_edge_response) > 0.1, "Laplacian should detect top edge"

        # Bottom edge
        bottom_edge_response = cp.abs(result[68:70, 50, 0])
        assert cp.mean(bottom_edge_response) > 0.1, "Laplacian should detect bottom edge"

        # Left edge
        left_edge_response = cp.abs(result[50, 30:32, 0])
        assert cp.mean(left_edge_response) > 0.1, "Laplacian should detect left edge"

        # Right edge
        right_edge_response = cp.abs(result[50, 68:70, 0])
        assert cp.mean(right_edge_response) > 0.1, "Laplacian should detect right edge"

        # Center should have low response (uniform region)
        center_response = cp.abs(result[45:55, 45:55, 0])
        assert cp.mean(center_response) < 0.05, "Laplacian should have low response in uniform regions"

    def test_laplacian_has_positive_negative_values(self, sample_image):
        """Test that Laplacian produces both positive and negative values"""
        result = laplacian(sample_image, ksize=1)

        # Laplacian is 2nd derivative, so it should have both positive and negative values
        assert cp.any(result > 0), "Laplacian should have positive values"
        assert cp.any(result < 0), "Laplacian should have negative values"

    def test_laplacian_different_ksizes(self, sample_image):
        """Test different kernel sizes"""
        result_1 = laplacian(sample_image, ksize=1)
        result_3 = laplacian(sample_image, ksize=3)
        result_5 = laplacian(sample_image, ksize=5)
        result_7 = laplacian(sample_image, ksize=7)

        # All should have same shape
        assert result_1.shape == result_3.shape == result_5.shape == result_7.shape

        # Larger kernels produce smoother responses
        assert not cp.array_equal(result_1, result_3)
        assert not cp.array_equal(result_3, result_5)

    def test_laplacian_ksize_default(self, sample_image):
        """Test default ksize parameter"""
        result_default = laplacian(sample_image)
        result_explicit = laplacian(sample_image, ksize=3)

        # Default should be ksize=3
        cp.testing.assert_array_equal(result_default, result_explicit)

    def test_laplacian_invalid_ksize(self, sample_image):
        """Test that invalid ksize raises ValueError"""
        with pytest.raises(ValueError, match="ksize must be"):
            laplacian(sample_image, ksize=2)  # Even number

        with pytest.raises(ValueError, match="ksize must be"):
            laplacian(sample_image, ksize=9)  # Too large

    def test_laplacian_rejects_uint8(self):
        """Test that uint8 input is rejected"""
        image = cp.random.randint(0, 256, (100, 100, 3), dtype=cp.uint8)

        with pytest.raises(TypeError, match="float32"):
            laplacian(image, ksize=1)

    def test_laplacian_empty_image(self):
        """Test behavior with empty/zero image"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        result = laplacian(image, ksize=1)

        # Uniform zero image should produce near-zero Laplacian
        assert cp.allclose(result, 0.0, atol=1e-6)

    def test_laplacian_uniform_image(self):
        """Test behavior with uniform non-zero image"""
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.5
        result = laplacian(image, ksize=1)

        # Uniform image should produce near-zero Laplacian
        assert cp.allclose(result, 0.0, atol=1e-6)

    @pytest.mark.parametrize("ksize", [1, 3, 5, 7])
    def test_laplacian_all_ksizes_run(self, sample_image, ksize):
        """Test that all kernel sizes execute without errors"""
        result = laplacian(sample_image, ksize=ksize)
        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_laplacian_opencv_reference_ksize1(self, sample_image):
        """Reference test with OpenCV for ksize=1 (basic 3x3 kernel)"""
        # Convert to numpy for OpenCV
        img_np = cp.asnumpy(sample_image)

        # Apply pixtreme laplacian
        result_px = laplacian(sample_image, ksize=1)

        # Apply OpenCV Laplacian (ksize=1 means 3x3 aperture)
        # Note: OpenCV expects BGR, but we test channel-by-channel
        result_cv_list = []
        for c in range(3):
            lap_cv = cv2.Laplacian(img_np[:, :, c], cv2.CV_32F, ksize=1)
            result_cv_list.append(lap_cv)
        result_cv = np.stack(result_cv_list, axis=-1)

        # Convert back to CuPy
        result_cv_cp = cp.asarray(result_cv)

        # Check correlation (pixtreme may differ in normalization/border handling)
        # We don't expect exact match, but strong correlation
        correlation = cp.corrcoef(result_px.ravel(), result_cv_cp.ravel())[0, 1]
        assert correlation > 0.90, f"Correlation with OpenCV should be high, got {float(correlation)}"

    def test_laplacian_multichannel_independence(self, sample_image):
        """Test that channels are processed independently"""
        # Create image with different patterns per channel
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70, 0] = 1.0  # Red square
        image[20:50, 20:50, 1] = 1.0  # Different green square
        image[40:80, 40:80, 2] = 1.0  # Different blue square

        result = laplacian(image, ksize=1)

        # Each channel should have different edge patterns
        assert not cp.array_equal(result[:, :, 0], result[:, :, 1])
        assert not cp.array_equal(result[:, :, 1], result[:, :, 2])
