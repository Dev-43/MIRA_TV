from pathlib import Path
import pytest

from mira_tv.explore import explore_screen
from mira_tv.fixture_driver import FixtureDriver

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_explore_synthetic_clean_home():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    cfg = {"screen": "home", "max_probes": 100, "max_depth": 8}
    result = explore_screen(driver, cfg)

    assert result.screen == "home"
    assert result.probes <= 100
    # synthetic_clean home has 8 elements
    expected_home_elements = {
        "home.drawer.1",
        "home.drawer.2",
        "home.hero.1",
        "home.card.1",
        "home.card.2",
        "home.card.3",
        "home.card.4",
        "home.card.5",
    }
    for el in expected_home_elements:
        assert el in result.graph.nodes, f"Missing element {el} in graph"
        assert el in result.shots, f"Missing screenshot for {el}"

    # Verify screenshots are non-empty PNGs
    for el, shot in result.shots.items():
        assert isinstance(shot, bytes)
        assert shot.startswith(b"\x89PNG")


def test_explore_determinism():
    driver1 = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    driver2 = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    cfg = {"screen": "home", "max_probes": 100, "max_depth": 8}

    res1 = explore_screen(driver1, cfg)
    res2 = explore_screen(driver2, cfg)

    assert res1.graph.to_dict() == res2.graph.to_dict()
    assert res1.probes == res2.probes


def test_explore_probe_cap_respected():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    cfg = {"screen": "home", "max_probes": 7, "max_depth": 8}
    res = explore_screen(driver, cfg)
    assert res.probes <= 7 + 1  # May execute at most the current probe step


def test_explore_details_screen():
    driver = FixtureDriver(FIXTURES_DIR / "synthetic_clean")
    cfg = {"screen": "details", "max_probes": 50, "max_depth": 5}
    res = explore_screen(driver, cfg)

    assert "details.btn.play" in res.graph.nodes
    assert "details.btn.trailer" in res.graph.nodes
    assert "details.btn.addlist" in res.graph.nodes
