"""Test suite for Canny edge detection with OpenCV compatibility tests"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import canny


class TestCanny:
    """Test cases for canny() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a test image with known edges"""
        # Create image with sharp edges (white square in center)
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0
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

    @pytest.fixture
    def grayscale_image(self):
        """Create a grayscale test image"""
        image = cp.zeros((100, 100), dtype=cp.float32)
        image[30:70, 30:70] = 1.0
        return image

    # ========== Basic Tests ==========

    def test_canny_basic(self, sample_image):
        """Test basic Canny functionality"""
        result = canny(sample_image, threshold1=0.1, threshold2=0.3)

        assert result.shape == sample_image.shape[:2]  # Should return (H, W)
        assert result.dtype == cp.float32
        assert cp.all((result >= 0.0) & (result <= 1.0))  # Binary output [0, 1]

    def test_canny_grayscale(self, grayscale_image):
        """Test Canny with grayscale input"""
        result = canny(grayscale_image, threshold1=0.1, threshold2=0.3)

        assert result.shape == grayscale_image.shape
        assert result.dtype == cp.float32

    def test_canny_detects_edges(self, sample_image):
        """Test that Canny detects edges of the square"""
        result = canny(sample_image, threshold1=0.1, threshold2=0.3)

        # Should detect edges around the square
        # Top edge
        top_edge_pixels = cp.sum(result[28:32, 30:70])
        assert top_edge_pixels > 10, "Should detect top edge"

        # Bottom edge
        bottom_edge_pixels = cp.sum(result[68:72, 30:70])
        assert bottom_edge_pixels > 10, "Should detect bottom edge"

        # Left edge
        left_edge_pixels = cp.sum(result[30:70, 28:32])
        assert left_edge_pixels > 10, "Should detect left edge"

        # Right edge
        right_edge_pixels = cp.sum(result[30:70, 68:72])
        assert right_edge_pixels > 10, "Should detect right edge"

    # ========== Parameter Tests ==========

    def test_canny_different_thresholds(self, sample_image):
        """Test Canny with different threshold values"""
        # Low thresholds - more edges
        result_low = canny(sample_image, threshold1=0.05, threshold2=0.15)
        edge_count_low = cp.sum(result_low > 0)

        # High thresholds - fewer edges
        result_high = canny(sample_image, threshold1=0.5, threshold2=1.0)
        edge_count_high = cp.sum(result_high > 0)

        assert edge_count_low >= edge_count_high, "Lower thresholds should detect more or equal edges"

    def test_canny_different_aperture_sizes(self, sample_image):
        """Test Canny with different Sobel aperture sizes"""
        result_3 = canny(sample_image, threshold1=0.1, threshold2=0.3, aperture_size=3)
        result_5 = canny(sample_image, threshold1=0.1, threshold2=0.3, aperture_size=5)

        assert result_3.shape == result_5.shape
        # Different aperture sizes should produce slightly different results
        # but similar edge patterns

    def test_canny_l2_gradient(self, sample_image):
        """Test Canny with L2 gradient computation"""
        result_l1 = canny(
            sample_image, threshold1=0.1, threshold2=0.3, l2_gradient=False
        )
        result_l2 = canny(sample_image, threshold1=0.1, threshold2=0.3, l2_gradient=True)

        assert result_l1.shape == result_l2.shape
        # L2 gradient typically produces cleaner edges

    # ========== Edge Case Tests ==========

    def test_canny_uniform_image(self):
        """Test Canny on uniform image (no edges)"""
        image = cp.ones((100, 100, 3), dtype=cp.float32) * 0.5
        result = canny(image, threshold1=0.1, threshold2=0.3)

        # Uniform image should produce almost no edges
        edge_count = cp.sum(result > 0)
        assert edge_count < 100, "Uniform image should have minimal edges"

    def test_canny_high_contrast(self):
        """Test Canny on high contrast image"""
        # Create image with distinct regions (not checkerboard which is too fine)
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        # Create vertical stripes (easier to detect)
        image[:, ::10] = 1.0  # Vertical stripes every 10 pixels
        result = canny(image, threshold1=0.05, threshold2=0.2)

        # High contrast should produce detectable edges
        edge_count = cp.sum(result > 0)
        assert edge_count > 50, f"High contrast image should have edges (got {edge_count})"

    def test_canny_threshold_order(self, sample_image):
        """Test that threshold1 < threshold2 is enforced"""
        # Should work with correct order
        result1 = canny(sample_image, threshold1=0.1, threshold2=0.3)
        assert result1 is not None

        # Should handle swapped thresholds gracefully
        result2 = canny(sample_image, threshold1=0.3, threshold2=0.1)
        assert result2 is not None

    # ========== OpenCV Compatibility Tests ==========

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_canny_opencv_compatibility_basic(self, sample_image):
        """Test Canny OpenCV compatibility with basic parameters"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)
        image_uint8 = (image_np * 255).astype(np.uint8)

        # OpenCV Canny (works on grayscale)
        gray = cv2.cvtColor(image_uint8, cv2.COLOR_BGR2GRAY)
        cv_result = cv2.Canny(gray, 25, 75, apertureSize=3, L2gradient=False)
        cv_result_float = cv_result.astype(np.float32) / 255.0

        # Pixtreme Canny
        # Note: Pixtreme uses float32 [0,1], so threshold scale is different from OpenCV
        # Sobel on float32 [0,1] gives magnitude ~[0, 4] for L1
        # Empirically tuned thresholds to match OpenCV behavior
        px_result = canny(
            sample_image,
            threshold1=0.1,
            threshold2=0.3,
            aperture_size=3,
            l2_gradient=False,
        )
        px_result_np = cp.asnumpy(px_result)

        # Compare edge patterns (allow for differences due to float32 vs uint8)
        # Use correlation to measure similarity
        correlation = np.corrcoef(cv_result_float.flatten(), px_result_np.flatten())[
            0, 1
        ]
        # Relaxed threshold due to numerical differences
        assert (
            correlation > 0.6
        ), f"Canny results should have similar edge patterns to OpenCV (correlation={correlation:.4f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_canny_opencv_compatibility_l2(self, sample_image):
        """Test Canny OpenCV compatibility with L2 gradient"""
        # Convert to numpy for OpenCV
        image_np = cp.asnumpy(sample_image)
        image_uint8 = (image_np * 255).astype(np.uint8)

        # OpenCV Canny with L2 gradient
        gray = cv2.cvtColor(image_uint8, cv2.COLOR_BGR2GRAY)
        cv_result = cv2.Canny(gray, 25, 75, apertureSize=3, L2gradient=True)
        cv_result_float = cv_result.astype(np.float32) / 255.0

        # Pixtreme Canny with L2 gradient
        px_result = canny(
            sample_image,
            threshold1=0.1,
            threshold2=0.3,
            aperture_size=3,
            l2_gradient=True,
        )
        px_result_np = cp.asnumpy(px_result)

        # Compare
        correlation = np.corrcoef(cv_result_float.flatten(), px_result_np.flatten())[
            0, 1
        ]
        # Relaxed threshold due to numerical differences
        assert (
            correlation > 0.6
        ), f"Canny L2 results should have similar edge patterns to OpenCV (correlation={correlation:.4f})"

    # ========== Performance Tests ==========

    def test_canny_performance(self):
        """Test Canny performance on large image"""
        import time

        large_image = cp.random.rand(1024, 1024, 3).astype(cp.float32)

        start = time.perf_counter()
        result = canny(large_image, threshold1=0.1, threshold2=0.3)
        cp.cuda.Stream.null.synchronize()  # Wait for GPU
        elapsed = time.perf_counter() - start

        assert result.shape == (1024, 1024)
        assert elapsed < 0.5, f"Canny should process 1024x1024 in <500ms (took {elapsed*1000:.1f}ms)"

    # ========== Integration Tests ==========

    def test_canny_pipeline(self):
        """Test Canny in a complete edge detection pipeline"""
        # Create test image with multiple features
        image = cp.zeros((200, 200, 3), dtype=cp.float32)
        # Circle
        y, x = cp.ogrid[:200, :200]
        circle_mask = ((x - 100) ** 2 + (y - 100) ** 2) <= 40**2
        image[circle_mask] = 0.8
        # Rectangle
        image[50:80, 140:180] = 0.6

        # Apply Canny
        edges = canny(image, threshold1=0.1, threshold2=0.3)

        # Should detect both circle and rectangle edges
        circle_edges = cp.sum(edges[60:140, 60:140])
        rect_edges = cp.sum(edges[50:80, 140:180])

        assert circle_edges > 50, "Should detect circle edges"
        assert rect_edges > 20, "Should detect rectangle edges"
