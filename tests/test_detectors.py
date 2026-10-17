"""Tests for defect detectors: Defect dataclass and detect_unreachable (Task D4)."""
from pathlib import Path
from typing import Dict

import pytest

from mira_tv.detectors import Defect, detect_unreachable
from mira_tv.explore import ScreenResult, explore_screen
from mira_tv.fixture_driver import FixtureDriver
from mira_tv.graph import Graph


def test_defect_dataclass_properties_and_serialization() -> None:
    defect = Defect(
        type="UNREACHABLE",
        screen="details",
        element_id="details.btn.addlist",
        path=["RIGHT", "DOWN"],
        detail="never focused in 60 probes",
        screenshot="shots/details.btn.addlist.png",
        ai_explanation="The Add to List button cannot be reached via D-pad navigation.",
        ai_source="bedrock",
    )
    assert defect.id == "UNREACHABLE:details.btn.addlist"
    serialized = defect.to_dict()
    assert serialized["id"] == "UNREACHABLE:details.btn.addlist"
    assert serialized["type"] == "UNREACHABLE"
    assert serialized["screen"] == "details"
    assert serialized["element_id"] == "details.btn.addlist"
    assert serialized["path"] == ["RIGHT", "DOWN"]
    assert serialized["evidence"]["detail"] == "never focused in 60 probes"
    assert serialized["evidence"]["screenshot"] == "shots/details.btn.addlist.png"
    assert serialized["ai_explanation"] == "The Add to List button cannot be reached via D-pad navigation."
    assert serialized["ai_source"] == "bedrock"


def test_detect_unreachable_all_present() -> None:
    graph = Graph()
    graph.add_node("home.drawer.1", "home", {"x": 0, "y": 0, "w": 100, "h": 50})
    graph.add_node("home.card.1", "home", {"x": 100, "y": 0, "w": 100, "h": 50})
    result = ScreenResult(screen="home", graph=graph, shots={}, probes=10)

    expected = {"home": ["home.drawer.1", "home.card.1"]}
    defects = detect_unreachable(result, expected)
    assert defects == []


def test_detect_unreachable_missing_elements_and_deterministic_order() -> None:
    graph = Graph()
    graph.add_node("home.card.1", "home", {"x": 100, "y": 0, "w": 100, "h": 50})
    result = ScreenResult(screen="home", graph=graph, shots={}, probes=25)

    expected = ["home.drawer.2", "home.drawer.1", "home.card.1"]
    defects = detect_unreachable(result, expected)
    assert len(defects) == 2
    # Deterministic alphabetical sort: home.drawer.1 before home.drawer.2
    assert defects[0].id == "UNREACHABLE:home.drawer.1"
    assert defects[0].path == []
    assert defects[0].detail == "never focused in 25 probes"
    assert defects[1].id == "UNREACHABLE:home.drawer.2"


def test_detect_unreachable_synthetic_fixtures() -> None:
    # 1. Clean synthetic details screen has all elements reachable
    clean_driver = FixtureDriver(Path("fixtures/synthetic_clean"))
    details_cfg = {
        "screen": "details",
        "entry_steps": ["RIGHT", "CENTER"],
        "exit_targets": ["home.hero.1"],
        "max_probes": 50,
        "max_depth": 5,
    }
    clean_result = explore_screen(clean_driver, details_cfg)
    expected_details = [
        "details.btn.play",
        "details.btn.addlist",
        "details.btn.trailer",
        "details.btn.back",
    ]
    clean_defects = detect_unreachable(clean_result, expected_details)
    assert clean_defects == []

    # 2. Buggy synthetic details screen has addlist unreachable
    buggy_driver = FixtureDriver(Path("fixtures/synthetic_bugs"))
    buggy_result = explore_screen(buggy_driver, details_cfg)
    buggy_defects = detect_unreachable(buggy_result, expected_details)
    assert len(buggy_defects) == 1
    assert buggy_defects[0].id == "UNREACHABLE:details.btn.addlist"
    assert buggy_defects[0].element_id == "details.btn.addlist"
    assert buggy_defects[0].screen == "details"
    assert buggy_defects[0].path == []
    assert "never focused" in buggy_defects[0].detail
