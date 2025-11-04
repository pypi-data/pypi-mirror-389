"""Test suite for box_blur filter with OpenCV compatibility tests"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import box_blur


class TestBoxBlur:
    """Test cases for box_blur() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with known patterns"""
        # Create image with sharp edges
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # White square in center
        return image

    def test_box_blur_basic(self, sample_image):
        """Test basic box blur functionality"""
        result = box_blur(sample_image, ksize=5)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32
        assert cp.all(result >= 0.0)
        assert cp.all(result <= 1.0)

    def test_box_blur_smoothing_effect(self, sample_image):
        """Test that box blur actually smooths the image"""
        result = box_blur(sample_image, ksize=5)

        # Edge pixels should be smoothed (not pure 0 or 1)
        edge_pixel = result[29, 50, 0]  # Just outside the white square
        assert 0.0 < edge_pixel < 0.5, f"Edge should be smoothed, got {edge_pixel}"

        # Center should still be bright (but might be slightly dimmed)
        center_pixel = result[50, 50, 0]
        assert center_pixel > 0.8, f"Center should remain bright, got {center_pixel}"

    def test_box_blur_kernel_sizes(self, sample_image):
        """Test different kernel sizes"""
        for ksize in [3, 5, 7, 9, 11]:
            result = box_blur(sample_image, ksize=ksize)
            assert result.shape == sample_image.shape

    def test_box_blur_uniform_image(self):
        """Test on uniform image (should remain unchanged)"""
        uniform = cp.ones((50, 50, 3), dtype=cp.float32) * 0.5
        result = box_blur(uniform, ksize=5)

        # Uniform image should remain uniform
        assert cp.allclose(result, uniform, atol=1e-6)

    def test_box_blur_single_channel(self):
        """Test with grayscale image"""
        gray = cp.random.rand(100, 100).astype(cp.float32)
        result = box_blur(gray, ksize=5)

        assert result.shape == (100, 100, 3)  # Grayscale expanded to 3 channels for CUDA kernels
        assert result.dtype == cp.float32

    def test_box_blur_large_kernel(self):
        """Test with large kernel size"""
        image = cp.random.rand(200, 200, 3).astype(cp.float32)
        result = box_blur(image, ksize=51)

        assert result.shape == image.shape
        # Large kernel should create strong smoothing
        assert cp.std(result) < cp.std(image)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV required")
    def test_box_blur_opencv_compatibility_ksize3(self, sample_image):
        """Test OpenCV compatibility with ksize=3"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)

        # Our implementation
        result_px = box_blur(sample_image, ksize=3)
        result_px_np = cp.asnumpy(result_px)

        # OpenCV implementation (normalized box filter with BORDER_REPLICATE)
        result_cv = cv2.boxFilter(image_np, ddepth=-1, ksize=(3, 3), normalize=True, borderType=cv2.BORDER_REPLICATE)

        # Should be very close (allow small numerical differences)
        max_diff = np.abs(result_px_np - result_cv).max()
        assert max_diff < 1e-5, f"Max difference from OpenCV: {max_diff}"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV required")
    def test_box_blur_opencv_compatibility_ksize5(self, sample_image):
        """Test OpenCV compatibility with ksize=5"""
        image_np = cp.asnumpy(sample_image)

        result_px = box_blur(sample_image, ksize=5)
        result_px_np = cp.asnumpy(result_px)

        result_cv = cv2.boxFilter(image_np, ddepth=-1, ksize=(5, 5), normalize=True, borderType=cv2.BORDER_REPLICATE)

        max_diff = np.abs(result_px_np - result_cv).max()
        assert max_diff < 1e-5, f"Max difference from OpenCV: {max_diff}"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV required")
    def test_box_blur_opencv_compatibility_ksize9(self):
        """Test OpenCV compatibility with ksize=9 on random image"""
        # Random image for more rigorous testing
        image = cp.random.rand(64, 64, 3).astype(cp.float32)
        image_np = cp.asnumpy(image)

        result_px = box_blur(image, ksize=9)
        result_px_np = cp.asnumpy(result_px)

        result_cv = cv2.boxFilter(image_np, ddepth=-1, ksize=(9, 9), normalize=True, borderType=cv2.BORDER_REPLICATE)

        max_diff = np.abs(result_px_np - result_cv).max()
        mean_diff = np.abs(result_px_np - result_cv).mean()

        assert max_diff < 1e-5, f"Max difference from OpenCV: {max_diff}"
        assert mean_diff < 1e-6, f"Mean difference from OpenCV: {mean_diff}"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV required")
    def test_box_blur_opencv_compatibility_large_image(self):
        """Test OpenCV compatibility on larger image"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        image_np = cp.asnumpy(image)

        result_px = box_blur(image, ksize=7)
        result_px_np = cp.asnumpy(result_px)

        result_cv = cv2.boxFilter(image_np, ddepth=-1, ksize=(7, 7), normalize=True, borderType=cv2.BORDER_REPLICATE)

        max_diff = np.abs(result_px_np - result_cv).max()
        assert max_diff < 1e-5, f"Max difference from OpenCV: {max_diff}"

    def test_box_blur_border_handling(self):
        """Test border pixel handling"""
        # Small image to easily check borders
        image = cp.ones((10, 10, 3), dtype=cp.float32)
        image[0:3, 0:3] = 0.0  # Black square in top-left corner

        result = box_blur(image, ksize=3)

        # Top-left corner (0,0) should remain black
        # Its neighbors are all black with BORDER_REPLICATE
        assert result[0, 0, 0] < 0.2

        # Edge of black region should be blurred
        # Pixel (1, 4) is at the edge - mix of black and white
        edge_pixel = result[1, 3, 0]
        assert 0.2 < edge_pixel < 0.8, f"Edge should be blurred, got {edge_pixel}"

    def test_box_blur_performance(self):
        """Test performance on large image"""

        image = cp.random.rand(1024, 1024, 3).astype(cp.float32)

        start = cp.cuda.Event()
        end = cp.cuda.Event()

        start.record()
        _ = box_blur(image, ksize=9)
        end.record()
        end.synchronize()

        elapsed_ms = cp.cuda.get_elapsed_time(start, end)

        # Should complete quickly (< 50ms for 1024x1024)
        assert elapsed_ms < 50, f"Box blur took {elapsed_ms:.2f}ms (expected < 50ms)"
