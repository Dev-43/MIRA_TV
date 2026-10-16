"""Screen exploration algorithm (BUILD_D.md D3). Owner: D.

Implements exact deterministic BFS explorer:
- explore_screen(driver, screen_cfg) -> ScreenResult
- Return ScreenResult(screen, graph, shots, probes)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .driver import Driver, FocusEvent
from .graph import Graph
from .keys import PROBE_KEYS, inverse


@dataclass
class ScreenResult:
    screen: str
    graph: Graph
    shots: Dict[str, bytes]
    probes: int


def explore_screen(driver: Driver, screen_cfg: Dict[str, Any]) -> ScreenResult:
    screen_name = screen_cfg.get("screen", "")
    max_probes = screen_cfg.get("max_probes", 80)
    max_depth = screen_cfg.get("max_depth", 8)

    graph = Graph()
    shots: Dict[str, bytes] = {}
    probes = 0

    e0 = driver.reset_to_screen(screen_cfg)
    graph.add_node(e0.element_id, e0.screen, e0.bounds)
    shots[e0.element_id] = driver.screenshot()

    queue: List[Tuple[str, List[str]]] = [(e0.element_id, [])]
    seen: Set[str] = {e0.element_id}
    current_focus_id: Optional[str] = e0.element_id

    while queue and probes < max_probes:
        el, path = queue.pop(0)

        for key in PROBE_KEYS:
            if probes >= max_probes:
                break

            # Ensure driver is currently focused on `el`
            if current_focus_id != el:
                e_reset = driver.reset_to_screen(screen_cfg)
                current_focus_id = e_reset.element_id
                for step in path:
                    ev_step = driver.press(step)
                    if ev_step:
                        current_focus_id = ev_step.element_id

            ev = driver.press(key)
            probes += 1

            new_id = ev.element_id if ev else el
            if ev:
                graph.add_node(ev.element_id, ev.screen, ev.bounds)
                current_focus_id = ev.element_id
                if new_id not in shots:
                    shots[new_id] = driver.screenshot()
            else:
                current_focus_id = el

            graph.add_edge(el, key, None if ev is None else new_id)

            if ev and ev.screen == screen_name and new_id not in seen and len(path) + 1 <= max_depth:
                seen.add(new_id)
                queue.append((new_id, path + [key]))

            if ev and key in ("UP", "DOWN", "LEFT", "RIGHT"):
                inv_key = inverse(key)
                if inv_key:
                    back = driver.press(inv_key)
                    probes += 1
                    back_id = back.element_id if back else None
                    if back:
                        graph.add_node(back.element_id, back.screen, back.bounds)
                        current_focus_id = back.element_id
                    else:
                        current_focus_id = new_id
                    graph.add_edge(new_id, inv_key, back_id)
            elif ev and key == "BACK":
                # Screen may have changed on BACK, force a reset on next iteration
                current_focus_id = None

    return ScreenResult(
        screen=screen_name,
        graph=graph,
        shots=shots,
        probes=probes,
    )
