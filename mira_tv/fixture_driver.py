"""Replay driver over a fixture folder (BUILD_D.md D2). Owner: D.

fixture.json: package, entry{screen: element}, elements{id: screen, bounds, edges, screenshot}.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, Optional, Union

from .driver import Driver, DriverError, FocusEvent


class FixtureDriver(Driver):
    def __init__(self, fixture_dir: Union[str, Path]):
        self.fixture_dir = Path(fixture_dir)
        fixture_file = self.fixture_dir / "fixture.json"
        if not fixture_file.exists():
            raise DriverError(f"fixture.json not found in {self.fixture_dir}")

        try:
            with open(fixture_file, "r", encoding="utf-8") as f:
                self.data: Dict[str, Any] = json.load(f)
        except Exception as e:
            raise DriverError(f"Failed to load fixture.json: {e}") from e

        self.elements: Dict[str, Any] = self.data.get("elements", {})
        self.entry: Dict[str, str] = self.data.get("entry", {})
        self.current_element: Optional[str] = None
        self._seq: int = 0

    def _event_for_element(self, element_id: str) -> FocusEvent:
        if element_id not in self.elements:
            raise DriverError(f"Element '{element_id}' not found in fixture elements")
        el = self.elements[element_id]
        b = el.get("bounds", {"x": 0, "y": 0, "w": 0, "h": 0})
        return FocusEvent(
            seq=self._seq,
            screen=el.get("screen", ""),
            element_id=element_id,
            bounds=(int(b.get("x", 0)), int(b.get("y", 0)), int(b.get("w", 0)), int(b.get("h", 0))),
            ts=int(time.time() * 1000),
        )

    def reset_to_screen(self, screen_cfg: dict) -> FocusEvent:
        screen = screen_cfg.get("screen")
        if not screen:
            raise DriverError("screen_cfg missing 'screen'")

        entry_el = self.entry.get(screen)
        if not entry_el:
            raise DriverError(f"No entry element defined in fixture for screen '{screen}'")

        if entry_el not in self.elements:
            raise DriverError(f"Entry element '{entry_el}' missing from fixture elements")

        self._seq = 1
        self.current_element = entry_el

        # Replay entry steps
        for step in screen_cfg.get("entry_steps", []):
            ev = self.press(step)
            # If a step resulted in a new focus event, current_element is updated

        return self._event_for_element(self.current_element)

    def press(self, key: str) -> Optional[FocusEvent]:
        if not self.current_element:
            raise DriverError("Cannot press key: driver has not been reset to a screen")

        curr = self.elements.get(self.current_element)
        if not curr:
            raise DriverError(f"Current element '{self.current_element}' not found in fixture")

        edges = curr.get("edges", {})
        next_id = edges.get(key)

        # None or same element = focus did not change
        if next_id is None or next_id == self.current_element:
            return None

        if next_id not in self.elements:
            raise DriverError(f"Target element '{next_id}' via key '{key}' not in fixture")

        self.current_element = next_id
        self._seq += 1
        return self._event_for_element(self.current_element)

    def screenshot(self) -> bytes:
        if not self.current_element:
            raise DriverError("Cannot capture screenshot: driver has not been reset to a screen")

        curr = self.elements.get(self.current_element)
        if not curr:
            raise DriverError(f"Current element '{self.current_element}' not found in fixture")

        rel_path = curr.get("screenshot")
        if not rel_path:
            raise DriverError(f"No screenshot path specified for element '{self.current_element}'")

        shot_path = self.fixture_dir / rel_path
        if not shot_path.exists():
            raise DriverError(f"Screenshot file '{shot_path}' does not exist")

        try:
            return shot_path.read_bytes()
        except OSError as e:
            raise DriverError(f"Failed to read screenshot '{shot_path}': {e}") from e

    def swap_fixture(self, new_fixture_dir: Union[str, Path]) -> None:
        """Swap fixture source directory (e.g., from synthetic_bugs to synthetic_clean)."""
        self.fixture_dir = Path(new_fixture_dir)
        fixture_file = self.fixture_dir / "fixture.json"
        if not fixture_file.exists():
            raise DriverError(f"fixture.json not found in {self.fixture_dir}")
        try:
            with open(fixture_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            raise DriverError(f"Failed to load fixture.json from {self.fixture_dir}: {e}") from e

        self.elements = self.data.get("elements", {})
        self.entry = self.data.get("entry", {})

    def close(self) -> None:
        self.current_element = None
