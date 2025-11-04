"""pixtreme-core: High-Performance GPU Image Processing Core Library

Core functionality for image I/O, color space conversions, and geometric transforms.
"""

__version__ = "0.8.6"

# I/O operations
# Color operations
from .color import (
    apply_lut,
    bgr_to_grayscale,
    bgr_to_hsv,
    bgr_to_rgb,
    bgr_to_ycbcr,
    hsv_to_bgr,
    hsv_to_rgb,
    ndi_uyvy422_to_ycbcr444,
    read_lut,
    rgb_to_bgr,
    rgb_to_grayscale,
    rgb_to_hsv,
    rgb_to_ycbcr,
    uyvy422_to_ycbcr444,
    ycbcr_full_to_legal,
    ycbcr_legal_to_full,
    ycbcr_to_bgr,
    ycbcr_to_grayscale,
    ycbcr_to_rgb,
    yuv420p_to_ycbcr444,
    yuv422p10le_to_ycbcr444,
)

# Constants
from .constants import (
    # EXR encoding
    IMWRITE_EXR_COMPRESSION,
    IMWRITE_EXR_COMPRESSION_B44,
    IMWRITE_EXR_COMPRESSION_B44A,
    IMWRITE_EXR_COMPRESSION_DWAA,
    IMWRITE_EXR_COMPRESSION_DWAB,
    IMWRITE_EXR_COMPRESSION_NONE,
    IMWRITE_EXR_COMPRESSION_PIZ,
    IMWRITE_EXR_COMPRESSION_PXR24,
    IMWRITE_EXR_COMPRESSION_RLE,
    IMWRITE_EXR_COMPRESSION_ZIP,
    IMWRITE_EXR_COMPRESSION_ZIPS,
    IMWRITE_EXR_TYPE,
    IMWRITE_EXR_TYPE_FLOAT,
    IMWRITE_EXR_TYPE_HALF,
    # JPEG encoding
    IMWRITE_JPEG_CHROMA_QUALITY,
    IMWRITE_JPEG_LUMA_QUALITY,
    IMWRITE_JPEG_OPTIMIZE,
    IMWRITE_JPEG_PROGRESSIVE,
    IMWRITE_JPEG_QUALITY,
    IMWRITE_JPEG_RST_INTERVAL,
    IMWRITE_JPEG_SAMPLING_FACTOR,
    # PNG encoding
    IMWRITE_PNG_BILEVEL,
    IMWRITE_PNG_COMPRESSION,
    IMWRITE_PNG_FILTER,
    IMWRITE_PNG_FILTER_AVG,
    IMWRITE_PNG_FILTER_NONE,
    IMWRITE_PNG_FILTER_PAETH,
    IMWRITE_PNG_FILTER_SUB,
    IMWRITE_PNG_FILTER_UP,
    IMWRITE_PNG_STRATEGY,
    IMWRITE_PNG_STRATEGY_DEFAULT,
    IMWRITE_PNG_STRATEGY_FILTERED,
    IMWRITE_PNG_STRATEGY_FIXED,
    IMWRITE_PNG_STRATEGY_HUFFMAN_ONLY,
    IMWRITE_PNG_STRATEGY_RLE,
    # TIFF encoding
    IMWRITE_TIFF_COMPRESSION,
    IMWRITE_TIFF_COMPRESSION_ADOBE_DEFLATE,
    IMWRITE_TIFF_COMPRESSION_CCITTFAX3,
    IMWRITE_TIFF_COMPRESSION_CCITTFAX4,
    IMWRITE_TIFF_COMPRESSION_CCITTRLE,
    IMWRITE_TIFF_COMPRESSION_DEFLATE,
    IMWRITE_TIFF_COMPRESSION_JPEG,
    IMWRITE_TIFF_COMPRESSION_LZW,
    IMWRITE_TIFF_COMPRESSION_NONE,
    IMWRITE_TIFF_RESUNIT,
    IMWRITE_TIFF_XDPI,
    IMWRITE_TIFF_YDPI,
    # Interpolation
    INTER_AREA,
    INTER_AUTO,
    INTER_B_SPLINE,
    INTER_CATMULL_ROM,
    INTER_CUBIC,
    INTER_LANCZOS2,
    INTER_LANCZOS3,
    INTER_LANCZOS4,
    INTER_LINEAR,
    INTER_MITCHELL,
    INTER_NEAREST,
)
from .io import (
    destroy_all_windows,
    imdecode,
    imencode,
    imread,
    imshow,
    imwrite,
    waitkey,
)

# Transform operations
from .transform import (
    affine_transform,
    get_inverse_matrix,
    merge_tiles,
    resize,
    tile_image,
)
from .transform import (
    affine_transform as affine,
)

# Type aliases (PEP 695)
from .types import DType

# Utils
from .utils.device import Device
from .utils.dlpack import to_cupy, to_numpy, to_tensor
from .utils.dtypes import (
    to_dtype,
    to_float16,
    to_float32,
    to_float64,
    to_uint8,
    to_uint16,
)

