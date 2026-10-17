"""Defect detectors: UNREACHABLE, TRAP (BUILD_D.md D4). Owner: D.

Pure functions returning List[Defect]:
- detect_unreachable(result, expected_ids) -> List[Defect]
- detect_trap(result, exit_targets) -> List[Defect]
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from .explore import ScreenResult


@dataclass
class Defect:
    type: str  # "UNREACHABLE" | "TRAP" | "NO_FOCUS_INDICATOR"
    screen: str
    element_id: str
    path: List[str]
    detail: str
    screenshot: Optional[str] = None
    ai_explanation: Optional[str] = None
    ai_source: str = "stub"

    @property
    def id(self) -> str:
        return f"{self.type}:{self.element_id}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "screen": self.screen,
            "element_id": self.element_id,
            "path": list(self.path),
            "evidence": {
                "detail": self.detail,
                "screenshot": self.screenshot,
            },
            "ai_explanation": self.ai_explanation,
            "ai_source": self.ai_source,
        }


def detect_unreachable(
    result: ScreenResult,
    expected_ids: Union[Dict[str, Sequence[str]], Sequence[str]],
) -> List[Defect]:
    """Every expected ID on the screen not visited in graph.nodes is UNREACHABLE.

    Returns defects sorted by (screen, type, element_id).
    """
    if isinstance(expected_ids, dict):
        target_ids = list(expected_ids.get(result.screen, []))
    else:
        target_ids = list(expected_ids)

    defects: List[Defect] = []
    for el_id in target_ids:
        if el_id not in result.graph.nodes:
            defects.append(
                Defect(
                    type="UNREACHABLE",
                    screen=result.screen,
                    element_id=el_id,
                    path=[],
                    detail=f"never focused in {result.probes} probes",
                )
            )

    defects.sort(key=lambda d: (d.screen, d.type, d.element_id))
    return defects
