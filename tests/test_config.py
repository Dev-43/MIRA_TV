from mira_tv.config import load_config, load_dotenv


def test_defaults(tmp_path):
    c = load_config(env={}, dotenv_path=str(tmp_path / "missing.env"))
    assert c.adb_path == "adb" and c.key_delay_ms == 400 and c.max_ai_calls == 12
    assert c.bedrock_mode == "stub" and c.indicator_diff_min == 4.0


def test_dotenv_parsing(tmp_path):
    f = tmp_path / ".env"
    f.write_text('# comment\n\nMIRA_KEY_DELAY_MS=250\nAWS_REGION="eu-west-1"\nbadline\n', encoding="utf-8")
    assert load_dotenv(f) == {"MIRA_KEY_DELAY_MS": "250", "AWS_REGION": "eu-west-1"}


def test_env_overrides_dotenv(tmp_path):
    f = tmp_path / ".env"
    f.write_text("MIRA_KEY_DELAY_MS=250\n", encoding="utf-8")
    c = load_config(env={"MIRA_KEY_DELAY_MS": "100"}, dotenv_path=str(f))
    assert c.key_delay_ms == 100
    c2 = load_config(env={}, dotenv_path=str(f))
    assert c2.key_delay_ms == 250


def test_bad_values_fall_back(tmp_path):
    c = load_config(env={"MIRA_KEY_DELAY_MS": "abc", "MIRA_BEDROCK_MODE": "weird"},
                    dotenv_path=str(tmp_path / "x.env"))
    assert c.key_delay_ms == 400 and c.bedrock_mode == "stub"
