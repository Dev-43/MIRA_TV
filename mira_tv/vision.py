"""Vision and focus indicator analysis (BUILD_D.md D5). Owner: D.

Functions:
- indicator_diff(shot_focused, shot_other, bounds) -> Optional[float]
- detect_no_indicator(result, diff_min=4.0) -> List[Defect]
- annotate(png_bytes, bounds, color=(255, 0, 0)) -> bytes
"""
from __future__ import annotations

import io
from typing import Any, Dict, Optional, Tuple, Union
from PIL import Image, ImageChops, ImageStat


def _load_image(img: Union[bytes, Image.Image]) -> Image.Image:
    if isinstance(img, Image.Image):
        return img.convert("RGB")
    return Image.open(io.BytesIO(img)).convert("RGB")


def indicator_diff(
    shot_focused: Union[bytes, Image.Image],
    shot_other: Union[bytes, Image.Image],
    bounds: Dict[str, Any],
) -> Optional[float]:
    """Calculate mean absolute pixel difference across element's bounds region.

    Uses Pillow only:
    - If bounds are zero, negative, or invalid, returns None (skip with note).
    - Otherwise crops bounding box from both images, computes absolute difference,
      and returns mean absolute difference across RGB channels (0.0 to 255.0).
    """
    x = int(bounds.get("x", 0))
    y = int(bounds.get("y", 0))
    w = int(bounds.get("w", 0))
    h = int(bounds.get("h", 0))

    if w <= 0 or h <= 0:
        return None

    im_focused = _load_image(shot_focused)
    im_other = _load_image(shot_other)

    # Ensure bounds do not exceed image dimensions
    img_w, img_h = im_focused.size
    x0 = max(0, min(x, img_w - 1))
    y0 = max(0, min(y, img_h - 1))
    x1 = max(x0 + 1, min(x + w, img_w))
    y1 = max(y0 + 1, min(y + h, img_h))

    box = (x0, y0, x1, y1)
    crop_focused = im_focused.crop(box)
    crop_other = im_other.crop(box)

    # Compute absolute pixel difference using ImageChops
    diff = ImageChops.difference(crop_focused, crop_other)
    stat = ImageStat.Stat(diff)
    # Mean of RGB channels (0.0 to 255.0)
    means = stat.mean
    if not means:
        return 0.0
    return float(sum(means) / len(means))
