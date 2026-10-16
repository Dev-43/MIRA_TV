import io
import json
from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch
import pytest

from mira_tv.adb_driver import AdbDriver
from mira_tv.config import Config
from mira_tv.driver import FocusEvent
from mira_tv.explore import explore_screen
from mira_tv.fixture_driver import FixtureDriver
from mira_tv.record import record_fixture

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_record_from_fixture_driver(tmp_path):
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    scenario = {
        "package": "com.amazon.mira.synthetic",
        "screens": [
            {"screen": "home", "entry_steps": [], "max_probes": 50, "max_depth": 5}
        ]
    }
    out_dir = tmp_path / "recorded_fixture"
    data = record_fixture(driver, scenario, out_dir)

    assert (out_dir / "fixture.json").is_file()
    assert (out_dir / "shots").is_dir()
    assert len(data["elements"]) > 0

    # Load recorded fixture with FixtureDriver and re-explore
    re_driver = FixtureDriver(out_dir)
    res = explore_screen(re_driver, {"screen": "home", "max_probes": 50, "max_depth": 5})

    # The re-explored graph must match the elements recorded
    for el in res.graph.nodes:
        assert el in data["elements"]


@patch("subprocess.run")
@patch("subprocess.Popen")
def test_record_against_mocked_adb_driver(mock_popen, mock_run, tmp_path):
    mock_proc = MagicMock()
    mock_proc.stdout = io.StringIO("")
    mock_popen.return_value = mock_proc

    ev1 = FocusEvent(seq=1, screen="home", element_id="home.drawer.1", bounds=(0, 0, 100, 50), ts=1760000000000)
    fake_png = b"\x89PNG\r\n\x1a\nFakeScreenshot"

    config = Config(settle_ms=10, reset_wait_ms=10)
    scenario = {
        "package": "com.amazon.mira.sample",
        "screens": [{"screen": "home", "entry_steps": [], "max_probes": 10, "max_depth": 2}]
    }

    driver = AdbDriver(config, scenario)

    def on_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if "start" in cmd:
            driver._events_queue.put(ev1)
        if "screencap" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=fake_png, stderr=b"")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = on_run

    out_dir = tmp_path / "mocked_recorded"
    data = record_fixture(driver, scenario, out_dir)
    driver.close()

    assert (out_dir / "fixture.json").is_file()
    assert (out_dir / "shots" / "home.drawer.1.png").is_file()
    assert (out_dir / "shots" / "home.drawer.1.png").read_bytes() == fake_png

    # Load with FixtureDriver and verify
    fix_driver = FixtureDriver(out_dir)
    ev_re = fix_driver.reset_to_screen({"screen": "home"})
    assert ev_re.element_id == "home.drawer.1"
    assert fix_driver.screenshot() == fake_png
    fix_driver.close()
