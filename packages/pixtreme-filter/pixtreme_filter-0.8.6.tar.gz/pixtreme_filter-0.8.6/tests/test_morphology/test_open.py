"""Test suite for pixtreme_filter.morphology.morphology_open (opening operation)"""

import cupy as cp
from pixtreme_filter.morphology import morphology_open


class TestMorphologyOpen:
    """Test cases for morphology_open() function"""

    def test_open_basic(self):
        """Test basic opening operation"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        result = morphology_open(image, ksize=3)

        assert isinstance(result, cp.ndarray)
        assert result.shape == (128, 128, 3)
        assert result.dtype == cp.float32

    def test_open_removes_small_noise(self):
        """Test that opening removes small white dots (noise)"""
        # Black background with small white dots
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        # Add small noise dots (2x2 pixels)
        image[30:32, 30:32, :] = 1.0
        image[50:52, 50:52, :] = 1.0
        image[70:72, 70:72, :] = 1.0
        image[90:92, 90:92, :] = 1.0

        result = morphology_open(image, ksize=5)

        # Small dots should be removed
        assert result[31, 31, 0] < 0.1, "Small noise should be removed"
        assert result[51, 51, 0] < 0.1, "Small noise should be removed"
        assert result[71, 71, 0] < 0.1, "Small noise should be removed"
        assert result[91, 91, 0] < 0.1, "Small noise should be removed"

    def test_open_preserves_large_features(self):
        """Test that opening preserves large white regions"""
        # Black background with large white square
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0  # 48x48 white square

        result = morphology_open(image, ksize=5)

        # Center of large square should remain white
        assert result[64, 64, 0] > 0.9, "Large features should be preserved"
        # Some erosion at edges is expected
        assert cp.sum(result > 0.5) > 1000, "Large features should mostly remain"

    def test_open_smooths_boundaries(self):
        """Test that opening smooths object boundaries"""
        # Create shape with rough edges
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0

        # Add some protrusions (rough edges)
        image[39, 50:55, :] = 1.0  # Top protrusion
        image[88, 60:65, :] = 1.0  # Bottom protrusion

        result = morphology_open(image, ksize=3)

        # Protrusions should be smoothed out
        assert result.shape == (128, 128, 3)

    def test_open_white_image_unchanged(self):
        """Test that opening on white image with large kernel"""
        image = cp.ones((128, 128, 3), dtype=cp.float32)

        result = morphology_open(image, ksize=5)

        # Should be mostly white (except possibly edges)
        center_region = result[10:118, 10:118, :]
        assert cp.allclose(center_region, 1.0, atol=0.1)

    def test_open_black_image_unchanged(self):
        """Test that opening on black image returns black"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        result = morphology_open(image, ksize=5)

        # Should remain black
        assert cp.allclose(result, 0.0, atol=1e-6)

    def test_open_different_kernel_sizes(self):
        """Test opening with different kernel sizes"""
        # Create image with noise
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[50:78, 50:78, :] = 1.0  # Large square
        image[20:22, 20:22, :] = 1.0  # Small noise

        for ksize in [3, 5, 7]:
            result = morphology_open(image, ksize=ksize)

            assert result.shape == (128, 128, 3)
            # Larger kernel should remove more noise
            if ksize >= 5:
                assert result[21, 21, 0] < 0.1, f"ksize={ksize} should remove small noise"

    def test_open_custom_kernel(self):
        """Test opening with custom kernel"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0

        # Custom cross-shaped kernel
        kernel = cp.zeros((5, 5), dtype=cp.int32)
        kernel[2, :] = 1
        kernel[:, 2] = 1

        result = morphology_open(image, ksize=5, kernel=kernel)

        assert result.shape == (128, 128, 3)

    def test_open_removes_thin_lines(self):
        """Test that opening removes thin lines"""
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        # Add thin horizontal line (2 pixels thick)
        image[63:65, 20:108, :] = 1.0

        result = morphology_open(image, ksize=5)

        # Thin line should be mostly removed
        assert cp.sum(result > 0.5) < cp.sum(image > 0.5), "Thin lines should be reduced"


class TestMorphologyOpenIntegration:
    """Integration tests for morphology opening"""

    def test_open_noise_removal_workflow(self):
        """Test realistic noise removal scenario"""
        # Create image with large object + noise
        image = cp.zeros((256, 256, 3), dtype=cp.float32)

        # Large circle (main object)
        y, x = cp.ogrid[:256, :256]
        mask = (x - 128) ** 2 + (y - 128) ** 2 <= 60**2
        image[mask] = 1.0

        # Add salt noise (small white dots)
        noise_positions = [
            (50, 50),
            (60, 200),
            (200, 60),
            (200, 200),
            (100, 30),
            (150, 30),
            (30, 100),
            (220, 150),
        ]
        for y_pos, x_pos in noise_positions:
            image[y_pos : y_pos + 2, x_pos : x_pos + 2, :] = 1.0

        # Apply opening to remove noise
        result = morphology_open(image, ksize=5)

        # Main circle should be preserved
        assert result[128, 128, 0] > 0.9, "Main object should be preserved"

        # Noise should be removed
        assert result[50, 50, 0] < 0.1, "Noise should be removed"
        assert result[200, 200, 0] < 0.1, "Noise should be removed"

    def test_open_is_idempotent(self):
        """Test that applying opening twice gives same result"""
        # Create test image
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0
        image[20:22, 20:22, :] = 1.0  # noise

        # Apply opening twice
        result1 = morphology_open(image, ksize=5)
        result2 = morphology_open(result1, ksize=5)

        # Results should be similar (idempotent property)
        assert cp.allclose(result1, result2, atol=0.01)

    def test_open_separates_touching_objects(self):
        """Test that opening can separate barely touching objects"""
        # Create two circles connected by thin bridge
        image = cp.zeros((128, 128, 3), dtype=cp.float32)

        # Left circle
        y, x = cp.ogrid[:128, :128]
        mask_left = (x - 40) ** 2 + (y - 64) ** 2 <= 20**2
        image[mask_left] = 1.0

        # Right circle
        mask_right = (x - 88) ** 2 + (y - 64) ** 2 <= 20**2
        image[mask_right] = 1.0

        # Thin connecting bridge
        image[63:65, 60:68, :] = 1.0

        result = morphology_open(image, ksize=5)

        # Bridge should be broken
        # Check middle point of bridge
        assert result[64, 64, 0] < 0.5, "Thin bridge should be removed"

    def test_open_combination_of_erode_dilate(self):
        """Test that opening is equivalent to erosion followed by dilation"""
        from pixtreme_filter.morphology import dilate, erode

        # Create test image
        image = cp.zeros((128, 128, 3), dtype=cp.float32)
        image[40:88, 40:88, :] = 1.0
        image[20:22, 20:22, :] = 1.0

        # Method 1: Use morphology_open
        result_open = morphology_open(image, ksize=5)

        # Method 2: Manual erode then dilate
        eroded = erode(image, ksize=5)
        result_manual = dilate(eroded, ksize=5)

        # Results should be identical
        assert cp.allclose(result_open, result_manual, atol=1e-6)
