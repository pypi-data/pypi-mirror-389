"""Test suite for Sobel edge detection with OpenCV compatibility tests"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import sobel


class TestSobel:
    """Test cases for sobel() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with known edges"""
        # Create image with sharp edges (vertical and horizontal)
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # White square in center
        return image

    @pytest.fixture
    def gradient_image(self):
        """Create a smooth gradient for testing edge detection"""
        # Horizontal gradient (0 -> 1 from left to right)
        x = cp.linspace(0, 1, 100, dtype=cp.float32)
        image = cp.tile(x, (100, 1))
        # Add channel dimension
        image = cp.stack([image] * 3, axis=-1)
        return image

    def test_sobel_basic_x(self, sample_image):
        """Test basic Sobel-X functionality"""
        result = sobel(sample_image, dx=1, dy=0, ksize=3)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_sobel_basic_y(self, sample_image):
        """Test basic Sobel-Y functionality"""
        result = sobel(sample_image, dx=0, dy=1, ksize=3)

        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_sobel_detects_vertical_edges(self, sample_image):
        """Test that Sobel-X detects vertical edges"""
        result = sobel(sample_image, dx=1, dy=0, ksize=3)

        # Sobel-X should detect vertical edges (left and right sides of square)
        # Left edge (transition from 0 to 1)
        left_edge_response = cp.abs(result[50, 30:35, 0])
        assert cp.any(left_edge_response > 0.5), "Sobel-X should detect left vertical edge"

        # Right edge (transition from 1 to 0)
        right_edge_response = cp.abs(result[50, 65:70, 0])
        assert cp.any(right_edge_response > 0.5), "Sobel-X should detect right vertical edge"

        # Top and bottom should have weaker response
        top_edge_response = cp.abs(result[30:35, 50, 0])
        assert cp.mean(top_edge_response) < cp.mean(left_edge_response), (
            "Sobel-X should respond more to vertical edges than horizontal"
        )

    def test_sobel_detects_horizontal_edges(self, sample_image):
        """Test that Sobel-Y detects horizontal edges"""
        result = sobel(sample_image, dx=0, dy=1, ksize=3)

        # Sobel-Y should detect horizontal edges (top and bottom of square)
        # Top edge
        top_edge_response = cp.abs(result[30:35, 50, 0])
        assert cp.any(top_edge_response > 0.5), "Sobel-Y should detect top horizontal edge"

        # Bottom edge
        bottom_edge_response = cp.abs(result[65:70, 50, 0])
        assert cp.any(bottom_edge_response > 0.5), "Sobel-Y should detect bottom horizontal edge"

        # Left and right should have weaker response
        left_edge_response = cp.abs(result[50, 30:35, 0])
        assert cp.mean(left_edge_response) < cp.mean(top_edge_response), (
            "Sobel-Y should respond more to horizontal edges than vertical"
        )

    def test_sobel_different_ksizes(self, sample_image):
        """Test different kernel sizes"""
        result_3 = sobel(sample_image, dx=1, dy=0, ksize=3)
        result_5 = sobel(sample_image, dx=1, dy=0, ksize=5)
        result_7 = sobel(sample_image, dx=1, dy=0, ksize=7)

        # All should have same shape
        assert result_3.shape == result_5.shape == result_7.shape

        # Larger kernels typically produce smoother gradients
        assert not cp.array_equal(result_3, result_5)
        assert not cp.array_equal(result_5, result_7)

    def test_sobel_single_channel(self):
        """Test Sobel on single-channel (grayscale) image"""
        # Create grayscale image
        image = cp.zeros((100, 100), dtype=cp.float32)
        image[30:70, 30:70] = 1.0

        result = sobel(image, dx=1, dy=0, ksize=3)

        # Result will be 3D (H, W, 3) - grayscale expanded to 3 channels for CUDA kernels
        assert result.shape == (100, 100, 3)
        assert result.dtype == cp.float32

    def test_sobel_gradient_magnitude(self, gradient_image):
        """Test Sobel on smooth gradient"""
        # Horizontal gradient should be detected by Sobel-X
        result_x = sobel(gradient_image, dx=1, dy=0, ksize=3)
        result_y = sobel(gradient_image, dx=0, dy=1, ksize=3)

        # X gradient should be relatively uniform and positive
        center_x = result_x[40:60, 40:60, 0]
        assert cp.mean(center_x) > 0, "Sobel-X should detect positive horizontal gradient"

        # Y gradient should be near zero (no vertical gradient)
        center_y = result_y[40:60, 40:60, 0]
        assert cp.abs(cp.mean(center_y)) < 0.1, "Sobel-Y should be near zero for horizontal gradient"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_sobel_opencv_compatibility_x_ksize3(self, sample_image):
        """Test Sobel-X OpenCV compatibility with ksize=3"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)

        # Apply Sobel using both implementations
        result_px = sobel(sample_image, dx=1, dy=0, ksize=3)
        result_cv = cv2.Sobel(image_np, cv2.CV_32F, dx=1, dy=0, ksize=3)

        # Convert back to CuPy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Calculate difference
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nSobel-X ksize=3: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # OpenCV compatibility check
        assert max_diff < 1e-5, f"Max difference {max_diff} exceeds threshold 1e-5"
        assert mean_diff < 1e-6, f"Mean difference {mean_diff} exceeds threshold 1e-6"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_sobel_opencv_compatibility_y_ksize3(self, sample_image):
        """Test Sobel-Y OpenCV compatibility with ksize=3"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)

        # Apply Sobel using both implementations
        result_px = sobel(sample_image, dx=0, dy=1, ksize=3)
        result_cv = cv2.Sobel(image_np, cv2.CV_32F, dx=0, dy=1, ksize=3)

        # Convert back to CuPy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Calculate difference
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nSobel-Y ksize=3: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # OpenCV compatibility check
        assert max_diff < 1e-5, f"Max difference {max_diff} exceeds threshold 1e-5"
        assert mean_diff < 1e-6, f"Mean difference {mean_diff} exceeds threshold 1e-6"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_sobel_opencv_compatibility_ksize5(self, sample_image):
        """Test Sobel OpenCV compatibility with ksize=5"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)

        # Apply Sobel-X using both implementations
        result_px = sobel(sample_image, dx=1, dy=0, ksize=5)
        result_cv = cv2.Sobel(image_np, cv2.CV_32F, dx=1, dy=0, ksize=5)

        # Convert back to CuPy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Calculate difference
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nSobel-X ksize=5: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # OpenCV compatibility check
        assert max_diff < 1e-5, f"Max difference {max_diff} exceeds threshold 1e-5"
        assert mean_diff < 1e-6, f"Mean difference {mean_diff} exceeds threshold 1e-6"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_sobel_opencv_compatibility_large_image(self):
        """Test Sobel OpenCV compatibility with larger image"""
        # Create larger test image with known pattern (not random)
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        # Create vertical stripes (to test Sobel-X)
        for i in range(0, 512, 64):
            image[:, i : i + 32] = 1.0
        image_np = cp.asnumpy(image)

        # Apply Sobel-X using both implementations
        result_px = sobel(image, dx=1, dy=0, ksize=3)
        result_cv = cv2.Sobel(image_np, cv2.CV_32F, dx=1, dy=0, ksize=3)

        # Convert back to CuPy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Calculate difference
        max_diff = np.max(np.abs(result_px_np - result_cv))
        mean_diff = np.mean(np.abs(result_px_np - result_cv))

        print(f"\nSobel-X 512x512: max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # OpenCV compatibility check
        assert max_diff < 1e-5, f"Max difference {max_diff} exceeds threshold 1e-5"
        assert mean_diff < 1e-6, f"Mean difference {mean_diff} exceeds threshold 1e-6"

    def test_sobel_performance(self):
        """Test Sobel performance on large image"""
        import time

        # Create large test image
        image = cp.random.rand(1024, 1024, 3).astype(cp.float32)

        # Warm-up
        _ = sobel(image, dx=1, dy=0, ksize=3)

        # Measure performance
        start = time.time()
        _ = sobel(image, dx=1, dy=0, ksize=3)
        cp.cuda.Stream.null.synchronize()  # Wait for GPU to finish
        elapsed = time.time() - start

        print(f"\nSobel performance: {elapsed * 1000:.2f}ms for 1024x1024 image")

        # Should complete in reasonable time (<100ms)
        assert elapsed < 0.1, f"Sobel took {elapsed * 1000:.2f}ms (expected <100ms)"
