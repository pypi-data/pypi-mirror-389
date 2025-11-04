"""Morphological operations (opening, closing, gradient)

These operations are combinations of basic erosion and dilation:
- Opening: Erosion followed by dilation (removes noise)
- Closing: Dilation followed by erosion (fills holes)
- Gradient: Dilation minus erosion (edge detection)
"""

import cupy as cp

from .dilate import dilate
from .erode import erode


def morphology_open(image: cp.ndarray, ksize: int, kernel: cp.ndarray | None = None) -> cp.ndarray:
    """Morphological opening (erosion followed by dilation)

    Opening removes small white noise while preserving large features.
    It also smooths object boundaries and separates barely touching objects.

    Parameters
    ----------
    image : cp.ndarray (float32)
        Input RGB image (HxWx3), value range [0, 1]
    ksize : int
        Kernel size
    kernel : cp.ndarray | None
        Structuring element (kernel). Binary 2D array

    Returns
    -------
    cp.ndarray
        RGB image after opening operation

    Notes
    -----
    Opening = Erosion → Dilation
    - Removes small white objects (noise)
    - Preserves large white objects
    - Smooths object boundaries
    - Separates touching objects
    """
    # Step 1: Erosion (shrinks white regions, removes noise)
    eroded = erode(image, ksize=ksize, kernel=kernel)

    # Step 2: Dilation (expands remaining white regions back)
    opened = dilate(eroded, ksize=ksize, kernel=kernel)

    return opened


def morphology_close(image: cp.ndarray, ksize: int, kernel: cp.ndarray | None = None) -> cp.ndarray:
    """Morphological closing (dilation followed by erosion)

    Closing fills small black holes (pepper noise) while preserving large features.
    It also smooths object boundaries and connects nearby objects.

    Parameters
    ----------
    image : cp.ndarray (float32)
        Input RGB image (HxWx3), value range [0, 1]
    ksize : int
        Kernel size
    kernel : cp.ndarray | None
        Structuring element (kernel). Binary 2D array

    Returns
    -------
    cp.ndarray
        RGB image after closing operation

    Notes
    -----
    Closing = Dilation → Erosion
    - Fills small black holes (pepper noise)
    - Preserves large black regions
    - Smooths object boundaries
    - Connects nearby objects
    """
    # Step 1: Dilation (expands white regions, fills small holes)
    dilated = dilate(image, ksize=ksize, kernel=kernel)

    # Step 2: Erosion (shrinks white regions back)
    closed = erode(dilated, ksize=ksize, kernel=kernel)

    return closed


def morphology_gradient(image: cp.ndarray, ksize: int, kernel: cp.ndarray | None = None) -> cp.ndarray:
    """Morphological gradient (dilation minus erosion)

    Gradient detects edges and boundaries of objects in the image.
    It highlights transitions between different intensity regions.

    Parameters
    ----------
    image : cp.ndarray (float32)
        Input RGB image (HxWx3), value range [0, 1]
    ksize : int
        Kernel size
    kernel : cp.ndarray | None
        Structuring element (kernel). Binary 2D array

    Returns
    -------
    cp.ndarray
        RGB image showing morphological gradient (edges)

    Notes
    -----
    Gradient = Dilation - Erosion
    - Detects object boundaries and edges
    - Highlights transitions between regions
    - Larger kernel produces thicker edge detection
    - Uniform regions have near-zero gradient
    """
    # Step 1: Dilation (expands white regions)
    dilated = dilate(image, ksize=ksize, kernel=kernel)

    # Step 2: Erosion (shrinks white regions)
    eroded = erode(image, ksize=ksize, kernel=kernel)

    # Step 3: Difference (edge detection)
    gradient = dilated - eroded

    return gradient


def morphology_tophat(image: cp.ndarray, ksize: int, kernel: cp.ndarray | None = None) -> cp.ndarray:
    """Morphological top hat (image minus opening)

    Top hat extracts small bright features from a dark or uneven background.
    It is the difference between the original image and its morphological opening.

    Parameters
    ----------
    image : cp.ndarray (float32)
        Input RGB image (HxWx3) or grayscale (HxW), value range [0, 1]
    ksize : int
        Kernel size - controls the size of features to extract
        Larger ksize extracts larger features
    kernel : cp.ndarray | None
        Structuring element (kernel). Binary 2D array

    Returns
    -------
    cp.ndarray
        RGB or grayscale image showing extracted bright features

    Notes
    -----
    Top Hat = Image - Opening(Image)
    - Extracts small bright features (spots, peaks)
    - Removes background and large-scale variations
    - Useful for:
      - Background removal
      - Peak detection
      - Small object detection (particles, stars, etc.)
    - Kernel size determines what is "small":
      - Small ksize (3-5): Extracts very fine features
      - Medium ksize (7-11): General purpose
      - Large ksize (15+): Extracts medium-scale features only

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import morphology_tophat
    >>> # Image with bright spots on uneven background
    >>> image = cp.random.uniform(0.3, 0.5, (512, 512, 3)).astype(cp.float32)
    >>> image[100:103, 100:103] = 1.0  # Bright spot
    >>> # Extract only the bright spots
    >>> spots = morphology_tophat(image, ksize=11)
    """
    # Step 1: Morphological opening (removes small features)
    opened = morphology_open(image, ksize=ksize, kernel=kernel)

    # Step 2: Subtract opening from original (extracts what was removed)
    tophat = image - opened

    return tophat


def morphology_blackhat(image: cp.ndarray, ksize: int, kernel: cp.ndarray | None = None) -> cp.ndarray:
    """Morphological black hat (closing minus image)

    Black hat extracts small dark features from a bright or uneven background.
    It is the difference between the morphological closing and the original image.

    Parameters
    ----------
    image : cp.ndarray (float32)
        Input RGB image (HxWx3) or grayscale (HxW), value range [0, 1]
    ksize : int
        Kernel size - controls the size of features to extract
        Larger ksize extracts larger features
    kernel : cp.ndarray | None
        Structuring element (kernel). Binary 2D array

    Returns
    -------
    cp.ndarray
        RGB or grayscale image showing extracted dark features

    Notes
    -----
    Black Hat = Closing(Image) - Image
    - Extracts small dark features (holes, valleys)
    - Removes background and large-scale variations
    - Useful for:
      - Hole detection
      - Valley detection
      - Small dark object detection (defects, scratches, etc.)
    - Kernel size determines what is "small":
      - Small ksize (3-5): Extracts very fine features
      - Medium ksize (7-11): General purpose
      - Large ksize (15+): Extracts medium-scale features only

    Examples
    --------
    >>> import cupy as cp
    >>> from pixtreme_filter import morphology_blackhat
    >>> # Image with dark holes on uneven background
    >>> image = cp.random.uniform(0.6, 0.8, (512, 512, 3)).astype(cp.float32)
    >>> image[100:103, 100:103] = 0.0  # Dark hole
    >>> # Extract only the dark holes
    >>> holes = morphology_blackhat(image, ksize=11)
    """
    # Step 1: Morphological closing (fills small holes)
    closed = morphology_close(image, ksize=ksize, kernel=kernel)

    # Step 2: Subtract original from closing (extracts what was filled)
    blackhat = closed - image

    return blackhat
