"""Remote keys, ADB keycodes and inverse mapping (BUILD.md glossary)."""

KEYCODES = {
    "UP": 19,
    "DOWN": 20,
    "LEFT": 21,
    "RIGHT": 22,
    "CENTER": 23,
    "BACK": 4,
}

INVERSE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}

# Keys the explorer probes from every element, in this order.
PROBE_KEYS = ["UP", "DOWN", "LEFT", "RIGHT", "BACK"]


def keycode(key: str) -> int:
    try:
        return KEYCODES[key]
    except KeyError:
        raise ValueError(f"unknown key: {key!r}") from None


def inverse(key: str):
    """Return the inverse key, or None for CENTER/BACK."""
    if key not in KEYCODES:
        raise ValueError(f"unknown key: {key!r}")
    return INVERSE.get(key)
