"""Vision and focus indicator analysis (BUILD_D.md D5). Owner: D.

Functions:
- indicator_diff(shot_focused, shot_other, bounds) -> Optional[float]
- detect_no_indicator(result, diff_min=4.0) -> List[Defect]
- annotate(png_bytes, bounds, color=(255, 0, 0)) -> bytes
"""
from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple, Union
from PIL import Image, ImageChops, ImageDraw, ImageStat

if TYPE_CHECKING:
    from .detectors import Defect


def _load_image(img: Union[bytes, Image.Image]) -> Image.Image:
    if isinstance(img, Image.Image):
        return img.convert("RGB")
    return Image.open(io.BytesIO(img)).convert("RGB")


def _normalize_bounds(bounds: Any) -> Optional[Tuple[int, int, int, int]]:
    if isinstance(bounds, (list, tuple)) and len(bounds) >= 4:
        x, y, w, h = int(bounds[0]), int(bounds[1]), int(bounds[2]), int(bounds[3])
    elif isinstance(bounds, dict):
        x = int(bounds.get("x", 0))
        y = int(bounds.get("y", 0))
        w = int(bounds.get("w", 0))
        h = int(bounds.get("h", 0))
    else:
        return None
    if w <= 0 or h <= 0:
        return None
    return (x, y, w, h)


def indicator_diff(
    shot_focused: Union[bytes, Image.Image],
    shot_other: Union[bytes, Image.Image],
    bounds: Union[Dict[str, Any], Tuple[int, int, int, int], Sequence[int]],
) -> Optional[float]:
    """Calculate mean absolute pixel difference across element's bounds region.

    Uses Pillow only:
    - If bounds are zero, negative, or invalid, returns None (skip with note).
    - Otherwise crops bounding box from both images, computes absolute difference,
      and returns mean absolute difference across RGB channels (0.0 to 255.0).
    """
    norm = _normalize_bounds(bounds)
    if norm is None:
        return None

    x, y, w, h = norm

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


def detect_no_indicator(
    result: Any,
    diff_min: float = 4.0,
) -> List[Defect]:
    """Detect elements where focused state is virtually indistinguishable from unfocused state.

    Compares the element's screenshot when focused against a neighbor element's screenshot.
    Returns list of Defect objects (type NO_FOCUS_INDICATOR) sorted deterministically.
    """
    from .detectors import Defect

    screen_nodes = [
        (node_id, data)
        for node_id, data in result.graph.nodes.items()
        if data.screen == result.screen
    ]
    if not screen_nodes:
        return []

    entry_id = screen_nodes[0][0]
    defects: List[Defect] = []

    for el_id, node_data in screen_nodes:
        shot_focused = result.shots.get(el_id)
        if not shot_focused:
            continue

        bounds = node_data.bounds
        if _normalize_bounds(bounds) is None:
            # Zero or invalid bounds: skip with note per BUILD_D.md
            continue

        # Find a neighbor on the same screen that has a screenshot
        neighbor_id: Optional[str] = None
        # Check outgoing edges first
        for key, dst in result.graph.edges.get(el_id, {}).items():
            if dst and dst != el_id and dst in result.shots:
                dst_data = result.graph.nodes.get(dst)
                if dst_data and dst_data.screen == result.screen:
                    neighbor_id = dst
                    break

        # Fallback to any other screen node with a screenshot
        if not neighbor_id:
            for other_id, other_data in screen_nodes:
                if other_id != el_id and other_id in result.shots:
                    neighbor_id = other_id
                    break

        if not neighbor_id:
            continue

        shot_other = result.shots[neighbor_id]
        diff = indicator_diff(shot_focused, shot_other, bounds)

        if diff is not None and diff < diff_min:
            path = result.graph.shortest_path(entry_id, el_id) or []
            defects.append(
                Defect(
                    type="NO_FOCUS_INDICATOR",
                    screen=result.screen,
                    element_id=el_id,
                    path=path,
                    detail=f"indicator diff {diff:.2f} < {diff_min:.1f} (compared with {neighbor_id})",
                )
            )

    defects.sort(key=lambda d: (d.screen, d.type, d.element_id))
    return defects


def annotate(
    png_bytes: bytes,
    bounds: Union[Dict[str, Any], Tuple[int, int, int, int], Sequence[int]],
    color: Union[Tuple[int, int, int], str] = (255, 0, 0),
) -> bytes:
    """Draw a 6 px rectangle around element bounds and downscale image to max width 1280.

    Color can be (R, G, B) or 'red' / 'green'.
    """
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")

    # Map color names if string
    outline_color: Tuple[int, int, int]
    if isinstance(color, str):
        c = color.strip().lower()
        if c == "green":
            outline_color = (0, 220, 100)
        else:  # default to red
            outline_color = (255, 60, 60)
    else:
        outline_color = (int(color[0]), int(color[1]), int(color[2]))

    norm = _normalize_bounds(bounds)
    if norm is not None:
        x, y, w, h = norm
        draw = ImageDraw.Draw(im)
        draw.rectangle([x, y, x + w, y + h], outline=outline_color, width=6)

    # Downscale to max width 1280
    max_width = 1280
    if im.width > max_width:
        ratio = max_width / im.width
        new_height = max(1, int(im.height * ratio))
        resample = getattr(Image, "Resampling", Image).LANCZOS
        im = im.resize((max_width, new_height), resample=resample)

    out = io.BytesIO()
    im.save(out, format="PNG")
    return out.getvalue()
