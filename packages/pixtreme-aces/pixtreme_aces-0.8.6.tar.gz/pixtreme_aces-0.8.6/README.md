# pixtreme-aces

ACES Color Management for pixtreme (OCIO ACES 1.2 Compliant)

## Overview

`pixtreme-aces` provides professional ACES color management functionality for VFX and color grading workflows. It implements the Academy Color Encoding System (ACES) 1.2 standard with full GPU acceleration.

## Features

- **ACES 1.2 Compliance**: Matrix values match OpenColorIO-Config-ACES standard
- **Industry Standard Workflow**: Compatible with Nuke, Houdini, Maya color pipelines
- **GPU Accelerated**: All operations run on CUDA-enabled GPUs via CuPy
- **Type Preservation**: Seamlessly works with both NumPy and CuPy arrays

## Installation

**Requirements**:
- Python >= 3.12
- CUDA Toolkit 12.x
- NVIDIA GPU with compute capability >= 6.0

```bash
pip install pixtreme-aces
```

Requires `pixtreme-core` and CUDA Toolkit 12.x.

## Quick Start

```python
import pixtreme_aces as aces
import pixtreme_core as px

# Read display-referred image (Rec.709/sRGB)
img = px.imread("input.jpg")

# Convert to ACES2065-1 (scene-referred, linear AP0)
aces_img = aces.rec709_to_aces2065_1(img)

# Work in ACES color space
# ... color grading, compositing, etc.

# Convert back to Rec.709 for display
output = aces.aces2065_1_to_rec709(aces_img)

px.imwrite("output.jpg", output)
```

## Color Space Conversions

### ACES Working Spaces

- **ACES2065-1**: Archive format (linear AP0, wide gamut)
- **ACEScg**: CG/VFX working space (linear AP1)
- **ACEScct**: Grading space (log-encoded AP1)

```python
# ACES2065-1 ↔ ACEScg
acescg = aces.aces2065_1_to_acescg(aces_img)
aces_img = aces.acescg_to_aces2065_1(acescg)

# ACES2065-1 ↔ ACEScct
acescct = aces.aces2065_1_to_acescct(aces_img)
aces_img = aces.acescct_to_aces2065_1(acescct)
```

## References

- [ACES Central](https://acescentral.com)
- [ACES Technical Documentation](https://docs.acescentral.com)
- [OpenColorIO-Config-ACES](https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES)
- SMPTE ST 2065-1: ACES2065-1 specification

## License

MIT License - see LICENSE file for details.

ACES® is a trademark of the Academy of Motion Picture Arts and Sciences (A.M.P.A.S.).
This software is not endorsed by A.M.P.A.S.

## Links

- Repository: https://github.com/sync-dev-org/pixtreme
