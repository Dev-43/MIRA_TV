from mira_tv.cli import main


def test_no_args_prints_help(capsys):
    assert main([]) == 0
    assert "validate-events" in capsys.readouterr().out


def test_unimplemented_returns_2():
    assert main(["explore"]) == 2


def test_validate_events_file(tmp_path, capsys):
    f = tmp_path / "log.txt"
    f.write_text('I ReactNativeJS: MIRA_FOCUS {"seq":1,"screen":"home","element_id":"home.a.1",'
                 '"bounds":{"x":0,"y":0,"w":1,"h":1},"ts":5}\nnoise\n', encoding="utf-8")
    assert main(["validate-events", "--file", str(f)]) == 0
    assert "valid MIRA_FOCUS events: 1" in capsys.readouterr().out


def test_validate_events_missing_file():
    assert main(["validate-events", "--file", "nope.txt"]) == 2
