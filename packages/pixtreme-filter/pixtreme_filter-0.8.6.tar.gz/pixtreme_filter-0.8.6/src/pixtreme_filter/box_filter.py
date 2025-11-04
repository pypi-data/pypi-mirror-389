"""Box filter implementation with normalize parameter (1-channel specialized)

This module provides box_filter() for 1-channel (grayscale) images,
complementing box_blur() which handles 3-channel (RGB) images.

Design:
- box_blur()  : 3-channel RGB images, always normalized (convenience)
- box_filter(): 1-channel grayscale, normalize parameter (advanced use)
"""

import cupy as cp

from ._kernel_utils import calculate_grid_config

# Border type constants (OpenCV-compatible)
BORDER_REPLICATE = 0
BORDER_REFLECT_101 = 4

# CUDA kernel for horizontal box filter (1-channel, multiple border types)
horizontal_box_filter_1ch_kernel_code = r"""
extern "C" __global__
void horizontal_box_filter_1ch_kernel(const float* input, float* output,
                                     int height, int width, int ksize, int normalize, int border_type) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        float sum = 0.0f;
        int radius = ksize / 2;

        for (int k = -radius; k <= radius; k++) {
            int px = x + k;

            // Border handling (OpenCV-compatible)
            if (border_type == 0) {  // BORDER_REPLICATE
                px = min(max(px, 0), width - 1);
            } else if (border_type == 4) {  // BORDER_REFLECT_101
                if (px < 0) {
                    px = -px;
                } else if (px >= width) {
                    px = 2 * width - px - 2;
                }
            }

            sum += input[y * width + px];
        }

        int out_idx = y * width + x;
        if (normalize) {
            output[out_idx] = sum / (float)ksize;
        } else {
            output[out_idx] = sum;
        }
    }
}
"""

horizontal_box_filter_1ch_kernel = cp.RawKernel(
    horizontal_box_filter_1ch_kernel_code, "horizontal_box_filter_1ch_kernel"
)

# CUDA kernel for vertical box filter (1-channel, multiple border types)
vertical_box_filter_1ch_kernel_code = r"""
extern "C" __global__
void vertical_box_filter_1ch_kernel(const float* input, float* output,
                                   int height, int width, int ksize, int normalize, int border_type) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        float sum = 0.0f;
        int radius = ksize / 2;

        for (int k = -radius; k <= radius; k++) {
            int py = y + k;

            // Border handling (OpenCV-compatible)
            if (border_type == 0) {  // BORDER_REPLICATE
                py = min(max(py, 0), height - 1);
            } else if (border_type == 4) {  // BORDER_REFLECT_101
                if (py < 0) {
                    py = -py;
                } else if (py >= height) {
                    py = 2 * height - py - 2;
                }
            }

            sum += input[py * width + x];
        }

        int out_idx = y * width + x;
        if (normalize) {
            output[out_idx] = sum / (float)ksize;
        } else {
            output[out_idx] = sum;
        }
    }
}
"""

vertical_box_filter_1ch_kernel = cp.RawKernel(
    vertical_box_filter_1ch_kernel_code, "vertical_box_filter_1ch_kernel"
)


