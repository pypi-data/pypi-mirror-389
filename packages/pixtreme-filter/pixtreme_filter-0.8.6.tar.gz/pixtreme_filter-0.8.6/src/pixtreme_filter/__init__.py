"""pixtreme-filter: GPU-accelerated image filtering operations"""

__version__ = "0.8.6"

from .bilateral import bilateral_filter
from .box import box_blur
from .box_filter import box_filter
from .canny import canny
from .dog import dog
from .gaussian import GaussianBlur, gaussian_blur, get_gaussian_kernel
from .harris_corner import corner_harris
from .histogram import clahe, equalize_hist
from .laplacian import laplacian
from .median import median_blur
from .morphology import (
    create_dilate_kernel,
    create_erode_kernel,
    dilate,
    erode,
    morphology_blackhat,
    morphology_close,
    morphology_gradient,
    morphology_open,
    morphology_tophat,
)
from .sobel import sobel
from .template_matching import (
    TM_CCORR,
    TM_CCORR_NORMED,
    TM_CCOEFF,
    TM_CCOEFF_NORMED,
    TM_SQDIFF,
    TM_SQDIFF_NORMED,
    match_template,
)
from .unsharp import unsharp_mask
from .white_balance import white_balance

__all__ = [
    "bilateral_filter",
    "box_blur",
    "box_filter",
    "canny",
    "clahe",
    "corner_harris",
    "dog",
    "GaussianBlur",
    "gaussian_blur",
    "get_gaussian_kernel",
    "erode",
    "create_erode_kernel",
    "dilate",
    "create_dilate_kernel",
    "equalize_hist",
    "laplacian",
    "match_template",
    "median_blur",
    "morphology_blackhat",
    "morphology_close",
    "morphology_gradient",
    "morphology_open",
    "morphology_tophat",
    "sobel",
    "TM_CCORR",
    "TM_CCORR_NORMED",
    "TM_CCOEFF",
    "TM_CCOEFF_NORMED",
    "TM_SQDIFF",
    "TM_SQDIFF_NORMED",
    "unsharp_mask",
    "white_balance",
]
