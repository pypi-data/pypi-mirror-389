# pixtreme-draw

GPU-accelerated drawing primitives for pixtreme

## Overview

`pixtreme-draw` provides high-performance drawing operations for rendering shapes, text, and masks directly on GPU memory.

## Features

- **Shape Drawing**: Circles, rectangles with anti-aliasing
- **Text Rendering**: GPU-accelerated text with custom fonts
- **Mask Generation**: Rounded masks for compositing
- **Zero-Copy**: Direct GPU memory operations via CuPy

## Installation

**Requirements**:
- Python >= 3.12
- CUDA Toolkit 12.x
- NVIDIA GPU with compute capability >= 6.0

```bash
pip install pixtreme-draw
```

Requires `pixtreme-core`, `pixtreme-filter`, and CUDA Toolkit 12.x.

## Quick Start

```python
import pixtreme_draw as pd
import pixtreme_core as px

# Read image
img = px.imread("input.jpg")

# Draw filled circle
img = pd.circle(img, center_x=256, center_y=256, radius=100, color=(0.0, 1.0, 0.0))

# Draw filled rectangle
img = pd.rectangle(img, top_left_x=100, top_left_y=100, bottom_right_x=300, bottom_right_y=300, color=(1.0, 0.0, 0.0))

# Add text label with background
img = pd.add_label(img, text="Hello World", org=(50, 50), color=(1.0, 1.0, 1.0))

# Save result
px.imwrite("output.jpg", img)
```

## API

### Shape Drawing

```python
# Circle (filled)
pd.circle(image, center_x, center_y, radius, color=(1.0, 1.0, 1.0))

# Rectangle (filled)
pd.rectangle(image, top_left_x, top_left_y, bottom_right_x, bottom_right_y, color=(1.0, 1.0, 1.0))
```

### Text Rendering

```python
# Simple text
pd.put_text(image, text, org, font_face=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1.0, color=(1.0, 1.0, 1.0), thickness=2)

# Text with background label
pd.add_label(image, text, org=(0, 0), font_scale=1.0, color=(1.0, 1.0, 1.0), label_color=(0.0, 0.0, 0.0))
```

### Mask Generation

```python
# Rounded mask for compositing
mask = pd.create_rounded_mask(dsize=(512, 512), radius_ratio=0.1, blur_size=0, sigma=1.0)
```

## License

MIT License - see LICENSE file for details.

## Links

- Repository: https://github.com/sync-dev-org/pixtreme
