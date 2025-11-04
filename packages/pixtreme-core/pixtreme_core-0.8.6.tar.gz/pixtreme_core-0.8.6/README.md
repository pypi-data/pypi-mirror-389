# pixtreme-core

High-Performance GPU Image Processing Core Library

## Overview

`pixtreme-core` provides the fundamental building blocks for GPU-accelerated image processing:

- **I/O**: Hardware-accelerated image reading/writing via NVIDIA nvimgcodec
- **Color**: Color space conversions (BGR, RGB, HSV, YCbCr, LUT operations)
- **Transform**: Geometric transformations (resize, affine, tiling) with 11 interpolation methods
- **Utils**: Framework interoperability (NumPy, CuPy, PyTorch) via DLPack

All operations work directly on GPU memory using CuPy arrays for maximum performance.

## Installation

**Requirements**:
- Python >= 3.12
- CUDA Toolkit 12.x
- NVIDIA GPU with compute capability >= 6.0

```bash
pip install pixtreme-core
```

### OpenCV Variants

`pixtreme-core` uses `opencv-python` by default. For different environments:

- **Headless environments** (no GUI): Replace with `opencv-python-headless`
  ```bash
  pip uninstall opencv-python
  pip install opencv-python-headless
  ```

- **Contrib modules needed**: Replace with `opencv-contrib-python`
  ```bash
  pip uninstall opencv-python
  pip install opencv-contrib-python
  ```

All variants provide the same `cv2` module and are compatible with pixtreme.

## Quick Start

```python
import pixtreme_core as px

# Read image (returns CuPy array on GPU)
img = px.imread("input.jpg")

# Resize with auto-selected interpolation
img = px.resize(img, (512, 512))

# Convert color space
img = px.bgr_to_rgb(img)

# Write image
px.imwrite("output.jpg", img)
```

## Features

### Image I/O
- `imread()`: Hardware-accelerated JPEG/PNG decoding
- `imwrite()`: Efficient image encoding
- `imshow()`: Display with matplotlib

### Color Conversions
- BGR ↔ RGB, HSV, YCbCr, Grayscale
- 3D LUT operations with trilinear/tetrahedral interpolation
- Video format support (UYVY422, YUV420p, YUV422p10le)
- Legal/full range YCbCr conversion

### Geometric Transforms
- `resize()`: 11 interpolation methods including Lanczos, Mitchell, Catmull-Rom
- `affine()`: Affine transformations
- `tile_image()`, `merge_tiles()`: Tiling workflow for large images
- `erode()`: Morphological erosion

### Framework Interoperability
- `to_cupy()`, `to_numpy()`, `to_tensor()`: Zero-copy conversions via DLPack
- `to_uint8()`, `to_uint16()`, `to_float32()`: Type conversions with range scaling

## License

MIT License - see LICENSE file for details.

## Links

- Repository: https://github.com/sync-dev-org/pixtreme
- Documentation: https://github.com/sync-dev-org/pixtreme/blob/main/README.md
