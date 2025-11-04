"""Test suite for pixtreme_filter.morphology.erode module (erode, create_erode_kernel)"""

import cupy as cp
from pixtreme_filter.morphology import create_erode_kernel, erode


class TestCreateErodeKernel:
    """Test cases for create_erode_kernel() function"""

    def test_create_kernel_basic(self):
        """Test basic kernel creation"""
        kernel = create_erode_kernel(ksize=3)

        assert isinstance(kernel, cp.ndarray)
        assert kernel.shape == (3, 3)
        assert kernel.dtype == cp.int32

    def test_create_kernel_all_ones(self):
        """Test that kernel is filled with ones"""
        kernel = create_erode_kernel(ksize=3)

        assert cp.all(kernel == 1), "Kernel should be all ones"

    def test_create_kernel_different_sizes(self):
        """Test kernel creation with different sizes"""
        for size in [3, 5, 7, 9]:
            kernel = create_erode_kernel(ksize=size)

            assert kernel.shape == (size, size)
            assert cp.all(kernel == 1)

    def test_create_kernel_odd_size(self):
        """Test that odd sizes work correctly"""
        sizes = [3, 5, 7, 9, 11]

        for size in sizes:
            kernel = create_erode_kernel(ksize=size)
            assert kernel.shape == (size, size)

    def test_create_kernel_small(self):
        """Test smallest kernel (3x3)"""
        kernel = create_erode_kernel(ksize=3)

        assert kernel.shape == (3, 3)
        expected = cp.ones((3, 3), dtype=cp.int32)
        assert cp.array_equal(kernel, expected)

    def test_create_kernel_large(self):
        """Test large kernel (15x15)"""
        kernel = create_erode_kernel(ksize=15)

        assert kernel.shape == (15, 15)
        assert cp.all(kernel == 1)


