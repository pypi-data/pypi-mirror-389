"""Harris Corner Detection for feature point detection"""

import cupy as cp

from .box_filter import BORDER_REFLECT_101, box_filter
from .sobel import sobel


def corner_harris(
    image: cp.ndarray, blockSize: int, ksize: int = 3, k: float = 0.04
) -> cp.ndarray:
    """
    Detect corners using Harris corner detection algorithm.

    The Harris corner detector computes a corner response function based on
    the structure tensor (gradient covariance matrix). Corners have large
    eigenvalues in multiple directions, while edges have one large eigenvalue.

    Parameters
    ----------
    image : cp.ndarray
        Input image (H, W) or (H, W, C), dtype must be float32.
        If color, will be converted to grayscale.
        Value range [0, 1].
    blockSize : int
        Size of neighborhood for structure tensor aggregation (must be odd, >= 3).
        Controls the scale of corner detection.
    ksize : int, optional
        Sobel kernel size for gradient computation (must be odd, >= 3), default 3.
        Larger values produce smoother gradients.
    k : float, optional
        Harris detector free parameter, typical range [0.04, 0.06], default 0.04.
        Smaller k makes detector more sensitive to corners vs edges.

    Returns
    -------
    cp.ndarray
        Corner response map of shape (H, W), dtype float32.
        Positive values indicate corners (higher = stronger corner).
        Local maxima above a threshold are corner candidates.

    Raises
    ------
    ValueError
        If input dtype is not float32, or parameters are invalid.

    Notes
    -----
    **Algorithm**:

    1. Convert to grayscale (if color)
    2. Compute gradients: Ix = Sobel(image, dx=1, dy=0)
                         Iy = Sobel(image, dx=0, dy=1)
    3. Compute structure tensor components:
       - Ixx = Ix²
       - Iyy = Iy²
       - Ixy = Ix × Iy
    4. Apply Gaussian smoothing (window of size blockSize):
       - Sxx = GaussianBlur(Ixx)
       - Syy = GaussianBlur(Iyy)
       - Sxy = GaussianBlur(Ixy)
    5. Compute Harris response:
       - det(M) = Sxx × Syy - Sxy²
       - trace(M) = Sxx + Syy
       - R = det(M) - k × trace(M)²

    **Corner Response Interpretation**:
    - R > 0: Corner (two large eigenvalues)
    - R < 0: Edge (one large eigenvalue)
    - R ≈ 0: Flat region (two small eigenvalues)

    **Parameters**:
    - blockSize: Larger values detect larger-scale corners, more smoothing
    - ksize: Larger Sobel kernels reduce noise in gradients
    - k: Typical values 0.04-0.06. Smaller k is more sensitive to corners.

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import corner_harris
    >>> # Create checkerboard pattern
    >>> image = cp.zeros((64, 64), dtype=cp.float32)
    >>> for i in range(8):
    ...     for j in range(8):
    ...         if (i + j) % 2 == 0:
    ...             image[i*8:(i+1)*8, j*8:(j+1)*8] = 1.0
    >>> # Detect corners
    >>> response = corner_harris(image, blockSize=3, ksize=3, k=0.04)
    >>> # Find corner locations (threshold and non-maximum suppression)
    >>> threshold = 0.01 * float(cp.max(response))
    >>> corners = cp.where(response > threshold)
    >>> print(f"Detected {len(corners[0])} corner candidates")

    References
    ----------
    Harris, C., & Stephens, M. (1988). A combined corner and edge detector.
    Alvey vision conference, 15(50), 10-5244.
    """
    # Validate input
    if image.dtype != cp.float32:
        raise ValueError(f"Image must be float32, got {image.dtype}")

    # Validate blockSize
    if blockSize < 3:
        raise ValueError(f"blockSize must be at least 3, got {blockSize}")
    if blockSize % 2 == 0:
        raise ValueError(f"blockSize must be odd, got {blockSize}")

    # Validate ksize
    if ksize < 3:
        raise ValueError(f"ksize must be at least 3, got {ksize}")
    if ksize % 2 == 0:
        raise ValueError(f"ksize must be odd, got {ksize}")

    # Convert to grayscale if color
    if image.ndim == 3:
        # Simple average (OpenCV uses weighted: 0.299*R + 0.587*G + 0.114*B)
        # But for Harris, simple average is acceptable
        gray = cp.mean(image, axis=2, dtype=cp.float32)
    else:
        gray = image

    # Step 1: Compute gradients using Sobel
    # Apply scale normalization for OpenCV compatibility
    # Reference: OpenCV corner.cpp - scale = 1/((1<<(aperture_size-1))*block_size)
    # This ensures corner response values are comparable across different parameter choices
    scale = 1.0 / ((1 << (ksize - 1)) * blockSize)

    # Note: sobel() always returns (H, W, 3) even for grayscale input
    # Use BORDER_REFLECT_101 to match OpenCV's default border handling
    Ix_3ch = sobel(gray, dx=1, dy=0, ksize=ksize, border_type=BORDER_REFLECT_101)
    Iy_3ch = sobel(gray, dx=0, dy=1, ksize=ksize, border_type=BORDER_REFLECT_101)

    # Extract first channel and apply scale normalization
    Ix = Ix_3ch[:, :, 0] * scale
    Iy = Iy_3ch[:, :, 0] * scale

    # Step 2: Compute structure tensor components
    Ixx = Ix * Ix
    Iyy = Iy * Iy
    Ixy = Ix * Iy

    # Step 3: Apply box filter smoothing to structure tensor
    # OpenCV uses boxFilter(normalize=false) for covariance matrix computation
    # Reference: OpenCV corner.cpp uses boxFilter with normalize=false
    # This computes unnormalized sums for structure tensor aggregation
    Sxx = box_filter(Ixx, ksize=blockSize, normalize=False)
    Syy = box_filter(Iyy, ksize=blockSize, normalize=False)
    Sxy = box_filter(Ixy, ksize=blockSize, normalize=False)

    # Step 4: Compute Harris response
    # R = det(M) - k * trace(M)^2
    # where M = [[Sxx, Sxy], [Sxy, Syy]]
    det_M = Sxx * Syy - Sxy * Sxy
    trace_M = Sxx + Syy
    R = det_M - k * (trace_M * trace_M)

    return R
