import io
import subprocess
from unittest.mock import MagicMock, patch
import pytest

from mira_tv.adb_driver import AdbDriver
from mira_tv.config import Config
from mira_tv.driver import DriverError, FocusEvent


@pytest.fixture
def test_config():
    return Config(
        adb_path="adb",
        adb_serial="emulator-5554",
        key_delay_ms=0,
        settle_ms=10,
        reset_wait_ms=10,
        indicator_diff_min=4.0,
        artifacts_dir="artifacts",
        bedrock_mode="stub",
        aws_region="us-east-1",
        bedrock_model_id="",
        max_ai_calls=12,
    )


@pytest.fixture
def scenario():
    return {
        "package": "com.amazon.mira.sample",
        "launch_activity": "com.amazon.mira.sample.MainActivity",
    }


@patch("subprocess.Popen")
def test_adb_driver_init_starts_logcat(mock_popen, test_config, scenario):
    mock_proc = MagicMock()
    mock_proc.stdout = io.StringIO("")
    mock_popen.return_value = mock_proc

    driver = AdbDriver(test_config, scenario)
    assert mock_popen.called
    cmd_called = mock_popen.call_args[0][0]
    assert cmd_called == ["adb", "-s", "emulator-5554", "logcat", "-v", "raw", "-s", "ReactNativeJS:V"]
    driver.close()


@patch("subprocess.run")
@patch("subprocess.Popen")
def test_screenshot_success(mock_popen, mock_run, test_config, scenario):
    mock_popen.return_value = MagicMock(stdout=io.StringIO(""))
    png_bytes = b"\x89PNG\r\n\x1a\nFakeScreenshot"
    mock_run.return_value = subprocess.CompletedProcess(
        args=["adb", "exec-out", "screencap", "-p"],
        returncode=0,
        stdout=png_bytes,
        stderr=b"",
    )

    driver = AdbDriver(test_config, scenario)
    shot = driver.screenshot()
    assert shot == png_bytes
    driver.close()


@patch("subprocess.run")
@patch("subprocess.Popen")
def test_subprocess_timeout_raises_driver_error(mock_popen, mock_run, test_config, scenario):
    mock_popen.return_value = MagicMock(stdout=io.StringIO(""))
    mock_run.side_effect = subprocess.TimeoutExpired(cmd=["adb"], timeout=20.0)

    driver = AdbDriver(test_config, scenario)
    with pytest.raises(DriverError, match="timed out"):
        driver.screenshot()
    driver.close()


@patch("subprocess.run")
@patch("subprocess.Popen")
def test_reset_to_screen_and_press(mock_popen, mock_run, test_config, scenario):
    mock_proc = MagicMock()
    mock_proc.stdout = io.StringIO("")
    mock_popen.return_value = mock_proc

    ev1 = FocusEvent(seq=1, screen="home", element_id="home.drawer.1", bounds=(0, 0, 100, 50), ts=1760000000000)

    driver = AdbDriver(test_config, scenario)

    def on_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if "start" in cmd:
            driver._events_queue.put(ev1)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = on_run

    ev = driver.reset_to_screen({"screen": "home"})
    assert isinstance(ev, FocusEvent)
    assert ev.element_id == "home.drawer.1"
    assert ev.seq == 1

    # Simulate logcat emitting seq 2 on pressing RIGHT
    ev2_raw = FocusEvent(seq=2, screen="home", element_id="home.hero.1", bounds=(200, 0, 800, 300), ts=1760000001000)
    driver._events_queue.put(ev2_raw)

    ev2 = driver.press("RIGHT")
    assert ev2 is not None
    assert ev2.element_id == "home.hero.1"
    assert ev2.seq == 2

    # Press again with no subsequent event in queue -> returns None
    ev3 = driver.press("RIGHT")
    assert ev3 is None

    driver.close()
