"""Tests for defect detectors: Defect dataclass and detect_unreachable (Task D4)."""
from pathlib import Path
from typing import Dict

import pytest

from mira_tv.detectors import Defect, detect_trap, detect_unreachable
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


def test_detect_trap_no_traps() -> None:
    graph = Graph()
    graph.add_node("home.drawer.1", "home", {"x": 0, "y": 0, "w": 100, "h": 50})
    graph.add_node("home.card.1", "home", {"x": 100, "y": 0, "w": 100, "h": 50})
    graph.add_edge("home.drawer.1", "RIGHT", "home.card.1")
    graph.add_edge("home.card.1", "LEFT", "home.drawer.1")

    result = ScreenResult(screen="home", graph=graph, shots={}, probes=4)
    traps = detect_trap(result, exit_targets=["home.drawer.1"])
    assert traps == []


def test_detect_trap_synthetic_fixtures() -> None:
    home_cfg = {
        "screen": "home",
        "entry_steps": [],
        "exit_targets": ["home.drawer.1"],
        "max_probes": 80,
        "max_depth": 8,
    }

    # 1. Clean synthetic home screen has no traps
    clean_driver = FixtureDriver(Path("fixtures/synthetic_clean"))
    clean_result = explore_screen(clean_driver, home_cfg)
    clean_traps = detect_trap(clean_result, home_cfg["exit_targets"])
    assert clean_traps == []

    # 2. Buggy synthetic home screen has pocket at card.4 and card.5
    buggy_driver = FixtureDriver(Path("fixtures/synthetic_bugs"))
    buggy_result = explore_screen(buggy_driver, home_cfg)
    buggy_traps = detect_trap(buggy_result, home_cfg["exit_targets"])
    assert len(buggy_traps) == 1
    trap = buggy_traps[0]
    assert trap.id == "TRAP:home.card.4"
    assert trap.type == "TRAP"
    assert trap.screen == "home"
    assert trap.element_id == "home.card.4"
    assert len(trap.path) > 0  # Reconstructed path from entry
    assert "2 node(s) in trapped region" in trap.detail
    assert "home.card.4" in trap.detail and "home.card.5" in trap.detail


def test_golden_clean_vs_bugs_summary() -> None:
    home_cfg = {
        "screen": "home",
        "entry_steps": [],
        "exit_targets": ["home.drawer.1"],
        "max_probes": 80,
        "max_depth": 8,
    }
    details_cfg = {
        "screen": "details",
        "entry_steps": ["RIGHT", "CENTER"],
        "exit_targets": ["home.hero.1"],
        "max_probes": 60,
        "max_depth": 8,
    }
    expected = {
        "home": [
            "home.drawer.1",
            "home.drawer.2",
            "home.hero.1",
            "home.card.1",
            "home.card.2",
            "home.card.3",
            "home.card.4",
            "home.card.5",
        ],
        "details": [
            "details.btn.play",
            "details.btn.addlist",
            "details.btn.trailer",
            "details.btn.back",
        ],
    }

    # Synthetic clean -> 0 defects
    clean_driver = FixtureDriver(Path("fixtures/synthetic_clean"))
    c_home = explore_screen(clean_driver, home_cfg)
    c_details = explore_screen(clean_driver, details_cfg)
    clean_defects = (
        detect_unreachable(c_home, expected)
        + detect_trap(c_home, home_cfg["exit_targets"])
        + detect_unreachable(c_details, expected)
        + detect_trap(c_details, details_cfg["exit_targets"])
    )
    assert clean_defects == []

    # Synthetic bugs -> exactly UNREACHABLE:details.btn.addlist and TRAP:home.card.4
    buggy_driver = FixtureDriver(Path("fixtures/synthetic_bugs"))
    b_home = explore_screen(buggy_driver, home_cfg)
    b_details = explore_screen(buggy_driver, details_cfg)
    buggy_defects = (
        detect_unreachable(b_home, expected)
        + detect_trap(b_home, home_cfg["exit_targets"])
        + detect_unreachable(b_details, expected)
        + detect_trap(b_details, details_cfg["exit_targets"])
    )
    assert [d.id for d in buggy_defects] == [
        "TRAP:home.card.4",
        "UNREACHABLE:details.btn.addlist",
    ]
