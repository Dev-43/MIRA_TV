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


def test_record_missing_scenario(tmp_path):
    assert main(["record", "--out", str(tmp_path / "out"), "--scenario", "nonexistent.json"]) == 2


def test_record_cli_with_fixture_driver(tmp_path, capsys):
    scenario_file = tmp_path / "scenario.json"
    scenario_file.write_text('{"package": "test.pkg", "screens": [{"screen": "home", "max_probes": 10}]}', encoding="utf-8")
    out_dir = tmp_path / "cli_rec"

    rc = main(["record", "--out", str(out_dir), "--scenario", str(scenario_file), "--driver", "fixture", "--fixture", "fixtures/synthetic_clean"])
    assert rc == 0
    assert "Recorded" in capsys.readouterr().out
    assert (out_dir / "fixture.json").is_file()

