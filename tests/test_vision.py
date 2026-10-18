"""Tests for vision and focus indicator diff calculation (Task D5)."""
from pathlib import Path
from PIL import Image, ImageDraw

from mira_tv.vision import annotate, detect_no_indicator, indicator_diff


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


def test_detect_no_indicator_clean_and_bugs() -> None:
    from mira_tv.explore import explore_screen
    from mira_tv.fixture_driver import FixtureDriver

    home_cfg = {
        "screen": "home",
        "entry_steps": [],
        "exit_targets": ["home.drawer.1"],
        "max_probes": 80,
        "max_depth": 8,
    }

    # 1. Clean synthetic fixture -> 0 defects
    clean_driver = FixtureDriver(Path("fixtures/synthetic_clean"))
    clean_result = explore_screen(clean_driver, home_cfg)
    clean_no_ind = detect_no_indicator(clean_result, diff_min=4.0)
    assert clean_no_ind == []

    # 2. Buggy synthetic fixture -> detects NO_FOCUS_INDICATOR:home.card.2
    buggy_driver = FixtureDriver(Path("fixtures/synthetic_bugs"))
    buggy_result = explore_screen(buggy_driver, home_cfg)
    buggy_no_ind = detect_no_indicator(buggy_result, diff_min=4.0)
    assert len(buggy_no_ind) == 1
    d = buggy_no_ind[0]
    assert d.id == "NO_FOCUS_INDICATOR:home.card.2"
    assert d.type == "NO_FOCUS_INDICATOR"
    assert d.screen == "home"
    assert d.element_id == "home.card.2"
    assert len(d.path) > 0
    assert "indicator diff" in d.detail


def test_annotate_downscales_and_draws() -> None:
    import io

    # Create 1920x1080 test image
    orig = Image.new("RGB", (1920, 1080), (20, 20, 20))
    buf = io.BytesIO()
    orig.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # Annotate with red rectangle
    bounds = {"x": 200, "y": 200, "w": 400, "h": 300}
    ann_bytes = annotate(png_bytes, bounds, color="red")

    ann_im = Image.open(io.BytesIO(ann_bytes))
    assert ann_im.width == 1280
    assert ann_im.height == 720  # proportional 16:9

    # Annotate already small image (800x600) -> stays 800 width
    small = Image.new("RGB", (800, 600), (30, 30, 30))
    small_buf = io.BytesIO()
    small.save(small_buf, format="PNG")
    small_ann = annotate(small_buf.getvalue(), (10, 10, 50, 50), color="green")
    small_im = Image.open(io.BytesIO(small_ann))
    assert small_im.width == 800
    assert small_im.height == 600

    # Annotate with zero bounds should not raise
    zero_ann = annotate(png_bytes, (0, 0, 0, 0))
    zero_im = Image.open(io.BytesIO(zero_ann))
    assert zero_im.width == 1280
