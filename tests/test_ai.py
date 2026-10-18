"""Tests for Bedrock explanation layer: prompt template, stub mode, and caching (Task D6)."""
from pathlib import Path
import pytest

from mira_tv.ai import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    ExplanationEngine,
    compute_cache_key,
    explain,
    explain_stub,
)
from mira_tv.config import Config
from mira_tv.detectors import Defect


def test_system_prompt_guardrails() -> None:
    assert PROMPT_VERSION == "1"
    assert "at most 60 words" in SYSTEM_PROMPT
    assert "Do not change the verdict" in SYSTEM_PROMPT


def test_explain_stub_concise_words_constraint() -> None:
    defects = [
        Defect("UNREACHABLE", "details", "details.btn.addlist", [], "never focused"),
        Defect("TRAP", "home", "home.card.4", ["RIGHT"], "trapped"),
        Defect("NO_FOCUS_INDICATOR", "home", "home.card.2", ["RIGHT"], "diff < 4.0"),
    ]
    for d in defects:
        text = explain_stub(d)
        word_count = len(text.split())
        assert word_count <= 60, f"Stub explanation exceeds 60 words ({word_count}): {text}"
        assert d.element_id in text
        assert d.screen in text


def test_explain_stub_mode() -> None:
    cfg = Config(bedrock_mode="stub")
    defect = Defect("UNREACHABLE", "details", "details.btn.addlist", [], "never focused")
    dummy_png = b"\x89PNG\r\n\x1a\nfakeimage"

    text, source = explain(defect, dummy_png, cfg=cfg)
    assert source == "stub"
    assert "details.btn.addlist" in text


def test_compute_cache_key_determinism() -> None:
    key1 = compute_cache_key("1", "anthropic.claude-v1", "TRAP:home.card.4", b"png1")
    key2 = compute_cache_key("1", "anthropic.claude-v1", "TRAP:home.card.4", b"png1")
    key3 = compute_cache_key("1", "anthropic.claude-v1", "TRAP:home.card.4", b"png2")

    assert len(key1) == 64
    assert key1 == key2
    assert key1 != key3


def test_cache_hit_and_miss(tmp_path: Path) -> None:
    cfg = Config(bedrock_mode="cache", bedrock_model_id="anthropic.claude-v1")
    engine = ExplanationEngine(cfg=cfg, cache_dir=tmp_path)
    defect = Defect("TRAP", "home", "home.card.4", ["RIGHT"], "trapped in card pocket")
    img = b"fake-annotated-image-bytes"

    # 1. Cache miss -> falls back to stub text and source "stub"
    text1, source1 = engine.explain(defect, img)
    assert source1 == "stub"
    assert "home.card.4" in text1

    # 2. Put cache entry
    key = compute_cache_key(PROMPT_VERSION, cfg.bedrock_model_id, defect.id, img)
    custom_explanation = "This is a vetted cached Bedrock response explaining the trap."
    engine.put_cache_entry(key, custom_explanation, defect.id)

    # 3. Cache hit -> returns cached text and source "cache"
    text2, source2 = engine.explain(defect, img)
    assert source2 == "cache"
    assert text2 == custom_explanation

    # 4. Corrupted cache file -> falls back to stub
    cache_file = tmp_path / f"{key}.json"
    cache_file.write_text("NOT_VALID_JSON", encoding="utf-8")
    text3, source3 = engine.explain(defect, img)
    assert source3 == "stub"


class FakeBedrockClient:
    def __init__(self, response_text: str = "Live explanation from Bedrock Claude.", should_fail: bool = False):
        self.response_text = response_text
        self.should_fail = should_fail
        self.calls = 0

    def converse(self, **kwargs) -> dict:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("Bedrock connection timeout")
        return {
            "output": {
                "message": {
                    "content": [{"text": self.response_text}],
                }
            }
        }


def test_live_mode_success_and_caching(tmp_path: Path) -> None:
    fake_client = FakeBedrockClient(response_text="Focus is unreachable due to missing link.")
    cfg = Config(bedrock_mode="live", bedrock_model_id="us.anthropic.claude-3-haiku-20240307-v1:0", max_ai_calls=5)
    engine = ExplanationEngine(cfg=cfg, cache_dir=tmp_path, client=fake_client)
    defect = Defect("UNREACHABLE", "details", "details.btn.addlist", [], "never focused")
    img = b"fake-png-data"

    text, source = engine.explain(defect, img)
    assert source == "bedrock"
    assert text == "Focus is unreachable due to missing link."
    assert engine.ai_calls == 1
    assert fake_client.calls == 1

    # Verify response was persisted to disk cache
    key = compute_cache_key(PROMPT_VERSION, cfg.bedrock_model_id, defect.id, img)
    assert (tmp_path / f"{key}.json").is_file()


def test_live_mode_hard_cap(tmp_path: Path) -> None:
    fake_client = FakeBedrockClient(response_text="Explanation")
    cfg = Config(bedrock_mode="live", bedrock_model_id="anthropic.claude", max_ai_calls=2)
    engine = ExplanationEngine(cfg=cfg, cache_dir=tmp_path, client=fake_client)
    defect = Defect("TRAP", "home", "home.card.4", ["RIGHT"], "trapped")
    img = b"fake-png"

    # First 2 calls succeed with live Bedrock
    t1, s1 = engine.explain(defect, img)
    assert s1 == "bedrock"
    t2, s2 = engine.explain(defect, img)
    assert s2 == "bedrock"
    assert engine.ai_calls == 2
    assert fake_client.calls == 2

    # 3rd call exceeds max_ai_calls=2 -> falls back to stub, does NOT call client
    t3, s3 = engine.explain(defect, img)
    assert s3 == "stub"
    assert fake_client.calls == 2  # Client was NOT called again


def test_live_mode_exception_fallback(tmp_path: Path) -> None:
    fake_client = FakeBedrockClient(should_fail=True)
    cfg = Config(bedrock_mode="live", bedrock_model_id="anthropic.claude", max_ai_calls=5)
    engine = ExplanationEngine(cfg=cfg, cache_dir=tmp_path, client=fake_client)
    defect = Defect("NO_FOCUS_INDICATOR", "home", "home.card.2", ["RIGHT"], "diff < 4.0")
    img = b"fake-png"

    # Exception in Bedrock call must NOT crash; must return stub
    text, source = engine.explain(defect, img)
    assert source == "stub"
    assert "home.card.2" in text
