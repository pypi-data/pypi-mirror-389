# 🚀 pixtreme

> **Blazing-fast GPU-accelerated image processing for Python**

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![CUDA](https://img.shields.io/badge/CUDA-12.x-green.svg)](https://developer.nvidia.com/cuda-downloads)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pixtreme.svg)](https://pypi.org/project/pixtreme/)

## 🌟 Highlights

- **⚡ Lightning Fast**: CUDA-optimized kernels deliver real-time performance
- **🎨 Professional Color Pipeline**: Full ACES workflow, 3D LUTs, 10-bit precision
- **🧠 AI-Ready**: Seamless integration with ONNX, PyTorch, and TensorRT
- **🔗 Zero-Copy Interop**: DLPack support for PyTorch, TensorFlow, JAX
- **📊 Extensive Format Support**: OpenEXR, JPEG, PNG, TIFF, and more

## 📋 Table of Contents

- [Breaking Changes](#breaking-changes)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Performance Notes](#performance-notes)
- [License](#license)

## ⚠️ Breaking Changes

### v0.8.6: TensorRT Dependency Update (2025-11-04)

**📦 DEPENDENCY CHANGE: TensorRT dependency updated to tensorrt-cu12** - v0.8.6 updates the TensorRT optional dependency from the generic `tensorrt` package to the CUDA 12-specific `tensorrt-cu12` package.

**What changed**:
- **Package name updated**: `pixtreme-upscale[tensorrt]` now depends on `tensorrt-cu12>=10.11.0.33` instead of `tensorrt>=10.11.0.33`
- **CUDA 12 specific**: Aligns with pixtreme's CUDA 12.x requirement (already specified in documentation)
- **Installation unchanged**: Use the same installation commands - pip will automatically install the correct package

**Why this change**:
- **Consistency**: Explicitly targets CUDA 12.x builds of TensorRT (pixtreme already requires CUDA 12.x)
- **Clarity**: Package name now clearly indicates CUDA version compatibility
- **Alignment**: Matches NVIDIA's recommended package naming for CUDA 12 environments

**Who should upgrade**:
- **All users of pixtreme-upscale[tensorrt]** - No code changes required, dependency resolution updated automatically
- Users who had installation issues with the generic `tensorrt` package may see improved compatibility

**Upgrade**:
```bash
pip install --upgrade pixtreme-upscale[tensorrt]>=0.8.6
# or
pip install --upgrade pixtreme[all]>=0.8.6
```

**Note**: If you previously installed `tensorrt` manually, you may want to uninstall it and let pip install `tensorrt-cu12` instead:
```bash
pip uninstall tensorrt
pip install pixtreme-upscale[tensorrt]>=0.8.6
```

### v0.8.5: Float32-Only Architecture Enforcement (2025-10-29)

**🔥 BREAKING CHANGE: All filter functions now strictly require float32 input** - v0.8.5 enforces pixtreme's core design principle that all image processing happens in float32.

**What changed**:
- **Filter functions reject uint8 input**: `bilateral_filter`, `unsharp_mask`, `box_blur`, `gaussian_blur`, `sobel`, `median_blur` now raise `ValueError` if given uint8 arrays
- **Explicit conversion required**: Users must call `to_float32()` before filtering uint8 images
- **No more implicit conversions**: Filters no longer silently convert uint8 → float32

**Why this change**:
- **Design consistency**: pixtreme is fundamentally a float32-based library for GPU processing
- **User control**: Explicit conversions prevent unexpected behavior and give users full control
- **Performance**: Eliminates hidden conversion overhead and potential precision issues

**Migration guide**:
```python
# OLD (v0.8.4 and earlier - implicit conversion)
import cupy as cp
from pixtreme_filter import bilateral_filter

img_uint8 = cp.random.randint(0, 256, (512, 512, 3), dtype=cp.uint8)
result = bilateral_filter(img_uint8, d=5, sigma_color=75, sigma_space=5.0)  # Worked in v0.8.4

# NEW (v0.8.5+ - explicit conversion required)
from pixtreme_core.utils.dtypes import to_float32

img_uint8 = cp.random.randint(0, 256, (512, 512, 3), dtype=cp.uint8)
img_float = to_float32(img_uint8)  # Explicit: uint8 [0-255] → float32 [0-1]
result = bilateral_filter(img_float, d=5, sigma_color=0.2, sigma_space=5.0)  # Note: sigma_color adjusted for [0-1] range
```

**Note**: sigma_color parameter values differ between uint8 and float32:
- uint8 images: typical range 10-150 (for values 0-255)
- float32 images: typical range 0.05-0.5 (for values 0-1)

**New features in v0.8.5**:
- **Bilateral filter**: Edge-preserving smoothing added to pixtreme-filter
  - GPU-accelerated CUDA kernel implementation
  - OpenCV-compatible API and behavior
  - Effective for noise reduction while maintaining sharp edges

**Bug fixes**:
- **Windows cp932 encoding**: Fixed UnicodeEncodeError when printing from `model_convert.py` and `onnx_upscaler.py` on Windows systems
  - Replaced all emoji characters with ASCII equivalents
  - All diagnostic messages now safe for cp932 encoding

**Who should upgrade**:
- **All users upgrading to v0.8.5** - Code changes required for filter functions
- Users wanting bilateral filter or Windows emoji fix can upgrade safely with migration

**Upgrade**:
```bash
pip install --upgrade pixtreme[all]>=0.8.5
```

### v0.8.4: Critical Bugfix for Type Hints (2025-10-27)

**🔥 CRITICAL BUGFIX: Fixed runtime import errors in non-PyTorch environments** - v0.8.3 still had issues with type hint evaluation causing `AttributeError` when PyTorch is not installed.

**What was fixed**:
- **Type hints wrapped in string literals**: All `torch.device` and `torch.Tensor` references in type annotations now use string literals (`"torch.Tensor"`) to prevent runtime evaluation
- **Root cause**: While v0.8.3 added `from __future__ import annotations`, some environments (Python 3.13, pydantic) still evaluate annotations at runtime
- **Impact**: `pixtreme-core` now imports successfully in all environments, regardless of PyTorch installation status

**Who should upgrade**:
- **All v0.8.3 users immediately** - v0.8.3 is broken in non-PyTorch environments
- Users running Python 3.13 or using libraries that evaluate annotations at runtime

**Upgrade**:
```bash
pip install --upgrade pixtreme-core>=0.8.4
# or
pip install --upgrade pixtreme[all]>=0.8.4
```

**Technical details**: Changed type hints from `torch.device` to `"torch.device"` in `dlpack.py:25,26,47,64` to ensure compatibility with all annotation evaluation strategies.

### v0.8.3: nvimgcodec v0.6.0+ Required (2025-10-27)

**⚠️ BREAKING CHANGE: nvimgcodec >= 0.6.0 now required** - v0.8.3 drops support for nvimgcodec v0.5.x to simplify code and adopt the latest API.

**What changed**:
- **Dependency updated**: `nvidia-nvimgcodec-cu12[all]>=0.6.0` (was >=0.5.0)
- **dlpack.py**: Improved `TYPE_CHECKING` pattern for torch imports (fixes community-reported issue)
- **imread.py**: Simplified to use nvimgcodec v0.6.0 API only (removed backward compatibility code)

**nvimgcodec v0.6.0 API Changes**:
- `DecodeSource` class removed from Python API (deprecated in v0.6.0-beta.6)
- Direct file path passing to `Decoder.read()` is the new standard
- Cleaner, simpler API with better performance

**Who should upgrade**:
- **All users** - v0.8.3 requires nvimgcodec >= 0.6.0
- If you need nvimgcodec < 0.6.0, stay on pixtreme v0.8.2

**Upgrade**:
```bash
pip install --upgrade pixtreme-core>=0.8.3
# or
pip install --upgrade pixtreme[all]>=0.8.3
```

**Note**: This will automatically upgrade nvimgcodec to v0.6.0+ due to dependency requirements.

### v0.8.2: Critical Bugfix (2025-10-27)

**Fixed import error when PyTorch not installed** - v0.8.0 had a critical bug where `pixtreme-core` would fail to import in environments without PyTorch.

**What was fixed**:
- Added `from __future__ import annotations` to prevent runtime evaluation of type hints
- `torch.device` type annotations no longer cause `AttributeError` when torch is not installed
- Module imports now succeed with `TORCH_AVAILABLE=False` flag set correctly

**Who should upgrade**:
- **All v0.8.0 users** - v0.8.0 is broken in non-PyTorch environments
- Users who install `pixtreme-core` without the full `pixtreme[all]` bundle

**Upgrade**:
```bash
pip install --upgrade pixtreme-core>=0.8.2
# or
pip install --upgrade pixtreme[all]>=0.8.2
```

### v0.8.0: Morphology Operations Reorganization

**Morphology module moved from core to filter** - The `erode` function and related morphology operations have been relocated to the `pixtreme-filter` package for better organization.

**API Changes**:
- `erode()` moved from `pixtreme-core` to `pixtreme-filter`
- New operations added: `dilate()`, `morphology_open()`, `morphology_close()`, `morphology_gradient()`
- All morphology functions now in unified `pixtreme_filter.morphology` module

**Migration**: Update your imports:
```python
# OLD (v0.7.x and earlier)
from pixtreme_core import erode

# NEW (v0.8.0+)
from pixtreme_filter.morphology import erode, dilate, morphology_open, morphology_close, morphology_gradient

# Or use the convenience import
import pixtreme as px
px.erode(image, ksize=5)  # Still works if pixtreme-filter is installed
```

**Installation**: Ensure `pixtreme-filter` is installed:
```bash
pip install pixtreme[filter]  # or pixtreme[all] for all features
```

### v0.7.3: Type System & Build Modernization

**Python 3.12+ now required** - pixtreme v0.7.3 drops Python 3.10/3.11 support and requires Python 3.12 or later.

**Type System Improvements**:
- Full mypy compatibility with strict type checking
- Improved error messages with detailed value reporting
- 15+ type annotation bugs fixed across core modules

**Build System Optimization**:
- License classifier added to all packages (MIT)
- Issues URL standardized across packages
- Pre-commit hooks for local quality checks (mypy, ruff, version consistency)
- sdist/wheel metadata improvements

**Developer Experience**:
- uv-native pre-commit config (no virtualenv overhead)
- Better error reporting in dtype conversions and validation
- Comprehensive metadata for PyPI display

**Migration**: Update Python to 3.12+ and reinstall:
```bash
# Ensure Python 3.12 or later
python --version  # Should show 3.12.x or 3.13.x

pip install --upgrade pixtreme>=0.7.3
```

### v0.6.3: Bug Fixes and API Restoration

**v0.6.3 restores missing APIs from v0.6.0** and includes important bug fixes:

**Restored APIs** (accidentally removed in v0.6.0):
- I/O functions: `destroy_all_windows()`, `imdecode()`, `imencode()`, `waitkey()`
- Type conversions: `to_dtype()`, `to_float16()`, `to_float64()`
- Transform functions: `affine_transform()`, `get_inverse_matrix()`

**Bug Fixes**:
- `imwrite()` now returns `bool` (success/failure) instead of `None`
- LUT parser improved to skip non-numeric lines in `.cube` files
- Comprehensive test suite added (297 tests, 99.7% pass rate)

**Migration**: If you encountered `AttributeError` for these functions in v0.6.0, upgrade to v0.6.3:
```bash
pip install --upgrade pixtreme>=0.6.3
```

### v0.6.0: Modular Package Structure

**pixtreme is now split into modular packages** for better flexibility:

- `pixtreme-core`: Core functionality (always installed)
- `pixtreme-aces`: ACES color management (optional)
- `pixtreme-filter`: Image filtering (optional)
- `pixtreme-draw`: Drawing primitives (optional)
- `pixtreme-upscale`: Deep learning upscalers (optional)

**Backward compatibility**: `import pixtreme as px` still works with all installed packages.

**Migration**: No code changes needed. `pip install pixtreme[all]` for previous behavior.

### v0.5.2: _cp Functions Removed

**🚨 IMPORTANT: v0.5.1 is broken - use v0.5.2 or later**

v0.5.1 contains a critical bug that prevents import. If you have v0.5.1 installed, upgrade immediately:
```bash
pip install --upgrade pixtreme>=0.5.2
```

**`_cp` functions have been removed** from the main pixtreme package in v0.5.2 (attempted in v0.5.1 but broken).

The following functions are now available only in the `pixtreme-legacy` package:
- `apply_lut_cp` → Use `apply_lut` instead
- `uyvy422_to_ycbcr444_cp` → Use `uyvy422_to_ycbcr444` instead
- `ndi_uyvy422_to_ycbcr444_cp` → Use `ndi_uyvy422_to_ycbcr444` instead
- `yuv420p_to_ycbcr444_cp` → Use `yuv420p_to_ycbcr444` instead
- `yuv422p10le_to_ycbcr444_cp` → Use `yuv422p10le_to_ycbcr444` instead

### Migration Path

**Option 1: Use pixtreme-legacy (Temporary)**:
```bash
pip install pixtreme-legacy
```

```python
from pixtreme_legacy import apply_lut_cp
result = apply_lut_cp(image, lut)  # Works without warnings
```

**Option 2: Migrate to standard functions (Recommended)**:
```python
from pixtreme import apply_lut
result = apply_lut(image, lut)  # No warning
```

### Legacy Support

If you need continued support for `_cp` functions, install `pixtreme-legacy`:
```bash
pip install pixtreme-legacy
```


## ✨ Features

### 🎯 Image Processing
- **11 Interpolation Methods**: Nearest, Linear, Cubic, Area, Lanczos (2/3/4), Mitchell, B-Spline, Catmull-Rom
- **Advanced Transforms**: Affine transformations, tiling with overlap blending
- **Morphological Operations**: Erosion with custom kernels
- **GPU-Accelerated Filters**: Gaussian blur, custom convolutions

### 🎨 Color Science
- **Color Spaces**: BGR/RGB, HSV, YCbCr, YUV (4:2:0, 4:2:2), Grayscale
- **ACES Pipeline**: Complete Academy Color Encoding System workflow
- **3D LUT Processing**: Trilinear and tetrahedral interpolation
- **10-bit Precision**: Professional video color accuracy

### 🤖 Deep Learning
- **Multi-Backend Support**: ONNX Runtime, PyTorch, TensorRT
- **Super Resolution**: Built-in upscaling with various models
- **Batch Processing**: Efficient multi-image inference
- **Model Optimization**: Automatic conversion and optimization tools

### 🔧 Advanced Features
- **Memory I/O**: Encode/decode images in memory
- **Hardware Acceleration**: NVIDIA nvimgcodec support
- **Drawing Tools**: GPU-accelerated shapes and text rendering
- **Framework Integration**: Zero-copy tensor sharing via DLPack

## 🚀 Installation

### Requirements
- Python >= 3.12
- CUDA Toolkit 12.x
- NVIDIA GPU with compute capability >= 6.0

### Quick Install

**v0.6.0 introduces modular packages** - install only what you need:

```bash
# Core only (I/O, color, transform, utils)
pip install pixtreme

# Core + ACES color management
pip install pixtreme[aces]

# Core + image filters
pip install pixtreme[filter]

# Core + drawing primitives
pip install pixtreme[draw]

# Core + deep learning upscalers
pip install pixtreme[upscale]

# All features
pip install pixtreme[all]

# All features + legacy support + TensorRT
pip install pixtreme[full]
```

### Individual Packages

You can also install packages individually:

```bash
pip install pixtreme-core      # Core functionality
pip install pixtreme-aces      # ACES color management
pip install pixtreme-filter    # Image filtering
pip install pixtreme-draw      # Drawing primitives
pip install pixtreme-upscale   # Deep learning upscalers
pip install pixtreme-legacy    # Legacy _cp functions
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sync-dev-org/pixtreme.git
cd pixtreme

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup development environment
uv python pin 3.12
uv sync --extra dev --extra opencv
```

## 💡 Quick Start

```python
import pixtreme as px

# Read image directly to GPU as float32 (BGR format)
image = px.imread("photo.jpg")

# All operations work on GPU memory
image_rgb = px.bgr_to_rgb(image)
image_hsv = px.rgb_to_hsv(image_rgb)

# High-quality resize with 11 interpolation methods
image = px.resize(image, (1920, 1080), interpolation=px.INTER_LANCZOS4)

# Choose backend based on your needs
upscaler = px.OnnxUpscaler("models/realesrgan.onnx")     # Balanced
# upscaler = px.TrtUpscaler("models/realesrgan.trt")     # Fastest
# upscaler = px.TorchUpscaler("models/realesrgan.pth")   # Most flexible

# Upscale with single method call
upscaled = upscaler.get(image)

# Professional color grading with 3D LUT
lut = px.read_lut("cinematic_look.cube")
graded = px.apply_lut(image, lut, interpolation=1)  # Tetrahedral

# Save with format-specific options
px.imwrite("output.jpg", graded, param=95)
```

## 📖 API Reference

### 🎮 Device Management

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `get_device_id()` | - | `int` | Get current CUDA device ID |
| `get_device_count()` | - | `int` | Get number of available GPUs |
| `Device(id)` | `id: int` | Context manager | Context manager for device selection |

### 🎨 Color Module (`pixtreme.color`)

#### Basic Color Conversions
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `bgr_to_rgb(image)` | `image: np.ndarray or cp.ndarray` | `np.ndarray or cp.ndarray` | Convert BGR to RGB format |
| `rgb_to_bgr(image)` | `image: np.ndarray or cp.ndarray` | `np.ndarray or cp.ndarray` | Convert RGB to BGR format |
| `bgr_to_grayscale(image)` | `image: cp.ndarray` | `cp.ndarray` | Convert BGR to grayscale |
| `rgb_to_grayscale(image)` | `image: cp.ndarray` | `cp.ndarray` | Convert to grayscale (Rec.709) |
| `bgr_to_hsv(image)` | `image: cp.ndarray` | `cp.ndarray` | Convert BGR to HSV |
| `hsv_to_bgr(image)` | `image: cp.ndarray` | `cp.ndarray` | Convert HSV to BGR |
| `rgb_to_hsv(image)` | `image: cp.ndarray` | `cp.ndarray` | Convert RGB to HSV |
| `hsv_to_rgb(image)` | `image: cp.ndarray` | `cp.ndarray` | Convert HSV to RGB |

#### YCbCr/YUV Conversions
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `bgr_to_ycbcr(image)` | `image: cp.ndarray` | `cp.ndarray` | BGR to YCbCr (10-bit precision) |
| `rgb_to_ycbcr(image)` | `image: cp.ndarray` | `cp.ndarray` | RGB to YCbCr (10-bit precision) |
| `ycbcr_to_bgr(image)` | `image: cp.ndarray` | `cp.ndarray` | YCbCr to BGR conversion |
| `ycbcr_to_rgb(image)` | `image: cp.ndarray` | `cp.ndarray` | YCbCr to RGB conversion |
| `ycbcr_to_grayscale(image)` | `image: cp.ndarray` | `cp.ndarray` | Extract Y channel as grayscale |
| `ycbcr_full_to_legal(image)` | `image: cp.ndarray` | `cp.ndarray` | Full to Legal range conversion |
| `ycbcr_legal_to_full(image)` | `image: cp.ndarray` | `cp.ndarray` | Legal to Full range conversion |
| `yuv420p_to_ycbcr444(yuv420_data, width, height, interpolation)` | `yuv420_data: cp.ndarray, width: int, height: int, interpolation: int = 1` | `cp.ndarray` | YUV 4:2:0 to YCbCr 4:4:4 |
| `yuv420p_to_ycbcr444_cp(yuv420_data, width, height, interpolation)` | `yuv420_data: cp.ndarray, width: int, height: int, interpolation: int = 1` | `cp.ndarray` | YUV 4:2:0 to YCbCr 4:4:4 (CuPy native) |
| `yuv422p10le_to_ycbcr444(ycbcr422_data, width, height)` | `ycbcr422_data: cp.ndarray, width: int, height: int` | `cp.ndarray` | 10-bit YUV 4:2:2 to YCbCr 4:4:4 |
| `yuv422p10le_to_ycbcr444_cp(ycbcr422_data, width, height)` | `ycbcr422_data: cp.ndarray, width: int, height: int` | `cp.ndarray` | 10-bit YUV 4:2:2 to YCbCr 4:4:4 (CuPy) |
| `uyvy422_to_ycbcr444(uyvy_data, height, width)` | `uyvy_data: cp.ndarray, height: int, width: int` | `cp.ndarray` | UYVY 4:2:2 to YCbCr 4:4:4 |
| `uyvy422_to_ycbcr444_cp(uyvy_data, height, width)` | `uyvy_data: cp.ndarray, height: int, width: int` | `cp.ndarray` | UYVY 4:2:2 to YCbCr 4:4:4 (CuPy native) |
| `ndi_uyvy422_to_ycbcr444(uyvy_data)` | `uyvy_data: cp.ndarray` | `cp.ndarray` | NDI UYVY to YCbCr 4:4:4 |
| `ndi_uyvy422_to_ycbcr444_cp(uyvy_data)` | `uyvy_data: cp.ndarray` | `cp.ndarray` | NDI UYVY to YCbCr 4:4:4 (CuPy native) |

#### ACES Color Pipeline
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `rec709_to_aces2065_1(image, tonemap)` | `image: cp.ndarray \| np.ndarray, tonemap: bool = True` | `cp.ndarray \| np.ndarray` | Rec.709 to ACES2065-1 IDT. Preserves input type (NumPy/CuPy). OCIO ACES 1.2 compliant |
| `aces2065_1_to_rec709(image, tonemap)` | `image: cp.ndarray \| np.ndarray, tonemap: bool = True` | `cp.ndarray \| np.ndarray` | ACES2065-1 to Rec.709 ODT. Preserves input type (NumPy/CuPy). OCIO ACES 1.2 compliant |
| `aces2065_1_to_acescct(image)` | `image: cp.ndarray \| np.ndarray` | `cp.ndarray \| np.ndarray` | ACES2065-1 (AP0) to ACEScct (AP1 log-encoded). Preserves input type |
| `aces2065_1_to_acescg(image)` | `image: cp.ndarray \| np.ndarray` | `cp.ndarray \| np.ndarray` | ACES2065-1 (AP0) to ACEScg (AP1 linear). Preserves input type |
| `acescct_to_aces2065_1(image)` | `image: cp.ndarray \| np.ndarray` | `cp.ndarray \| np.ndarray` | ACEScct (AP1 log-encoded) to ACES2065-1 (AP0). Preserves input type |
| `acescg_to_aces2065_1(image)` | `image: cp.ndarray \| np.ndarray` | `cp.ndarray \| np.ndarray` | ACEScg (AP1 linear) to ACES2065-1 (AP0). Preserves input type |

#### 3D LUT Processing
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `read_lut(file_path, use_cache, cache_dir)` | `file_path: str, use_cache: bool = True, cache_dir: str = "cache"` | `cp.ndarray` | Read .cube format LUT files |
| `apply_lut(image, lut, interpolation)` | `image: cp.ndarray, lut: cp.ndarray, interpolation: int = 0` | `cp.ndarray` | Apply 3D LUT (0=trilinear, 1=tetrahedral) |
| `apply_lut_cp(image, lut, interpolation)` | `image: cp.ndarray, lut: cp.ndarray, interpolation: int = 0` | `cp.ndarray` | Apply 3D LUT (CuPy native implementation) |

### 🖼️ Draw Module (`pixtreme.draw`)

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `circle(image, center_x, center_y, radius, color)` | `image: cp.ndarray, center_x: int, center_y: int, radius: int, color: tuple = (1.0, 1.0, 1.0)` | `cp.ndarray` | Draw filled circle |
| `rectangle(image, top_left_x, top_left_y, bottom_right_x, bottom_right_y, color)` | `image: cp.ndarray, top_left_x: int, top_left_y: int, bottom_right_x: int, bottom_right_y: int, color: tuple = (1.0, 1.0, 1.0)` | `cp.ndarray` | Draw filled rectangle |
| `put_text(image, text, org, font_face, font_scale, color, thickness, line_type, density)` | `image: cp.ndarray, text: str, org: tuple[int, int], font_face: int = cv2.FONT_HERSHEY_SIMPLEX, font_scale: float = 1.0, color: tuple = (1.0, 1.0, 1.0), thickness: int = 2, line_type: int = cv2.LINE_AA, density: float = 1.0` | `cp.ndarray` | Draw text with supersampling |
| `add_label(image, text, org, font_face, font_scale, color, thickness, line_type, label_size, label_color, label_align, density)` | `image: cp.ndarray, text: str, org: tuple = (0, 0), font_face: int = cv2.FONT_HERSHEY_SIMPLEX, font_scale: float = 1.0, color: tuple = (1.0, 1.0, 1.0), thickness: int = 2, line_type: int = cv2.LINE_AA, label_size: int = 20, label_color: tuple = (0.0, 0.0, 0.0), label_align: str = "bottom", density: float = 1.0` | `cp.ndarray` | Add labeled banner |
| `create_rounded_mask(dsize, mask_offsets, radius_ratio, density, blur_size, sigma)` | `dsize: tuple = (512, 512), mask_offsets: tuple = (0.1, 0.1, 0.1, 0.1), radius_ratio: float = 0.1, density: int = 1, blur_size: int = 0, sigma: float = 1.0` | `cp.ndarray` | Create rounded rectangle mask |

### 🔨 Filter Module (`pixtreme.filter`)

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `gaussian_blur(image, kernel_size, sigma, kernel)` | `image: cp.ndarray, kernel_size: int, sigma: float, kernel: cp.ndarray or None = None` | `cp.ndarray` | Apply Gaussian blur |
| `get_gaussian_kernel(ksize, sigma)` | `ksize: int, sigma: float` | `cp.ndarray` | Generate 1D Gaussian kernel |
| `GaussianBlur(kernel_size, sigma)` | Class - `kernel_size: int, sigma: float` | Class instance | Gaussian blur filter class |

### 🔄 Transform Module (`pixtreme.transform`)

#### Image Operations
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `resize(src, dsize, fx, fy, interpolation)` | `src: cp.ndarray, dsize: tuple[int, int] or None = None, fx: float or None = None, fy: float or None = None, interpolation: int = INTER_AUTO` | `cp.ndarray` | Resize image with 11 interpolation methods |
| `affine_transform(src, M, dsize, flags)` | `src: cp.ndarray, M: cp.ndarray, dsize: tuple, flags: int = INTER_AUTO` | `cp.ndarray` | Apply affine transformation matrix |
| `get_inverse_matrix(M)` | `M: cp.ndarray` | `cp.ndarray` | Calculate inverse transformation matrix |
| `crop_from_kps(image, kps, size)` | `image: cp.ndarray, kps: cp.ndarray, size: int = 512` | `tuple[cp.ndarray, cp.ndarray]` | Crop image based on keypoints |
| `erode(image, kernel_size, kernel, border_value)` | `image: cp.ndarray, kernel_size: int, kernel: cp.ndarray or None = None, border_value: float = 0.0` | `cp.ndarray` | Morphological erosion |
| `create_erode_kernel(kernel_size)` | `kernel_size: int` | `cp.ndarray` | Create erosion kernel |
| `stack_images(images, axis)` | `images: list[cp.ndarray], axis: int = 0` | `cp.ndarray` | Stack multiple images |
| `subsample_image(image, factor)` | `image: cp.ndarray, factor: int` | `cp.ndarray` | Fast downsampling |
| `subsample_image_back(image, original_shape, factor)` | `image: cp.ndarray, original_shape: tuple, factor: int` | `cp.ndarray` | Upsample back to original |
| `tile_image(input_image, tile_size, overlap)` | `input_image: cp.ndarray, tile_size: int = 128, overlap: int = 16` | `tuple[list[cp.ndarray], tuple]` | Split image into tiles |
| `merge_tiles(tiles, original_shape, padded_shape, scale, tile_size, overlap)` | `tiles: list[cp.ndarray], original_shape: tuple[int, int, int], padded_shape: tuple[int, int, int], scale: int, tile_size: int = 128, overlap: int = 16` | `cp.ndarray` | Merge tiles with blending |
| `add_padding(input_image, patch_size, overlap)` | `input_image: cp.ndarray, patch_size: int = 128, overlap: int = 16` | `cp.ndarray` | Add padding for tiling |
| `create_gaussian_weights(size, sigma)` | `size: int, sigma: int` | `cp.ndarray` | Create Gaussian weight map |

#### Interpolation Constants
- `INTER_NEAREST` = 0 - Nearest neighbor
- `INTER_LINEAR` = 1 - Bilinear
- `INTER_CUBIC` = 2 - Bicubic
- `INTER_AREA` = 3 - Area-based resampling
- `INTER_LANCZOS4` = 4 - Lanczos (8x8)
- `INTER_AUTO` = 5 - Auto-select
- `INTER_MITCHELL` = 6 - Mitchell-Netravali
- `INTER_B_SPLINE` = 7 - B-spline
- `INTER_CATMULL_ROM` = 8 - Catmull-Rom
- `INTER_LANCZOS2` = 9 - Lanczos (4x4)
- `INTER_LANCZOS3` = 10 - Lanczos (6x6)

### 📁 I/O Module (`pixtreme.io`)

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `imread(input_path, dtype)` | `input_path: str, dtype: str = "fp32"` | `cp.ndarray` | Read image to GPU (defaults to float32, always returns BGR) |
| `imwrite(output_path, image, params)` | `output_path: str, image: cp.ndarray or np.ndarray, params: list or None = None` | `bool` | Write image with OpenCV-compatible params (JPEG quality, PNG compression, etc.) |
| `imencode(image, ext, params)` | `image: cp.ndarray, ext: str = ".png", params: list or None = None` | `bytes` | Encode image to memory with OpenCV-compatible params |
| `imdecode(src, dtype)` | `src: bytes, dtype: str = "fp32"` | `cp.ndarray` | Decode image from memory (always returns BGR) |
| `imshow(title, image, scale, is_rgb)` | `title: str, image: np.ndarray or cp.ndarray, scale: float = 1.0, is_rgb: bool = False` | `None` | Display image |
| `waitkey(delay)` | `delay: int` | `int` | Wait for keyboard input |
| `destroy_all_windows()` | - | `None` | Close all OpenCV windows |

### 🤖 Upscale Module (`pixtreme.upscale`)

| Class | Constructor Parameters | Method | Description |
|-------|------------------------|--------|-------------|
| `OnnxUpscaler` | `model_path: str or None = None, model_bytes: bytes or None = None, device_id: int = 0, provider_options: list or None = None` | `get(image: cp.ndarray) -> cp.ndarray` | ONNX Runtime upscaling |
| `TrtUpscaler` | `model_path: str or None = None, model_bytes: bytes or None = None, device_id: int = 0` | `get(image: cp.ndarray) -> cp.ndarray` | TensorRT optimized upscaling |
| `TorchUpscaler` | `model_path: str or None = None, model_bytes: bytes or None = None, device: str = "cuda"` | `get(image: cp.ndarray) -> cp.ndarray` | PyTorch native upscaling |

### 🔧 Utils Module (`pixtreme.utils`)

#### Type Conversions
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `to_uint8(image)` | `image: np.ndarray or cp.ndarray` | `np.ndarray or cp.ndarray` | Convert to 8-bit (0-255) |
| `to_uint16(image)` | `image: np.ndarray or cp.ndarray` | `np.ndarray or cp.ndarray` | Convert to 16-bit unsigned |
| `to_float16(image)` | `image: np.ndarray or cp.ndarray` | `np.ndarray or cp.ndarray` | Convert to 16-bit float |
| `to_float32(image, clip)` | `image: np.ndarray or cp.ndarray, clip: bool = True` | `np.ndarray or cp.ndarray` | Convert to 32-bit float. If clip=True, clamps to [0,1]. If clip=False, preserves values outside [0,1] for scene-referred workflows (ACES) |
| `to_float64(image)` | `image: np.ndarray or cp.ndarray` | `np.ndarray or cp.ndarray` | Convert to 64-bit float |
| `to_dtype(image, dtype)` | `image: np.ndarray or cp.ndarray, dtype: str` | `np.ndarray or cp.ndarray` | Convert to specified dtype |

#### Framework Interoperability
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `to_cupy(image)` | `image: np.ndarray or torch.Tensor or nvimgcodec.Image` | `cp.ndarray` | Convert to CuPy array |
| `to_numpy(image)` | `image: cp.ndarray or torch.Tensor or nvimgcodec.Image` | `np.ndarray` | Convert to NumPy array |
| `to_tensor(image, device)` | `image: np.ndarray or cp.ndarray, device: str or torch.device or None = None` | `torch.Tensor` | Convert to PyTorch tensor |

#### Batch Processing
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `guess_image_layout(image)` | `image: np.ndarray or cp.ndarray` | `str` | Detect image layout (HW, HWC, CHW, etc.) |
| `image_to_batch(image, size, scalefactor, mean, swap_rb, layout)` | `image: cp.ndarray, size: int or tuple[int, int] or None = None, scalefactor: float or None = None, mean: float or tuple or None = None, swap_rb: bool = True, layout: str = "HWC"` | `cp.ndarray` | Convert single image to batch |
| `images_to_batch(images, size, scalefactor, mean, swap_rb, layout)` | `images: list[cp.ndarray], size: int or tuple[int, int] or None = None, scalefactor: float or None = None, mean: float or tuple or None = None, swap_rb: bool = True, layout: str = "HWC"` | `cp.ndarray` | Convert images to batch format |
| `batch_to_images(batch, scalefactor, mean, swap_rb, layout)` | `batch: cp.ndarray, scalefactor: float or tuple or None = None, mean: float or tuple or None = None, swap_rb: bool = True, layout: str = "NCHW"` | `list[cp.ndarray]` | Convert batch to images |

#### Model Conversion
| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `check_torch_model(model_path)` | `model_path: str` | `bool` | Validate PyTorch model |
| `check_onnx_model(model_path)` | `model_path: str` | `bool` | Validate ONNX model |
| `torch_to_onnx(model_path, onnx_path, input_shape, opset_version, precision, dynamic_axes, device)` | `model_path: str, onnx_path: str, input_shape: tuple = (1,3,1080,1920), opset_version: int = 20, precision: str = "fp32", dynamic_axes: dict or None = None, device: str = "cuda"` | `None` | Convert PyTorch to ONNX |
| `onnx_to_onnx_dynamic(input_path, output_path, opset, irver)` | `input_path: str, output_path: str, opset: int or None = None, irver: int or None = None` | `None` | Add dynamic shape support |
| `onnx_to_trt(onnx_path, engine_path, precision, workspace)` | `onnx_path: str, engine_path: str, precision: str = "fp16", workspace: int = 1<<30` | `None` | Convert ONNX to TensorRT |
| `onnx_to_trt_dynamic_shape(onnx_path, engine_path, precision, workspace)` | `onnx_path: str, engine_path: str, precision: str = "fp16", workspace: int = 1<<30` | `None` | TensorRT with dynamic shapes |
| `onnx_to_trt_fixed_shape(onnx_path, engine_path, precision, workspace, input_shape)` | `onnx_path: str, engine_path: str, precision: str = "fp16", workspace: int = 1<<30, input_shape: tuple = (1,3,1080,1920)` | `None` | TensorRT with fixed shape |



## Performance Notes

- All color conversion operations use optimized CUDA kernels
- Supports both legal range (16-235) and full range (0-255) for video processing
- 10-bit precision support for professional video workflows
- Zero-copy tensor sharing via DLPack for framework interoperability
- Batch processing support for multiple images

## License

pixtreme is distributed under the MIT License (see [LICENSE](LICENSE)).

## Authors

minamik (@minamikik)

## Acknowledgments

sync.dev
