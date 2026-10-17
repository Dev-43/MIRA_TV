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


def detect_trap(
    result: ScreenResult,
    exit_targets: Sequence[str],
) -> List[Defect]:
    """Compute reverse_reachable from exit_targets plus any node on another screen.

    Every visited node on this screen not in that set is trapped.
    Reports one TRAP defect for the first trapped node in BFS order:
    - path: shortest path from screen entry to it
    - detail: how many nodes are in the trapped region
    """
    screen_nodes = [
        node_id
        for node_id, data in result.graph.nodes.items()
        if data.screen == result.screen
    ]
    if not screen_nodes:
        return []

    # Target set: designated exit targets + any discovered node on a different screen
    all_targets = set(exit_targets)
    for node_id, data in result.graph.nodes.items():
        if data.screen != result.screen:
            all_targets.add(node_id)

    escapable = result.graph.reverse_reachable(all_targets)
    trapped_nodes = [node_id for node_id in screen_nodes if node_id not in escapable]

    if not trapped_nodes:
        return []

    # First trapped node encountered in BFS order
    first_trapped = trapped_nodes[0]
    entry_id = screen_nodes[0]
    path = result.graph.shortest_path(entry_id, first_trapped) or []

    detail = (
        f"{len(trapped_nodes)} node(s) in trapped region: "
        f"{', '.join(sorted(trapped_nodes))}"
    )

    defect = Defect(
        type="TRAP",
        screen=result.screen,
        element_id=first_trapped,
        path=path,
        detail=detail,
    )
    return [defect]
