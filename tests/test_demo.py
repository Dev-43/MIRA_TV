"""Tests for end-to-end demo execution pipeline (Task D7, Acceptance Criteria)."""
import json
from pathlib import Path
import pytest

from mira_tv.cli import main
from mira_tv.demo import run_demo
from mira_tv.validate import validate_report


def test_run_demo_fixture_mode_acceptance(tmp_path: Path) -> None:
    """Acceptance test: demo --mode fixture produces a valid report.json with >= 3 defects, all after=PASS."""
    report_html_path = run_demo(
        mode="fixture",
        fixture_dir="fixtures/synthetic_bugs",
        clean_fixture_dir="fixtures/synthetic_clean",
        artifacts_dir=tmp_path,
    )

    assert report_html_path.is_file()
    run_dir = report_html_path.parent

    # 1. report.json exists and is valid against Contract C2
    report_json_path = run_dir / "report.json"
    assert report_json_path.is_file()
    data = json.loads(report_json_path.read_text(encoding="utf-8"))

    val_errors = validate_report(data)
    assert val_errors == [], f"report.json validation failed: {val_errors}"

    # 2. At least 3 defects found and all verified after=PASS
    defects = data["defects"]
    assert len(defects) >= 3

    defect_ids = {d["id"] for d in defects}
    assert "UNREACHABLE:details.btn.addlist" in defect_ids
    assert "TRAP:home.card.4" in defect_ids
    assert "NO_FOCUS_INDICATOR:home.card.2" in defect_ids

    verify_items = data["verify"]
    assert len(verify_items) >= 3
    for v in verify_items:
        assert v["before"] == "FAIL"
        assert v["after"] == "PASS"
        assert (run_dir / v["before_screenshot"]).is_file()
        assert (run_dir / v["after_screenshot"]).is_file()

    summary = data["summary"]
    assert summary["defects_found"] >= 3
    assert summary["fixed_verified"] >= 3

    # 3. Standalone report.html inlines CSS and JSON data
    html_text = report_html_path.read_text(encoding="utf-8")
    assert "<style>" in html_text
    assert "UNREACHABLE:details.btn.addlist" in html_text
    assert "TRAP:home.card.4" in html_text
    assert "NO_FOCUS_INDICATOR:home.card.2" in html_text


def test_demo_cli_execution(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_dir = tmp_path / "cli_artifacts"
    rc = main(["demo", "--mode", "fixture", "--out", str(out_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Demo completed successfully" in captured.out
    assert "report.html" in captured.out
