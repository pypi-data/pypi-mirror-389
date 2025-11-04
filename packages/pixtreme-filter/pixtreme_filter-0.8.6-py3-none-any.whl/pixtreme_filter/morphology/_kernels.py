"""CUDA kernels for morphological operations

This module contains RawKernel implementations for GPU-accelerated
morphological operations (erosion, dilation, etc.).
"""

import cupy as cp

# Erosion kernel
erode_kernel_code = r"""
extern "C" __global__ void erode_kernel(
    const float* input,
    float* output,
    const int* kernel,
    const int kernel_size,
    const int width,
    const int height,
    const int kernel_center,
    const float border_value
) {
    // Calculate the pixel coordinates for the current thread
    const int x = blockIdx.x * blockDim.x + threadIdx.x;
    const int y = blockIdx.y * blockDim.y + threadIdx.y;

    // Out of bounds check
    if (x >= width || y >= height) return;

    // Process each channel (RGB)
    for (int c = 0; c < 3; c++) {
        float min_val = 1.0f;  // Initialize to maximum for float32

        // Find minimum value in kernel area
        for (int ky = 0; ky < kernel_size; ky++) {
            for (int kx = 0; kx < kernel_size; kx++) {
                // Coordinates in input image with kernel offset
                const int img_x = x + (kx - kernel_center);
                const int img_y = y + (ky - kernel_center);

                // Check if current kernel position is 1
                if (kernel[ky * kernel_size + kx] == 1) {
                    float pixel_value;

                    // Check if within image bounds
                    if (img_x >= 0 && img_x < width && img_y >= 0 && img_y < height) {
                        // Get value from input image
                        pixel_value = input[(img_y * width + img_x) * 3 + c];
                    } else {
                        // Use border_value for out of bounds
                        pixel_value = border_value;
                    }

                    min_val = min(min_val, pixel_value);
                }
            }
        }

        // Output result
        output[(y * width + x) * 3 + c] = min_val;
    }
}
"""

erode_kernel = cp.RawKernel(erode_kernel_code, "erode_kernel")


# Dilation kernel
dilate_kernel_code = r"""
extern "C" __global__ void dilate_kernel(
    const float* input,
    float* output,
    const int* kernel,
    const int kernel_size,
    const int width,
    const int height,
    const int kernel_center,
    const float border_value
) {
    // Calculate the pixel coordinates for the current thread
    const int x = blockIdx.x * blockDim.x + threadIdx.x;
    const int y = blockIdx.y * blockDim.y + threadIdx.y;

    // Out of bounds check
    if (x >= width || y >= height) return;

    // Process each channel (RGB)
    for (int c = 0; c < 3; c++) {
        float max_val = 0.0f;  // Initialize to minimum for float32

        // Find maximum value in kernel area
        for (int ky = 0; ky < kernel_size; ky++) {
            for (int kx = 0; kx < kernel_size; kx++) {
                // Coordinates in input image with kernel offset
                const int img_x = x + (kx - kernel_center);
                const int img_y = y + (ky - kernel_center);

                // Check if current kernel position is 1
                if (kernel[ky * kernel_size + kx] == 1) {
                    float pixel_value;

                    // Check if within image bounds
                    if (img_x >= 0 && img_x < width && img_y >= 0 && img_y < height) {
                        // Get value from input image
                        pixel_value = input[(img_y * width + img_x) * 3 + c];
                    } else {
                        // Use border_value for out of bounds
                        pixel_value = border_value;
                    }

                    max_val = max(max_val, pixel_value);
                }
            }
        }

        // Output result
        output[(y * width + x) * 3 + c] = max_val;
    }
}
"""

dilate_kernel = cp.RawKernel(dilate_kernel_code, "dilate_kernel")
