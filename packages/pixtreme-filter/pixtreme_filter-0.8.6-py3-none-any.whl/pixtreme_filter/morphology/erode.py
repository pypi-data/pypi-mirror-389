"""Morphological erosion operation"""

import cupy as cp
import numpy as np
from pixtreme_core.utils.dtypes import to_float32

from ._kernels import erode_kernel


def create_erode_kernel(ksize: int) -> cp.ndarray:
    """Create kernel for erosion processing

    Parameters
    ----------
    ksize : int
        Kernel size

    Returns
    -------
    cp.ndarray
        Kernel
    """
    kernel = cp.ones((ksize, ksize), dtype=cp.int32)
    return kernel


def erode(
    image: cp.ndarray,
    ksize: int,
    kernel: cp.ndarray | None = None,
    border_value: float = 0.0,
) -> cp.ndarray:
    """Perform GPU-based erosion processing on RGB images

    Parameters
    ----------
    image : cp.ndarray (float32)
        Input RGB image (HxWx3), value range [0, 1]
    ksize : int
        Kernel size (used if kernel is None)
    kernel : cp.ndarray | None
        Structuring element (kernel). Binary 2D array
    border_value : float
        Pixel value outside boundaries

    Returns
    -------
    cp.ndarray
        RGB image after erosion processing
    """
    image = to_float32(image)

    if kernel is None:
        kernel = create_erode_kernel(ksize)

    height, width = image.shape[:2]
    ksize = kernel.shape[0]
    kernel_center = ksize // 2

    # Prepare output array
    output_image = cp.empty_like(image)

    # Calculate block size and grid size
    block_size = (16, 16)
    grid_size = (
        (width + block_size[0] - 1) // block_size[0],
        (height + block_size[1] - 1) // block_size[1],
    )

    # Execute kernel
    erode_kernel(
        grid_size,
        block_size,
        (
            image.ravel(),
            output_image.ravel(),
            kernel,
            ksize,
            width,
            height,
            kernel_center,
            np.float32(border_value),
        ),
    )

    return output_image
