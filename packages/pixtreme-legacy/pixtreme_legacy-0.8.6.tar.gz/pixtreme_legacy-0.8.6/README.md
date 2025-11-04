# pixtreme-legacy

**⚠️ Legacy Compatibility Package**: This package provides `_cp` functions removed from pixtreme v0.5.2+.

## Status

- **Maintenance Mode**: Functions migrated from main pixtreme package in v0.5.2
- **Note**: v0.5.1 was broken; use v0.5.2 or later
- **Recommendation**: Migrate to standard functions (without `_cp` suffix) when possible

## Purpose

This package provides backward compatibility for `_cp` functions that were removed from the main `pixtreme` package in v0.5.1. It contains the following functions:

- `apply_lut_cp` - Apply 3D LUT with CuPy implementation
- `uyvy422_to_ycbcr444_cp` - Convert UYVY422 to YCbCr444
- `ndi_uyvy422_to_ycbcr444_cp` - Convert NDI UYVY422 to YCbCr444
- `yuv420p_to_ycbcr444_cp` - Convert YUV420 to YCbCr444
- `yuv422p10le_to_ycbcr444_cp` - Convert YUV422p10le to YCbCr444

## Installation

**Requirements**:
- Python >= 3.12
- CUDA Toolkit 12.x
- NVIDIA GPU with compute capability >= 6.0

```bash
pip install pixtreme-legacy
```

## Usage

```python
from pixtreme_legacy import apply_lut_cp

# No warnings - clean compatibility layer
result = apply_lut_cp(image, lut)
```

**Note**: This package depends on `pixtreme>=0.6.0` for common utilities (`to_float32`, `resize`, etc.).

## Migration Guide

Replace `_cp` functions with their standard equivalents:

### Before (deprecated)
```python
from pixtreme import apply_lut_cp
result = apply_lut_cp(image, lut, interpolation=0)
```

### After (recommended)
```python
from pixtreme import apply_lut
result = apply_lut(image, lut, interpolation=0)
```

## Why were _cp functions deprecated?

The `_cp` suffix originally indicated "CuPy native" implementations, as opposed to CUDA kernel implementations. However:

1. **Redundancy**: Both implementations exist in the main functions now
2. **Confusion**: Users don't need to choose between implementations
3. **Maintenance**: Duplicate APIs increase maintenance burden

The standard functions (without `_cp`) now automatically select the best implementation.

## Timeline

- **v0.4.0**: `_cp` functions available without warnings
- **v0.5.0**: `_cp` functions deprecated with warnings, `pixtreme-legacy` package created
- **v0.5.1**: **BROKEN** - Attempted `_cp` function removal but incomplete (do not use)
- **v0.5.2**: `_cp` functions **fully removed from main package**, migrated to `pixtreme-legacy` without warnings
- **v0.6.0**: Main `pixtreme` package split into modular packages (`pixtreme-core`, `pixtreme-aces`, `pixtreme-filter`, `pixtreme-draw`, `pixtreme-upscale`)

## License

MIT License (same as pixtreme)
