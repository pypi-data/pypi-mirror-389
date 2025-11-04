"""White balance color correction for removing color casts"""

import cupy as cp


def white_balance(image: cp.ndarray, method: str = "gray_world") -> cp.ndarray:
    """
    Apply white balance color correction to remove color casts.

    White balance adjusts the colors in an image to make neutral colors appear
    truly neutral, compensating for different lighting conditions.

    Three methods are supported:
    - Gray World: Assumes the average color should be gray
    - White Patch: Assumes the brightest pixel should be white
    - Simple: Stretches each channel independently to [0, 1]

    Parameters
    ----------
    image : cp.ndarray
        Input image (H, W) or (H, W, C), dtype must be float32.
        Value range [0, 1].
    method : str, optional
        White balance method, one of:
        - "gray_world" (default): Scale channels to equal means
        - "white_patch": Scale channels so max values reach 1.0
        - "simple": Stretch each channel independently to [0, 1]

    Returns
    -------
    cp.ndarray
        White balanced image, same shape and dtype as input.
        Values clipped to [0, 1] range.

    Raises
    ------
    ValueError
        If input dtype is not float32 or method is unknown.

    Notes
    -----
    **Gray World Algorithm**:
        Assumes the average color of a scene is achromatic (gray).
        Each channel is scaled so its mean equals the global mean:

        channel_out = channel_in * (global_mean / channel_mean)

        Best for: Images with diverse colors, outdoor scenes

    **White Patch Algorithm**:
        Assumes the brightest object in the scene is white.
        Each channel is scaled so its maximum reaches 1.0:

        channel_out = channel_in / max(channel_in)

        Best for: Images with clear highlights, indoor scenes

    **Simple Algorithm**:
        Stretches each channel independently to use the full [0, 1] range:

        channel_out = (channel_in - min) / (max - min)

        Best for: Low-contrast images needing contrast enhancement

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import white_balance
    >>> # Image with blue color cast
    >>> image = cp.random.rand(512, 512, 3).astype(cp.float32)
    >>> image[:, :, 2] *= 1.5  # Increase blue channel
    >>> image = cp.clip(image, 0.0, 1.0)
    >>> # Remove color cast with gray world
    >>> balanced = white_balance(image, method="gray_world")
    >>> # Use white patch method
    >>> balanced = white_balance(image, method="white_patch")
    >>> # Simple stretch
    >>> balanced = white_balance(image, method="simple")
    """
    # Validate input
    if image.dtype != cp.float32:
        raise ValueError(
            f"Input image must be float32, got {image.dtype}. "
            "Convert using image.astype(cp.float32)"
        )

    if not (2 <= image.ndim <= 3):
        raise ValueError(
            f"Input image must be 2D (H, W) or 3D (H, W, C), got shape {image.shape}"
        )

    # Handle grayscale images by adding channel dimension
    is_grayscale = image.ndim == 2
    if is_grayscale:
        image = cp.stack([image] * 3, axis=-1)

    # Validate method
    valid_methods = ["gray_world", "white_patch", "simple"]
    if method not in valid_methods:
        raise ValueError(
            f"Unknown white balance method: {method}. "
            f"Valid methods: {valid_methods}"
        )

    # Apply white balance based on method
    if method == "gray_world":
        result = _white_balance_gray_world(image)
    elif method == "white_patch":
        result = _white_balance_white_patch(image)
    elif method == "simple":
        result = _white_balance_simple(image)
    else:
        # Should never reach here due to validation above
        raise ValueError(f"Unknown method: {method}")

    # Clip to valid range
    result = cp.clip(result, 0.0, 1.0)

    # Remove channel dimension if input was grayscale
    if is_grayscale:
        result = result[:, :, 0]

    return result


def _white_balance_gray_world(image: cp.ndarray) -> cp.ndarray:
    """
    Gray World white balance algorithm.

    Assumes the average color of the image should be achromatic (gray).
    Each channel is scaled so its mean equals the global mean across all channels.

    Parameters
    ----------
    image : cp.ndarray
        Input RGB image (H, W, 3), dtype float32

    Returns
    -------
    cp.ndarray
        White balanced image
    """
    # Calculate mean for each channel
    mean_r = cp.mean(image[:, :, 0])
    mean_g = cp.mean(image[:, :, 1])
    mean_b = cp.mean(image[:, :, 2])

    # Calculate global mean across all channels
    global_mean = (mean_r + mean_g + mean_b) / 3.0

    # Avoid division by zero
    eps = 1e-6

    # Scale each channel to match global mean
    result = image.copy()
    result[:, :, 0] = image[:, :, 0] * (global_mean / (mean_r + eps))
    result[:, :, 1] = image[:, :, 1] * (global_mean / (mean_g + eps))
    result[:, :, 2] = image[:, :, 2] * (global_mean / (mean_b + eps))

    return result


def _white_balance_white_patch(image: cp.ndarray) -> cp.ndarray:
    """
    White Patch white balance algorithm.

    Assumes the brightest object in the scene should be white (1.0).
    Each channel is scaled so its maximum value reaches 1.0.

    Parameters
    ----------
    image : cp.ndarray
        Input RGB image (H, W, 3), dtype float32

    Returns
    -------
    cp.ndarray
        White balanced image
    """
    # Find maximum for each channel
    max_r = cp.max(image[:, :, 0])
    max_g = cp.max(image[:, :, 1])
    max_b = cp.max(image[:, :, 2])

    # Avoid division by zero
    eps = 1e-6

    # Scale each channel so its max reaches 1.0
    result = image.copy()
    result[:, :, 0] = image[:, :, 0] / (max_r + eps)
    result[:, :, 1] = image[:, :, 1] / (max_g + eps)
    result[:, :, 2] = image[:, :, 2] / (max_b + eps)

    return result


def _white_balance_simple(image: cp.ndarray) -> cp.ndarray:
    """
    Simple white balance algorithm.

    Stretches each channel independently to use the full [0, 1] range.
    This is essentially histogram stretching per channel.

    Parameters
    ----------
    image : cp.ndarray
        Input RGB image (H, W, 3), dtype float32

    Returns
    -------
    cp.ndarray
        White balanced image
    """
    result = cp.empty_like(image)

    for c in range(3):
        channel = image[:, :, c]
        min_val = cp.min(channel)
        max_val = cp.max(channel)

        # Avoid division by zero (uniform channel)
        if max_val - min_val < 1e-6:
            result[:, :, c] = channel
        else:
            # Stretch to [0, 1]
            result[:, :, c] = (channel - min_val) / (max_val - min_val)

    return result
