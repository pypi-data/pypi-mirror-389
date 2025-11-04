"""Canny edge detection with GPU acceleration using CuPy"""

import cupy as cp

from pixtreme_filter.gaussian import gaussian_blur
from pixtreme_filter.sobel import sobel


# CUDA kernel for non-maximum suppression
nms_kernel = cp.RawKernel(
    r"""
extern "C" __global__
void nms_kernel(
    const float* magnitude,
    const float* angle,
    float* output,
    int height,
    int width
) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;

    if (x >= width || y >= height) return;

    // Skip borders
    if (x == 0 || x == width - 1 || y == 0 || y == height - 1) {
        output[y * width + x] = 0.0f;
        return;
    }

    int idx = y * width + x;
    float current_mag = magnitude[idx];
    float current_angle = angle[idx];

    // Convert angle to degrees and normalize to [0, 180)
    float angle_deg = current_angle * 180.0f / 3.14159265359f;
    while (angle_deg < 0.0f) angle_deg += 180.0f;
    while (angle_deg >= 180.0f) angle_deg -= 180.0f;

    // Quantize to 4 directions
    int direction;
    if ((angle_deg >= 0.0f && angle_deg < 22.5f) || (angle_deg >= 157.5f && angle_deg < 180.0f)) {
        direction = 0;  // Horizontal
    } else if (angle_deg >= 22.5f && angle_deg < 67.5f) {
        direction = 1;  // Diagonal /
    } else if (angle_deg >= 67.5f && angle_deg < 112.5f) {
        direction = 2;  // Vertical
    } else {
        direction = 3;  // Diagonal backslash
    }

    // Get neighbors along gradient direction
    float neighbor1, neighbor2;
    if (direction == 0) {  // Horizontal
        neighbor1 = magnitude[y * width + (x - 1)];
        neighbor2 = magnitude[y * width + (x + 1)];
    } else if (direction == 1) {  // Diagonal /
        neighbor1 = magnitude[(y - 1) * width + (x + 1)];
        neighbor2 = magnitude[(y + 1) * width + (x - 1)];
    } else if (direction == 2) {  // Vertical
        neighbor1 = magnitude[(y - 1) * width + x];
        neighbor2 = magnitude[(y + 1) * width + x];
    } else {  // Diagonal backslash
        neighbor1 = magnitude[(y - 1) * width + (x - 1)];
        neighbor2 = magnitude[(y + 1) * width + (x + 1)];
    }

    // Keep only if local maximum
    if (current_mag >= neighbor1 && current_mag >= neighbor2) {
        output[idx] = current_mag;
    } else {
        output[idx] = 0.0f;
    }
}
""",
    "nms_kernel",
)