__all__ = [
    "__version__",
    # I/O
    "destroy_all_windows",
    "imdecode",
    "imencode",
    "imread",
    "imshow",
    "imwrite",
    "waitkey",
    # Utils - Device
    "Device",
    # Utils - DLPack
    "to_cupy",
    "to_numpy",
    "to_tensor",
    # Utils - dtypes
    "to_dtype",
    "to_float16",
    "to_float32",
    "to_float64",
    "to_uint16",
    "to_uint8",
    # Color - LUT
    "apply_lut",
    "read_lut",
    # Color - BGR/RGB
    "bgr_to_rgb",
    "rgb_to_bgr",
    # Color - Grayscale
    "bgr_to_grayscale",
    "rgb_to_grayscale",
    # Color - HSV
    "bgr_to_hsv",
    "hsv_to_bgr",
    "hsv_to_rgb",
    "rgb_to_hsv",
    # Color - YCbCr
    "bgr_to_ycbcr",
    "rgb_to_ycbcr",
    "ycbcr_full_to_legal",
    "ycbcr_legal_to_full",
    "ycbcr_to_bgr",
    "ycbcr_to_grayscale",
    "ycbcr_to_rgb",
    # Color - Video formats
    "uyvy422_to_ycbcr444",
    "ndi_uyvy422_to_ycbcr444",
    "yuv420p_to_ycbcr444",
    "yuv422p10le_to_ycbcr444",
    # Constants - Interpolation
    "INTER_AREA",
    "INTER_AUTO",
    "INTER_B_SPLINE",
    "INTER_CATMULL_ROM",
    "INTER_CUBIC",
    "INTER_LANCZOS2",
    "INTER_LANCZOS3",
    "INTER_LANCZOS4",
    "INTER_LINEAR",
    "INTER_MITCHELL",
    "INTER_NEAREST",
    # Constants - JPEG encoding
    "IMWRITE_JPEG_CHROMA_QUALITY",
    "IMWRITE_JPEG_LUMA_QUALITY",
    "IMWRITE_JPEG_OPTIMIZE",
    "IMWRITE_JPEG_PROGRESSIVE",
    "IMWRITE_JPEG_QUALITY",
    "IMWRITE_JPEG_RST_INTERVAL",
    "IMWRITE_JPEG_SAMPLING_FACTOR",
    # Constants - PNG encoding
    "IMWRITE_PNG_BILEVEL",
    "IMWRITE_PNG_COMPRESSION",
    "IMWRITE_PNG_FILTER",
    "IMWRITE_PNG_FILTER_AVG",
    "IMWRITE_PNG_FILTER_NONE",
    "IMWRITE_PNG_FILTER_PAETH",
    "IMWRITE_PNG_FILTER_SUB",
    "IMWRITE_PNG_FILTER_UP",
    "IMWRITE_PNG_STRATEGY",
    "IMWRITE_PNG_STRATEGY_DEFAULT",
    "IMWRITE_PNG_STRATEGY_FILTERED",
    "IMWRITE_PNG_STRATEGY_FIXED",
    "IMWRITE_PNG_STRATEGY_HUFFMAN_ONLY",
    "IMWRITE_PNG_STRATEGY_RLE",
    # Constants - TIFF encoding
    "IMWRITE_TIFF_COMPRESSION",
    "IMWRITE_TIFF_COMPRESSION_ADOBE_DEFLATE",
    "IMWRITE_TIFF_COMPRESSION_CCITTFAX3",
    "IMWRITE_TIFF_COMPRESSION_CCITTFAX4",
    "IMWRITE_TIFF_COMPRESSION_CCITTRLE",
    "IMWRITE_TIFF_COMPRESSION_DEFLATE",
    "IMWRITE_TIFF_COMPRESSION_JPEG",
    "IMWRITE_TIFF_COMPRESSION_LZW",
    "IMWRITE_TIFF_COMPRESSION_NONE",
    "IMWRITE_TIFF_RESUNIT",
    "IMWRITE_TIFF_XDPI",
    "IMWRITE_TIFF_YDPI",
    # Constants - EXR encoding
    "IMWRITE_EXR_COMPRESSION",
    "IMWRITE_EXR_COMPRESSION_B44",
    "IMWRITE_EXR_COMPRESSION_B44A",
    "IMWRITE_EXR_COMPRESSION_DWAA",
    "IMWRITE_EXR_COMPRESSION_DWAB",
    "IMWRITE_EXR_COMPRESSION_NONE",
    "IMWRITE_EXR_COMPRESSION_PIZ",
    "IMWRITE_EXR_COMPRESSION_PXR24",
    "IMWRITE_EXR_COMPRESSION_RLE",
    "IMWRITE_EXR_COMPRESSION_ZIP",
    "IMWRITE_EXR_COMPRESSION_ZIPS",
    "IMWRITE_EXR_TYPE",
    "IMWRITE_EXR_TYPE_FLOAT",
    "IMWRITE_EXR_TYPE_HALF",
    # Transform - Operations
    "affine",
    "affine_transform",
    "get_inverse_matrix",
    "merge_tiles",
    "resize",
    "tile_image",
    # Type aliases (PEP 695)
    "DType",
]
