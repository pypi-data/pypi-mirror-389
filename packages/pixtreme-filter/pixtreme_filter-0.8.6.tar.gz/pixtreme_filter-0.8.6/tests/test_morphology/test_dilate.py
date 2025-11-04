"""Test suite for pixtreme_filter.morphology.dilate module (dilate, create_dilate_kernel)"""

import cupy as cp
from pixtreme_filter.morphology import create_dilate_kernel, dilate


class TestCreateDilateKernel:
    """Test cases for create_dilate_kernel() function"""

    def test_create_kernel_basic(self):
        """Test basic kernel creation"""
        kernel = create_dilate_kernel(ksize=3)

        assert isinstance(kernel, cp.ndarray)
        assert kernel.shape == (3, 3)
        assert kernel.dtype == cp.int32

    def test_create_kernel_all_ones(self):
        """Test that kernel is filled with ones"""
        kernel = create_dilate_kernel(ksize=3)

        assert cp.all(kernel == 1), "Kernel should be all ones"

    def test_create_kernel_different_sizes(self):
        """Test kernel creation with different sizes"""
        for size in [3, 5, 7, 9]:
            kernel = create_dilate_kernel(ksize=size)

            assert kernel.shape == (size, size)
            assert cp.all(kernel == 1)


class TestDilate:
    """Test cases for dilate() function"""

    def test_dilate_basic(self):
        """Test basic dilation"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        result = dilate(image, ksize=3)

        assert isinstance(result, cp.ndarray)
        assert result.shape == (128, 128, 3)
        assert result.dtype == cp.float32

    def test_dilate_white_image(self):
        """Test dilation on white image (no change with border_value=1.0)"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        result = dilate(image, ksize=3, border_value=1.0)

        # White image should remain white when border_value=1.0
        assert cp.allclose(result, 1.0, atol=1e-6)

    def test_dilate_black_image(self):
        """Test dilation on black image (no change with default border_value)"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        result = dilate(image, ksize=3)  # Use default border_value=0.0

        # Black image should remain black
        assert cp.allclose(result, 0.0, atol=1e-6)

    def test_dilate_expands_white_regions(self):
        """Test that dilation expands white regions"""
        # Create white square in black background
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0  # 48x48 white square

        result = dilate(image, ksize=3)

        # White region should be larger
        # Check that edges expanded outward
        assert result[39, 64, 0] > 0.9, "Top edge should expand"
        assert result[88, 64, 0] > 0.9, "Bottom edge should expand"
        assert result[64, 39, 0] > 0.9, "Left edge should expand"
        assert result[64, 88, 0] > 0.9, "Right edge should expand"

        # Center should still be white
        assert result[64, 64, 0] > 0.9, "Center should remain white"

    def test_dilate_different_ksizes(self):
        """Test dilation with different kernel sizes"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0  # White square

        for ksize in [3, 5, 7]:
            result = dilate(image, ksize=ksize)

            # Larger kernel should dilate more
            assert result.shape == (128, 128, 3)

    def test_dilate_custom_kernel(self):
        """Test dilation with custom kernel"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0

        # Create custom cross-shaped kernel
        kernel = cp.zeros((5, 5), dtype=cp.int32)
        kernel[2, :] = 1  # Horizontal line
        kernel[:, 2] = 1  # Vertical line

        result = dilate(image, ksize=5, kernel=kernel)

        assert result.shape == (128, 128, 3)

    def test_dilate_border_value_zero(self):
        """Test dilation with default border_value=0.0 (no white edges)"""
        # Black image with white center
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[60:68, 60:68, :] = 1.0

        result = dilate(image, ksize=3)  # Default border_value=0.0

        # White region should expand, but edges should stay black
        assert result.shape == (128, 128, 3)
        # Check edges are still black (no white border)
        assert result[0, 64, 0] < 0.1, "Top edge should remain black"
        assert result[127, 64, 0] < 0.1, "Bottom edge should remain black"
        assert result[64, 0, 0] < 0.1, "Left edge should remain black"
        assert result[64, 127, 0] < 0.1, "Right edge should remain black"

    def test_dilate_border_value_one(self):
        """Test dilation with explicit border_value=1.0 (creates white edges)"""
        # Black image
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        result = dilate(image, ksize=3, border_value=1.0)

        # Edges should become white due to border_value=1.0
        assert result[0, 64, 0] > 0.9, "Top edge should be white from border"
        assert result[127, 64, 0] > 0.9, "Bottom edge should be white from border"
        assert result[64, 0, 0] > 0.9, "Left edge should be white from border"
        assert result[64, 127, 0] > 0.9, "Right edge should be white from border"

    def test_dilate_preserves_dtype(self):
        """Test that dtype is preserved"""
        image = cp.random.rand(128, 128, 3).astype(cp.float32)
        result = dilate(image, ksize=3)

        assert result.dtype == cp.float32

    def test_dilate_values_in_range(self):
        """Test that output values are in valid range"""
        image = cp.random.rand(128, 128, 3).astype(cp.float32)
        result = dilate(image, ksize=3)

        assert cp.all(result >= 0.0), "All values should be >= 0"
        assert cp.all(result <= 1.0), "All values should be <= 1"

    def test_dilate_larger_kernel_more_dilation(self):
        """Test that larger kernel causes more dilation"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0  # White square

        result_3 = dilate(image, ksize=3)
        result_7 = dilate(image, ksize=7)

        # Larger kernel should dilate more (more black pixels become white)
        white_pixels_3 = cp.sum(result_3 > 0.5)
        white_pixels_7 = cp.sum(result_7 > 0.5)

        assert white_pixels_7 > white_pixels_3, "Larger kernel should dilate more"

    def test_dilate_uint8_input(self):
        """Test that uint8 input is converted to float32"""
        image_uint8 = (cp.random.rand(128, 128, 3) * 255).astype(cp.uint8)

        result = dilate(image_uint8, ksize=3)

        assert result.dtype == cp.float32
        assert result.shape == (128, 128, 3)

    def test_dilate_channels_independent(self):
        """Test that channels are processed independently"""
        # Red channel: black, Green: white, Blue: gray
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[:, :, 0] = 0.0  # Red
        image[:, :, 1] = 1.0  # Green
        image[:, :, 2] = 0.5  # Blue

        result = dilate(image, ksize=3, border_value=0.5)

        # Channels should be processed independently
        assert result.shape == (128, 128, 3)