def box_filter(
    image: cp.ndarray,
    ksize: int,
    normalize: bool = True,
    border_type: int = BORDER_REFLECT_101,
) -> cp.ndarray:
    """
    Apply box filter to a grayscale image.

    Box filter replaces each pixel with the sum (or average if normalized)
    of pixels in a kernel-sized neighborhood. This is a separable filter
    implemented as horizontal then vertical passes.

    This function is specialized for 1-channel (grayscale) images and is
    used for advanced image processing tasks like Harris Corner detection
    structure tensor computation.

    Equivalent to OpenCV cv::boxFilter() for 1-channel images.

    Parameters
    ----------
    image : cp.ndarray
        Input grayscale image (H, W), dtype must be float32.
        Value range [0, 1] for standard images.
    ksize : int
        Kernel size (must be odd integer, >= 1).
    normalize : bool, optional
        If True (default), divide by kernel area (average filter).
        If False, return unnormalized sum (useful for covariance matrices,
        integral images, Harris Corner structure tensors).
    border_type : int, optional
        Border handling method (default: BORDER_REFLECT_101, OpenCV default).
        - BORDER_REPLICATE (0): aaa|abcdefgh|hhh
        - BORDER_REFLECT_101 (4): dcb|abcdefgh|gfe (default, OpenCV compatible)

    Returns
    -------
    cp.ndarray
        Filtered grayscale image of shape (H, W), dtype float32.

    Raises
    ------
    ValueError
        If input dtype is not float32, or parameters are invalid.

    Notes
    -----
    **Algorithm**:

    Box filter is a separable filter:
    1. Horizontal pass: Sum/average along each row
    2. Vertical pass: Sum/average along each column

    **Border Handling**:

    Default is BORDER_REFLECT_101 (OpenCV default):
    - BORDER_REFLECT_101: dcb|abcdefgh|gfe (mirror reflection excluding boundary)
    - BORDER_REPLICATE: aaa|abcdefgh|hhh (clamp/replicate edge pixels)

    **Normalize Parameter**:

    - normalize=True: Output is average (equivalent to box_blur for 1-channel)
    - normalize=False: Output is unnormalized sum

    OpenCV documentation states that boxFilter(normalize=False) is
    "useful for computing various integral characteristics over each pixel
    neighborhood, such as covariance matrices of image derivatives"
    (used in Harris Corner detection).

    **Performance**:

    - Separable implementation: O(w*h*k) instead of O(w*h*k²)
    - GPU-accelerated CUDA kernels
    - Typical: <50ms for 1024x1024 image

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import box_filter
    >>> # Create test image
    >>> image = cp.random.rand(512, 512).astype(cp.float32)
    >>> # Normalized box filter (average)
    >>> blurred = box_filter(image, ksize=5, normalize=True)
    >>> # Unnormalized box filter (sum) for Harris Corner
    >>> Ixx = image * image  # Gradient product
    >>> Sxx = box_filter(Ixx, ksize=3, normalize=False)  # Structure tensor

    References
    ----------
    OpenCV boxFilter documentation:
    https://docs.opencv.org/master/d4/d86/group__imgproc__filter.html#gad533230ebf2d42509547d514f7d3fbc3
    """
    # Validate input
    if image.dtype != cp.float32:
        raise ValueError(f"Image must be float32, got {image.dtype}")

    if image.ndim != 2:
        raise ValueError(
            f"Image must be 2D (grayscale), got shape {image.shape}. "
            "Use box_blur() for 3-channel RGB images."
        )

    # Validate ksize
    if ksize < 1:
        raise ValueError(f"ksize must be at least 1, got {ksize}")
    if ksize % 2 == 0:
        raise ValueError(f"ksize must be odd, got {ksize}")

    height, width = image.shape

    # Allocate intermediate and output buffers
    temp = cp.empty((height, width), dtype=cp.float32)
    output = cp.empty((height, width), dtype=cp.float32)

    # Calculate CUDA grid and block configuration
    grid_size, block_size = calculate_grid_config(width, height)

    # Convert bool to int for CUDA kernel
    normalize_int = 1 if normalize else 0

    # Apply horizontal pass (flatten to 1D for CUDA kernel)
    horizontal_box_filter_1ch_kernel(
        grid_size,
        block_size,
        (image.reshape(-1), temp.reshape(-1), height, width, ksize, normalize_int, border_type),
    )

    # Apply vertical pass (flatten to 1D for CUDA kernel)
    vertical_box_filter_1ch_kernel(
        grid_size,
        block_size,
        (temp.reshape(-1), output.reshape(-1), height, width, ksize, normalize_int, border_type),
    )

    return output
