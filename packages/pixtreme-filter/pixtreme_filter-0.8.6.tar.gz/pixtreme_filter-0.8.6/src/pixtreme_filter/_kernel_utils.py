"""Shared utilities for CUDA kernel-based filters

This module provides common helper functions for GPU-accelerated image filters
that use separable convolution (horizontal + vertical passes).
"""

import cupy as cp


def prepare_image_for_filter(image: cp.ndarray) -> cp.ndarray:
    """Prepare image for filter processing.

    Performs:
    1. Validate float32 dtype (required for all filters)
    2. Convert 2D grayscale to 3D (H, W) -> (H, W, 1)
    3. Ensure contiguous memory layout

    Args:
        image: Input image (H, W, C) or (H, W), must be float32

    Returns:
        Prepared image as contiguous float32 array (H, W, C)

    Raises:
        ValueError: If image is not float32
    """
    # Validate dtype - filters require float32 input
    if image.dtype != cp.float32:
        raise ValueError(
            f"Filter requires float32 input, got {image.dtype}. "
            f"Use to_float32() to convert: from pixtreme_core.utils.dtypes import to_float32"
        )

    # Ensure 3D array with 3 channels (replicate grayscale to RGB)
    # IMPORTANT: CUDA kernels assume 3-channel input (idx, idx+1, idx+2)
    if image.ndim == 2:
        # Replicate grayscale to 3 channels
        image = cp.stack([image, image, image], axis=-1)

    # Ensure contiguous memory layout for efficient CUDA access
    return cp.ascontiguousarray(image)


def allocate_filter_buffers(
    image_shape: tuple[int, ...],
) -> tuple[cp.ndarray, cp.ndarray]:
    """Allocate temporary and output buffers for filtering.

    Args:
        image_shape: Shape of the image (H, W, C)

    Returns:
        Tuple of (temp_buffer, output_buffer), both with same shape as input
    """
    temp = cp.empty(image_shape, dtype=cp.float32)
    output = cp.empty(image_shape, dtype=cp.float32)
    return temp, output


def calculate_grid_config(
    width: int,
    height: int,
    block_size: tuple[int, int] = (16, 16),
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Calculate CUDA grid and block configuration for 2D image processing.

    Args:
        width: Image width
        height: Image height
        block_size: CUDA block size (threads per block), default (16, 16)

    Returns:
        Tuple of (grid_size, block_size)
        - grid_size: Number of blocks in (x, y) dimensions
        - block_size: Threads per block in (x, y) dimensions
    """
    grid_size = (
        (width + block_size[0] - 1) // block_size[0],
        (height + block_size[1] - 1) // block_size[1],
    )
    return grid_size, block_size


# Note: We don't provide apply_separable_filter() as a high-level wrapper
# because different filters have different kernel argument patterns.
# Instead, use the helper functions above in your filter implementation:
#
# Example usage in a separable filter:
#   image = prepare_image_for_filter(image)
#   height, width = image.shape[:2]
#   temp, output = allocate_filter_buffers(image.shape)
#   grid_size, block_size = calculate_grid_config(width, height)
#
#   # Run horizontal pass
#   horizontal_kernel(grid_size, block_size, (...custom args...))
#
#   # Run vertical pass
#   vertical_kernel(grid_size, block_size, (...custom args...))
