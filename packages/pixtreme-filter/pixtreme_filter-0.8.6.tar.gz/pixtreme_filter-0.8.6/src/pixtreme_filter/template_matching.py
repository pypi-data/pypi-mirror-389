"""Template matching for object detection and pattern search"""

import cupy as cp
from cupyx.scipy import signal

# Template matching method constants (OpenCV-compatible)
TM_SQDIFF = 0
TM_SQDIFF_NORMED = 1
TM_CCORR = 2
TM_CCORR_NORMED = 3
TM_CCOEFF = 4
TM_CCOEFF_NORMED = 5


def match_template(image: cp.ndarray, template: cp.ndarray, method: int) -> cp.ndarray:
    """
    Search for a template within an image using various matching methods.

    Template matching slides the template image over the input image and
    computes a similarity metric at each location, producing a response map.

    Parameters
    ----------
    image : cp.ndarray
        Input image (H, W) or (H, W, C), dtype must be float32.
        Value range [0, 1].
    template : cp.ndarray
        Template image to search for (h, w) or (h, w, C), dtype must be float32.
        Must have same number of dimensions as image.
        Must not be larger than image.
    method : int
        Matching method, one of:
        - TM_SQDIFF (0): Sum of squared differences (lower is better)
        - TM_SQDIFF_NORMED (1): Normalized SQDIFF, range [0, 1] (lower is better)
        - TM_CCORR (2): Cross-correlation (higher is better)
        - TM_CCORR_NORMED (3): Normalized CCORR, range [0, 1] (higher is better)
        - TM_CCOEFF (4): Correlation coefficient (higher is better)
        - TM_CCOEFF_NORMED (5): Normalized CCOEFF, range [-1, 1] (higher is better)

    Returns
    -------
    cp.ndarray
        Response map of shape (H - h + 1, W - w + 1), dtype float32.
        Each value represents the match quality at that location.

    Raises
    ------
    ValueError
        If input types are invalid, shapes incompatible, or template larger than image.

    Notes
    -----
    **Method Characteristics**:

    TM_SQDIFF:
        result = Σ(Image - Template)²
        Lower values indicate better matches. Minimum at best match location.

    TM_SQDIFF_NORMED:
        Normalized version of SQDIFF. Values in [0, 1].

    TM_CCORR:
        result = Σ(Image × Template)
        Higher values indicate better matches. Maximum at best match location.

    TM_CCORR_NORMED:
        Normalized version of CCORR. Values in [0, 1].

    TM_CCOEFF:
        result = Σ((Image - mean(Image)) × (Template - mean(Template)))
        Correlation coefficient. Higher values indicate better matches.

    TM_CCOEFF_NORMED:
        Normalized version of CCOEFF. Values in [-1, 1].
        Most robust to lighting changes.

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import match_template, TM_CCOEFF_NORMED
    >>> # Create image and template
    >>> image = cp.random.rand(200, 200, 3).astype(cp.float32)
    >>> template = image[50:70, 50:70]  # Extract template
    >>> # Find template in image
    >>> result = match_template(image, template, method=TM_CCOEFF_NORMED)
    >>> # Find best match location
    >>> min_val, max_val = float(cp.min(result)), float(cp.max(result))
    >>> min_loc = cp.unravel_index(cp.argmin(result), result.shape)
    >>> max_loc = cp.unravel_index(cp.argmax(result), result.shape)
    >>> print(f"Best match at: {max_loc}")
    """
    # Validate input
    if image.dtype != cp.float32 or template.dtype != cp.float32:
        raise ValueError(
            f"Image and template must be float32, got image={image.dtype}, template={template.dtype}"
        )

    if image.ndim != template.ndim:
        raise ValueError(
            f"Image and template must have the same number of dimensions, "
            f"got image.ndim={image.ndim}, template.ndim={template.ndim}"
        )

    # Check template size
    if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
        raise ValueError(
            f"Template must not be larger than image. "
            f"Image shape: {image.shape[:2]}, Template shape: {template.shape[:2]}"
        )

    # Validate method
    if method not in [TM_SQDIFF, TM_SQDIFF_NORMED, TM_CCORR, TM_CCORR_NORMED, TM_CCOEFF, TM_CCOEFF_NORMED]:
        raise ValueError(f"Unknown matching method: {method}")

    # Apply matching method
    if method == TM_SQDIFF:
        result = _match_template_sqdiff(image, template)
    elif method == TM_SQDIFF_NORMED:
        result = _match_template_sqdiff_normed(image, template)
    elif method == TM_CCORR:
        result = _match_template_ccorr(image, template)
    elif method == TM_CCORR_NORMED:
        result = _match_template_ccorr_normed(image, template)
    elif method == TM_CCOEFF:
        result = _match_template_ccoeff(image, template)
    elif method == TM_CCOEFF_NORMED:
        result = _match_template_ccoeff_normed(image, template)

    return result


