"""Tests for vision and focus indicator diff calculation (Task D5)."""
from pathlib import Path
from PIL import Image, ImageDraw

from mira_tv.vision import indicator_diff


def test_indicator_diff_zero_or_invalid_bounds() -> None:
    im1 = Image.new("RGB", (100, 100), (0, 0, 0))
    im2 = Image.new("RGB", (100, 100), (255, 255, 255))

    # All zeros
    assert indicator_diff(im1, im2, {"x": 0, "y": 0, "w": 0, "h": 0}) is None
    # Negative width
    assert indicator_diff(im1, im2, {"x": 10, "y": 10, "w": -5, "h": 20}) is None
    # Zero height
    assert indicator_diff(im1, im2, {"x": 10, "y": 10, "w": 20, "h": 0}) is None


def test_indicator_diff_identical_images() -> None:
    im1 = Image.new("RGB", (200, 200), (40, 50, 60))
    im2 = Image.new("RGB", (200, 200), (40, 50, 60))
    bounds = {"x": 20, "y": 20, "w": 50, "h": 50}

    diff = indicator_diff(im1, im2, bounds)
    assert diff is not None
    assert diff == 0.0


def test_indicator_diff_known_difference() -> None:
    # 100x100 images: im1 is black (0,0,0), im2 has a 50x50 white square (255,255,255)
    im1 = Image.new("RGB", (100, 100), (0, 0, 0))
    im2 = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im2)
    draw.rectangle([10, 10, 60, 60], fill=(255, 255, 255))

    bounds = {"x": 10, "y": 10, "w": 50, "h": 50}
    diff = indicator_diff(im1, im2, bounds)
    assert diff is not None
    # In the cropped 50x50 region, pixels are 255 in im2 and 0 in im1 -> mean diff is ~255.0
    assert diff > 250.0


def test_indicator_diff_synthetic_fixture_shots() -> None:
    clean_shots = Path("fixtures/synthetic_clean/shots")
    buggy_shots = Path("fixtures/synthetic_bugs/shots")

    # In clean fixture, home.card.1 focused has cyan border, home.card.2 focused has no cyan border on card.1
    card1_focused = clean_shots / "home.card.1.png"
    card2_focused = clean_shots / "home.card.2.png"
    card1_bounds = {"x": 260, "y": 480, "w": 340, "h": 220}

    clean_diff = indicator_diff(
        card1_focused.read_bytes(),
        card2_focused.read_bytes(),
        card1_bounds,
    )
    assert clean_diff is not None
    assert clean_diff > 4.0  # Well above the 4.0 threshold

    # In buggy fixture, home.card.2 has planted NO_FOCUS_INDICATOR
    # Its screenshot when focused (home.card.2.png) is identical in its bounds to when card.1 is focused
    buggy_card2_focused = buggy_shots / "home.card.2.png"
    buggy_card1_focused = buggy_shots / "home.card.1.png"
    card2_bounds = {"x": 640, "y": 480, "w": 340, "h": 220}

    buggy_diff = indicator_diff(
        buggy_card2_focused.read_bytes(),
        buggy_card1_focused.read_bytes(),
        card2_bounds,
    )
    assert buggy_diff is not None
    assert buggy_diff < 0.5  # Virtually 0.0 because border was omitted
