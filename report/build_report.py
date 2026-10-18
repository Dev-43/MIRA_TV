"""Report builder (BUILD_D.md D8, Contract C5). Owner: D.

Compiles single-file artifacts/<run_id>/report.html from template.html, style.css, and report.json.
Contract requirements:
- Reads artifacts/<run_id>/report.json
- Inlines report/style.css replacing exact tag: <link rel="stylesheet" href="style.css">
- Replaces exact token: /*__MIRA_REPORT_JSON__*/null with report.json content
- Copies referenced screenshots into run directory
- Raises ValueError if the link tag or token is missing
- Writes artifacts/<run_id>/report.html
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Union


LINK_TAG = '<link rel="stylesheet" href="style.css">'
JSON_TOKEN = '/*__MIRA_REPORT_JSON__*/null'


def build_report(
    run_dir: Union[str, Path],
    template_path: Union[str, Path] = "report/template.html",
    css_path: Union[str, Path] = "report/style.css",
) -> str:
    """Compile static single-file HTML report in run_dir.

    Returns the path to the generated report.html as a string.
    """
    run_path = Path(run_dir)
    if not run_path.is_dir():
        raise FileNotFoundError(f"Run directory not found: {run_path}")

    report_json_file = run_path / "report.json"
    if not report_json_file.is_file():
        raise FileNotFoundError(f"report.json not found in {run_path}")

    report_raw = report_json_file.read_text(encoding="utf-8")
    report_data = json.loads(report_raw)

    # 1. Copy any external referenced screenshots into run directory
    shots_to_check: list[str] = []
    for defect in report_data.get("defects", []):
        ev = defect.get("evidence", {})
        if ev.get("screenshot"):
            shots_to_check.append(ev["screenshot"])
    for v in report_data.get("verify", []):
        if v.get("before_screenshot"):
            shots_to_check.append(v["before_screenshot"])
        if v.get("after_screenshot"):
            shots_to_check.append(v["after_screenshot"])

    for rel_shot in shots_to_check:
        target_path = run_path / rel_shot
        if not target_path.exists():
            # Check if source exists relative to current working directory
            src = Path(rel_shot)
            if src.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target_path)

    # 2. Read template
    tpl_file = Path(template_path)
    if not tpl_file.is_file():
        raise FileNotFoundError(f"Template not found: {template_path}")
    tpl_content = tpl_file.read_text(encoding="utf-8")

    # 3. Check and replace stylesheet tag
    if LINK_TAG not in tpl_content:
        raise ValueError(f"Template is missing required stylesheet tag: '{LINK_TAG}'")

    css_file = Path(css_path)
    if not css_file.is_file():
        raise FileNotFoundError(f"Stylesheet not found: {css_path}")
    css_content = css_file.read_text(encoding="utf-8")

    inline_style = f"<style>\n{css_content}\n</style>"
    html_with_css = tpl_content.replace(LINK_TAG, inline_style)

    # 4. Check and replace JSON token
    if JSON_TOKEN not in html_with_css:
        raise ValueError(f"Template is missing required JSON token: '{JSON_TOKEN}'")

    final_html = html_with_css.replace(JSON_TOKEN, report_raw)

    out_file = run_path / "report.html"
    out_file.write_text(final_html, encoding="utf-8")
    return str(out_file)
