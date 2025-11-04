"""Unsharp mask filter for image sharpening"""

import cupy as cp

from .gaussian import gaussian_blur


def unsharp_mask(
    image: cp.ndarray,
    sigma: float,
    amount: float,
    threshold: int = 0,
) -> cp.ndarray:
    """
    Apply unsharp mask filter to sharpen an image.

    Unsharp masking is a technique that sharpens an image by subtracting
    a blurred version from the original and adding the difference back
    with a scaling factor (amount).

    Algorithm:
    1. Blur the image using Gaussian blur
    2. Calculate the difference (detail layer): detail = image - blurred
    3. Add scaled detail back: sharpened = image + amount * detail

    This is equivalent to OpenCV's approach:
    cv2.addWeighted(image, 1 + amount, blurred, -amount, 0)

    Args:
        image: Input image as CuPy array (H, W, C) or (H, W).
               Requires float32 dtype.
        sigma: Standard deviation for Gaussian blur. Higher values blur
               more, affecting broader features. Typical range: 0.5-10.0.
        amount: Sharpening strength. Higher values create stronger sharpening.
                Typical range: 0.5-2.5. amount=0 returns unchanged image.
        threshold: (Not yet implemented) Minimum brightness change required
                   to apply sharpening. Default 0 (sharpen all pixels).

    Returns:
        Sharpened image with same shape, float32 dtype.

    Examples:
        >>> import cupy as cp
        >>> from pixtreme_filter import unsharp_mask
        >>> # Subtle sharpening
        >>> image = cp.random.rand(512, 512, 3).astype(cp.float32)
        >>> sharpened = unsharp_mask(image, sigma=1.0, amount=0.5)
        >>> # Strong sharpening
        >>> sharpened = unsharp_mask(image, sigma=2.0, amount=2.0)

    Notes:
        - OpenCV compatible (max error < 1e-5 vs cv2.GaussianBlur + cv2.addWeighted)
        - GPU-accelerated via existing gaussian_blur implementation
        - Output values may exceed [0, 1] range due to sharpening
          (values are NOT clipped by default)
    """
    if not isinstance(image, cp.ndarray):
        raise TypeError(f"Expected CuPy array, got {type(image)}")

    if image.ndim not in (2, 3):
        raise ValueError(f"Expected 2D or 3D array, got shape {image.shape}")

    if sigma <= 0:
        raise ValueError(f"sigma must be positive, got {sigma}")

    if threshold != 0:
        raise NotImplementedError("threshold parameter is not yet implemented. Use threshold=0.")

    # Validate dtype - unsharp_mask requires float32 input
    if image.dtype != cp.float32:
        raise ValueError(
            f"unsharp_mask requires float32 input, got {image.dtype}. "
            f"Use to_float32() to convert: from pixtreme_core.utils.dtypes import to_float32"
        )

    # Calculate kernel size from sigma (OpenCV-style: ksize = 0 means auto-calculate)
    # OpenCV uses: ksize = round(sigma * 4) * 2 + 1 (for float32 images)
    # Source: cv::getGaussianKernel() with ksize=0
    ksize = max(3, int(round(sigma * 4)) * 2 + 1)

    # Step 1: Blur the image
    blurred = gaussian_blur(image, ksize=ksize, sigma=sigma)

    # Step 2 & 3: Calculate detail and add back scaled
    # detail = image - blurred
    # sharpened = image + amount * detail
    # Simplified: sharpened = image + amount * (image - blurred)
    #           = image * (1 + amount) - blurred * amount
    #
    # This matches OpenCV's cv2.addWeighted(image, 1+amount, blurred, -amount, 0)
    sharpened = image + amount * (image - blurred)

    return sharpened
