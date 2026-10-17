"""Bedrock Converse explanation layer (BUILD_D.md D6). Owner: D.

Provides plain-language developer explanations of deterministically proven defects.
Guardrails:
- Fixed system prompt (PROMPT_VERSION = "1"), max 60 words, never changes verdict.
- Modes: 'stub' | 'cache' | 'live' (default 'stub').
- Deterministic SHA-256 disk caching in ai_cache/<key>.json.
- Hard cap MIRA_MAX_AI_CALLS (12).
- Never crashes a run: fallback to stub on error.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .config import Config, load_config
from .detectors import Defect

logger = logging.getLogger(__name__)

PROMPT_VERSION = "1"
SYSTEM_PROMPT = (
    "You are a TV app QA assistant. A deterministic test already proved the defect "
    "described. In at most 60 words, explain what a remote-control user would experience "
    "and the most likely cause. Do not change the verdict."
)


def explain_stub(defect: Defect) -> str:
    """Deterministic plain-language template text for stub mode and fallback."""
    if defect.type == "UNREACHABLE":
        return (
            f"Control '{defect.element_id}' on screen '{defect.screen}' cannot be focused "
            f"via remote-control navigation. Remote users cannot interact with this element."
        )
    elif defect.type == "TRAP":
        return (
            f"Focus is trapped at '{defect.element_id}' on screen '{defect.screen}'. "
            f"Remote users cannot navigate back or exit this region using D-pad keys or BACK."
        )
    elif defect.type == "NO_FOCUS_INDICATOR":
        return (
            f"Element '{defect.element_id}' on screen '{defect.screen}' lacks a visible "
            f"focus indicator. Remote users cannot determine which element is currently selected."
        )
    return (
        f"Defect '{defect.id}' was detected on screen '{defect.screen}'. "
        f"Remote navigation behavior is impaired."
    )


def compute_cache_key(
    prompt_version: str,
    model_id: str,
    defect_id: str,
    image_bytes: bytes,
) -> str:
    """Cache key = sha256(PROMPT_VERSION + model_id + defect_id + sha256(image bytes))."""
    image_sha = hashlib.sha256(image_bytes).hexdigest()
    raw = f"{prompt_version}:{model_id}:{defect_id}:{image_sha}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ExplanationEngine:
    """Manages AI explanation generation across stub, cache, and live Bedrock modes."""

    def __init__(self, cfg: Optional[Config] = None):
        self.config = cfg or load_config()
        self.ai_calls = 0

    def explain(
        self,
        defect: Defect,
        annotated_png: bytes,
    ) -> Tuple[str, str]:
        """Explain a defect. Returns (explanation_text, ai_source).

        ai_source is one of 'bedrock' | 'cache' | 'stub'.
        """
        mode = self.config.bedrock_mode.lower()
        if mode == "stub":
            return explain_stub(defect), "stub"

        # cache and live modes are implemented in subsequent steps
        return explain_stub(defect), "stub"


_DEFAULT_ENGINE: Optional[ExplanationEngine] = None


def explain(
    defect: Defect,
    annotated_png: bytes,
    cfg: Optional[Config] = None,
) -> Tuple[str, str]:
    """Convenience functional wrapper around ExplanationEngine.explain."""
    global _DEFAULT_ENGINE
    if cfg is not None:
        return ExplanationEngine(cfg).explain(defect, annotated_png)
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = ExplanationEngine()
    return _DEFAULT_ENGINE.explain(defect, annotated_png)
