import json

from mira_tv.telemetry import parse_line, parse_lines

PAYLOAD = {"seq": 3, "screen": "home", "element_id": "home.card.1",
           "bounds": {"x": 10, "y": 20, "w": 300, "h": 200}, "ts": 1760000000000}


def line(prefix="", suffix=""):
    return f"{prefix}MIRA_FOCUS {json.dumps(PAYLOAD)}{suffix}"


def test_plain_line():
    ev = parse_line(line())
    assert ev.element_id == "home.card.1" and ev.seq == 3
    assert ev.bounds == (10, 20, 300, 200) and ev.screen == "home"


def test_logcat_prefix_and_quotes():
    ev = parse_line(line("10-18 10:15:00.123  1234  1234 I ReactNativeJS: '", "'"))
    assert ev is not None and ev.element_id == "home.card.1"


def test_no_marker():
    assert parse_line("I ReactNativeJS: hello") is None


def test_malformed_json():
    assert parse_line("MIRA_FOCUS {not json}") is None
    assert parse_line("MIRA_FOCUS no braces here") is None


def test_missing_fields_rejected():
    bad = dict(PAYLOAD)
    del bad["element_id"]
    assert parse_line("MIRA_FOCUS " + json.dumps(bad)) is None


def test_zero_seq_rejected():
    bad = dict(PAYLOAD, seq=0)
    assert parse_line("MIRA_FOCUS " + json.dumps(bad)) is None


def test_parse_lines_counts_bad():
    events, bad = parse_lines([line(), "noise", "MIRA_FOCUS {oops}", line()])
    assert len(events) == 2 and bad == 1


def test_never_raises_on_garbage():
    for g in ["", "{", "}", "MIRA_FOCUS ", "MIRA_FOCUS {", "MIRA_FOCUS }{", "MIRA_FOCUS [1,2]"]:
        assert parse_line(g) is None


def test_noisy_logcat_stream_with_escapes_and_trailing():
    noisy = (
        "04-16 20:15:33.456 1234 5678 D ReactNativeJS: [MIRA] log message before "
        'MIRA_FOCUS {"seq":4,"screen":"home","element_id":"home.card.2","bounds":{"x":600,"y":500,"w":340,"h":220},"ts":1760000000001}'
        " (trailing React stack trace or log metadata)\n"
    )
    ev = parse_line(noisy)
    assert ev is not None
    assert ev.element_id == "home.card.2"
    assert ev.seq == 4
    assert ev.bounds == (600, 500, 340, 220)


def test_zero_bounds_allowed():
    # As per spec: (0,0,0,0) = unknown bounds, should be accepted
    zero_bounds = dict(PAYLOAD, bounds={"x": 0, "y": 0, "w": 0, "h": 0}, seq=5)
    ev = parse_line("MIRA_FOCUS " + json.dumps(zero_bounds))
    assert ev is not None
    assert ev.bounds == (0, 0, 0, 0)

