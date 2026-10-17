"""Defect fix verification and regression detection (BUILD_D.md D7, Contract C2). Owner: D.

Functions:
- verify_defect(...) -> VerifyItem
- verify_all(...) -> List[VerifyItem]
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .detectors import Defect, detect_trap, detect_unreachable
from .driver import Driver
from .explore import ScreenResult, explore_screen
from .fixture_driver import FixtureDriver
from .patches import apply as patch_apply
from .vision import annotate, detect_no_indicator

logger = logging.getLogger(__name__)


@dataclass
class VerifyItem:
    defect_id: str
    fix: str
    before: str  # "FAIL"
    after: str   # "PASS" | "FAIL"
    before_screenshot: str
    after_screenshot: str
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "defect_id": self.defect_id,
            "fix": self.fix,
            "before": self.before,
            "after": self.after,
            "before_screenshot": self.before_screenshot,
            "after_screenshot": self.after_screenshot,
        }


def _safe_name(defect_id: str) -> str:
    return defect_id.replace(":", "_").replace(".", "_")


def verify_defect(
    driver: Driver,
    defect: Defect,
    fix_patch: str,
    scenario: Dict[str, Any],
    expected_elements: Dict[str, Any],
    screen_result_before: ScreenResult,
    out_dir: Path,
    mode: str = "fixture",
    clean_fixture_dir: Optional[Union[str, Path]] = None,
    indicator_diff_min: float = 4.0,
    repo_root: Optional[Path] = None,
    initial_defects: Optional[Sequence[Defect]] = None,
) -> VerifyItem:
    """Verify that applying a fix removes the defect and introduces no regressions.

    Captures annotated before (red) and after (green) screenshots.
    Returns VerifyItem with before='FAIL' and after='PASS' or 'FAIL'.
    """
    screens_cfg = scenario.get("screens", [])
    screen_cfg = next((s for s in screens_cfg if s.get("screen") == defect.screen), None)
    if not screen_cfg:
        raise ValueError(f"Screen '{defect.screen}' not found in scenario configuration")

    shots_dir = out_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_name(defect.id)

    # 1. Capture before screenshot with red border
    bounds: Any = {"x": 0, "y": 0, "w": 0, "h": 0}
    raw_before: Optional[bytes] = None
    if defect.element_id in screen_result_before.shots:
        raw_before = screen_result_before.shots[defect.element_id]
        if defect.element_id in screen_result_before.graph.nodes:
            bounds = screen_result_before.graph.nodes[defect.element_id].bounds
    elif screen_result_before.shots:
        # Fallback to first available shot on the screen
        first_el = next(iter(screen_result_before.shots))
        raw_before = screen_result_before.shots[first_el]
        if first_el in screen_result_before.graph.nodes:
            bounds = screen_result_before.graph.nodes[first_el].bounds
    else:
        raw_before = driver.screenshot()

    before_rel = f"shots/{slug}_before.png"
    before_ann = annotate(raw_before, bounds, color="red")
    (out_dir / before_rel).write_bytes(before_ann)

    # 2. Apply fix (live mode: git patch; fixture mode: swap to clean fixture)
    if mode == "live":
        patch_apply(fix_patch, repo_root=repo_root)
    elif mode == "fixture" and isinstance(driver, FixtureDriver):
        clean_path = clean_fixture_dir or Path("fixtures/synthetic_clean")
        driver.swap_fixture(clean_path)

    # 3. Relaunch and re-explore only the affected screen
    result_after = explore_screen(driver, screen_cfg)

    # 4. Rerun all detectors
    defects_after: List[Defect] = []
    defects_after.extend(detect_unreachable(result_after, expected_elements))
    defects_after.extend(detect_trap(result_after, screen_cfg.get("exit_targets", [])))
    defects_after.extend(detect_no_indicator(result_after, diff_min=indicator_diff_min))

    defects_after_ids = {d.id for d in defects_after}

    # 5. Evaluate PASS/FAIL
    after_status = "PASS"
    detail_msg = "Fix verified successfully; defect resolved."

    if defect.id in defects_after_ids:
        after_status = "FAIL"
        detail_msg = f"Defect '{defect.id}' is still present after fix."
    else:
        # Check regression rule: a fix may not introduce any new defect that was absent before
        initial_ids = {d.id for d in (initial_defects or [])}
        regressions = [did for did in defects_after_ids if did not in initial_ids]
        if regressions:
            after_status = "FAIL"
            detail_msg = f"Fix introduced new defect(s): {', '.join(regressions)}"

    # 6. Capture after screenshot with green border
    raw_after: Optional[bytes] = None
    bounds_after: Any = bounds
    if defect.element_id in result_after.shots:
        raw_after = result_after.shots[defect.element_id]
        if defect.element_id in result_after.graph.nodes:
            bounds_after = result_after.graph.nodes[defect.element_id].bounds
    elif result_after.shots:
        first_el = next(iter(result_after.shots))
        raw_after = result_after.shots[first_el]
        if first_el in result_after.graph.nodes:
            bounds_after = result_after.graph.nodes[first_el].bounds
    else:
        raw_after = driver.screenshot()

    after_rel = f"shots/{slug}_after.png"
    after_ann = annotate(raw_after, bounds_after, color="green")
    (out_dir / after_rel).write_bytes(after_ann)

    return VerifyItem(
        defect_id=defect.id,
        fix=fix_patch,
        before="FAIL",
        after=after_status,
        before_screenshot=before_rel,
        after_screenshot=after_rel,
        detail=detail_msg,
    )
