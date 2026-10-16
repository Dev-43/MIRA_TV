"""Live ADB driver (BUILD_D.md D2). Owner: D. NOT IMPLEMENTED YET.

Requirements: subprocess adb with 20 s timeouts; keys via `adb shell input keyevent <code>`;
screenshots via `adb exec-out screencap -p`; background thread reading `adb logcat -v raw`;
relaunch = `am force-stop <package>` then `am start -n <package>/<launch_activity>`;
reset last-seen seq to 0 on relaunch. Unit-test only with a mocked subprocess.
"""
from __future__ import annotations

from typing import Optional

from .driver import Driver, FocusEvent


class AdbDriver(Driver):
    def __init__(self, config, scenario):
        raise NotImplementedError("D2: AdbDriver")

    def reset_to_screen(self, screen_cfg: dict) -> FocusEvent:
        raise NotImplementedError

    def press(self, key: str) -> Optional[FocusEvent]:
        raise NotImplementedError

    def screenshot(self) -> bytes:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError
