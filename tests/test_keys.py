import pytest

from mira_tv.keys import KEYCODES, PROBE_KEYS, inverse, keycode


def test_keycodes():
    assert keycode("UP") == 19 and keycode("DOWN") == 20
    assert keycode("LEFT") == 21 and keycode("RIGHT") == 22
    assert keycode("CENTER") == 23 and keycode("BACK") == 4


def test_unknown_key():
    with pytest.raises(ValueError):
        keycode("HOME")
    with pytest.raises(ValueError):
        inverse("HOME")


def test_inverse():
    assert inverse("UP") == "DOWN" and inverse("LEFT") == "RIGHT"
    assert inverse("CENTER") is None and inverse("BACK") is None


def test_probe_keys_are_known():
    assert all(k in KEYCODES for k in PROBE_KEYS)
