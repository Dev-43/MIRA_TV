"""Tests for Bedrock explanation layer: prompt template, stub mode, and caching (Task D6)."""
import pytest

from mira_tv.ai import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
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