def _cross_correlate_sum(image: cp.ndarray, template: cp.ndarray) -> cp.ndarray:
    """
    Compute sum of cross-correlation: Σ(I × T) for each window.

    For multi-channel images, sums across all channels.
    """
    if image.ndim == 2:
        # Grayscale: simple correlation
        return signal.correlate(image, template, mode="valid", method="fft")
    else:
        # Multi-channel: sum correlation across channels
        result = cp.zeros(
            (image.shape[0] - template.shape[0] + 1, image.shape[1] - template.shape[1] + 1),
            dtype=cp.float32,
        )
        for c in range(image.shape[2]):
            result += signal.correlate(image[:, :, c], template[:, :, c], mode="valid", method="fft")
        return result


def _sum_over_window(image: cp.ndarray, template_shape: tuple) -> cp.ndarray:
    """
    Compute sum of image values in each sliding window.

    For multi-channel images, sums across all channels.
    """
    if image.ndim == 2:
        # Grayscale
        ones = cp.ones(template_shape[:2], dtype=cp.float32)
        return signal.correlate(image, ones, mode="valid", method="fft")
    else:
        # Multi-channel: sum across all channels
        result = cp.zeros(
            (image.shape[0] - template_shape[0] + 1, image.shape[1] - template_shape[1] + 1),
            dtype=cp.float32,
        )
        ones = cp.ones(template_shape[:2], dtype=cp.float32)
        for c in range(image.shape[2]):
            result += signal.correlate(image[:, :, c], ones, mode="valid", method="fft")
        return result


def _sum_of_squares_over_window(image: cp.ndarray, template_shape: tuple) -> cp.ndarray:
    """
    Compute sum of squared image values in each sliding window.

    For multi-channel images, sums across all channels.
    """
    image_sq = image * image
    if image.ndim == 2:
        ones = cp.ones(template_shape[:2], dtype=cp.float32)
        return signal.correlate(image_sq, ones, mode="valid", method="fft")
    else:
        result = cp.zeros(
            (image.shape[0] - template_shape[0] + 1, image.shape[1] - template_shape[1] + 1),
            dtype=cp.float32,
        )
        ones = cp.ones(template_shape[:2], dtype=cp.float32)
        for c in range(image.shape[2]):
            result += signal.correlate(image_sq[:, :, c], ones, mode="valid", method="fft")
        return result


def _match_template_sqdiff(image: cp.ndarray, template: cp.ndarray) -> cp.ndarray:
    """
    TM_SQDIFF: Sum of Squared Differences
    result = Σ(I - T)² = Σ(I²) - 2×Σ(I×T) + Σ(T²)
    """
    sum_image_sq = _sum_of_squares_over_window(image, template.shape)
    cross_corr = _cross_correlate_sum(image, template)
    sum_template_sq = cp.sum(template * template)

    result = sum_image_sq - 2.0 * cross_corr + sum_template_sq
    result = cp.maximum(result, 0.0)  # Clamp negative values from numerical errors

    return result


