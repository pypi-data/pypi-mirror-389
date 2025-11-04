"""Difference of Gaussians (DoG) filter for blob detection and band-pass filtering"""

import cupy as cp

from pixtreme_filter.gaussian import gaussian_blur


def dog(
    image: cp.ndarray,
    sigma1: float,
    sigma2: float,
    ksize1: int | None = None,
    ksize2: int | None = None,
) -> cp.ndarray:
    """
    Apply Difference of Gaussians (DoG) filter.

    DoG is a band-pass filter that enhances features at a specific scale range.
    It is computed as the difference between two Gaussian blurs with different
    standard deviations:

        DoG = GaussianBlur(image, sigma1) - GaussianBlur(image, sigma2)

    DoG is commonly used for:
    - Blob detection (SIFT, SURF feature detection)
    - Edge enhancement
    - Scale-space analysis
    - Band-pass filtering

    Parameters
    ----------
    image : cp.ndarray
        Input image (H, W) or (H, W, C), dtype must be float32.
    sigma1 : float
        Standard deviation for the first Gaussian blur.
        Typically the smaller sigma (finer scale).
    sigma2 : float
        Standard deviation for the second Gaussian blur.
        Typically the larger sigma (coarser scale).
    ksize1 : int or None, optional
        Kernel size for the first Gaussian blur.
        If None, automatically calculated from sigma1.
    ksize2 : int or None, optional
        Kernel size for the second Gaussian blur.
        If None, automatically calculated from sigma2.

    Returns
    -------
    cp.ndarray
        DoG filtered image, same shape and dtype as input.
        Positive values indicate bright features on dark background.
        Negative values indicate dark features on bright background.

    Notes
    -----
    - The ratio sigma2/sigma1 determines the scale range:
      - Small ratio (1.2-1.6): Detects fine details
      - Medium ratio (2-3): General purpose blob detection
      - Large ratio (5+): Detects coarse features
    - Reversing sigma1 and sigma2 negates the result
    - Equal sigmas produce near-zero output

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import dog
    >>> image = cp.random.rand(512, 512, 3).astype(cp.float32)
    >>> # Detect medium-scale blobs
    >>> blobs = dog(image, sigma1=1.0, sigma2=3.0)
    >>> # Detect fine details
    >>> details = dog(image, sigma1=1.0, sigma2=1.6)
    """
    # Validate input
    if image.dtype != cp.float32:
        raise ValueError(
            f"Input image must be float32, got {image.dtype}. "
            "Convert using image.astype(cp.float32)"
        )

    if not (2 <= image.ndim <= 3):
        raise ValueError(
            f"Input image must be 2D (H, W) or 3D (H, W, C), got shape {image.shape}"
        )

    if sigma1 <= 0 or sigma2 <= 0:
        raise ValueError(
            f"sigma1 and sigma2 must be positive, got sigma1={sigma1}, sigma2={sigma2}"
        )

    # Handle grayscale images by adding channel dimension
    is_grayscale = image.ndim == 2
    if is_grayscale:
        image = cp.stack([image] * 3, axis=-1)

    # Calculate kernel sizes if not provided
    if ksize1 is None:
        ksize1 = round(sigma1 * 4) * 2 + 1
    if ksize2 is None:
        ksize2 = round(sigma2 * 4) * 2 + 1

    # Apply two Gaussian blurs
    blur1 = gaussian_blur(image, ksize=ksize1, sigma=sigma1)
    blur2 = gaussian_blur(image, ksize=ksize2, sigma=sigma2)

    # Compute difference
    result = blur1 - blur2

    # Remove channel dimension if input was grayscale
    if is_grayscale:
        result = result[:, :, 0]

    return result
