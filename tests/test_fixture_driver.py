from pathlib import Path
import pytest

from mira_tv.driver import DriverError, FocusEvent
from mira_tv.fixture_driver import FixtureDriver

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_init_missing_fixture(tmp_path):
    with pytest.raises(DriverError, match="fixture.json not found"):
        FixtureDriver(tmp_path)


def test_reset_to_screen():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    ev = driver.reset_to_screen({"screen": "home"})
    assert isinstance(ev, FocusEvent)
    assert ev.element_id == "home.drawer.1"
    assert ev.screen == "home"
    assert ev.seq == 1
    assert ev.bounds == (60, 80, 140, 60)
    assert ev.ts > 0


def test_reset_with_entry_steps():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    ev = driver.reset_to_screen({"screen": "home", "entry_steps": ["RIGHT"]})
    assert ev.element_id == "home.hero.1"
    assert ev.screen == "home"
    assert ev.seq == 2


def test_press_navigation():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    driver.reset_to_screen({"screen": "home"})
    assert driver.current_element == "home.drawer.1"

    # Move RIGHT to hero
    ev = driver.press("RIGHT")
    assert ev is not None
    assert ev.element_id == "home.hero.1"
    assert ev.seq == 2

    # Move DOWN to card.1
    ev2 = driver.press("DOWN")
    assert ev2 is not None
    assert ev2.element_id == "home.card.1"
    assert ev2.seq == 3

    # Move LEFT back to drawer.2
    ev3 = driver.press("LEFT")
    assert ev3 is not None
    assert ev3.element_id == "home.drawer.2"
    assert ev3.seq == 4


def test_press_null_edge_returns_none():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    driver.reset_to_screen({"screen": "home"})

    # UP from home.drawer.1 is None
    ev = driver.press("UP")
    assert ev is None
    # seq and current element remain unchanged
    assert driver.current_element == "home.drawer.1"


def test_screenshot():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    driver.reset_to_screen({"screen": "home"})
    shot = driver.screenshot()
    assert isinstance(shot, bytes)
    assert shot.startswith(b"\x89PNG\r\n\x1a\n")


def test_unknown_screen_error():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    with pytest.raises(DriverError, match="No entry element"):
        driver.reset_to_screen({"screen": "non_existent"})


def test_press_before_reset_error():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    with pytest.raises(DriverError, match="driver has not been reset"):
        driver.press("UP")
