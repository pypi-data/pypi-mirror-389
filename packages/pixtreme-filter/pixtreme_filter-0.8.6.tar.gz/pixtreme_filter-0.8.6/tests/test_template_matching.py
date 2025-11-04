"""Test suite for template matching with OpenCV compatibility"""

import cupy as cp
import numpy as np
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_filter import (
    match_template,
    TM_SQDIFF,
    TM_SQDIFF_NORMED,
    TM_CCORR,
    TM_CCORR_NORMED,
    TM_CCOEFF,
    TM_CCOEFF_NORMED,
)


class TestTemplateMatching:
    """Test cases for match_template() function"""

    @pytest.fixture
    def sample_image(self):
        """Create test image with a pattern"""
        image = cp.random.uniform(0.3, 0.5, (200, 200, 3)).astype(cp.float32)
        # Add a bright square pattern
        image[50:70, 50:70] = 1.0
        return image

    @pytest.fixture
    def sample_template(self):
        """Create template to search for"""
        # Create a pattern with variation (not uniform) for CCOEFF testing
        template = cp.ones((20, 20, 3), dtype=cp.float32)
        # Add some variation to make it non-uniform
        template[5:15, 5:15] = 0.5
        return template

    @pytest.fixture
    def grayscale_image(self):
        """Create grayscale test image"""
        image = cp.random.uniform(0.3, 0.5, (200, 200)).astype(cp.float32)
        image[50:70, 50:70] = 1.0
        return image

    @pytest.fixture
    def grayscale_template(self):
        """Create grayscale template"""
        template = cp.ones((20, 20), dtype=cp.float32)
        # Add variation for CCOEFF testing
        template[5:15, 5:15] = 0.5
        return template

    # ========== Basic Tests ==========

    def test_match_template_basic(self, sample_image, sample_template):
        """Test basic template matching functionality"""
        result = match_template(sample_image, sample_template, method=TM_SQDIFF)

        # Output should be 2D array
        assert result.ndim == 2
        assert result.dtype == cp.float32

        # Output size should be (H - h + 1, W - w + 1)
        expected_h = sample_image.shape[0] - sample_template.shape[0] + 1
        expected_w = sample_image.shape[1] - sample_template.shape[1] + 1
        assert result.shape == (expected_h, expected_w)

    def test_match_template_grayscale(self, grayscale_image, grayscale_template):
        """Test template matching with grayscale images"""
        result = match_template(grayscale_image, grayscale_template, method=TM_SQDIFF)

        assert result.ndim == 2
        assert result.dtype == cp.float32

    def test_match_template_finds_pattern(self, sample_image, sample_template):
        """Test that template matching finds the correct pattern location"""
        result = match_template(sample_image, sample_template, method=TM_SQDIFF)

        # For TM_SQDIFF, minimum value indicates best match
        min_val = float(cp.min(result))
        min_loc = cp.unravel_index(cp.argmin(result), result.shape)
        min_y, min_x = int(min_loc[0]), int(min_loc[1])

        # Best match should be around (50, 50) where we placed the bright square
        assert abs(min_y - 50) < 5, f"Expected match near y=50, got y={min_y}"
        assert abs(min_x - 50) < 5, f"Expected match near x=50, got x={min_x}"
        # With patterned template, check that minimum is significantly lower than mean
        assert min_val < float(cp.mean(result)), f"Minimum SQDIFF should be lower than average"

    # ========== Method Tests ==========

    def test_match_template_sqdiff(self, sample_image, sample_template):
        """Test TM_SQDIFF method"""
        result = match_template(sample_image, sample_template, method=TM_SQDIFF)

        # SQDIFF: lower is better, minimum at best match
        assert cp.min(result) >= 0.0, "SQDIFF should be non-negative"

    def test_match_template_sqdiff_normed(self, sample_image, sample_template):
        """Test TM_SQDIFF_NORMED method"""
        result = match_template(sample_image, sample_template, method=TM_SQDIFF_NORMED)

        # Normalized SQDIFF: values in [0, 1], lower is better
        assert cp.min(result) >= 0.0, "SQDIFF_NORMED minimum should be >= 0"
        assert cp.max(result) <= 1.0, "SQDIFF_NORMED maximum should be <= 1"

    def test_match_template_ccorr(self, sample_image, sample_template):
        """Test TM_CCORR method"""
        result = match_template(sample_image, sample_template, method=TM_CCORR)

        # CCORR: higher is better, maximum at best match
        assert result.shape[0] > 0 and result.shape[1] > 0

    def test_match_template_ccorr_normed(self, sample_image, sample_template):
        """Test TM_CCORR_NORMED method"""
        result = match_template(sample_image, sample_template, method=TM_CCORR_NORMED)

        # Normalized CCORR: values in [0, 1], higher is better
        assert cp.min(result) >= 0.0, "CCORR_NORMED minimum should be >= 0"
        assert cp.max(result) <= 1.0, "CCORR_NORMED maximum should be <= 1"

    def test_match_template_ccoeff(self, sample_image, sample_template):
        """Test TM_CCOEFF method"""
        result = match_template(sample_image, sample_template, method=TM_CCOEFF)

        # CCOEFF: can be negative, higher is better
        assert result.shape[0] > 0 and result.shape[1] > 0

    def test_match_template_ccoeff_normed(self, sample_image, sample_template):
        """Test TM_CCOEFF_NORMED method"""
        result = match_template(sample_image, sample_template, method=TM_CCOEFF_NORMED)

        # Normalized CCOEFF: values in [-1, 1], higher is better
        assert cp.min(result) >= -1.0, "CCOEFF_NORMED minimum should be >= -1"
        assert cp.max(result) <= 1.0, "CCOEFF_NORMED maximum should be <= 1"

    # ========== Edge Case Tests ==========

    def test_match_template_template_larger_than_image(self):
        """Test error when template is larger than image"""
        image = cp.ones((10, 10, 3), dtype=cp.float32)
        template = cp.ones((20, 20, 3), dtype=cp.float32)

        with pytest.raises(ValueError, match="Template must not be larger than image"):
            match_template(image, template, method=TM_SQDIFF)

    def test_match_template_template_same_size_as_image(self):
        """Test when template is same size as image"""
        image = cp.ones((20, 20, 3), dtype=cp.float32) * 0.5
        template = cp.ones((20, 20, 3), dtype=cp.float32) * 0.5

        result = match_template(image, template, method=TM_SQDIFF)

        # Result should be 1x1
        assert result.shape == (1, 1)

    def test_match_template_small_template(self):
        """Test with very small template"""
        image = cp.random.rand(100, 100, 3).astype(cp.float32)
        template = cp.ones((3, 3, 3), dtype=cp.float32) * 0.5

        result = match_template(image, template, method=TM_SQDIFF)

        assert result.shape == (98, 98)

    def test_match_template_invalid_dtype(self):
        """Test error with invalid dtype"""
        image = cp.ones((100, 100, 3), dtype=cp.uint8)
        template = cp.ones((20, 20, 3), dtype=cp.uint8)

        with pytest.raises(ValueError, match="must be float32"):
            match_template(image, template, method=TM_SQDIFF)

    def test_match_template_shape_mismatch(self):
        """Test error when image and template have different channels"""
        image = cp.ones((100, 100, 3), dtype=cp.float32)
        template = cp.ones((20, 20), dtype=cp.float32)

        with pytest.raises(ValueError, match="must have the same number of dimensions"):
            match_template(image, template, method=TM_SQDIFF)

    # ========== OpenCV Compatibility Tests ==========

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_template_opencv_sqdiff(self, sample_image, sample_template):
        """Test TM_SQDIFF matches OpenCV"""
        image_np = cp.asnumpy(sample_image)
        template_np = cp.asnumpy(sample_template)

        # OpenCV result
        result_cv = cv2.matchTemplate(image_np, template_np, cv2.TM_SQDIFF)

        # Pixtreme result
        result_px = match_template(sample_image, sample_template, method=TM_SQDIFF)
        result_px_np = cp.asnumpy(result_px)

        # Compare (FFT-based correlation has acceptable numerical error)
        max_diff = np.abs(result_cv - result_px_np).max()
        assert max_diff < 1e-3, f"TM_SQDIFF should match OpenCV (max_diff={max_diff:.6f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_template_opencv_sqdiff_normed(self, sample_image, sample_template):
        """Test TM_SQDIFF_NORMED matches OpenCV"""
        image_np = cp.asnumpy(sample_image)
        template_np = cp.asnumpy(sample_template)

        result_cv = cv2.matchTemplate(image_np, template_np, cv2.TM_SQDIFF_NORMED)
        result_px = match_template(sample_image, sample_template, method=TM_SQDIFF_NORMED)
        result_px_np = cp.asnumpy(result_px)

        max_diff = np.abs(result_cv - result_px_np).max()
        assert max_diff < 1e-5, f"TM_SQDIFF_NORMED should match OpenCV (max_diff={max_diff:.6f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_template_opencv_ccorr(self, sample_image, sample_template):
        """Test TM_CCORR matches OpenCV"""
        image_np = cp.asnumpy(sample_image)
        template_np = cp.asnumpy(sample_template)

        result_cv = cv2.matchTemplate(image_np, template_np, cv2.TM_CCORR)
        result_px = match_template(sample_image, sample_template, method=TM_CCORR)
        result_px_np = cp.asnumpy(result_px)

        max_diff = np.abs(result_cv - result_px_np).max()
        assert max_diff < 1e-3, f"TM_CCORR should match OpenCV (max_diff={max_diff:.6f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_template_opencv_ccorr_normed(self, sample_image, sample_template):
        """Test TM_CCORR_NORMED matches OpenCV"""
        image_np = cp.asnumpy(sample_image)
        template_np = cp.asnumpy(sample_template)

        result_cv = cv2.matchTemplate(image_np, template_np, cv2.TM_CCORR_NORMED)
        result_px = match_template(sample_image, sample_template, method=TM_CCORR_NORMED)
        result_px_np = cp.asnumpy(result_px)

        max_diff = np.abs(result_cv - result_px_np).max()
        assert max_diff < 1e-5, f"TM_CCORR_NORMED should match OpenCV (max_diff={max_diff:.6f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_template_opencv_ccoeff(self, sample_image, sample_template):
        """Test TM_CCOEFF matches OpenCV"""
        image_np = cp.asnumpy(sample_image)
        template_np = cp.asnumpy(sample_template)

        result_cv = cv2.matchTemplate(image_np, template_np, cv2.TM_CCOEFF)
        result_px = match_template(sample_image, sample_template, method=TM_CCOEFF)
        result_px_np = cp.asnumpy(result_px)

        max_diff = np.abs(result_cv - result_px_np).max()
        assert max_diff < 1e-3, f"TM_CCOEFF should match OpenCV (max_diff={max_diff:.6f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_template_opencv_ccoeff_normed(self, sample_image, sample_template):
        """Test TM_CCOEFF_NORMED matches OpenCV"""
        image_np = cp.asnumpy(sample_image)
        template_np = cp.asnumpy(sample_template)

        result_cv = cv2.matchTemplate(image_np, template_np, cv2.TM_CCOEFF_NORMED)
        result_px = match_template(sample_image, sample_template, method=TM_CCOEFF_NORMED)
        result_px_np = cp.asnumpy(result_px)

        max_diff = np.abs(result_cv - result_px_np).max()
        assert max_diff < 1e-3, f"TM_CCOEFF_NORMED should match OpenCV (max_diff={max_diff:.6f})"

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not available")
    def test_match_template_opencv_grayscale(self, grayscale_image, grayscale_template):
        """Test grayscale template matching matches OpenCV"""
        image_np = cp.asnumpy(grayscale_image)
        template_np = cp.asnumpy(grayscale_template)

        result_cv = cv2.matchTemplate(image_np, template_np, cv2.TM_CCOEFF_NORMED)
        result_px = match_template(grayscale_image, grayscale_template, method=TM_CCOEFF_NORMED)
        result_px_np = cp.asnumpy(result_px)

        max_diff = np.abs(result_cv - result_px_np).max()
        assert max_diff < 1e-3, f"Grayscale matching should match OpenCV (max_diff={max_diff:.6f})"

    # ========== Performance Tests ==========

    def test_match_template_performance(self):
        """Test template matching performance"""
        import time

        large_image = cp.random.rand(1024, 1024, 3).astype(cp.float32)
        template = cp.random.rand(64, 64, 3).astype(cp.float32)

        start = time.perf_counter()
        result = match_template(large_image, template, method=TM_CCOEFF_NORMED)
        cp.cuda.Stream.null.synchronize()
        elapsed = time.perf_counter() - start

        assert result.shape == (1024 - 64 + 1, 1024 - 64 + 1)
        assert elapsed < 1.0, f"Template matching should process 1024x1024 in <1s (took {elapsed*1000:.1f}ms)"

    # ========== Integration Tests ==========

    def test_match_template_multi_object_detection(self):
        """Test finding multiple instances of template"""
        # Create image with multiple instances of pattern
        image = cp.zeros((200, 200, 3), dtype=cp.float32)
        # Create patterns with variation (bright border, darker center)
        for y, x in [(20, 20), (100, 100), (150, 50)]:
            image[y:y+20, x:x+20] = 1.0
            image[y+5:y+15, x+5:x+15] = 0.5

        # Create template matching the pattern
        template = cp.ones((20, 20, 3), dtype=cp.float32)
        template[5:15, 5:15] = 0.5

        result = match_template(image, template, method=TM_CCOEFF_NORMED)

        # Find peaks (high correlation)
        threshold = 0.9
        peaks = result > threshold
        num_peaks = int(cp.sum(peaks))

        # Should find approximately 3 matches (allowing for overlaps)
        assert num_peaks >= 3, f"Should find at least 3 matches, found {num_peaks}"

    def test_match_template_with_canny_edges(self):
        """Test template matching on edge images (common use case)"""
        from pixtreme_filter import canny

        # Create simple image with edges
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[30:70, 30:70] = 1.0  # Square

        # Extract edges
        edges = canny(image, threshold1=0.1, threshold2=0.3)
        edges_3ch = cp.stack([edges] * 3, axis=-1)  # Convert to 3-channel

        # Create template from edges of smaller square
        template = cp.zeros((20, 20, 3), dtype=cp.float32)
        template[5:15, 5:15] = 1.0
        template_edges = canny(template, threshold1=0.1, threshold2=0.3)
        template_edges_3ch = cp.stack([template_edges] * 3, axis=-1)

        # Match templates on edge images using CCORR (more stable for binary images)
        result = match_template(edges_3ch, template_edges_3ch, method=TM_CCORR)

        assert result.shape == (81, 81)
        # For binary edge images, just check that matching produces valid results
        assert not cp.any(cp.isnan(result)), "Result should not contain NaN"
        assert cp.max(result) > 0, "Should find some edge correlation"
