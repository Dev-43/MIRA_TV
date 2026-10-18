"""Tests for single-file HTML report builder (Task D8, Contract C5)."""
import json
from pathlib import Path
import pytest

from report.build_report import build_report


@pytest.fixture
def sample_report_data() -> dict:
    return {
        "schema_version": "1",
        "run_id": "20261017T120000Z",
        "mode": "fixture",
        "app": {"package": "com.amazon.mira.synthetic", "git_commit": "abc1234"},
        "screens": [
            {
                "screen": "home",
                "probes": 15,
                "elements_seen": ["home.drawer.1"],
                "graph_before": {"nodes": [], "edges": []},
                "graph_after": None,
            }
        ],
        "defects": [
            {
                "id": "UNREACHABLE:details.btn.addlist",
                "type": "UNREACHABLE",
                "screen": "details",
                "element_id": "details.btn.addlist",
                "path": [],
                "evidence": {"detail": "never focused in 60 probes", "screenshot": "shots/addlist.png"},
                "ai_explanation": "Button cannot be focused.",
                "ai_source": "stub",
            }
        ],
        "verify": [
            {
                "defect_id": "UNREACHABLE:details.btn.addlist",
                "fix": "fixes/FIX-01-unreachable.patch",
                "before": "FAIL",
                "after": "PASS",
                "before_screenshot": "shots/addlist_before.png",
                "after_screenshot": "shots/addlist_after.png",
            }
        ],
        "summary": {"defects_found": 1, "fixed_verified": 1, "ai_calls": 0},
    }


def test_build_report_with_production_template(tmp_path: Path, sample_report_data: dict) -> None:
    # 1. Create run directory with report.json
    run_dir = tmp_path / "20261017T120000Z"
    run_dir.mkdir(parents=True)
    (run_dir / "report.json").write_text(json.dumps(sample_report_data), encoding="utf-8")

    # 2. Build report using production template and css
    html_path_str = build_report(
        run_dir=run_dir,
        template_path="report/template.html",
        css_path="report/style.css",
    )

    out_html = Path(html_path_str)
    assert out_html.is_file()
    content = out_html.read_text(encoding="utf-8")

    # CSS inlined, no external link tag
    assert '<link rel="stylesheet" href="style.css">' not in content
    assert "<style>" in content
    assert "</style>" in content

    # JSON token replaced, not remaining
    assert "/*__MIRA_REPORT_JSON__*/null" not in content
    assert '"run_id": "20261017T120000Z"' in content
    assert "UNREACHABLE:details.btn.addlist" in content


def test_build_report_missing_link_tag(tmp_path: Path, sample_report_data: dict) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "report.json").write_text(json.dumps(sample_report_data), encoding="utf-8")

    # Template missing link tag
    tpl = tmp_path / "bad_template.html"
    tpl.write_text("<html><body>/*__MIRA_REPORT_JSON__*/null</body></html>", encoding="utf-8")
    css = tmp_path / "style.css"
    css.write_text("body { color: red; }", encoding="utf-8")

    with pytest.raises(ValueError, match="Template is missing required stylesheet tag"):
        build_report(run_dir, template_path=tpl, css_path=css)


def test_build_report_missing_json_token(tmp_path: Path, sample_report_data: dict) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "report.json").write_text(json.dumps(sample_report_data), encoding="utf-8")

    # Template missing JSON token
    tpl = tmp_path / "bad_template.html"
    tpl.write_text('<html><head><link rel="stylesheet" href="style.css"></head><body>No token</body></html>', encoding="utf-8")
    css = tmp_path / "style.css"
    css.write_text("body { color: red; }", encoding="utf-8")

    with pytest.raises(ValueError, match="Template is missing required JSON token"):
        build_report(run_dir, template_path=tpl, css_path=css)


def test_build_report_missing_report_json(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty_run"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="report.json not found"):
        build_report(empty_dir)
