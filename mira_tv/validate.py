"""Hand-written validators (no jsonschema dependency). Each returns a list of error strings."""
from __future__ import annotations

DEFECT_TYPES = ("UNREACHABLE", "TRAP", "NO_FOCUS_INDICATOR")
AI_SOURCES = ("bedrock", "cache", "stub", "none")


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate_focus_event(d: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(d, dict):
        return ["event is not an object"]
    if not _is_int(d.get("seq")) or d.get("seq", 0) < 1:
        errs.append("seq must be an integer >= 1")
    for k in ("screen", "element_id"):
        if not isinstance(d.get(k), str) or not d.get(k):
            errs.append(f"{k} must be a non-empty string")
    if not _is_int(d.get("ts")):
        errs.append("ts must be an integer")
    b = d.get("bounds")
    if not isinstance(b, dict):
        errs.append("bounds must be an object")
    else:
        for k in ("x", "y", "w", "h"):
            if not _is_int(b.get(k)):
                errs.append(f"bounds.{k} must be an integer")
    return errs


def validate_report(r: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(r, dict):
        return ["report is not an object"]
    if r.get("schema_version") != "1":
        errs.append('schema_version must be "1"')
    for k in ("run_id", "mode"):
        if not isinstance(r.get(k), str) or not r.get(k):
            errs.append(f"{k} must be a non-empty string")
    if r.get("mode") not in ("live", "fixture"):
        errs.append("mode must be 'live' or 'fixture'")
    app = r.get("app")
    if not isinstance(app, dict) or "package" not in app or "git_commit" not in app:
        errs.append("app must have package and git_commit")
    for k in ("screens", "defects", "verify"):
        if not isinstance(r.get(k), list):
            errs.append(f"{k} must be a list")
    for i, d in enumerate(r.get("defects") or []):
        if not isinstance(d, dict):
            errs.append(f"defects[{i}] must be an object")
            continue
        if d.get("type") not in DEFECT_TYPES:
            errs.append(f"defects[{i}].type invalid")
        for k in ("id", "screen", "element_id"):
            if not isinstance(d.get(k), str) or not d.get(k):
                errs.append(f"defects[{i}].{k} must be a non-empty string")
        if isinstance(d.get("id"), str) and isinstance(d.get("element_id"), str) \
                and d.get("type") in DEFECT_TYPES \
                and d["id"] != f"{d['type']}:{d['element_id']}":
            errs.append(f"defects[{i}].id must be '<type>:<element_id>'")
        if not isinstance(d.get("path"), list):
            errs.append(f"defects[{i}].path must be a list")
        if d.get("ai_source") not in AI_SOURCES:
            errs.append(f"defects[{i}].ai_source invalid")
    for i, v in enumerate(r.get("verify") or []):
        if not isinstance(v, dict):
            errs.append(f"verify[{i}] must be an object")
            continue
        if v.get("before") != "FAIL":
            errs.append(f"verify[{i}].before must be 'FAIL'")
        if v.get("after") not in ("PASS", "FAIL"):
            errs.append(f"verify[{i}].after must be PASS or FAIL")
    s = r.get("summary")
    if not isinstance(s, dict) or not all(_is_int(s.get(k)) for k in ("defects_found", "fixed_verified", "ai_calls")):
        errs.append("summary needs integer defects_found, fixed_verified, ai_calls")
    return errs