class TestDilateIntegration:
    """Integration tests for dilation workflow"""

    def test_dilate_multiple_iterations(self):
        """Test applying dilation multiple times"""
        # Create black image with small white dot
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[64, 64, :] = 1.0

        # Apply dilation 3 times
        result = image
        for _ in range(3):
            result = dilate(result, ksize=3)

        # White region should expand
        assert result.shape == (128, 128, 3)
        # Center should still be white
        assert result[64, 64, 0] > 0.5

    def test_dilate_fills_gaps(self):
        """Test that dilation can fill small gaps"""
        # Create image with two nearby white regions
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[60:68, 40:48, :] = 1.0  # Left white square
        image[60:68, 52:60, :] = 1.0  # Right white square (4px gap)

        # Dilate with large kernel to connect regions
        result = dilate(image, ksize=5)

        # Gap should be filled
        assert result[64, 50, 0] > 0.5, "Gap should be filled by dilation"

    def test_dilate_preserves_large_features(self):
        """Test that large features are expanded"""
        # Create large white circle
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        y, x = cp.ogrid[:128, :128]
        mask = (x - 64) ** 2 + (y - 64) ** 2 <= 30**2
        image[mask] = 1.0

        result = dilate(image, ksize=5)

        # Circle should be larger
        # Check radius expanded
        assert result[64, 94, 0] > 0.5, "Circle should expand outward"

    def test_dilate_opposite_of_erode(self):
        """Test that dilate is conceptually opposite of erode"""
        from pixtreme_filter.morphology import erode

        # Create test image
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0

        # Erode should shrink, dilate should expand
        eroded = erode(image, ksize=3)
        dilated = dilate(image, ksize=3)

        # Count white pixels
        white_eroded = cp.sum(eroded > 0.5)
        white_dilated = cp.sum(dilated > 0.5)
        white_original = cp.sum(image > 0.5)

        assert white_eroded < white_original, "Erode should reduce white pixels"
        assert white_dilated > white_original, "Dilate should increase white pixels"
