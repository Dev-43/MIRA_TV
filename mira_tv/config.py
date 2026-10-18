"""Environment-driven configuration. Precedence: real environment > .env > defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str | os.PathLike = ".env") -> dict[str, str]:
    """Parse a simple KEY=VALUE file. Ignores blanks and comments. Never raises on a missing file."""
    values: dict[str, str] = {}
    p = Path(path)
    if not p.is_file():
        return values
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            values[key] = val
    return values


@dataclass(frozen=True)
class Config:
    adb_path: str = "adb"
    adb_serial: str = ""
    key_delay_ms: int = 400
    settle_ms: int = 600
    reset_wait_ms: int = 4000
    indicator_diff_min: float = 4.0
    artifacts_dir: str = "artifacts"
    bedrock_mode: str = "stub"  # stub | cache | live
    aws_region: str = "us-east-1"
    bedrock_model_id: str = ""
    max_ai_calls: int = 12


def _int(v: str, default: int) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _float(v: str, default: float) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def load_config(env: dict[str, str] | None = None, dotenv_path: str = ".env") -> Config:
    merged = dict(load_dotenv(dotenv_path))
    merged.update(os.environ if env is None else env)
    # Forward AWS credential variables to os.environ so boto3 discovers them
    for aws_key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_REGION", "AWS_DEFAULT_REGION", "AWS_BEARER_TOKEN_BEDROCK"):
        if aws_key in merged and aws_key not in os.environ:
            os.environ[aws_key] = merged[aws_key]
    d = Config()
    mode = merged.get("MIRA_BEDROCK_MODE", d.bedrock_mode).lower()
    if mode not in ("stub", "cache", "live"):
        mode = "stub"
    return Config(
        adb_path=merged.get("MIRA_ADB_PATH") or d.adb_path,
        adb_serial=merged.get("MIRA_ADB_SERIAL", d.adb_serial),
        key_delay_ms=_int(merged.get("MIRA_KEY_DELAY_MS"), d.key_delay_ms),
        settle_ms=_int(merged.get("MIRA_SETTLE_MS"), d.settle_ms),
        reset_wait_ms=_int(merged.get("MIRA_RESET_WAIT_MS"), d.reset_wait_ms),
        indicator_diff_min=_float(merged.get("MIRA_INDICATOR_DIFF_MIN"), d.indicator_diff_min),
        artifacts_dir=merged.get("MIRA_ARTIFACTS_DIR") or d.artifacts_dir,
        bedrock_mode=mode,
        aws_region=merged.get("AWS_REGION") or d.aws_region,
        bedrock_model_id=merged.get("BEDROCK_MODEL_ID", d.bedrock_model_id),
        max_ai_calls=_int(merged.get("MIRA_MAX_AI_CALLS"), d.max_ai_calls),
    )
