"""Tests for CLAHE (Contrast Limited Adaptive Histogram Equalization)"""

import cupy as cp
import numpy as np
import pytest

from pixtreme_filter.histogram import clahe


class TestCLAHEBasic:
    """Basic functionality tests for CLAHE"""

    def test_clahe_basic_execution(self):
        """Test that clahe executes without errors"""
        # Create low contrast test image
        image = cp.random.uniform(0.3, 0.5, (256, 256, 3)).astype(cp.float32)
        result = clahe(image)
        assert result.shape == image.shape
        assert result.dtype == cp.float32

    def test_clahe_grayscale(self):
        """Test CLAHE with grayscale image"""
        image = cp.random.uniform(0.3, 0.5, (256, 256)).astype(cp.float32)
        result = clahe(image)
        assert result.shape == image.shape
        assert result.dtype == cp.float32

    def test_clahe_output_range(self):
        """Test that output values are in valid range [0, 1]"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        result = clahe(image)
        assert float(cp.min(result)) >= 0.0
        assert float(cp.max(result)) <= 1.0

    def test_clahe_improves_contrast(self):
        """Test that CLAHE improves contrast for low-contrast images"""
        # Create low contrast image (narrow range)
        image = cp.random.uniform(0.4, 0.6, (256, 256, 3)).astype(cp.float32)
        result = clahe(image)

        # CLAHE should expand the range (improve contrast)
        input_range = float(cp.max(image) - cp.min(image))
        output_range = float(cp.max(result) - cp.min(result))
        assert output_range > input_range


class TestCLAHEParameters:
    """Parameter validation tests"""

    def test_clahe_invalid_dtype(self):
        """Test that non-float32 input raises TypeError"""
        image = cp.random.randint(0, 256, (256, 256, 3), dtype=cp.uint8)
        with pytest.raises(TypeError, match="Input must be float32"):
            clahe(image)

    def test_clahe_custom_clip_limit(self):
        """Test CLAHE with custom clip limit"""
        image = cp.random.uniform(0.3, 0.5, (256, 256, 3)).astype(cp.float32)

        # Lower clip limit = less contrast enhancement
        result_low = clahe(image, clip_limit=1.0)
        # Higher clip limit = more contrast enhancement
        result_high = clahe(image, clip_limit=40.0)

        assert result_low.shape == image.shape
        assert result_high.shape == image.shape

        # Higher clip limit should produce different result
        # (not checking which is "better", just that they differ)
        diff = float(cp.mean(cp.abs(result_high - result_low)))
        assert diff > 1e-6

    def test_clahe_custom_tile_grid_size(self):
        """Test CLAHE with custom tile grid size"""
        image = cp.random.uniform(0.3, 0.5, (256, 256, 3)).astype(cp.float32)

        # Different tile sizes
        result_4x4 = clahe(image, tile_grid_size=(4, 4))
        result_8x8 = clahe(image, tile_grid_size=(8, 8))
        result_16x16 = clahe(image, tile_grid_size=(16, 16))

        assert result_4x4.shape == image.shape
        assert result_8x8.shape == image.shape
        assert result_16x16.shape == image.shape

        # Different tile sizes should produce different results
        diff_4_8 = float(cp.mean(cp.abs(result_4x4 - result_8x8)))
        diff_8_16 = float(cp.mean(cp.abs(result_8x8 - result_16x16)))
        assert diff_4_8 > 1e-6
        assert diff_8_16 > 1e-6

    def test_clahe_invalid_clip_limit(self):
        """Test that invalid clip_limit raises ValueError"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        with pytest.raises(ValueError, match="clip_limit must be positive"):
            clahe(image, clip_limit=0.0)
        with pytest.raises(ValueError, match="clip_limit must be positive"):
            clahe(image, clip_limit=-1.0)

    def test_clahe_invalid_tile_grid_size(self):
        """Test that invalid tile_grid_size raises ValueError"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        with pytest.raises(ValueError, match="tile_grid_size must be positive"):
            clahe(image, tile_grid_size=(0, 8))
        with pytest.raises(ValueError, match="tile_grid_size must be positive"):
            clahe(image, tile_grid_size=(8, 0))


class TestCLAHEOpenCVCompatibility:
    """OpenCV compatibility tests"""

    def test_clahe_opencv_compatibility_grayscale(self):
        """Test CLAHE compatibility with OpenCV (grayscale)"""
        pytest.importorskip("cv2")
        import cv2

        # Create test image with known pattern
        np.random.seed(42)
        image_np = np.random.uniform(0.3, 0.5, (256, 256)).astype(np.float32)
        image_cp = cp.asarray(image_np)

        # Apply CLAHE with pixtreme
        result_px = clahe(image_cp, clip_limit=40.0, tile_grid_size=(8, 8))

        # Apply CLAHE with OpenCV
        # OpenCV expects uint8, so convert
        image_uint8 = (image_np * 255).astype(np.uint8)
        clahe_cv = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(8, 8))
        result_cv_uint8 = clahe_cv.apply(image_uint8)
        result_cv = result_cv_uint8.astype(np.float32) / 255.0

        # Convert pixtreme result to numpy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Check correlation (should be > 0.95 for good compatibility)
        correlation = np.corrcoef(result_px_np.ravel(), result_cv.ravel())[0, 1]
        print(f"CLAHE correlation with OpenCV: {correlation:.6f}")
        assert correlation > 0.95, f"Correlation {correlation} too low"

        # Check mean absolute difference (should be small)
        mean_diff = np.mean(np.abs(result_px_np - result_cv))
        print(f"CLAHE mean difference: {mean_diff:.6f}")
        assert mean_diff < 0.05, f"Mean diff {mean_diff} too large"

    def test_clahe_opencv_compatibility_multichannel(self):
        """Test CLAHE with multichannel images (process each channel independently)"""
        pytest.importorskip("cv2")
        import cv2

        # Create RGB test image
        np.random.seed(42)
        image_np = np.random.uniform(0.3, 0.5, (256, 256, 3)).astype(np.float32)
        image_cp = cp.asarray(image_np)

        # Apply CLAHE with pixtreme (processes each channel independently)
        result_px = clahe(image_cp, clip_limit=40.0, tile_grid_size=(8, 8))

        # Apply CLAHE with OpenCV (channel-by-channel)
        image_uint8 = (image_np * 255).astype(np.uint8)
        clahe_cv = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(8, 8))
        result_cv = np.zeros_like(image_np)
        for c in range(3):
            result_cv_uint8 = clahe_cv.apply(image_uint8[:, :, c])
            result_cv[:, :, c] = result_cv_uint8.astype(np.float32) / 255.0

        # Convert pixtreme result to numpy for comparison
        result_px_np = cp.asnumpy(result_px)

        # Check correlation per channel
        for c in range(3):
            correlation = np.corrcoef(
                result_px_np[:, :, c].ravel(), result_cv[:, :, c].ravel()
            )[0, 1]
            print(f"CLAHE channel {c} correlation: {correlation:.6f}")
            assert correlation > 0.95, f"Channel {c} correlation {correlation} too low"


class TestCLAHEEdgeCases:
    """Edge case tests"""

    def test_clahe_uniform_image(self):
        """Test CLAHE with uniform image (all pixels same value)"""
        image = cp.full((256, 256, 3), 0.5, dtype=cp.float32)
        result = clahe(image)
        # Uniform image should remain nearly uniform (histogram clipping may cause slight changes)
        # Check that all pixels have similar values
        assert cp.std(result) < 0.1  # Low standard deviation
        assert cp.allclose(result, cp.mean(result), atol=0.1)  # All values close to mean

    def test_clahe_binary_image(self):
        """Test CLAHE with binary image (only 0 and 1 values)"""
        image = cp.random.choice([0.0, 1.0], size=(256, 256, 3)).astype(cp.float32)
        result = clahe(image)
        # Should execute without errors
        assert result.shape == image.shape

    def test_clahe_single_tile(self):
        """Test CLAHE with single tile (equivalent to global equalization)"""
        image = cp.random.uniform(0.3, 0.5, (256, 256, 3)).astype(cp.float32)
        result = clahe(image, tile_grid_size=(1, 1))
        # Single tile CLAHE should behave like global histogram equalization
        assert result.shape == image.shape
