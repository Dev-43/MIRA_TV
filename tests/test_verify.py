"""Tests for defect fix verification and regression check (Task D7)."""
from pathlib import Path
from PIL import Image
import pytest

from mira_tv.detectors import Defect, detect_unreachable
from mira_tv.explore import explore_screen
from mira_tv.fixture_driver import FixtureDriver
from mira_tv.verify import VerifyItem, verify_defect


def test_verify_item_serialization() -> None:
    item = VerifyItem(
        defect_id="UNREACHABLE:details.btn.addlist",
        fix="fixes/FIX-01-unreachable.patch",
        before="FAIL",
        after="PASS",
        before_screenshot="shots/UNREACHABLE_details_btn_addlist_before.png",
        after_screenshot="shots/UNREACHABLE_details_btn_addlist_after.png",
    )
    d = item.to_dict()
    assert d["defect_id"] == "UNREACHABLE:details.btn.addlist"
    assert d["fix"] == "fixes/FIX-01-unreachable.patch"
    assert d["before"] == "FAIL"
    assert d["after"] == "PASS"
    assert "before.png" in d["before_screenshot"]
    assert "after.png" in d["after_screenshot"]


def test_verify_defect_fixture_mode_pass(tmp_path: Path) -> None:
    scenario = {
        "screens": [
            {
                "screen": "details",
                "entry_steps": ["RIGHT", "CENTER"],
                "exit_targets": ["home.hero.1"],
                "max_probes": 60,
                "max_depth": 8,
            }
        ]
    }
    expected = {
        "details": [
            "details.btn.play",
            "details.btn.addlist",
            "details.btn.trailer",
            "details.btn.back",
        ]
    }

    # 1. Start on buggy synthetic fixture
    driver = FixtureDriver(Path("fixtures/synthetic_bugs"))
    screen_cfg = scenario["screens"][0]
    res_before = explore_screen(driver, screen_cfg)

    defects_before = detect_unreachable(res_before, expected)
    assert len(defects_before) == 1
    target_defect = defects_before[0]
    assert target_defect.id == "UNREACHABLE:details.btn.addlist"

    # 2. Run verify_defect with clean fixture swap
    v_item = verify_defect(
        driver=driver,
        defect=target_defect,
        fix_patch="fixes/FIX-01-unreachable.patch",
        scenario=scenario,
        expected_elements=expected,
        screen_result_before=res_before,
        out_dir=tmp_path,
        mode="fixture",
        clean_fixture_dir=Path("fixtures/synthetic_clean"),
        initial_defects=defects_before,
    )

    assert v_item.before == "FAIL"
    assert v_item.after == "PASS"
    assert "resolved" in v_item.detail.lower()

    # Verify screenshots created
    before_img = tmp_path / v_item.before_screenshot
    after_img = tmp_path / v_item.after_screenshot
    assert before_img.is_file()
    assert after_img.is_file()
    assert Image.open(before_img).size == (1280, 720)
    assert Image.open(after_img).size == (1280, 720)


def test_verify_defect_fixture_mode_fail_when_still_buggy(tmp_path: Path) -> None:
    scenario = {
        "screens": [
            {
                "screen": "details",
                "entry_steps": ["RIGHT", "CENTER"],
                "exit_targets": ["home.hero.1"],
                "max_probes": 60,
                "max_depth": 8,
            }
        ]
    }
    expected = {
        "details": [
            "details.btn.play",
            "details.btn.addlist",
            "details.btn.trailer",
            "details.btn.back",
        ]
    }

    driver = FixtureDriver(Path("fixtures/synthetic_bugs"))
    screen_cfg = scenario["screens"][0]
    res_before = explore_screen(driver, screen_cfg)
    target_defect = detect_unreachable(res_before, expected)[0]

    # Swap to the SAME buggy fixture -> defect should still exist -> after="FAIL"
    v_item = verify_defect(
        driver=driver,
        defect=target_defect,
        fix_patch="fixes/FIX-01-unreachable.patch",
        scenario=scenario,
        expected_elements=expected,
        screen_result_before=res_before,
        out_dir=tmp_path,
        mode="fixture",
        clean_fixture_dir=Path("fixtures/synthetic_bugs"),
    )

    assert v_item.before == "FAIL"
    assert v_item.after == "FAIL"
    assert "still present" in v_item.detail.lower()
