"""Histogram equalization functions with GPU acceleration"""

import cupy as cp

from pixtreme_filter._kernel_utils import prepare_image_for_filter

# CUDA kernel for histogram computation using atomic operations
histogram_kernel = cp.RawKernel(
    r"""
extern "C" __global__
void compute_histogram(
    const float* input,
    int* histogram,
    int size,
    int num_bins
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (idx >= size) return;

    // Convert float [0, 1] to bin index [0, num_bins-1]
    float value = input[idx];
    // Clamp to [0, 1] range
    value = fminf(fmaxf(value, 0.0f), 1.0f);
    int bin = (int)(value * (num_bins - 1));

    // Atomic add to histogram
    atomicAdd(&histogram[bin], 1);
}
""",
    "compute_histogram",
)

# CUDA kernel for histogram equalization (apply LUT)
equalize_kernel = cp.RawKernel(
    r"""
extern "C" __global__
void apply_equalization(
    const float* input,
    float* output,
    const float* lut,
    int size,
    int num_bins
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (idx >= size) return;

    // Get input value and clamp to [0, 1]
    float value = input[idx];
    value = fminf(fmaxf(value, 0.0f), 1.0f);

    // Map to bin index
    int bin = (int)(value * (num_bins - 1));

    // Look up equalized value
    output[idx] = lut[bin];
}
""",
    "apply_equalization",
)

# CUDA kernel for CLAHE pixel mapping with bilinear interpolation
clahe_map_kernel = cp.RawKernel(
    r"""
extern "C" __global__
void apply_clahe_mapping(
    const float* input,
    float* output,
    const float* tile_luts,
    int height,
    int width,
    int tile_rows,
    int tile_cols,
    int tile_height,
    int tile_width,
    int num_bins
) {
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int x = blockIdx.x * blockDim.x + threadIdx.x;

    if (y >= height || x >= width) return;

    // Get pixel value and clamp to [0, 1]
    float pixel_value = input[y * width + x];
    pixel_value = fminf(fmaxf(pixel_value, 0.0f), 1.0f);

    // Map to bin index
    int bin_idx = (int)(pixel_value * (num_bins - 1));
    if (bin_idx >= num_bins) bin_idx = num_bins - 1;

    // Calculate tile center positions
    float tile_center_y = (float)tile_height / 2.0f;
    float tile_center_x = (float)tile_width / 2.0f;

    // Find the nearest tile centers
    // Normalized position within the grid (in tile coordinates)
    float ty = ((float)y + 0.5f - tile_center_y) / (float)tile_height;
    float tx = ((float)x + 0.5f - tile_center_x) / (float)tile_width;

    // Find the 4 surrounding tile centers
    int tile_y0 = (int)floorf(ty);
    int tile_y1 = tile_y0 + 1;
    int tile_x0 = (int)floorf(tx);
    int tile_x1 = tile_x0 + 1;

    // Clamp to valid tile range
    tile_y0 = max(0, min(tile_y0, tile_rows - 1));
    tile_y1 = max(0, min(tile_y1, tile_rows - 1));
    tile_x0 = max(0, min(tile_x0, tile_cols - 1));
    tile_x1 = max(0, min(tile_x1, tile_cols - 1));

    // Bilinear interpolation weights
    float fy = ty - floorf(ty);
    float fx = tx - floorf(tx);

    // Clamp weights to [0, 1]
    fy = fminf(fmaxf(fy, 0.0f), 1.0f);
    fx = fminf(fmaxf(fx, 0.0f), 1.0f);

    // Fetch LUT values from 4 surrounding tiles
    int lut_idx_00 = (tile_y0 * tile_cols + tile_x0) * num_bins + bin_idx;
    int lut_idx_01 = (tile_y0 * tile_cols + tile_x1) * num_bins + bin_idx;
    int lut_idx_10 = (tile_y1 * tile_cols + tile_x0) * num_bins + bin_idx;
    int lut_idx_11 = (tile_y1 * tile_cols + tile_x1) * num_bins + bin_idx;

    float val_00 = tile_luts[lut_idx_00];
    float val_01 = tile_luts[lut_idx_01];
    float val_10 = tile_luts[lut_idx_10];
    float val_11 = tile_luts[lut_idx_11];

    // Bilinear interpolation
    float val_0 = val_00 * (1.0f - fx) + val_01 * fx;
    float val_1 = val_10 * (1.0f - fx) + val_11 * fx;
    float result = val_0 * (1.0f - fy) + val_1 * fy;

    // Clamp output to [0, 1] range
    result = fminf(fmaxf(result, 0.0f), 1.0f);

    output[y * width + x] = result;
}
""",
    "apply_clahe_mapping",
)