def _match_template_sqdiff_normed(image: cp.ndarray, template: cp.ndarray) -> cp.ndarray:
    """
    TM_SQDIFF_NORMED: Normalized SQDIFF
    """
    sqdiff = _match_template_sqdiff(image, template)
    sum_image_sq = _sum_of_squares_over_window(image, template.shape)
    sum_template_sq = cp.sum(template * template)

    eps = 1e-8
    denom = cp.sqrt(sum_image_sq * sum_template_sq + eps)
    result = sqdiff / denom
    result = cp.clip(result, 0.0, 1.0)

    return result


def _match_template_ccorr(image: cp.ndarray, template: cp.ndarray) -> cp.ndarray:
    """
    TM_CCORR: Cross-Correlation
    result = Σ(I × T)
    """
    return _cross_correlate_sum(image, template)


def _match_template_ccorr_normed(image: cp.ndarray, template: cp.ndarray) -> cp.ndarray:
    """
    TM_CCORR_NORMED: Normalized Cross-Correlation
    """
    cross_corr = _cross_correlate_sum(image, template)
    sum_image_sq = _sum_of_squares_over_window(image, template.shape)
    sum_template_sq = cp.sum(template * template)

    eps = 1e-8
    denom = cp.sqrt(sum_image_sq * sum_template_sq + eps)
    result = cross_corr / denom
    result = cp.clip(result, 0.0, 1.0)

    return result


def _match_template_ccoeff(image: cp.ndarray, template: cp.ndarray) -> cp.ndarray:
    """
    TM_CCOEFF: Correlation Coefficient
    result = Σ((I - mean_I) × (T - mean_T))
           = Σ(I×T) - Σ(I)×mean_T - Σ(T)×mean_I + n×mean_I×mean_T
           = Σ(I×T) - n×mean_I×mean_T
    where mean_I = Σ(I)/n (per window), mean_T = Σ(T)/n
    """
    cross_corr = _cross_correlate_sum(image, template)
    sum_image = _sum_over_window(image, template.shape)
    sum_template = cp.sum(template)

    # Number of elements in template (including all channels)
    n = float(template.size)

    # mean_I = sum_image / n
    # mean_T = sum_template / n
    # result = cross_corr - n × (sum_image/n) × (sum_template/n)
    #        = cross_corr - (sum_image × sum_template) / n
    result = cross_corr - (sum_image * sum_template) / n

    return result


def _match_template_ccoeff_normed(image: cp.ndarray, template: cp.ndarray) -> cp.ndarray:
    """
    TM_CCOEFF_NORMED: Normalized Correlation Coefficient
    result = Σ((I - mean_I) × (T - mean_T)) / sqrt(Σ((I - mean_I)²) × Σ((T - mean_T)²))
    """
    ccoeff = _match_template_ccoeff(image, template)

    sum_image = _sum_over_window(image, template.shape)
    sum_image_sq = _sum_of_squares_over_window(image, template.shape)
    sum_template = cp.sum(template)
    sum_template_sq = cp.sum(template * template)

    n = float(template.size)

    # Variance of image windows: Σ((I - mean_I)²) = Σ(I²) - n×mean_I²
    #                                               = Σ(I²) - (Σ(I))²/n
    var_image = sum_image_sq - (sum_image * sum_image) / n
    var_image = cp.maximum(var_image, 0.0)  # Clamp negative values from numerical errors

    # Variance of template: Σ((T - mean_T)²) = Σ(T²) - n×mean_T²
    #                                         = Σ(T²) - (Σ(T))²/n
    var_template = sum_template_sq - (sum_template * sum_template) / n
    var_template = max(var_template, 0.0)  # Clamp negative values

    # Check for uniform template (zero variance)
    eps = 1e-7
    if var_template < eps:
        # Uniform template: result is 1.0 where image window is also uniform, 0 otherwise
        # OpenCV returns all zeros for uniform template
        return cp.zeros_like(ccoeff)

    denom = cp.sqrt(var_image * var_template + eps)
    result = ccoeff / denom
    result = cp.clip(result, -1.0, 1.0)

    return result
