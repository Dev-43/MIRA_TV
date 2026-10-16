"""Live exploration session recorder (BUILD_D.md D9). Owner: D.

Runs explore over every screen in scenario.json and outputs a fixture folder:
- <out_dir>/fixture.json
- <out_dir>/shots/<element_id>.png
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from .driver import Driver
from .explore import explore_screen


def record_fixture(driver: Driver, scenario: Dict[str, Any], out_dir: Union[str, Path]) -> Dict[str, Any]:
    out_path = Path(out_dir)
    shots_dir = out_path / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    package = scenario.get("package", "com.amazon.mira.recorded")
    entry_map: Dict[str, str] = {}
    elements_map: Dict[str, Any] = {}

    screens = scenario.get("screens", [])
    if not screens:
        # Fallback single screen default
        screens = [{"screen": "home", "entry_steps": [], "max_probes": 80, "max_depth": 8}]

    all_keys = ["UP", "DOWN", "LEFT", "RIGHT", "CENTER", "BACK"]

    for screen_cfg in screens:
        screen_name = screen_cfg.get("screen", "home")
        result = explore_screen(driver, screen_cfg)

        # Save screenshots
        for el_id, shot_bytes in result.shots.items():
            shot_file = shots_dir / f"{el_id}.png"
            shot_file.write_bytes(shot_bytes)

        # Record nodes and edges
        for el_id, node in result.graph.nodes.items():
            if node.screen == screen_name and screen_name not in entry_map:
                entry_map[screen_name] = el_id

            edges_dict: Dict[str, Any] = {}
            node_edges = result.graph.edges.get(el_id, {})
            for k in all_keys:
                edges_dict[k] = node_edges.get(k, None)

            elements_map[el_id] = {
                "screen": node.screen,
                "bounds": {
                    "x": node.bounds[0],
                    "y": node.bounds[1],
                    "w": node.bounds[2],
                    "h": node.bounds[3],
                },
                "edges": edges_dict,
                "screenshot": f"shots/{el_id}.png",
            }

    fixture_data = {
        "package": package,
        "entry": entry_map,
        "elements": elements_map,
    }

    with open(out_path / "fixture.json", "w", encoding="utf-8") as f:
        json.dump(fixture_data, f, indent=2)

    return fixture_data