def canny(
    image: cp.ndarray,
    threshold1: float,
    threshold2: float,
    aperture_size: int = 3,
    l2_gradient: bool = False,
) -> cp.ndarray:
    """
    Apply Canny edge detection algorithm.

    The Canny edge detector is a multi-stage algorithm:
    1. Gaussian blur for noise reduction
    2. Gradient calculation (magnitude and direction)
    3. Non-maximum suppression (edge thinning)
    4. Double threshold to classify edges
    5. Edge tracking by hysteresis

    Parameters
    ----------
    image : cp.ndarray
        Input image (H, W) or (H, W, C), dtype must be float32.
        If color image, converted to grayscale internally.
    threshold1 : float
        Lower threshold for hysteresis (weak edges).
    threshold2 : float
        Upper threshold for hysteresis (strong edges).
    aperture_size : int, optional
        Aperture size for Sobel operator (3, 5, or 7), default 3.
    l2_gradient : bool, optional
        If True, use L2 norm sqrt(dx^2 + dy^2) for gradient magnitude.
        If False, use L1 norm |dx| + |dy|. Default False.

    Returns
    -------
    cp.ndarray
        Binary edge map (H, W), dtype float32, values in [0, 1].
        1.0 indicates edge pixel, 0.0 indicates non-edge.

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import canny
    >>> image = cp.random.rand(512, 512, 3).astype(cp.float32)
    >>> edges = canny(image, threshold1=0.1, threshold2=0.3)
    >>> edges.shape
    (512, 512)
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

    if aperture_size not in (3, 5, 7):
        raise ValueError(
            f"aperture_size must be 3, 5, or 7, got {aperture_size}"
        )

    # Ensure threshold1 <= threshold2
    if threshold1 > threshold2:
        threshold1, threshold2 = threshold2, threshold1

    # Convert to grayscale if color image
    if image.ndim == 3:
        # Convert BGR to grayscale (OpenCV weights)
        gray = (
            0.114 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.299 * image[:, :, 2]
        )
    else:
        gray = image

    # Step 1: Compute gradients using Sobel
    # OpenCV's Canny doesn't use separate Gaussian blur - Sobel kernel includes smoothing
    # Add channel dimension for sobel
    gray_3ch = cp.stack([gray] * 3, axis=-1)

    dx = sobel(gray_3ch, dx=1, dy=0, ksize=aperture_size)[:, :, 0]
    dy = sobel(gray_3ch, dx=0, dy=1, ksize=aperture_size)[:, :, 0]

    # Compute gradient magnitude
    if l2_gradient:
        magnitude = cp.sqrt(dx**2 + dy**2)
    else:
        magnitude = cp.abs(dx) + cp.abs(dy)

    # Compute gradient direction (in radians)
    angle = cp.arctan2(dy, dx)

    # Step 2: Non-maximum suppression
    suppressed = _non_maximum_suppression(magnitude, angle)

    # Step 3 & 4: Double threshold and edge tracking by hysteresis
    edges = _hysteresis_threshold(suppressed, threshold1, threshold2)

    return edges


def _non_maximum_suppression(magnitude: cp.ndarray, angle: cp.ndarray) -> cp.ndarray:
    """
    Apply non-maximum suppression to thin edges using CUDA kernel.

    For each pixel, check if it's a local maximum in the gradient direction.
    If not, suppress it (set to 0).

    Parameters
    ----------
    magnitude : cp.ndarray
        Gradient magnitude (H, W), dtype float32.
    angle : cp.ndarray
        Gradient direction in radians (H, W), dtype float32.

    Returns
    -------
    cp.ndarray
        Suppressed gradient magnitude (H, W), dtype float32.
    """
    H, W = magnitude.shape
    suppressed = cp.zeros_like(magnitude)

    # Configure CUDA kernel
    block_size = (16, 16)
    grid_size = ((W + block_size[0] - 1) // block_size[0], (H + block_size[1] - 1) // block_size[1])

    # Launch kernel
    nms_kernel(
        grid_size,
        block_size,
        (magnitude, angle, suppressed, H, W),
    )

    return suppressed


def _hysteresis_threshold(
    magnitude: cp.ndarray, threshold1: float, threshold2: float
) -> cp.ndarray:
    """
    Apply double threshold and edge tracking by hysteresis using iterative dilation.

    Strong edges (magnitude >= threshold2) are kept.
    Weak edges (threshold1 <= magnitude < threshold2) are kept only if connected to strong edges.
    All other pixels are suppressed.

    This implementation uses iterative morphological dilation to propagate strong edges
    to connected weak edges, which is more GPU-friendly than BFS.

    Parameters
    ----------
    magnitude : cp.ndarray
        Gradient magnitude after NMS (H, W), dtype float32.
    threshold1 : float
        Lower threshold (weak edges).
    threshold2 : float
        Upper threshold (strong edges).

    Returns
    -------
    cp.ndarray
        Binary edge map (H, W), dtype float32, values in [0, 1].
    """
    # Classify pixels
    strong = magnitude >= threshold2
    weak = (magnitude >= threshold1) & (magnitude < threshold2)

    # Initialize output with strong edges
    edges = strong.astype(cp.float32)

    # Iteratively propagate strong edges to connected weak edges
    # Use binary dilation to expand the strong edge region
    prev_edges = cp.copy(edges)

    # Maximum iterations to prevent infinite loop
    max_iterations = 100

    for _ in range(max_iterations):
        # Dilate edges by 1 pixel (8-connected)
        # This expands the edge region to include neighboring pixels
        dilated = _binary_dilate_8connected(edges)

        # Only keep weak edges that are now connected to strong edges
        edges = dilated & (strong | weak)

        # Check convergence
        if cp.array_equal(edges, prev_edges):
            break

        prev_edges = cp.copy(edges)

    return edges.astype(cp.float32)


def _binary_dilate_8connected(binary_image: cp.ndarray) -> cp.ndarray:
    """
    Perform binary dilation with 8-connected structuring element.

    Parameters
    ----------
    binary_image : cp.ndarray
        Binary image (H, W), dtype float32 or bool.

    Returns
    -------
    cp.ndarray
        Dilated binary image (H, W), dtype bool.
    """
    H, W = binary_image.shape
    binary = binary_image.astype(cp.bool_)

    # Pad image to handle borders
    padded = cp.pad(binary, pad_width=1, mode='constant', constant_values=False)

    # Dilate using 8-connected neighbors (3x3 structuring element)
    dilated = cp.zeros_like(binary)

    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dy == 0 and dx == 0:
                continue
            # Shift and OR
            shifted = padded[1 + dy : H + 1 + dy, 1 + dx : W + 1 + dx]
            dilated |= shifted

    # Include original edges
    dilated |= binary

    return dilated
