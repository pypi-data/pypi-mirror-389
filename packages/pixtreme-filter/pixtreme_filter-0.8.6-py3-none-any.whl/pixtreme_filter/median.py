"""Median blur filter with OpenCV-compatible implementation"""

import cupy as cp

from ._kernel_utils import calculate_grid_config, prepare_image_for_filter

# CUDA kernel for median blur
# Uses insertion sort for small arrays (efficient for ksize <= 7)
median_blur_kernel_code = r"""
extern "C" __global__
void median_blur_kernel(const float* input, float* output,
                       int height, int width, int ksize) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        int radius = ksize / 2;
        int window_size = ksize * ksize;

        // Temporary arrays for sorting (one per channel)
        float values_r[49];  // Max 7x7 = 49 elements
        float values_g[49];
        float values_b[49];

        // Collect values from neighborhood
        int idx = 0;
        for (int dy = -radius; dy <= radius; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                // Replicate border (clamp coordinates)
                int py = min(max(y + dy, 0), height - 1);
                int px = min(max(x + dx, 0), width - 1);
                int in_idx = (py * width + px) * 3;

                values_r[idx] = input[in_idx];
                values_g[idx] = input[in_idx + 1];
                values_b[idx] = input[in_idx + 2];
                idx++;
            }
        }

        // Insertion sort for each channel
        // Red channel
        for (int i = 1; i < window_size; i++) {
            float key = values_r[i];
            int j = i - 1;
            while (j >= 0 && values_r[j] > key) {
                values_r[j + 1] = values_r[j];
                j--;
            }
            values_r[j + 1] = key;
        }

        // Green channel
        for (int i = 1; i < window_size; i++) {
            float key = values_g[i];
            int j = i - 1;
            while (j >= 0 && values_g[j] > key) {
                values_g[j + 1] = values_g[j];
                j--;
            }
            values_g[j + 1] = key;
        }

        // Blue channel
        for (int i = 1; i < window_size; i++) {
            float key = values_b[i];
            int j = i - 1;
            while (j >= 0 && values_b[j] > key) {
                values_b[j + 1] = values_b[j];
                j--;
            }
            values_b[j + 1] = key;
        }

        // Get median (middle element of sorted array)
        int median_idx = window_size / 2;
        int out_idx = (y * width + x) * 3;
        output[out_idx] = values_r[median_idx];
        output[out_idx + 1] = values_g[median_idx];
        output[out_idx + 2] = values_b[median_idx];
    }
}
"""

median_blur_kernel = cp.RawKernel(median_blur_kernel_code, "median_blur_kernel")


def median_blur(
    image: cp.ndarray,
    ksize: int,
) -> cp.ndarray:
    """
    Apply median blur filter to an image.

    Median blur replaces each pixel with the median of pixels in a kernel-sized
    neighborhood. It's highly effective at removing salt-and-pepper noise while
    preserving edges better than Gaussian or box blur.

    Uses OpenCV-compatible BORDER_REPLICATE for border handling.

    Parameters
    ----------
    image : cp.ndarray
        Input image (HxWx3 or HxW, float32 [0-1] or uint8)
    ksize : int
        Kernel size (odd number, 3-7 recommended for performance)

    Returns
    -------
    cp.ndarray
        Filtered image (HxWx3, float32 [0-1])

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import median_blur
    >>> # Remove salt-and-pepper noise
    >>> noisy_image = cp.random.rand(100, 100, 3).astype(cp.float32)
    >>> # Add noise
    >>> noise_mask = cp.random.rand(100, 100, 3) < 0.05
    >>> noisy_image[noise_mask] = cp.random.choice([0.0, 1.0], size=cp.sum(noise_mask))
    >>> # Apply median blur
    >>> clean_image = median_blur(noisy_image, ksize=5)

    Notes
    -----
    - Non-separable filter (cannot be split into horizontal + vertical passes)
    - Preserves edges better than Gaussian or box blur
    - Most effective for salt-and-pepper (impulse) noise
    - Larger kernel sizes (>7) may have reduced performance
    """
    # Validate kernel size
    if ksize % 2 == 0:
        raise ValueError(f"Kernel size must be odd, got {ksize}")
    if ksize < 3:
        raise ValueError(f"Kernel size must be >= 3, got {ksize}")
    if ksize > 7:
        # Warn but don't error - larger sizes work but may be slow
        import warnings

        warnings.warn(
            f"Kernel size {ksize} is large and may have reduced performance. Consider ksize <= 7 for optimal speed.",
            UserWarning,
            stacklevel=2,
        )

    # Prepare image (dtype conversion, 2D->3D, contiguous layout)
    image = prepare_image_for_filter(image)
    height, width = image.shape[:2]

    # Allocate output buffer
    output = cp.empty(image.shape, dtype=cp.float32)

    # Calculate CUDA grid and block configuration
    grid_size, block_size = calculate_grid_config(width, height)

    # Apply median blur kernel
    median_blur_kernel(
        grid_size,
        block_size,
        (image.reshape(-1), output.reshape(-1), height, width, ksize),
    )

    return output
