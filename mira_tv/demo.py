"""End-to-end demo execution orchestrator (BUILD_D.md D7, Acceptance Criteria). Owner: D.

Pipeline:
1. Apply bug patches (live mode)
2. Explore all screens and map focus topology
3. Detect defects: UNREACHABLE, TRAP, NO_FOCUS_INDICATOR
4. Generate AI explanations for discovered defects
5. Apply fixes one-by-one and verify each
6. Write validated artifacts/<run_id>/report.json (Contract C2)
7. Compile standalone artifacts/<run_id>/report.html (Contract C5)
8. Guaranteed restoration in finally block
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional, Sequence, Union

from .ai import ExplanationEngine
from .config import Config, load_config
from .detectors import Defect, detect_trap, detect_unreachable
from .driver import Driver
from .explore import ScreenResult, explore_screen
from .fixture_driver import FixtureDriver
from .patches import apply as patch_apply, revert as patch_revert
from .validate import validate_report
from .verify import VerifyItem, verify_defect
from .vision import annotate, detect_no_indicator
from report.build_report import build_report

logger = logging.getLogger(__name__)

SYNTHETIC_EXPECTED_ELEMENTS = {
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

SYNTHETIC_SCENARIO = {
    "package": "com.amazon.mira.synthetic",
    "launch_activity": "com.amazon.mira.synthetic.MainActivity",
    "screens": [
        {
            "screen": "home",
            "entry_steps": [],
            "exit_targets": ["home.drawer.1"],
            "max_probes": 80,
            "max_depth": 8,
        },
        {
            "screen": "details",
            "entry_steps": ["RIGHT", "CENTER"],
            "exit_targets": ["home.hero.1"],
            "max_probes": 60,
            "max_depth": 8,
        },
    ],
}


def _get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _safe_name(defect_id: str) -> str:
    return defect_id.replace(":", "_").replace(".", "_")


def run_demo(
    mode: str = "fixture",
    fixture_dir: Optional[Union[str, Path]] = None,
    clean_fixture_dir: Optional[Union[str, Path]] = None,
    scenario_path: Optional[Union[str, Path]] = None,
    expected_path: Optional[Union[str, Path]] = None,
    bug_map_path: Optional[Union[str, Path]] = None,
    no_restore: bool = False,
    artifacts_dir: Optional[Union[str, Path]] = None,
    cfg: Optional[Config] = None,
    repo_root: Optional[Path] = None,
) -> Path:
    """Run full QA pipeline end-to-end.

    Returns the path to the compiled report.html.
    """
    config = cfg or load_config()
    root = (repo_root or Path.cwd()).resolve()

    # 1. Resolve configuration files
    if scenario_path and Path(scenario_path).is_file():
        scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
    elif mode == "fixture":
        scenario = SYNTHETIC_SCENARIO
    else:
        scenario = json.loads(Path("contracts/scenario.json").read_text(encoding="utf-8"))

    if expected_path and Path(expected_path).is_file():
        expected_elements = json.loads(Path(expected_path).read_text(encoding="utf-8"))
    elif mode == "fixture":
        expected_elements = SYNTHETIC_EXPECTED_ELEMENTS
    else:
        expected_elements = json.loads(Path("contracts/expected_elements.json").read_text(encoding="utf-8"))

    # Load bug map
    bmap_file = Path(bug_map_path or "contracts/bug_map.json")
    if bmap_file.is_file():
        bug_map_raw = json.loads(bmap_file.read_text(encoding="utf-8"))
        bug_map = {k: v for k, v in bug_map_raw.items() if not k.startswith("_")}
    else:
        bug_map = {}

    # 2. Setup run directory
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_art = Path(artifacts_dir or config.artifacts_dir)
    run_dir = base_art / run_id
    shots_dir = run_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    git_commit = _get_git_commit()

    # 3. Initialize driver
    driver: Driver
    if mode == "fixture":
        fix_dir = Path(fixture_dir or "fixtures/synthetic_bugs")
        driver = FixtureDriver(fix_dir)
    else:
        from .adb_driver import AdbDriver
        driver = AdbDriver(config, scenario)

    applied_bugs: List[str] = []
    applied_fixes: List[str] = []

    try:
        # If live mode, apply all bug patches first
        if mode == "live":
            for defect_id, mapping in bug_map.items():
                bug_file = mapping.get("bug")
                if bug_file and (root / bug_file).is_file():
                    patch_apply(bug_file, repo_root=root)
                    applied_bugs.append(bug_file)

        # Step A: Explore all screens
        screens_report_data: List[Dict[str, Any]] = []
        screen_results_before: Dict[str, ScreenResult] = {}
        all_defects: List[Defect] = []

        for screen_cfg in scenario.get("screens", []):
            screen_name = screen_cfg.get("screen", "")
            res = explore_screen(driver, screen_cfg)
            screen_results_before[screen_name] = res

            # Run deterministic detectors
            unreachable = detect_unreachable(res, expected_elements)
            trap = detect_trap(res, screen_cfg.get("exit_targets", []))
            no_ind = detect_no_indicator(res, diff_min=config.indicator_diff_min)

            screen_defects = unreachable + trap + no_ind
            all_defects.extend(screen_defects)

            screens_report_data.append({
                "screen": screen_name,
                "probes": res.probes,
                "elements_seen": sorted(res.graph.nodes.keys()),
                "graph_before": res.graph.to_dict(),
                "graph_after": None,
            })

        # Deterministically sort defects
        all_defects.sort(key=lambda d: (d.screen, d.type, d.element_id))

        # Step B: AI Explanation generation
        ai_engine = ExplanationEngine(config, cache_dir=Path("ai_cache"))
        for defect in all_defects:
            shot_bytes: Optional[bytes] = None
            bounds: Any = {"x": 0, "y": 0, "w": 0, "h": 0}
            s_res = screen_results_before.get(defect.screen)

            if s_res and defect.element_id in s_res.shots:
                shot_bytes = s_res.shots[defect.element_id]
                if defect.element_id in s_res.graph.nodes:
                    bounds = s_res.graph.nodes[defect.element_id].bounds
            elif s_res and s_res.shots:
                first_k = next(iter(s_res.shots))
                shot_bytes = s_res.shots[first_k]
                if first_k in s_res.graph.nodes:
                    bounds = s_res.graph.nodes[first_k].bounds
            else:
                shot_bytes = driver.screenshot()

            ann_png = annotate(shot_bytes, bounds, color="red")
            slug = _safe_name(defect.id)
            defect_shot_rel = f"shots/{slug}_defect.png"
            (run_dir / defect_shot_rel).write_bytes(ann_png)

            defect.screenshot = defect_shot_rel
            explanation_text, ai_source = ai_engine.explain(defect, ann_png)
            defect.ai_explanation = explanation_text
            defect.ai_source = ai_source

        # Step C: Verify fixes one by one
        verify_items: List[VerifyItem] = []
        clean_fix_path = clean_fixture_dir or Path("fixtures/synthetic_clean")

        for defect in all_defects:
            mapping = bug_map.get(defect.id)
            if not mapping:
                continue

            fix_patch = mapping.get("fix", "")
            s_res = screen_results_before[defect.screen]

            v_item = verify_defect(
                driver=driver,
                defect=defect,
                fix_patch=fix_patch,
                scenario=scenario,
                expected_elements=expected_elements,
                screen_result_before=s_res,
                out_dir=run_dir,
                mode=mode,
                clean_fixture_dir=clean_fix_path,
                indicator_diff_min=config.indicator_diff_min,
                repo_root=root,
                initial_defects=all_defects,
            )
            verify_items.append(v_item)
            if mode == "live" and fix_patch:
                applied_fixes.append(fix_patch)

        # Step D: Construct report.json dictionary
        report_dict: Dict[str, Any] = {
            "schema_version": "1",
            "run_id": run_id,
            "mode": mode,
            "app": {
                "package": scenario.get("package", "com.amazon.mira.synthetic"),
                "git_commit": git_commit,
            },
            "screens": screens_report_data,
            "defects": [d.to_dict() for d in all_defects],
            "verify": [v.to_dict() for v in verify_items],
            "summary": {
                "defects_found": len(all_defects),
                "fixed_verified": sum(1 for v in verify_items if v.after == "PASS"),
                "ai_calls": ai_engine.ai_calls,
            },
        }

        # Step E: Schema validation
        val_errors = validate_report(report_dict)
        if val_errors:
            raise ValueError(f"report.json schema validation failed: {val_errors}")

        # Step F: Write report.json
        report_json_path = run_dir / "report.json"
        report_json_path.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")

        # Step G: Build standalone report.html
        build_report(run_dir)
        return run_dir / "report.html"

    finally:
        # Revert all applied patches in finally block (fixes first, then bugs)
        if mode == "live" and not no_restore:
            for fix_file in reversed(applied_fixes):
                try:
                    patch_revert(fix_file, repo_root=root)
                except Exception as e:
                    logger.error("Failed to revert fix patch %s: %s", fix_file, e)

            for bug_file in reversed(applied_bugs):
                try:
                    patch_revert(bug_file, repo_root=root)
                except Exception as e:
                    logger.error("Failed to revert bug patch %s: %s", bug_file, e)

        driver.close()
