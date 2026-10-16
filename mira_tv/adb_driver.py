"""Live ADB driver (BUILD_D.md D2). Owner: D.

Requirements:
- Subprocess adb with 20 s timeouts.
- Keys via `adb shell input keyevent <code>`.
- Screenshots via `adb exec-out screencap -p`.
- Background thread reading `adb logcat -v raw` lines into a queue and parsing them with `telemetry.py`.
- Relaunch = `am force-stop <package>` then `am start -n <package>/<launch_activity>`, wait `MIRA_RESET_WAIT_MS`.
- On relaunch, reset the last-seen `seq` to 0 (the app restarts its counter).
- Unit-tested only with a mocked subprocess.
"""
from __future__ import annotations

import queue
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

from .config import Config
from .driver import Driver, DriverError, FocusEvent
from .keys import keycode
from .telemetry import parse_line

ADB_TIMEOUT_S = 20.0


class AdbDriver(Driver):
    def __init__(self, config: Config, scenario: Dict[str, Any]):
        self.config = config
        self.scenario = scenario
        self.package = scenario.get("package", "")
        self.launch_activity = scenario.get("launch_activity", "")
        self._last_seq = 0
        self._curr_event: Optional[FocusEvent] = None
        self._events_queue: queue.Queue[FocusEvent] = queue.Queue()
        self._stop_logcat = threading.Event()
        self._logcat_proc: Optional[subprocess.Popen] = None
        self._logcat_thread: Optional[threading.Thread] = None

        self._start_logcat_stream()

    def _adb_cmd(self, *args: str) -> List[str]:
        cmd = [self.config.adb_path]
        if self.config.adb_serial:
            cmd.extend(["-s", self.config.adb_serial])
        cmd.extend(args)
        return cmd

    def _run_adb(self, *args: str, timeout: float = ADB_TIMEOUT_S) -> subprocess.CompletedProcess:
        cmd = self._adb_cmd(*args)
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise DriverError(f"ADB command timed out after {timeout}s: {' '.join(cmd)}") from e
        except OSError as e:
            raise DriverError(f"Failed to execute ADB command: {e}") from e

    def _start_logcat_stream(self) -> None:
        cmd = self._adb_cmd("logcat", "-v", "raw", "-s", "ReactNativeJS:V")
        try:
            self._logcat_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except OSError as e:
            raise DriverError(f"Failed to start logcat subprocess: {e}") from e

        def _reader():
            if not self._logcat_proc or not self._logcat_proc.stdout:
                return
            for line in self._logcat_proc.stdout:
                if self._stop_logcat.is_set():
                    break
                ev = parse_line(line)
                if ev is not None:
                    self._events_queue.put(ev)

        self._logcat_thread = threading.Thread(target=_reader, daemon=True)
        self._logcat_thread.start()

    def _drain_queue(self) -> List[FocusEvent]:
        events = []
        while not self._events_queue.empty():
            try:
                events.append(self._events_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def reset_to_screen(self, screen_cfg: dict) -> FocusEvent:
        if not self.package:
            raise DriverError("Cannot reset: scenario missing 'package'")

        activity = self.launch_activity
        if not activity:
            activity = f"{self.package}.MainActivity"
        component = f"{self.package}/{activity}" if "/" not in activity else activity

        # am force-stop <package>
        res = self._run_adb("shell", "am", "force-stop", self.package)
        if res.returncode != 0:
            raise DriverError(f"Failed to force-stop {self.package}: {res.stderr.decode(errors='replace')}")

        # Reset last seen seq to 0
        self._last_seq = 0
        self._drain_queue()

        # am start -n <package>/<activity>
        res = self._run_adb("shell", "am", "start", "-n", component)
        if res.returncode != 0:
            raise DriverError(f"Failed to start {component}: {res.stderr.decode(errors='replace')}")

        # Wait MIRA_RESET_WAIT_MS
        wait_s = self.config.reset_wait_ms / 1000.0
        time.sleep(wait_s)

        # Collect initial event
        deadline = time.time() + 2.0
        initial_event: Optional[FocusEvent] = None
        while time.time() < deadline:
            for ev in self._drain_queue():
                if ev.seq > self._last_seq:
                    self._last_seq = ev.seq
                    initial_event = ev
            if initial_event:
                break
            time.sleep(0.05)

        if not initial_event:
            raise DriverError("No MIRA_FOCUS event received after app launch")

        self._curr_event = initial_event

        # Replay entry steps
        for step in screen_cfg.get("entry_steps", []):
            time.sleep(self.config.key_delay_ms / 1000.0)
            self.press(step)

        return self._curr_event

    def press(self, key: str) -> Optional[FocusEvent]:
        code = keycode(key)
        prev_seq = self._last_seq

        # Send keyevent
        res = self._run_adb("shell", "input", "keyevent", str(code))
        if res.returncode != 0:
            raise DriverError(f"Failed to send keyevent {code}: {res.stderr.decode(errors='replace')}")

        # Wait settle time
        settle_s = self.config.settle_ms / 1000.0
        time.sleep(settle_s)

        # Check for newest focus event with seq > prev_seq
        newest: Optional[FocusEvent] = None
        for ev in self._drain_queue():
            if ev.seq > prev_seq:
                if newest is None or ev.seq > newest.seq:
                    newest = ev

        if newest:
            self._last_seq = newest.seq
            self._curr_event = newest
            return newest

        return None

    def screenshot(self) -> bytes:
        res = self._run_adb("exec-out", "screencap", "-p")
        if res.returncode != 0 or not res.stdout:
            raise DriverError(f"Failed to capture screenshot: {res.stderr.decode(errors='replace')}")
        return res.stdout

    def close(self) -> None:
        self._stop_logcat.set()
        if self._logcat_proc:
            try:
                self._logcat_proc.terminate()
            except OSError:
                pass
        if self._logcat_thread and self._logcat_thread.is_alive():
            self._logcat_thread.join(timeout=1.0)
