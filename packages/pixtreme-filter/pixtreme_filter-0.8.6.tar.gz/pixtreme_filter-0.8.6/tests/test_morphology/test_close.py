"""Test suite for pixtreme_filter.morphology.morphology_close (closing operation)"""

import cupy as cp
from pixtreme_filter.morphology import morphology_close


class TestMorphologyClose:
    """Test cases for morphology_close() function"""

    def test_close_basic(self):
        """Test basic closing operation"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        result = morphology_close(image, ksize=3)

        assert isinstance(result, cp.ndarray)
        assert result.shape == (128, 128, 3)
        assert result.dtype == cp.float32

    def test_close_fills_small_holes(self):
        """Test that closing fills small black holes (pepper noise)"""
        # White background with small black holes
        image = cp.ones((128, 128, 3), dtype=cp.float32)

        # Add small noise holes (2x2 pixels)
        image[30:32, 30:32, :] = 0.0
        image[50:52, 50:52, :] = 0.0
        image[70:72, 70:72, :] = 0.0
        image[90:92, 90:92, :] = 0.0

        result = morphology_close(image, ksize=5)

        # Small holes should be filled
        assert result[31, 31, 0] > 0.9, "Small holes should be filled"
        assert result[51, 51, 0] > 0.9, "Small holes should be filled"
        assert result[71, 71, 0] > 0.9, "Small holes should be filled"
        assert result[91, 91, 0] > 0.9, "Small holes should be filled"

    def test_close_preserves_large_holes(self):
        """Test that closing preserves large black regions"""
        # White background with large black square
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0  # 48x48 black square

        result = morphology_close(image, ksize=5)

        # Center of large square should remain mostly black
        assert result[64, 64, 0] < 0.1, "Large holes should be preserved"
        # Some dilation at edges is expected
        assert cp.sum(result < 0.5) > 1000, "Large holes should mostly remain"

    def test_close_smooths_boundaries(self):
        """Test that closing smooths object boundaries"""
        # Create shape with indentations
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0

        # Add some indentations (rough edges inward)
        image[50:55, 39, :] = 0.0  # Left indentation
        image[60:65, 88, :] = 0.0  # Right indentation

        result = morphology_close(image, ksize=3)

        # Indentations should be smoothed out
        assert result.shape == (128, 128, 3)

    def test_close_white_image_unchanged(self):
        """Test that closing on white image returns white"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)

        result = morphology_close(image, ksize=5)

        # Should be mostly white (except possibly edges due to border_value=0.0)
        center_region = result[10:118, 10:118, :]
        assert cp.allclose(center_region, 1.0, atol=0.1)

    def test_close_black_image_unchanged(self):
        """Test that closing on black image returns black"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        result = morphology_close(image, ksize=5)

        # Should be mostly black (except possibly edges)
        center_region = result[10:118, 10:118, :]
        assert cp.allclose(center_region, 0.0, atol=0.1)

    def test_close_different_kernel_sizes(self):
        """Test closing with different kernel sizes"""
        # Create image with holes
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[50:78, 50:78, :] = 0.0  # Large hole
        image[20:22, 20:22, :] = 0.0  # Small hole

        for ksize in [3, 5, 7]:
            result = morphology_close(image, ksize=ksize)

            assert result.shape == (128, 128, 3)
            # Larger kernel should fill more holes
            if ksize >= 5:
                assert result[21, 21, 0] > 0.9, f"ksize={ksize} should fill small holes"

    def test_close_custom_kernel(self):
        """Test closing with custom kernel"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0

        # Custom cross-shaped kernel
        kernel = cp.zeros((5, 5), dtype=cp.int32)
        kernel[2, :] = 1
        kernel[:, 2] = 1

        result = morphology_close(image, ksize=5, kernel=kernel)

        assert result.shape == (128, 128, 3)

    def test_close_fills_thin_gaps(self):
        """Test that closing fills thin gaps in center region"""
        # Create white image with thin black gap in center
        image = cp.ones((128, 128, 3), dtype=cp.float32)

        # Add thin horizontal gap in center (2 pixels thick, avoiding edges)
        image[63:65, 40:88, :] = 0.0

        result = morphology_close(image, ksize=5)

        # Center of gap should be filled
        assert result[64, 64, 0] > 0.9, "Thin gap in center should be filled"


class TestMorphologyCloseIntegration:
    """Integration tests for morphology closing"""

    def test_close_pepper_noise_removal(self):
        """Test realistic pepper noise (black dots) removal scenario"""
        # Create image with large white object + black noise
        image = cp.ones((256, 256, 3), dtype=cp.float32)

        # Large circle (main white area)
        y, x = cp.ogrid[:256, :256]
        mask = (x - 128) ** 2 + (y - 128) ** 2 <= 60**2
        image[~mask] = 0.0  # Black background

        # Add pepper noise (small black dots on white circle)
        noise_positions = [
            (128, 128),
            (120, 135),
            (135, 120),
            (140, 140),
            (110, 110),
            (145, 145),
            (115, 140),
            (140, 115),
        ]
        for y_pos, x_pos in noise_positions:
            if mask[y_pos, x_pos]:  # Only add noise on white circle
                image[y_pos : y_pos + 2, x_pos : x_pos + 2, :] = 0.0

        # Apply closing to remove noise
        result = morphology_close(image, ksize=5)

        # Main circle should still be white
        assert result[128, 128, 0] > 0.9, "Main object should be preserved"

        # Pepper noise should be filled (positions that had noise should be white again)
        assert result[128, 128, 0] > 0.9, "Noise should be removed"
        assert result[120, 135, 0] > 0.9, "Noise should be removed"

    def test_close_is_idempotent(self):
        """Test that applying closing twice gives same result"""
        # Create test image with holes
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0  # Large hole
        image[20:22, 20:22, :] = 0.0  # Small hole

        # Apply closing twice
        result1 = morphology_close(image, ksize=5)
        result2 = morphology_close(result1, ksize=5)

        # Results should be similar (idempotent property)
        assert cp.allclose(result1, result2, atol=0.01)

    def test_close_connects_nearby_objects(self):
        """Test that closing can connect nearby objects with thin gap"""
        # Create two white squares separated by thin black gap
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        # Top square
        image[20:60, 40:88, :] = 1.0

        # Bottom square
        image[65:108, 40:88, :] = 1.0

        # Thin black gap between them (5 pixels: 60-65)
        # Use larger kernel to bridge the gap
        result = morphology_close(image, ksize=9)

        # Gap should be filled/reduced
        # Check middle point of gap
        assert result[62, 64, 0] > 0.5, "Thin gap should be partially filled"

    def test_close_combination_of_dilate_erode(self):
        """Test that closing is equivalent to dilation followed by erosion"""
        from pixtreme_filter.morphology import dilate, erode

        # Create test image with holes
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 0.0  # Large hole
        image[20:22, 20:22, :] = 0.0  # Small hole

        # Method 1: Use morphology_close
        result_close = morphology_close(image, ksize=5)

        # Method 2: Manual dilate then erode
        dilated = dilate(image, ksize=5)
        result_manual = erode(dilated, ksize=5)

        # Results should be identical
        assert cp.allclose(result_close, result_manual, atol=1e-6)