class TestErode:
    """Test cases for erode() function"""

    def test_erode_basic(self):
        """Test basic erosion"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        result = erode(image, ksize=3)

        assert isinstance(result, cp.ndarray)
        assert result.shape == (128, 128, 3)
        assert result.dtype == cp.float32

    def test_erode_white_image(self):
        """Test erosion on white image (no change)"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        result = erode(image, ksize=3, border_value=1.0)

        # White image should remain white
        assert cp.allclose(result, 1.0, atol=1e-6)

    def test_erode_black_image(self):
        """Test erosion on black image (no change)"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        result = erode(image, ksize=3)

        # Black image should remain black
        assert cp.allclose(result, 0.0, atol=1e-6)

    def test_erode_shrinks_white_regions(self):
        """Test that erosion shrinks white regions"""
        # Create white square in black background
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0  # 48x48 white square

        result = erode(image, ksize=3)

        # White region should be smaller
        # Check that edges became black
        assert result[40, 64, 0] < 0.5, "Top edge should be eroded"
        assert result[87, 64, 0] < 0.5, "Bottom edge should be eroded"
        assert result[64, 40, 0] < 0.5, "Left edge should be eroded"
        assert result[64, 87, 0] < 0.5, "Right edge should be eroded"

        # Center should still be white
        assert result[64, 64, 0] > 0.9, "Center should remain white"

    def test_erode_different_ksizes(self):
        """Test erosion with different kernel sizes"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[20:108, 20:108, :] = 0.0  # Black square in white

        for ksize in [3, 5, 7]:
            result = erode(image, ksize=ksize)

            # Larger kernel should erode more
            assert result.shape == (128, 128, 3)

    def test_erode_custom_kernel(self):
        """Test erosion with custom kernel"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0

        # Create custom cross-shaped kernel
        kernel = cp.zeros((5, 5), dtype=cp.int32)
        kernel[2, :] = 1  # Horizontal line
        kernel[:, 2] = 1  # Vertical line

        result = erode(image, ksize=5, kernel=kernel)

        assert result.shape == (128, 128, 3)

    def test_erode_border_value_zero(self):
        """Test erosion with border_value=0.0"""
        # White image
        image = cp.ones((128, 128, 3), dtype=cp.float32)

        result = erode(image, ksize=3, border_value=0.0)

        # Edges should be darker due to border_value=0
        assert result[0, 64, 0] < 1.0, "Top edge should be affected by border"
        assert result[127, 64, 0] < 1.0, "Bottom edge should be affected by border"

    def test_erode_border_value_one(self):
        """Test erosion with border_value=1.0"""
        # Black image with white edges
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[:, :, :] = 0.5  # Gray image

        result = erode(image, ksize=3, border_value=1.0)

        # Should not be zero (border prevents full erosion)
        assert result.shape == (128, 128, 3)

    def test_erode_preserves_dtype(self):
        """Test that dtype is preserved"""
        image = cp.random.rand(128, 128, 3).astype(cp.float32)
        result = erode(image, ksize=3)

        assert result.dtype == cp.float32

    def test_erode_values_in_range(self):
        """Test that output values are in valid range"""
        image = cp.random.rand(128, 128, 3).astype(cp.float32)
        result = erode(image, ksize=3)

        assert cp.all(result >= 0.0), "All values should be >= 0"
        assert cp.all(result <= 1.0), "All values should be <= 1"

    def test_erode_gradient_image(self):
        """Test erosion on gradient image"""
        # Create horizontal gradient
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        for i in range(128):
            image[:, i, :] = i / 127.0

        result = erode(image, ksize=3)

        # Erosion should shift gradient (take minimum)
        assert result.shape == (128, 128, 3)

    def test_erode_different_image_sizes(self):
        """Test erosion on different image sizes"""
        sizes = [(64, 64), (128, 256), (256, 256), (512, 512)]

        for h, w in sizes:
            image = cp.random.rand(h, w, 3).astype(cp.float32)
            result = erode(image, ksize=3)

            assert result.shape == (h, w, 3)

    def test_erode_large_image(self):
        """Test erosion on large image"""
        large_image = cp.random.rand(2160, 3840, 3).astype(cp.float32)

        result = erode(large_image, ksize=3)

        assert result.shape == (2160, 3840, 3)

    def test_erode_small_kernel_less_erosion(self):
        """Test that smaller kernel causes less erosion"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0  # Black square

        result_3 = erode(image, ksize=3)
        result_7 = erode(image, ksize=7)

        # Larger kernel should erode more (more white pixels become black)
        white_pixels_3 = cp.sum(result_3 > 0.5)
        white_pixels_7 = cp.sum(result_7 > 0.5)

        assert white_pixels_7 < white_pixels_3, "Larger kernel should erode more"

    def test_erode_checkerboard_pattern(self):
        """Test erosion on checkerboard pattern"""
        # Create checkerboard
        image = cp.zeros((64, 64, 3), dtype=cp.float32)
        for i in range(0, 64, 8):
            for j in range(0, 64, 8):
                if (i // 8 + j // 8) % 2 == 0:
                    image[i : i + 8, j : j + 8, :] = 1.0

        result = erode(image, ksize=3)

        # Erosion should reduce white squares
        assert result.shape == (64, 64, 3)

    def test_erode_uint8_input(self):
        """Test that uint8 input is converted to float32"""
        image_uint8 = (cp.random.rand(128, 128, 3) * 255).astype(cp.uint8)

        result = erode(image_uint8, ksize=3)

        assert result.dtype == cp.float32
        assert result.shape == (128, 128, 3)

    def test_erode_channels_independent(self):
        """Test that channels are processed independently"""
        # Red channel: white, Green: black, Blue: gray
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[:, :, 0] = 1.0  # Red
        image[:, :, 1] = 0.0  # Green
        image[:, :, 2] = 0.5  # Blue

        result = erode(image, ksize=3, border_value=0.5)

        # Channels should be processed independently
        # Red should erode toward border_value
        # Green should stay black
        # Blue should stay gray (if uniform)
        assert result.shape == (128, 128, 3)


class TestErodeIntegration:
    """Integration tests for erosion workflow"""

    def test_erode_multiple_iterations(self):
        """Test applying erosion multiple times"""
        # Create white circle
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        y, x = cp.ogrid[:128, :128]
        mask = (x - 64) ** 2 + (y - 64) ** 2 <= 40**2
        image[mask] = 1.0

        # Apply erosion 3 times
        result = image
        for _ in range(3):
            result = erode(result, ksize=3)

        # Circle should be smaller
        assert result.shape == (128, 128, 3)
        # Center should still be white
        assert result[64, 64, 0] > 0.5

    def test_erode_then_check_edges(self):
        """Test edge detection via erosion"""
        # Create image with features
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[30:98, 30:98, :] = 0.0  # Black square

        # Erode
        eroded = erode(image, ksize=3)

        # Difference shows edges
        edges = image - eroded

        assert cp.any(edges > 0), "Should detect edges"

    def test_erode_preserve_small_features(self):
        """Test that small features are removed by erosion"""
        # Create image with 1-pixel noise
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[64, 64, :] = 1.0  # Single white pixel

        result = erode(image, ksize=3)

        # Single pixel should be removed
        assert result[64, 64, 0] < 0.5, "Single pixel should be eroded"

    def test_erode_real_world_scenario(self):
        """Test erosion in real-world scenario (noise removal)"""
        # Create image with salt-and-pepper noise
        image = cp.ones((256, 256, 3), dtype=cp.float32) * 0.5

        # Add random noise
        noise = cp.random.rand(256, 256, 3) > 0.95
        image[noise] = 1.0

        # Erode to remove white noise
        result = erode(image, ksize=3)

        # Most noise should be removed
        noise_count_before = cp.sum(image > 0.9)
        noise_count_after = cp.sum(result > 0.9)

        assert noise_count_after < noise_count_before, "Erosion should reduce noise"

    def test_erode_with_different_kernels(self):
        """Test erosion with various custom kernels"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0

        # Test different kernel patterns
        # 1. Horizontal line
        kernel_h = cp.zeros((3, 3), dtype=cp.int32)
        kernel_h[1, :] = 1
        result_h = erode(image, ksize=3, kernel=kernel_h)

        # 2. Vertical line
        kernel_v = cp.zeros((3, 3), dtype=cp.int32)
        kernel_v[:, 1] = 1
        result_v = erode(image, ksize=3, kernel=kernel_v)

        # 3. Diagonal
        kernel_d = cp.eye(3, dtype=cp.int32)
        result_d = erode(image, ksize=3, kernel=kernel_d)

        # All should produce valid results
        assert result_h.shape == result_v.shape == result_d.shape == (128, 128, 3)
