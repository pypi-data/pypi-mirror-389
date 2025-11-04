"""Test suite for pixtreme_filter.morphology.morphology_gradient (gradient operation)"""

import cupy as cp
from pixtreme_filter.morphology import morphology_gradient


class TestMorphologyGradient:
    """Test cases for morphology_gradient() function"""

    def test_gradient_basic(self):
        """Test basic gradient operation"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        result = morphology_gradient(image, ksize=3)

        assert isinstance(result, cp.ndarray)
        assert result.shape == (128, 128, 3)
        assert result.dtype == cp.float32

    def test_gradient_detects_edges(self):
        """Test that gradient detects edges of objects"""
        # Black background with white square
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0  # 48x48 white square

        result = morphology_gradient(image, ksize=3)

        # Center should have low gradient (uniform white)
        assert result[64, 64, 0] < 0.2, "Uniform regions should have low gradient"

        # Edges should have high gradient
        # Check points at the boundary (ksize=3 detects edges at boundary)
        assert result[40, 64, 0] > 0.5, "Edges should have high gradient"
        assert result[87, 64, 0] > 0.5, "Edges should have high gradient"
        assert result[64, 40, 0] > 0.5, "Edges should have high gradient"
        assert result[64, 87, 0] > 0.5, "Edges should have high gradient"

    def test_gradient_uniform_image_zero(self):
        """Test that gradient on uniform image is nearly zero"""
        # Uniform gray image
        image = cp.full((128, 128, 3), 0.5, dtype=cp.float32)

        result = morphology_gradient(image, ksize=3)

        # Center region should be near zero (no edges)
        center_region = result[10:118, 10:118, :]
        assert cp.allclose(center_region, 0.0, atol=0.1)

    def test_gradient_white_image(self):
        """Test gradient on white image"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)

        result = morphology_gradient(image, ksize=5)

        # Center should be nearly zero (uniform white)
        center_region = result[10:118, 10:118, :]
        assert cp.allclose(center_region, 0.0, atol=0.1)

    def test_gradient_black_image(self):
        """Test gradient on black image"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        result = morphology_gradient(image, ksize=5)

        # Center should be nearly zero (uniform black)
        center_region = result[10:118, 10:118, :]
        assert cp.allclose(center_region, 0.0, atol=0.1)

    def test_gradient_different_kernel_sizes(self):
        """Test gradient with different kernel sizes"""
        # Create image with edge
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0

        for ksize in [3, 5, 7]:
            result = morphology_gradient(image, ksize=ksize)

            assert result.shape == (128, 128, 3)
            # Larger kernel should produce thicker edge detection
            edge_pixels = cp.sum(result > 0.3)
            assert edge_pixels > 0, f"ksize={ksize} should detect edges"

    def test_gradient_custom_kernel(self):
        """Test gradient with custom kernel"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0

        # Custom cross-shaped kernel
        kernel = cp.zeros((5, 5), dtype=cp.int32)
        kernel[2, :] = 1
        kernel[:, 2] = 1

        result = morphology_gradient(image, ksize=5, kernel=kernel)

        assert result.shape == (128, 128, 3)
        # Cross kernel should still detect edges
        assert cp.sum(result > 0.3) > 0

    def test_gradient_values_in_range(self):
        """Test that gradient values are in valid range [0, 1]"""
        image = cp.random.rand(128, 128, 3).astype(cp.float32)

        result = morphology_gradient(image, ksize=5)

        assert cp.all(result >= 0.0), "Gradient should be non-negative"
        assert cp.all(result <= 1.0), "Gradient should not exceed 1.0"

    def test_gradient_circle_shape(self):
        """Test gradient on circular shape"""
        # Create circle
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        y, x = cp.ogrid[:128, :128]
        mask = (x - 64) ** 2 + (y - 64) ** 2 <= 30**2
        image[mask] = 1.0

        result = morphology_gradient(image, ksize=3)

        # Center of circle should have low gradient
        assert result[64, 64, 0] < 0.2, "Center should have low gradient"

        # Boundary points should have high gradient
        # Point on circle perimeter (approximate)
        assert result[64, 94, 0] > 0.5, "Circle boundary should have high gradient"


class TestMorphologyGradientIntegration:
    """Integration tests for morphology gradient"""

    def test_gradient_edge_detection_workflow(self):
        """Test realistic edge detection scenario"""
        # Create image with multiple objects
        image = cp.zeros((256, 256, 3), dtype=cp.float32)

        # Add square
        image[50:100, 50:100, :] = 1.0

        # Add circle
        y, x = cp.ogrid[:256, :256]
        mask = (x - 180) ** 2 + (y - 180) ** 2 <= 40**2
        image[mask] = 1.0

        # Apply gradient
        result = morphology_gradient(image, ksize=5)

        # Inside objects should have low gradient
        assert result[75, 75, 0] < 0.2, "Inside square should have low gradient"
        assert result[180, 180, 0] < 0.2, "Inside circle should have low gradient"

        # Background should have low gradient
        assert result[20, 20, 0] < 0.2, "Background should have low gradient"

        # Edges should have higher gradient values
        edge_sum = cp.sum(result > 0.3)
        assert edge_sum > 100, "Should detect edges of objects"

    def test_gradient_larger_kernel_thicker_edges(self):
        """Test that larger kernels produce thicker edge detection"""
        # Create simple edge
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[:, 64:, :] = 1.0  # Vertical edge at x=64

        result_k3 = morphology_gradient(image, ksize=3)
        result_k7 = morphology_gradient(image, ksize=7)

        # Larger kernel should detect more edge pixels
        edge_pixels_k3 = cp.sum(result_k3 > 0.3)
        edge_pixels_k7 = cp.sum(result_k7 > 0.3)

        assert edge_pixels_k7 > edge_pixels_k3, "Larger kernel should produce thicker edges"

    def test_gradient_combination_of_dilate_erode(self):
        """Test that gradient is equivalent to (dilation - erosion)"""
        from pixtreme_filter.morphology import dilate, erode

        # Create test image
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0

        # Method 1: Use morphology_gradient
        result_gradient = morphology_gradient(image, ksize=5)

        # Method 2: Manual dilate - erode
        dilated = dilate(image, ksize=5)
        eroded = erode(image, ksize=5)
        result_manual = dilated - eroded

        # Results should be identical
        assert cp.allclose(result_gradient, result_manual, atol=1e-6)

    def test_gradient_preserves_dtype(self):
        """Test that gradient preserves input dtype"""
        image = cp.random.rand(128, 128, 3).astype(cp.float32)

        result = morphology_gradient(image, ksize=5)

        assert result.dtype == cp.float32
