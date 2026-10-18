"""Generate fixtures/synthetic_clean and fixtures/synthetic_bugs with Pillow (BUILD_D.md D2).

Owner: D.
Generates:
- fixtures/synthetic_clean/fixture.json + shots/*.png
- fixtures/synthetic_bugs/fixture.json + shots/*.png
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1920
HEIGHT = 1080
BG_COLOR = (18, 24, 38)
PANEL_COLOR = (30, 41, 59)
TEXT_COLOR = (240, 240, 240)
BORDER_COLOR = (0, 229, 255)  # Cyan 6px focus border
BORDER_WIDTH = 6

HOME_ELEMENTS = {
    "home.drawer.1": {
        "screen": "home",
        "bounds": {"x": 60, "y": 80, "w": 140, "h": 60},
        "label": "Menu",
    },
    "home.drawer.2": {
        "screen": "home",
        "bounds": {"x": 60, "y": 160, "w": 140, "h": 60},
        "label": "Settings",
    },
    "home.hero.1": {
        "screen": "home",
        "bounds": {"x": 260, "y": 80, "w": 1560, "h": 360},
        "label": "Hero Feature Banner",
    },
    "home.card.1": {
        "screen": "home",
        "bounds": {"x": 260, "y": 480, "w": 340, "h": 220},
        "label": "Movie 1",
    },
    "home.card.2": {
        "screen": "home",
        "bounds": {"x": 640, "y": 480, "w": 340, "h": 220},
        "label": "Movie 2",
    },
    "home.card.3": {
        "screen": "home",
        "bounds": {"x": 1020, "y": 480, "w": 340, "h": 220},
        "label": "Movie 3",
    },
    "home.card.4": {
        "screen": "home",
        "bounds": {"x": 1400, "y": 480, "w": 340, "h": 220},
        "label": "Movie 4",
    },
    "home.card.5": {
        "screen": "home",
        "bounds": {"x": 1400, "y": 740, "w": 340, "h": 220},
        "label": "Movie 5",
    },
}

DETAILS_ELEMENTS = {
    "details.btn.play": {
        "screen": "details",
        "bounds": {"x": 260, "y": 400, "w": 240, "h": 80},
        "label": "Play Movie",
    },
    "details.btn.addlist": {
        "screen": "details",
        "bounds": {"x": 540, "y": 400, "w": 240, "h": 80},
        "label": "Add to List",
    },
    "details.btn.trailer": {
        "screen": "details",
        "bounds": {"x": 820, "y": 400, "w": 240, "h": 80},
        "label": "Watch Trailer",
    },
    "details.btn.back": {
        "screen": "details",
        "bounds": {"x": 260, "y": 200, "w": 180, "h": 60},
        "label": "< Back",
    },
}


def _get_clean_edges() -> Dict[str, Dict[str, Any]]:
    return {
        "home.drawer.1": {
            "UP": None,
            "DOWN": "home.drawer.2",
            "LEFT": None,
            "RIGHT": "home.hero.1",
            "CENTER": None,
            "BACK": None,
        },
        "home.drawer.2": {
            "UP": "home.drawer.1",
            "DOWN": None,
            "LEFT": None,
            "RIGHT": "home.card.1",
            "CENTER": None,
            "BACK": None,
        },
        "home.hero.1": {
            "UP": None,
            "DOWN": "home.card.1",
            "LEFT": "home.drawer.1",
            "RIGHT": None,
            "CENTER": "details.btn.play",
            "BACK": None,
        },
        "home.card.1": {
            "UP": "home.hero.1",
            "DOWN": None,
            "LEFT": "home.drawer.2",
            "RIGHT": "home.card.2",
            "CENTER": "details.btn.play",
            "BACK": "home.drawer.1",
        },
        "home.card.2": {
            "UP": "home.hero.1",
            "DOWN": None,
            "LEFT": "home.card.1",
            "RIGHT": "home.card.3",
            "CENTER": "details.btn.play",
            "BACK": "home.drawer.1",
        },
        "home.card.3": {
            "UP": "home.hero.1",
            "DOWN": None,
            "LEFT": "home.card.2",
            "RIGHT": "home.card.4",
            "CENTER": "details.btn.play",
            "BACK": "home.drawer.1",
        },
        "home.card.4": {
            "UP": "home.hero.1",
            "DOWN": "home.card.5",
            "LEFT": "home.card.3",
            "RIGHT": None,
            "CENTER": "details.btn.play",
            "BACK": "home.drawer.1",
        },
        "home.card.5": {
            "UP": "home.card.4",
            "DOWN": None,
            "LEFT": "home.card.3",
            "RIGHT": None,
            "CENTER": "details.btn.play",
            "BACK": "home.drawer.1",
        },
        "details.btn.play": {
            "UP": "details.btn.back",
            "DOWN": None,
            "LEFT": None,
            "RIGHT": "details.btn.addlist",
            "CENTER": None,
            "BACK": "home.hero.1",
        },
        "details.btn.addlist": {
            "UP": "details.btn.back",
            "DOWN": None,
            "LEFT": "details.btn.play",
            "RIGHT": "details.btn.trailer",
            "CENTER": None,
            "BACK": "home.hero.1",
        },
        "details.btn.trailer": {
            "UP": "details.btn.back",
            "DOWN": None,
            "LEFT": "details.btn.addlist",
            "RIGHT": None,
            "CENTER": None,
            "BACK": "home.hero.1",
        },
        "details.btn.back": {
            "UP": None,
            "DOWN": "details.btn.play",
            "LEFT": None,
            "RIGHT": None,
            "CENTER": "home.hero.1",
            "BACK": "home.hero.1",
        },
    }


def _get_buggy_edges() -> Dict[str, Dict[str, Any]]:
    edges = _get_clean_edges()
    # Bug 1: UNREACHABLE details.btn.addlist (disconnect inbound edges to it)
    # details.btn.play RIGHT jumps past addlist directly to trailer
    edges["details.btn.play"]["RIGHT"] = "details.btn.trailer"
    edges["details.btn.trailer"]["LEFT"] = "details.btn.play"
    edges["details.btn.back"]["DOWN"] = "details.btn.play"

    # Bug 2: TRAP home.card.4 and home.card.5 (pocket cannot exit back to home.drawer.1)
    # Entering card.4: LEFT is None, UP is None, BACK is None or card.5.
    edges["home.card.4"]["LEFT"] = None
    edges["home.card.4"]["UP"] = None
    edges["home.card.4"]["BACK"] = None
    edges["home.card.4"]["CENTER"] = None
    edges["home.card.5"]["LEFT"] = None
    edges["home.card.5"]["BACK"] = None
    edges["home.card.5"]["CENTER"] = None
    # Now from home.card.4/5, user can only toggle UP/DOWN between card.4 and card.5, but can never reach home.drawer.1!

    return edges


def render_screen(screen: str, focused_id: str | None, is_buggy: bool = False) -> Image.Image:
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    elements = HOME_ELEMENTS if screen == "home" else DETAILS_ELEMENTS

    # Draw header text
    title = "MIRA TV — HOME SCREEN" if screen == "home" else "MIRA TV — DETAILS SCREEN"
    draw.text((60, 20), title, fill=(160, 175, 200))

    # Render each element
    for el_id, data in elements.items():
        b = data["bounds"]
        x0, y0 = b["x"], b["y"]
        x1, y1 = x0 + b["w"], y0 + b["h"]

        # Base panel
        draw.rectangle([x0, y0, x1, y1], fill=PANEL_COLOR, outline=(50, 65, 85), width=2)
        draw.text((x0 + 15, y0 + 15), data["label"], fill=TEXT_COLOR)
        draw.text((x0 + 15, y0 + 40), el_id, fill=(120, 140, 165))

        # Focus indicator
        if el_id == focused_id:
            # Bug 3: NO_FOCUS_INDICATOR for home.card.2 in buggy mode
            if is_buggy and el_id == "home.card.2":
                pass  # Skip drawing focus border to plant NO_FOCUS_INDICATOR
            else:
                # Draw thick colored focus border
                draw.rectangle([x0, y0, x1, y1], outline=BORDER_COLOR, width=BORDER_WIDTH)

    return im


def generate_fixture(out_dir: Path, is_buggy: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    shots_dir = out_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    elements_dict = {}
    edges_map = _get_buggy_edges() if is_buggy else _get_clean_edges()

    all_elements = {**HOME_ELEMENTS, **DETAILS_ELEMENTS}

    for el_id, data in all_elements.items():
        screen = data["screen"]
        shot_filename = f"shots/{el_id}.png"
        shot_path = out_dir / shot_filename

        # Render screenshot when this element is focused
        img = render_screen(screen, focused_id=el_id, is_buggy=is_buggy)
        img.save(shot_path, format="PNG")

        elements_dict[el_id] = {
            "screen": screen,
            "bounds": data["bounds"],
            "edges": edges_map[el_id],
            "screenshot": shot_filename,
        }

    fixture_data = {
        "package": "com.amazon.mira.synthetic",
        "entry": {
            "home": "home.drawer.1",
            "details": "details.btn.play",
        },
        "elements": elements_dict,
    }

    with open(out_dir / "fixture.json", "w", encoding="utf-8") as f:
        json.dump(fixture_data, f, indent=2)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    clean_dir = repo_root / "fixtures" / "synthetic_clean"
    bugs_dir = repo_root / "fixtures" / "synthetic_bugs"

    print("Generating fixtures/synthetic_clean...")
    generate_fixture(clean_dir, is_buggy=False)
    print("Generating fixtures/synthetic_bugs...")
    generate_fixture(bugs_dir, is_buggy=True)
    print("Synthetic fixtures generated successfully.")


if __name__ == "__main__":
    main()
