"""Parser for C1 focus events: lines containing `MIRA_FOCUS {json}` in adb logcat output."""
from __future__ import annotations

import json
from typing import Iterable, List, Optional, Tuple

from .driver import FocusEvent
from .validate import validate_focus_event

MARKER = "MIRA_FOCUS "


def parse_line(line: str) -> Optional[FocusEvent]:
    """Return a FocusEvent, or None if the line has no valid event. Never raises."""
    idx = line.find(MARKER)
    if idx < 0:
        return None
    rest = line[idx + len(MARKER):]
    start = rest.find("{")
    end = rest.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        data = json.loads(rest[start:end + 1])
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or validate_focus_event(data):
        return None
    b = data["bounds"]
    return FocusEvent(
        seq=int(data["seq"]),
        screen=data["screen"],
        element_id=data["element_id"],
        bounds=(int(b["x"]), int(b["y"]), int(b["w"]), int(b["h"])),
        ts=int(data["ts"]),
    )


def parse_lines(lines: Iterable[str]) -> Tuple[List[FocusEvent], int]:
    """Parse many lines. Returns (events, bad_count). bad_count counts lines that mention
    the marker but failed to parse or validate."""
    events: List[FocusEvent] = []
    bad = 0
    for line in lines:
        if MARKER not in line:
            continue
        ev = parse_line(line)
        if ev is None:
            bad += 1
        else:
            events.append(ev)
    return events, bad