def equalize_hist(image: cp.ndarray, num_bins: int = 256) -> cp.ndarray:
    """Apply histogram equalization to improve image contrast.

    Histogram equalization redistributes pixel intensity values to achieve
    a more uniform histogram, thereby improving contrast. This is particularly
    effective for images with poor contrast or narrow intensity ranges.

    Note: pixtreme implementation uses float32 only. Each channel is processed
    independently for multi-channel images.

    Args:
        image: Input image as CuPy array (H, W, C) or (H, W).
               Must be float32 dtype in range [0, 1].
        num_bins: Number of histogram bins (default: 256).
                  Higher values provide more precision but use more memory.

    Returns:
        Equalized image as CuPy array with same shape as input.
        Output is float32 in range [0, 1].

    Raises:
        TypeError: If input is not float32

    Examples:
        >>> import cupy as cp
        >>> from pixtreme_filter import equalize_hist
        >>> # Low contrast image
        >>> image = cp.random.uniform(0.3, 0.5, (512, 512, 3)).astype(cp.float32)
        >>> equalized = equalize_hist(image)
        >>> # Equalized image will have better contrast
    """
    # Type checking
    if image.dtype != cp.float32:
        raise TypeError(f"Input must be float32, got {image.dtype}")

    # Prepare image (handle 2D grayscale, ensure contiguous)
    processed_image = prepare_image_for_filter(image)
    height, width, channels = processed_image.shape

    # Allocate output buffer
    output_buffer = cp.empty_like(processed_image)

    # Process each channel independently
    for c in range(channels):
        # Extract channel data
        channel_data = processed_image[:, :, c].ravel()
        channel_size = channel_data.size

        # Allocate histogram (int32 for atomic operations)
        histogram = cp.zeros(num_bins, dtype=cp.int32)

        # Compute histogram using CUDA kernel
        block_size = 256
        grid_size = (channel_size + block_size - 1) // block_size
        histogram_kernel(
            (grid_size,),
            (block_size,),
            (channel_data, histogram, channel_size, num_bins),
        )

        # Convert histogram to float32 for CDF calculation
        histogram_float = histogram.astype(cp.float32)

        # Compute cumulative distribution function (CDF)
        cdf = cp.cumsum(histogram_float)

        # Normalize CDF to [0, 1] range
        cdf_min = cp.min(cdf[cdf > 0]) if cp.any(cdf > 0) else 0.0
        cdf_max = float(cdf[-1])

        if cdf_max - cdf_min < 1e-7:
            # Uniform image (all pixels same value) - no equalization needed
            output_buffer[:, :, c] = processed_image[:, :, c]
            continue

        # Create lookup table (LUT) for histogram equalization
        lut = (cdf - cdf_min) / (cdf_max - cdf_min)

        # Apply equalization using LUT
        output_channel = cp.empty_like(channel_data)
        equalize_kernel(
            (grid_size,),
            (block_size,),
            (channel_data, output_channel, lut, channel_size, num_bins),
        )

        # Reshape back to 2D and assign to output
        output_buffer[:, :, c] = output_channel.reshape((height, width))

    # Return with original dimensionality
    if image.ndim == 2:
        return output_buffer[:, :, 0]
    else:
        return output_buffer


