"""Bilateral filter with OpenCV-compatible implementation"""

import cupy as cp

from ._kernel_utils import prepare_image_for_filter

# CUDA kernel for bilateral filter
# Edge-preserving filter that considers both spatial distance and color similarity
bilateral_filter_kernel_code = r"""
extern "C" __global__
void bilateral_filter_kernel(const float* input, float* output,
                            int height, int width, int d,
                            float sigma_color, float sigma_space) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y < height && x < width) {
        int radius = d / 2;

        // Precompute constants for Gaussian kernels
        float color_coeff = -0.5f / (sigma_color * sigma_color);
        float space_coeff = -0.5f / (sigma_space * sigma_space);

        // Get center pixel values
        int center_idx = (y * width + x) * 3;
        float center_r = input[center_idx];
        float center_g = input[center_idx + 1];
        float center_b = input[center_idx + 2];

        // Process each channel independently (OpenCV-compatible)
        // Red channel
        float sum_r = 0.0f;
        float sum_weight_r = 0.0f;
        for (int dy = -radius; dy <= radius; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                int py = min(max(y + dy, 0), height - 1);
                int px = min(max(x + dx, 0), width - 1);
                int neighbor_idx = (py * width + px) * 3;
                float neighbor_r = input[neighbor_idx];

                float spatial_dist = (float)(dx * dx + dy * dy);
                float spatial_weight = expf(spatial_dist * space_coeff);
                float color_diff = neighbor_r - center_r;
                float color_weight = expf(color_diff * color_diff * color_coeff);
                float weight = spatial_weight * color_weight;

                sum_r += neighbor_r * weight;
                sum_weight_r += weight;
            }
        }

        // Green channel
        float sum_g = 0.0f;
        float sum_weight_g = 0.0f;
        for (int dy = -radius; dy <= radius; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                int py = min(max(y + dy, 0), height - 1);
                int px = min(max(x + dx, 0), width - 1);
                int neighbor_idx = (py * width + px) * 3;
                float neighbor_g = input[neighbor_idx + 1];

                float spatial_dist = (float)(dx * dx + dy * dy);
                float spatial_weight = expf(spatial_dist * space_coeff);
                float color_diff = neighbor_g - center_g;
                float color_weight = expf(color_diff * color_diff * color_coeff);
                float weight = spatial_weight * color_weight;

                sum_g += neighbor_g * weight;
                sum_weight_g += weight;
            }
        }

        // Blue channel
        float sum_b = 0.0f;
        float sum_weight_b = 0.0f;
        for (int dy = -radius; dy <= radius; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                int py = min(max(y + dy, 0), height - 1);
                int px = min(max(x + dx, 0), width - 1);
                int neighbor_idx = (py * width + px) * 3;
                float neighbor_b = input[neighbor_idx + 2];

                float spatial_dist = (float)(dx * dx + dy * dy);
                float spatial_weight = expf(spatial_dist * space_coeff);
                float color_diff = neighbor_b - center_b;
                float color_weight = expf(color_diff * color_diff * color_coeff);
                float weight = spatial_weight * color_weight;

                sum_b += neighbor_b * weight;
                sum_weight_b += weight;
            }
        }

        // Normalize by total weight
        int out_idx = (y * width + x) * 3;
        output[out_idx] = sum_r / sum_weight_r;
        output[out_idx + 1] = sum_g / sum_weight_g;
        output[out_idx + 2] = sum_b / sum_weight_b;
    }
}
"""

bilateral_filter_kernel = cp.RawKernel(bilateral_filter_kernel_code, "bilateral_filter_kernel")


def bilateral_filter(
    image: cp.ndarray,
    d: int,
    sigma_color: float,
    sigma_space: float,
) -> cp.ndarray:
    """
    Apply bilateral filter to an image.

    Bilateral filter performs edge-preserving smoothing by considering both
    spatial proximity and color similarity. It's effective for noise reduction
    while preserving sharp edges.

    The filter combines two Gaussian kernels:
    - Spatial kernel: weights based on pixel distance
    - Color kernel: weights based on color difference

    Uses OpenCV-compatible BORDER_REPLICATE for border handling.

    Parameters
    ----------
    image : cp.ndarray
        Input image (H, W, C) or (H, W, 1), must be float32.
    d : int
        Diameter of each pixel neighborhood (odd number recommended).
        For real-time applications, d=5 is recommended.
        For offline high-quality filtering, d=9 is recommended.
    sigma_color : float
        Filter sigma in the color space. Larger values mean that farther
        colors will be mixed together.
        For float32 images in [0,1], typical range is 0.05-0.5.
    sigma_space : float
        Filter sigma in the coordinate space. Larger values mean that farther
        pixels will influence each other as long as their colors are close enough.
        Typical range is 5-50.

    Returns
    -------
    cp.ndarray
        Filtered image with same shape, float32 dtype.

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import bilateral_filter
    >>>
    >>> # Remove Gaussian noise while preserving edges
    >>> noisy_image = cp.random.rand(512, 512, 3).astype(cp.float32)
    >>> filtered = bilateral_filter(noisy_image, d=9, sigma_color=0.2, sigma_space=9.0)

    Notes
    -----
    - Bilateral filter is computationally expensive compared to Gaussian blur
    - Larger d values significantly increase computation time
    - The filter is non-separable (cannot be decomposed into 1D operations)
    - Edge-preserving property makes it superior to Gaussian blur for noise removal
    """
    # Validate d parameter
    if d <= 0:
        raise ValueError(f"d must be positive, got {d}")

    # Validate sigma parameters
    if sigma_color <= 0:
        raise ValueError(f"sigma_color must be positive, got {sigma_color}")
    if sigma_space <= 0:
        raise ValueError(f"sigma_space must be positive, got {sigma_space}")

    # Prepare image (ensure 3D and contiguous)
    # Note: prepare_image_for_filter() validates float32 dtype
    image_prepared = prepare_image_for_filter(image)
    height, width, channels = image_prepared.shape

    # Store original channel count for output
    original_channels = channels

    # Convert single-channel to 3-channel by replication
    if channels == 1:
        image_prepared = cp.repeat(image_prepared, 3, axis=2)
    elif channels != 3:
        raise ValueError(f"Bilateral filter requires 1 or 3-channel images, got {channels}")

    # Flatten to (H, W, 3) contiguous array
    image_flat = cp.ascontiguousarray(image_prepared)

    # Allocate output buffer
    output = cp.empty_like(image_flat)

    # Calculate grid and block dimensions
    block_size = (16, 16)
    grid_size = (
        (width + block_size[0] - 1) // block_size[0],
        (height + block_size[1] - 1) // block_size[1],
    )

    # Launch kernel
    bilateral_filter_kernel(
        grid_size,
        block_size,
        (
            image_flat,
            output,
            height,
            width,
            d,
            cp.float32(sigma_color),
            cp.float32(sigma_space),
        ),
    )

    # Convert back to original channel count if needed
    if original_channels == 1:
        output = output[:, :, 0:1]

    return output
