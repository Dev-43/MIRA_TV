"""Replay driver over a fixture folder (BUILD_D.md D2). Owner: D. NOT IMPLEMENTED YET.
fixture.json: package, entry{screen: element}, elements{id: screen,bounds,edges,screenshot}.
"""
from __future__ import annotations

from typing import Optional

from .driver import Driver, FocusEvent


class FixtureDriver(Driver):
    def __init__(self, fixture_dir: str):
        raise NotImplementedError("D2: FixtureDriver")

    def reset_to_screen(self, screen_cfg: dict) -> FocusEvent:
        raise NotImplementedError

    def press(self, key: str) -> Optional[FocusEvent]:
        raise NotImplementedError

    def screenshot(self) -> bytes:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError
