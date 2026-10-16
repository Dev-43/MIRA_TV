import pytest
from mira_tv.graph import Graph


def test_empty_graph():
    g = Graph()
    assert g.reachable_from("a") == set()
    assert g.shortest_path("a", "b") is None
    assert g.shortest_path("a", "a") == []
    assert g.reverse_reachable(["a"]) == {"a"}


def test_linear_path():
    g = Graph()
    g.add_node("a", "home", (0, 0, 10, 10))
    g.add_node("b", "home", (10, 0, 10, 10))
    g.add_node("c", "home", (20, 0, 10, 10))

    g.add_edge("a", "RIGHT", "b")
    g.add_edge("b", "RIGHT", "c")
    g.add_edge("c", "LEFT", "b")
    g.add_edge("b", "LEFT", "a")

    assert g.reachable_from("a") == {"a", "b", "c"}
    assert g.shortest_path("a", "c") == ["RIGHT", "RIGHT"]
    assert g.shortest_path("c", "a") == ["LEFT", "LEFT"]


def test_shortest_path_prefers_fewer_hops():
    g = Graph()
    # Path 1: a -> b -> c -> d (3 hops)
    # Path 2: a -> e -> d (2 hops)
    g.add_edge("a", "DOWN", "b")
    g.add_edge("b", "DOWN", "c")
    g.add_edge("c", "RIGHT", "d")
    g.add_edge("a", "RIGHT", "e")
    g.add_edge("e", "DOWN", "d")

    path = g.shortest_path("a", "d")
    assert path == ["RIGHT", "DOWN"]


def test_reverse_reachable_and_trap():
    g = Graph()
    # Main reachable component
    g.add_edge("exit", "RIGHT", "main1")
    g.add_edge("main1", "LEFT", "exit")

    # Trap pocket: can enter trap1 from main1, but once inside, can only cycle
    g.add_edge("main1", "DOWN", "trap1")
    g.add_edge("trap1", "RIGHT", "trap2")
    g.add_edge("trap2", "LEFT", "trap1")
    # No path from trap1 or trap2 back to exit!

    rev = g.reverse_reachable(["exit"])
    assert "exit" in rev
    assert "main1" in rev
    assert "trap1" not in rev
    assert "trap2" not in rev


def test_to_dict_format():
    g = Graph()
    g.add_node("home.1", "home", (10, 20, 30, 40))
    g.add_edge("home.1", "RIGHT", "home.2")

    d = g.to_dict()
    assert "nodes" in d and "edges" in d
    assert d["nodes"] == [{"id": "home.1", "x": 10, "y": 20, "w": 30, "h": 40}]
    assert d["edges"] == [{"from": "home.1", "key": "RIGHT", "to": "home.2"}]
