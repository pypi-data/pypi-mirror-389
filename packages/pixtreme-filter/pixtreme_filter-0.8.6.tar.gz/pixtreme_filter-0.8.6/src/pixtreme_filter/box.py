"""Box blur filter implementation with OpenCV-compatible border handling"""

import cupy as cp

from ._kernel_utils import (
    allocate_filter_buffers,
    calculate_grid_config,
    prepare_image_for_filter,
)

# CUDA kernel for horizontal box blur (OpenCV BORDER_REPLICATE compatible)
horizontal_box_kernel_code = r"""
extern "C" __global__
void horizontal_box_kernel(const float* input, float* output,
                          int height, int width, int ksize) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        float sum_r = 0.0f;
        float sum_g = 0.0f;
        float sum_b = 0.0f;
        int radius = ksize / 2;

        for (int k = -radius; k <= radius; k++) {
            // Replicate border (clamp coordinates)
            int px = min(max(x + k, 0), width - 1);
            int idx = (y * width + px) * 3;
            sum_r += input[idx];
            sum_g += input[idx + 1];
            sum_b += input[idx + 2];
        }

        int out_idx = (y * width + x) * 3;
        float kernel_size = (float)ksize;
        output[out_idx] = sum_r / kernel_size;
        output[out_idx + 1] = sum_g / kernel_size;
        output[out_idx + 2] = sum_b / kernel_size;
    }
}
"""

horizontal_box_kernel = cp.RawKernel(horizontal_box_kernel_code, "horizontal_box_kernel")

# CUDA kernel for vertical box blur
vertical_box_kernel_code = r"""
extern "C" __global__
void vertical_box_kernel(const float* input, float* output,
                        int height, int width, int ksize) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        float sum_r = 0.0f;
        float sum_g = 0.0f;
        float sum_b = 0.0f;
        int radius = ksize / 2;

        for (int k = -radius; k <= radius; k++) {
            // Replicate border (clamp coordinates)
            int py = min(max(y + k, 0), height - 1);
            int idx = (py * width + x) * 3;
            sum_r += input[idx];
            sum_g += input[idx + 1];
            sum_b += input[idx + 2];
        }

        int out_idx = (y * width + x) * 3;
        float kernel_size = (float)ksize;
        output[out_idx] = sum_r / kernel_size;
        output[out_idx + 1] = sum_g / kernel_size;
        output[out_idx + 2] = sum_b / kernel_size;
    }
}
"""

vertical_box_kernel = cp.RawKernel(vertical_box_kernel_code, "vertical_box_kernel")


def box_blur(
    image: cp.ndarray,
    ksize: int,
) -> cp.ndarray:
    """
    Apply box blur (mean filter) to an image.

    Box blur is a simple averaging filter that replaces each pixel with
    the mean of pixels in a kernel-sized neighborhood. It's faster than
    Gaussian blur but produces blockier results.

    Uses OpenCV-compatible BORDER_REPLICATE for border handling.

    Parameters
    ----------
    image : cp.ndarray
        Input image (HxWx3 or HxW, float32 [0-1] or uint8)
    ksize : int
        Kernel size (odd number recommended)

    Returns
    -------
    cp.ndarray
        Blurred image (HxWx3, float32 [0-1])

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import box_blur
    >>> image = cp.random.rand(100, 100, 3).astype(cp.float32)
    >>> blurred = box_blur(image, ksize=5)
    """
    # Prepare image (dtype conversion, 2D->3D, contiguous layout)
    image = prepare_image_for_filter(image)
    height, width = image.shape[:2]

    # Allocate temporary and output buffers
    temp, output = allocate_filter_buffers(image.shape)

    # Calculate CUDA grid and block configuration
    grid_size, block_size = calculate_grid_config(width, height)

    # Horizontal blur pass
    horizontal_box_kernel(
        grid_size,
        block_size,
        (image.reshape(-1), temp.reshape(-1), height, width, ksize),
    )

    # Vertical blur pass
    vertical_box_kernel(
        grid_size,
        block_size,
        (temp.reshape(-1), output.reshape(-1), height, width, ksize),
    )

    return output
