# pixtreme-filter

GPU-accelerated image filtering operations for pixtreme

## Overview

`pixtreme-filter` provides high-performance image filtering operations running on CUDA-enabled GPUs. All operations are optimized for real-time performance and work directly on GPU memory.

## Features

- **Gaussian Blur**: GPU-accelerated Gaussian blur with separable kernels
- **Box Blur**: Fast averaging filter using separable CUDA kernels
- **Unsharp Mask**: Image sharpening by enhancing edges
- **Sobel Edge Detection**: Gradient-based edge detection with separable kernels
- **Median Blur**: Salt-and-pepper noise removal with edge preservation
- **Bilateral Filter**: Edge-preserving smoothing filter
- **Morphology Operations**: Erosion, dilation, opening, closing, morphological gradient
- **Zero-Copy Operations**: Direct GPU memory processing via CuPy
- **OpenCV Compatibility**: API and behavior compatible with OpenCV

## Installation

**Requirements**:
- Python >= 3.12
- CUDA Toolkit 12.x
- NVIDIA GPU with compute capability >= 6.0

```bash
pip install pixtreme-filter
```

Requires `pixtreme-core` and CUDA Toolkit 12.x.

## Quick Start

```python
import pixtreme_filter as pf
import pixtreme_core as px

# Read image (returns float32 in [0, 1] range)
img = px.imread("input.jpg")

# Apply filters
blurred = pf.gaussian_blur(img, ksize=15, sigma=3.0)
sharpened = pf.unsharp_mask(img, sigma=1.5, amount=1.0)
edges = pf.sobel(img, dx=1, dy=0, ksize=3)
denoised = pf.bilateral_filter(img, d=9, sigma_color=0.2, sigma_space=9.0)

# Save result
px.imwrite("output.jpg", denoised)
```

## Important: Float32-Only Architecture

**All filters require float32 input images.** This is a core design principle of pixtreme.

```python
import cupy as cp
from pixtreme_core.utils.dtypes import to_float32

# If you have uint8 images, convert explicitly:
img_uint8 = cp.random.randint(0, 256, (512, 512, 3), dtype=cp.uint8)
img_float = to_float32(img_uint8)  # Converts to float32 [0, 1]

# Then apply filters
result = pf.bilateral_filter(img_float, d=5, sigma_color=0.2, sigma_space=5.0)
```

**Why float32-only?**
- Consistent precision across all operations
- GPU optimization (float32 is native for CUDA)
- Avoids implicit conversions and unexpected behavior
- Users have explicit control over type conversions

## API Reference

### Blurring Filters

#### Gaussian Blur

```python
# Separable Gaussian blur (fast, exact)
blurred = pf.gaussian_blur(image, ksize=15, sigma=3.0)

# Class-based API (for repeated operations)
blur = pf.GaussianBlur()
blurred = blur.get(image, ksize=15, sigma=3.0)

# Get kernel for custom operations
kernel = pf.get_gaussian_kernel(ksize=15, sigma=3.0)
```

#### Box Blur

```python
# Fast averaging filter (uniform kernel)
blurred = pf.box_blur(image, ksize=5)
```

- Matches `cv2.blur()` behavior (max error < 1e-5)
- Uses BORDER_REPLICATE for edge handling
- Separable implementation (horizontal + vertical passes)

#### Bilateral Filter

```python
# Edge-preserving smoothing
filtered = pf.bilateral_filter(image, d=9, sigma_color=0.2, sigma_space=9.0)
```

**Parameters**:
- `d`: Diameter of pixel neighborhood (recommended: 5 for real-time, 9 for quality)
- `sigma_color`: Filter sigma in color space (typical: 0.05-0.5 for float32)
- `sigma_space`: Filter sigma in coordinate space (typical: 5-50)

**Features**:
- Edge-preserving noise reduction
- Non-separable filter (slower than Gaussian)
- Channels processed independently (OpenCV-compatible)

### Sharpening

#### Unsharp Mask

```python
# Sharpen image by enhancing edges
sharpened = pf.unsharp_mask(image, sigma=1.5, amount=1.0, threshold=0)
```

**Parameters**:
- `sigma`: Gaussian blur standard deviation (0.5-10.0)
- `amount`: Sharpening strength (0.5-2.5, where 0=no effect)
- `threshold`: Minimum change required (not yet implemented, use 0)

**Algorithm**: `sharpened = image + amount * (image - gaussian_blur(image, sigma))`

### Edge Detection

#### Sobel

```python
# Detect vertical edges (horizontal gradient)
sobel_x = pf.sobel(image, dx=1, dy=0, ksize=3)

# Detect horizontal edges (vertical gradient)
sobel_y = pf.sobel(image, dx=0, dy=1, ksize=3)

# Compute gradient magnitude
magnitude = cp.sqrt(sobel_x**2 + sobel_y**2)
```

**Parameters**:
- `dx`: Order of derivative in x-direction (0 or 1)
- `dy`: Order of derivative in y-direction (0 or 1)
- `ksize`: Kernel size (3, 5, or 7, default 3)

- Matches `cv2.Sobel()` behavior (max error < 1e-5)
- Separable implementation (smoothing + derivative)

### Noise Removal

#### Median Blur

```python
# Remove salt-and-pepper noise while preserving edges
clean = pf.median_blur(noisy_image, ksize=5)
```

**Parameters**:
- `ksize`: Kernel size (odd number, 3-7 recommended)

**Features**:
- Non-linear filter (median of ksize×ksize neighborhood)
- Edge-preserving (better than Gaussian for impulse noise)
- Non-separable (slower than box/Gaussian blur)

### Morphology Operations

```python
from pixtreme_filter.morphology import (
    erode, dilate, morphology_open, morphology_close, morphology_gradient
)

# Basic operations
eroded = erode(image, ksize=5)
dilated = dilate(image, ksize=5)

# Compound operations
opened = morphology_open(image, ksize=5)   # Erode → Dilate (remove salt noise)
closed = morphology_close(image, ksize=5)  # Dilate → Erode (fill pepper noise)
gradient = morphology_gradient(image, ksize=3)  # Dilate - Erode (edge detection)

# Custom kernels
import cupy as cp
kernel = cp.ones((5, 5), dtype=cp.float32)
eroded = erode(image, ksize=5, kernel=kernel, border_value=0.0)
```

**Features**:
- GPU-accelerated CUDA kernels (8.5x faster than CuPy built-ins)
- Supports custom kernels
- Configurable border values (default 0.0)

## Performance Notes

- **Fastest**: box_blur, gaussian_blur (separable filters)
- **Medium**: sobel, unsharp_mask, median_blur (ksize <= 7)
- **Slower**: bilateral_filter (non-separable, exponential weighting)
- **GPU Memory**: All operations work directly on GPU memory (zero-copy with CuPy)

**Typical Performance (1024×1024 image, RTX 3090)**:
- Gaussian blur (ksize=15): < 50ms
- Box blur (ksize=15): < 50ms
- Unsharp mask: < 100ms
- Sobel (ksize=3): < 100ms
- Median blur (ksize=5): < 200ms
- Bilateral filter (d=5): < 500ms

## License

MIT License - see LICENSE file for details.

## Links

- Repository: https://github.com/sync-dev-org/pixtreme
- Documentation: https://github.com/sync-dev-org/pixtreme
- PyPI: https://pypi.org/project/pixtreme-filter/
