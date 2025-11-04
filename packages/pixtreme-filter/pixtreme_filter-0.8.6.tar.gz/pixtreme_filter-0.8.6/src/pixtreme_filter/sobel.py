"""Sobel edge detection filter with OpenCV-compatible implementation"""

import cupy as cp

from ._kernel_utils import (
    allocate_filter_buffers,
    calculate_grid_config,
    prepare_image_for_filter,
)
from .box_filter import BORDER_REFLECT_101, BORDER_REPLICATE


def get_sobel_kernels(dx: int, dy: int, ksize: int) -> tuple[cp.ndarray, cp.ndarray]:
    """Get separable Sobel filter kernels.

    Sobel filters are separable into smoothing and derivative kernels.
    For example, 3x3 Sobel-X = [1, 2, 1]^T * [-1, 0, 1]

    Args:
        dx: Order of derivative in x-direction (0 or 1)
        dy: Order of derivative in y-direction (0 or 1)
        ksize: Kernel size (3, 5, or 7)

    Returns:
        Tuple of (kernel1, kernel2) for separable convolution
        - kernel1: Applied in horizontal pass
        - kernel2: Applied in vertical pass
    """
    # Smoothing kernels (binomial coefficients)
    if ksize == 3:
        smooth = cp.array([1, 2, 1], dtype=cp.float32)
        deriv = cp.array([-1, 0, 1], dtype=cp.float32)
    elif ksize == 5:
        smooth = cp.array([1, 4, 6, 4, 1], dtype=cp.float32)
        deriv = cp.array([-1, -2, 0, 2, 1], dtype=cp.float32)
    elif ksize == 7:
        smooth = cp.array([1, 6, 15, 20, 15, 6, 1], dtype=cp.float32)
        deriv = cp.array([-1, -3, -5, 0, 5, 3, 1], dtype=cp.float32)
    else:
        raise ValueError(f"Invalid kernel size: {ksize}. Must be 3, 5, or 7")

    # Determine which kernel is applied in each direction
    if dx == 1 and dy == 0:
        # Sobel-X: horizontal derivative, vertical smoothing
        kernel1 = deriv  # Horizontal pass: derivative
        kernel2 = smooth  # Vertical pass: smoothing
    elif dx == 0 and dy == 1:
        # Sobel-Y: vertical derivative, horizontal smoothing
        kernel1 = smooth  # Horizontal pass: smoothing
        kernel2 = deriv  # Vertical pass: derivative
    else:
        raise ValueError(f"Invalid dx/dy combination: dx={dx}, dy={dy}. Must be (1,0) or (0,1)")

    return kernel1, kernel2


# CUDA kernel for horizontal separable convolution
horizontal_sobel_kernel_code = r"""
extern "C" __global__
void horizontal_sobel_kernel(const float* input, float* output,
                            const float* kernel, int height, int width, int ksize, int border_type) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        float sum_r = 0.0f;
        float sum_g = 0.0f;
        float sum_b = 0.0f;
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

            int idx = (y * width + px) * 3;
            float weight = kernel[k + radius];
            sum_r += input[idx] * weight;
            sum_g += input[idx + 1] * weight;
            sum_b += input[idx + 2] * weight;
        }

        int out_idx = (y * width + x) * 3;
        output[out_idx] = sum_r;
        output[out_idx + 1] = sum_g;
        output[out_idx + 2] = sum_b;
    }
}
"""

horizontal_sobel_kernel = cp.RawKernel(horizontal_sobel_kernel_code, "horizontal_sobel_kernel")

# CUDA kernel for vertical separable convolution
vertical_sobel_kernel_code = r"""
extern "C" __global__
void vertical_sobel_kernel(const float* input, float* output,
                          const float* kernel, int height, int width, int ksize, int border_type) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        float sum_r = 0.0f;
        float sum_g = 0.0f;
        float sum_b = 0.0f;
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

            int idx = (py * width + x) * 3;
            float weight = kernel[k + radius];
            sum_r += input[idx] * weight;
            sum_g += input[idx + 1] * weight;
            sum_b += input[idx + 2] * weight;
        }

        int out_idx = (y * width + x) * 3;
        output[out_idx] = sum_r;
        output[out_idx + 1] = sum_g;
        output[out_idx + 2] = sum_b;
    }
}
"""

vertical_sobel_kernel = cp.RawKernel(vertical_sobel_kernel_code, "vertical_sobel_kernel")


def sobel(
    image: cp.ndarray,
    dx: int,
    dy: int,
    ksize: int = 3,
    border_type: int = BORDER_REFLECT_101,
) -> cp.ndarray:
    """
    Apply Sobel edge detection filter to an image.

    Sobel is a discrete differentiation operator that computes an approximation
    of the gradient of the image intensity. It's commonly used for edge detection.

    Parameters
    ----------
    image : cp.ndarray
        Input image (HxWx3 or HxW, float32 [0-1] or uint8)
    dx : int
        Order of derivative in x-direction (0 or 1)
    dy : int
        Order of derivative in y-direction (0 or 1)
    ksize : int, optional
        Kernel size (3, 5, or 7), default 3
    border_type : int, optional
        Border handling method (default: BORDER_REFLECT_101, OpenCV default).
        - BORDER_REPLICATE (0): aaa|abcdefgh|hhh
        - BORDER_REFLECT_101 (4): dcb|abcdefgh|gfe (default, OpenCV compatible)

    Returns
    -------
    cp.ndarray
        Gradient image (HxWx3, float32)
        Note: Output can contain negative values (gradients)

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import sobel
    >>> image = cp.random.rand(100, 100, 3).astype(cp.float32)
    >>> # Detect vertical edges (horizontal gradient)
    >>> sobel_x = sobel(image, dx=1, dy=0, ksize=3)
    >>> # Detect horizontal edges (vertical gradient)
    >>> sobel_y = sobel(image, dx=0, dy=1, ksize=3)
    >>> # Compute gradient magnitude
    >>> magnitude = cp.sqrt(sobel_x**2 + sobel_y**2)
    """
    # Validate parameters
    if dx not in (0, 1) or dy not in (0, 1):
        raise ValueError(f"dx and dy must be 0 or 1, got dx={dx}, dy={dy}")
    if dx == dy:
        raise ValueError("dx and dy cannot both be 0 or both be 1")
    if ksize not in (3, 5, 7):
        raise ValueError(f"ksize must be 3, 5, or 7, got {ksize}")

    # Prepare image (dtype conversion, 2D->3D, contiguous layout)
    image = prepare_image_for_filter(image)
    height, width = image.shape[:2]

    # Get Sobel kernels
    kernel1, kernel2 = get_sobel_kernels(dx, dy, ksize)

    # Allocate temporary and output buffers
    temp, output = allocate_filter_buffers(image.shape)

    # Calculate CUDA grid and block configuration
    grid_size, block_size = calculate_grid_config(width, height)

    # Horizontal pass
    horizontal_sobel_kernel(
        grid_size,
        block_size,
        (
            image.reshape(-1),
            temp.reshape(-1),
            kernel1,
            height,
            width,
            ksize,
            border_type,
        ),
    )

    # Vertical pass
    vertical_sobel_kernel(
        grid_size,
        block_size,
        (
            temp.reshape(-1),
            output.reshape(-1),
            kernel2,
            height,
            width,
            ksize,
            border_type,
        ),
    )

    return output