def clahe(
    image: cp.ndarray, clip_limit: float = 40.0, tile_grid_size: tuple[int, int] = (8, 8)
) -> cp.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).

    CLAHE improves contrast locally by dividing the image into tiles and
    applying histogram equalization to each tile with a contrast limit.
    Bilinear interpolation is used to smoothly blend tile boundaries.

    Unlike global histogram equalization, CLAHE prevents over-amplification
    of noise in uniform regions by clipping the histogram before equalization.

    Note: pixtreme implementation uses float32 only. Each channel is processed
    independently for multi-channel images.

    Args:
        image: Input image as CuPy array (H, W, C) or (H, W).
               Must be float32 dtype in range [0, 1].
        clip_limit: Threshold for contrast limiting (default: 40.0).
                   Higher values allow more contrast enhancement.
                   Must be positive.
        tile_grid_size: Tuple (rows, cols) defining the grid size for tiling
                       (default: (8, 8)). Image is divided into this many tiles.
                       Both values must be positive integers.

    Returns:
        Enhanced image as CuPy array with same shape as input.
        Output is float32 in range [0, 1].

    Raises:
        TypeError: If input is not float32
        ValueError: If clip_limit <= 0 or tile_grid_size has non-positive values

    Examples:
        >>> import cupy as cp
        >>> from pixtreme_filter import clahe
        >>> # Low contrast image
        >>> image = cp.random.uniform(0.3, 0.5, (512, 512, 3)).astype(cp.float32)
        >>> enhanced = clahe(image, clip_limit=40.0, tile_grid_size=(8, 8))
        >>> # Enhanced image will have improved local contrast
    """
    # Type checking
    if image.dtype != cp.float32:
        raise TypeError(f"Input must be float32, got {image.dtype}")

    # Parameter validation
    if clip_limit <= 0:
        raise ValueError(f"clip_limit must be positive, got {clip_limit}")

    if tile_grid_size[0] <= 0 or tile_grid_size[1] <= 0:
        raise ValueError(
            f"tile_grid_size must be positive, got {tile_grid_size}"
        )

    # Prepare image (handle 2D grayscale, ensure contiguous)
    processed_image = prepare_image_for_filter(image)
    height, width, channels = processed_image.shape

    # Allocate output buffer
    output_buffer = cp.empty_like(processed_image)

    # Process each channel independently
    for c in range(channels):
        channel_data = processed_image[:, :, c]
        output_buffer[:, :, c] = _clahe_single_channel(
            channel_data, clip_limit, tile_grid_size, height, width
        )

    # Return with original dimensionality
    if image.ndim == 2:
        return output_buffer[:, :, 0]
    else:
        return output_buffer


def _clahe_single_channel(
    channel: cp.ndarray,
    clip_limit: float,
    tile_grid_size: tuple[int, int],
    height: int,
    width: int,
) -> cp.ndarray:
    """Apply CLAHE to a single channel.

    Args:
        channel: Single channel image (H, W) as float32
        clip_limit: Histogram clipping threshold
        tile_grid_size: (rows, cols) for tiling
        height: Image height
        width: Image width

    Returns:
        Enhanced channel (H, W) as float32
    """
    tile_rows, tile_cols = tile_grid_size
    tile_height = height // tile_rows
    tile_width = width // tile_cols

    # Allocate output
    output = cp.zeros((height, width), dtype=cp.float32)

    # Compute histogram and LUT for each tile
    num_bins = 256
    tile_luts_flat = cp.zeros((tile_rows * tile_cols, num_bins), dtype=cp.float32)

    for tile_row in range(tile_rows):
        for tile_col in range(tile_cols):
            # Extract tile region
            y_start = tile_row * tile_height
            y_end = y_start + tile_height
            x_start = tile_col * tile_width
            x_end = x_start + tile_width

            tile_data = channel[y_start:y_end, x_start:x_end].ravel()
            tile_size = tile_data.size

            # Compute histogram for this tile
            histogram = cp.zeros(num_bins, dtype=cp.int32)

            # Use CUDA kernel for histogram computation
            block_size = 256
            grid_size = (tile_size + block_size - 1) // block_size
            histogram_kernel(
                (grid_size,),
                (block_size,),
                (tile_data, histogram, tile_size, num_bins),
            )

            # Clip histogram
            histogram_float = histogram.astype(cp.float32)
            histogram_clipped = _clip_histogram(histogram_float, clip_limit, tile_size)

            # Compute CDF and create LUT
            cdf = cp.cumsum(histogram_clipped)
            cdf_min = cp.min(cdf[cdf > 0]) if cp.any(cdf > 0) else 0.0
            cdf_max = float(cdf[-1])

            if cdf_max - cdf_min < 1e-7:
                # Uniform tile - no equalization needed
                lut = cp.linspace(0, 1, num_bins, dtype=cp.float32)
            else:
                lut = (cdf - cdf_min) / (cdf_max - cdf_min)

            # Store LUT in flattened array
            tile_idx = tile_row * tile_cols + tile_col
            tile_luts_flat[tile_idx, :] = lut

    # Flatten tile LUTs for CUDA kernel
    tile_luts_flat_1d = tile_luts_flat.ravel()

    # Apply CLAHE mapping using CUDA kernel
    block_dim = (16, 16)
    grid_dim = (
        (width + block_dim[0] - 1) // block_dim[0],
        (height + block_dim[1] - 1) // block_dim[1],
    )

    clahe_map_kernel(
        grid_dim,
        block_dim,
        (
            channel.ravel(),
            output.ravel(),
            tile_luts_flat_1d,
            height,
            width,
            tile_rows,
            tile_cols,
            tile_height,
            tile_width,
            num_bins,
        ),
    )

    return output


def _clip_histogram(
    histogram: cp.ndarray, clip_limit: float, tile_size: int
) -> cp.ndarray:
    """Clip histogram and redistribute excess.

    Args:
        histogram: Histogram bins (256,) as float32
        clip_limit: Clipping threshold
        tile_size: Total number of pixels in tile

    Returns:
        Clipped and redistributed histogram
    """
    num_bins = len(histogram)

    # Calculate actual clip limit (relative to tile size)
    # clip_limit is typically given as a factor
    actual_clip = (clip_limit * tile_size) / num_bins

    # Clip histogram
    clipped = cp.minimum(histogram, actual_clip)

    # Calculate excess (total amount clipped)
    excess = cp.sum(histogram - clipped)

    # Redistribute excess uniformly across all bins
    redistribute = excess / num_bins
    clipped += redistribute

    return clipped
