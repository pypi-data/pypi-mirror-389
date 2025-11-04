"""Laplacian edge detection filter with GPU acceleration"""

import cupy as cp

from pixtreme_filter._kernel_utils import (
    calculate_grid_config,
    prepare_image_for_filter,
)
from pixtreme_filter.gaussian import gaussian_blur

# CUDA kernel for Laplacian filter (ksize=1, 3x3 kernel)
laplacian_kernel_ksize1 = cp.RawKernel(
    r"""
extern "C" __global__
void laplacian_filter_ksize1(
    const float* input,
    float* output,
    int height,
    int width,
    int channels
) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;

    if (x >= width || y >= height) return;

    // Laplacian kernel (ksize=1, 3x3):
    // [ 0,  1,  0]
    // [ 1, -4,  1]
    // [ 0,  1,  0]

    for (int c = 0; c < channels; c++) {
        float center = input[(y * width + x) * channels + c];

        // Border replication
        float top = (y > 0) ? input[((y-1) * width + x) * channels + c] : center;
        float bottom = (y < height-1) ? input[((y+1) * width + x) * channels + c] : center;
        float left = (x > 0) ? input[(y * width + (x-1)) * channels + c] : center;
        float right = (x < width-1) ? input[(y * width + (x+1)) * channels + c] : center;

        // Apply Laplacian kernel
        float result = top + bottom + left + right - 4.0f * center;

        output[(y * width + x) * channels + c] = result;
    }
}
""",
    "laplacian_filter_ksize1",
)


def laplacian(image: cp.ndarray, ksize: int = 3) -> cp.ndarray:
    """Apply Laplacian filter for edge detection.

    The Laplacian is a 2nd derivative filter that detects edges in all directions.
    It highlights regions of rapid intensity change and is useful for edge detection.

    Note: pixtreme implementation uses float32 only. Output contains both positive
    and negative values (gradients).

    Args:
        image: Input image as CuPy array (H, W, C) or (H, W).
               Must be float32 dtype in range [0, 1].
        ksize: Kernel size. Must be in [1, 3, 5, 7].
               - ksize=1: Basic 3x3 Laplacian kernel
               - ksize=3: Gaussian smoothing + Laplacian (5x5 effective)
               - ksize=5: More smoothing + Laplacian (7x7 effective)
               - ksize=7: Maximum smoothing + Laplacian (9x9 effective)
               Default: 3

    Returns:
        Filtered image as CuPy array with same shape as input.
        Output is float32 and may contain negative values.

    Raises:
        TypeError: If input is not float32
        ValueError: If ksize is not in [1, 3, 5, 7]

    Examples:
        >>> import cupy as cp
        >>> from pixtreme_filter import laplacian
        >>> image = cp.random.rand(512, 512, 3).astype(cp.float32)
        >>> edges = laplacian(image, ksize=1)  # Basic edge detection
        >>> edges_smooth = laplacian(image, ksize=3)  # Smoother edges
    """
    # Type checking
    if image.dtype != cp.float32:
        raise TypeError(f"Input must be float32, got {image.dtype}")

    # Validate ksize
    if ksize not in [1, 3, 5, 7]:
        raise ValueError(f"ksize must be in [1, 3, 5, 7], got {ksize}")

    # Prepare image (handle 2D grayscale, ensure contiguous)
    processed_image = prepare_image_for_filter(image)
    height, width, channels = processed_image.shape

    # Allocate output buffer
    output_buffer = cp.empty_like(processed_image)

    if ksize == 1:
        # Use basic 3x3 Laplacian kernel
        grid, block = calculate_grid_config(width, height)
        laplacian_kernel_ksize1(
            grid,
            block,
            (processed_image, output_buffer, height, width, channels),
        )
    else:
        # For ksize > 1, use Laplacian of Gaussian (LoG)
        # Step 1: Apply Gaussian smoothing
        # Map ksize to sigma: ksize=3→sigma=1.0, ksize=5→sigma=1.5, ksize=7→sigma=2.0
        sigma_map = {3: 1.0, 5: 1.5, 7: 2.0}
        sigma = sigma_map[ksize]

        # Apply Gaussian blur to smooth image (reduces noise before edge detection)
        smoothed = gaussian_blur(processed_image, ksize=ksize, sigma=sigma)

        # Step 2: Apply Laplacian to smoothed image
        grid, block = calculate_grid_config(width, height)
        laplacian_kernel_ksize1(
            grid,
            block,
            (smoothed, output_buffer, height, width, channels),
        )

    # Return with original dimensionality
    if image.ndim == 2:
        return output_buffer[:, :, 0]
    else:
        return output_buffer
