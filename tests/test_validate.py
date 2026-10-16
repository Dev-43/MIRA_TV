from mira_tv.validate import validate_focus_event, validate_report


def good_report():
    return {
        "schema_version": "1", "run_id": "20261018T101500Z", "mode": "fixture",
        "app": {"package": "p", "git_commit": "abc"},
        "screens": [],
        "defects": [{"id": "TRAP:home.card.4", "type": "TRAP", "screen": "home",
                     "element_id": "home.card.4", "path": ["RIGHT"],
                     "evidence": {"detail": "d", "screenshot": "a.png"},
                     "ai_explanation": None, "ai_source": "none"}],
        "verify": [{"defect_id": "TRAP:home.card.4", "fix": "f.patch", "before": "FAIL", "after": "PASS",
                    "before_screenshot": "a.png", "after_screenshot": "b.png"}],
        "summary": {"defects_found": 1, "fixed_verified": 1, "ai_calls": 0},
    }


def test_good_report_ok():
    assert validate_report(good_report()) == []


def test_bad_defect_id():
    r = good_report()
    r["defects"][0]["id"] = "TRAP:other"
    assert any("must be '<type>:<element_id>'" in e for e in validate_report(r))


def test_bad_type_and_after():
    r = good_report()
    r["defects"][0]["type"] = "NOPE"
    r["verify"][0]["after"] = "MAYBE"
    errs = validate_report(r)
    assert any("type invalid" in e for e in errs) and any("PASS or FAIL" in e for e in errs)


def test_missing_summary():
    r = good_report()
    del r["summary"]
    assert validate_report(r)


def test_focus_event_validation():
    ok = {"seq": 1, "screen": "home", "element_id": "home.a.1",
          "bounds": {"x": 0, "y": 0, "w": 0, "h": 0}, "ts": 1}
    assert validate_focus_event(ok) == []
    assert validate_focus_event({"seq": True, "screen": "", "element_id": 1, "bounds": [], "ts": "x"})
