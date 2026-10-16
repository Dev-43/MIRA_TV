"""Driver interface. Live (AdbDriver) and replay (FixtureDriver) implement the same methods."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


class DriverError(Exception):
    """Raised when a driver cannot complete an operation (no device, timeout, bad fixture)."""


@dataclass(frozen=True)
class FocusEvent:
    seq: int
    screen: str
    element_id: str
    bounds: Tuple[int, int, int, int]  # x, y, w, h in screenshot pixels; (0,0,0,0) = unknown
    ts: int


class Driver(ABC):
    @abstractmethod
    def reset_to_screen(self, screen_cfg: dict) -> FocusEvent:
        """Relaunch (live) or jump to entry (fixture), replay entry_steps, return first focus event."""

    @abstractmethod
    def press(self, key: str) -> Optional[FocusEvent]:
        """Press one key, wait for focus to settle, return the new focus event or None if focus did not change."""

    @abstractmethod
    def screenshot(self) -> bytes:
        """PNG bytes of the current screen."""

    @abstractmethod
    def close(self) -> None:
        """Release resources."""
