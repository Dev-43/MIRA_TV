"""Focus navigation graph (BUILD_D.md D3). Owner: D.

Represents UI focus topology: nodes (id, screen, bounds), edges (from, key, to|None).
Methods:
- add_node(id, screen, bounds)
- add_edge(from_id, key, to_id)
- reachable_from(id) -> set[str]
- shortest_path(a, b) -> list[str] | None (BFS)
- reverse_reachable(targets) -> set[str]
- to_dict() -> dict (C2 report schema)
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass
class Node:
    id: str
    screen: str
    bounds: Tuple[int, int, int, int]


class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Dict[str, Optional[str]]] = {}

    def add_node(self, node_id: str, screen: str, bounds: Tuple[int, int, int, int]) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(id=node_id, screen=screen, bounds=bounds)
        else:
            # Update bounds if new bounds are non-zero
            if bounds != (0, 0, 0, 0) and self.nodes[node_id].bounds == (0, 0, 0, 0):
                self.nodes[node_id].bounds = bounds
        if node_id not in self.edges:
            self.edges[node_id] = {}

    def add_edge(self, from_id: str, key: str, to_id: Optional[str]) -> None:
        if from_id not in self.edges:
            self.edges[from_id] = {}
        self.edges[from_id][key] = to_id

    def reachable_from(self, start_id: str) -> Set[str]:
        """All nodes reachable from start_id via directed edges."""
        if start_id not in self.nodes and start_id not in self.edges:
            return set()

        visited: Set[str] = {start_id}
        queue: deque[str] = deque([start_id])

        while queue:
            curr = queue.popleft()
            for key, target in self.edges.get(curr, {}).items():
                if target and target not in visited:
                    visited.add(target)
                    queue.append(target)

        return visited

    def shortest_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """BFS shortest path of key presses from start_id to end_id. Returns list of keys or None."""
        if start_id == end_id:
            return []

        if start_id not in self.nodes and start_id not in self.edges:
            return None

        visited: Set[str] = {start_id}
        queue: deque[Tuple[str, List[str]]] = deque([(start_id, [])])

        while queue:
            curr, path = queue.popleft()
            for key, target in self.edges.get(curr, {}).items():
                if not target:
                    continue
                if target == end_id:
                    return path + [key]
                if target not in visited:
                    visited.add(target)
                    queue.append((target, path + [key]))

        return None

    def reverse_reachable(self, target_ids: Iterable[str]) -> Set[str]:
        """All nodes that have at least one directed path to any node in target_ids."""
        targets = set(target_ids)
        if not targets:
            return set()

        # Build reverse adjacency list
        rev_adj: Dict[str, Set[str]] = {}
        for src, edge_map in self.edges.items():
            for key, dst in edge_map.items():
                if dst:
                    if dst not in rev_adj:
                        rev_adj[dst] = set()
                    rev_adj[dst].add(src)

        visited: Set[str] = set(targets)
        queue: deque[str] = deque(targets)

        while queue:
            curr = queue.popleft()
            for pred in rev_adj.get(curr, set()):
                if pred not in visited:
                    visited.add(pred)
                    queue.append(pred)

        return visited

    def to_dict(self) -> Dict[str, Any]:
        """Format as C2 report schema graph object."""
        node_list = []
        for nid in sorted(self.nodes.keys()):
            n = self.nodes[nid]
            node_list.append({
                "id": n.id,
                "x": n.bounds[0],
                "y": n.bounds[1],
                "w": n.bounds[2],
                "h": n.bounds[3],
            })

        edge_list = []
        for src in sorted(self.edges.keys()):
            for key in sorted(self.edges[src].keys()):
                dst = self.edges[src][key]
                edge_list.append({
                    "from": src,
                    "key": key,
                    "to": dst,
                })

        return {"nodes": node_list, "edges": edge_list}
