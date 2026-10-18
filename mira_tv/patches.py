"""Git patch application and reversal with checks (BUILD_D.md D7, Contract C3). Owner: D.

Functions:
- apply(patch_path, repo_root=None) -> None
- revert(patch_path, repo_root=None) -> None
"""
from __future__ import annotations

import logging
from pathlib import Path
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class PatchError(Exception):
    """Raised when patch application, verification, or reversal fails."""
    pass


def _run_git_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        res = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=20,
        )
        return res
    except subprocess.TimeoutExpired as e:
        raise PatchError(f"Git command timed out after 20s: {' '.join(cmd)}") from e
    except OSError as e:
        raise PatchError(f"Failed to execute git command: {e}") from e


def apply(patch_path: str | Path, repo_root: Optional[Path] = None) -> None:
    """Apply a unified diff patch after running git apply --check first.

    Raises PatchError if patch file is missing, check fails, or apply fails.
    """
    p = Path(patch_path)
    if not p.is_file():
        raise PatchError(f"Patch file not found: {patch_path}")

    root = (repo_root or Path.cwd()).resolve()

    # 1. Run git apply --check first
    check_cmd = ["git", "apply", "--check", str(p.resolve())]
    check_res = _run_git_cmd(check_cmd, root)
    if check_res.returncode != 0:
        err = check_res.stderr.strip() or check_res.stdout.strip()
        raise PatchError(f"git apply --check failed for {p.name}: {err}")

    # 2. Apply patch
    apply_cmd = ["git", "apply", str(p.resolve())]
    apply_res = _run_git_cmd(apply_cmd, root)
    if apply_res.returncode != 0:
        err = apply_res.stderr.strip() or apply_res.stdout.strip()
        raise PatchError(f"git apply failed for {p.name}: {err}")

    logger.info("Successfully applied patch %s in %s", p.name, root)


def revert(patch_path: str | Path, repo_root: Optional[Path] = None) -> None:
    """Revert an applied unified diff patch using git apply -R after check.

    Raises PatchError if patch file is missing, reverse check fails, or revert fails.
    """
    p = Path(patch_path)
    if not p.is_file():
        raise PatchError(f"Patch file not found: {patch_path}")

    root = (repo_root or Path.cwd()).resolve()

    # 1. Run git apply --reverse --check first
    check_cmd = ["git", "apply", "--reverse", "--check", str(p.resolve())]
    check_res = _run_git_cmd(check_cmd, root)
    if check_res.returncode != 0:
        err = check_res.stderr.strip() or check_res.stdout.strip()
        raise PatchError(f"git apply --reverse --check failed for {p.name}: {err}")

    # 2. Revert patch
    revert_cmd = ["git", "apply", "-R", str(p.resolve())]
    revert_res = _run_git_cmd(revert_cmd, root)
    if revert_res.returncode != 0:
        err = revert_res.stderr.strip() or revert_res.stdout.strip()
        raise PatchError(f"git apply -R failed for {p.name}: {err}")

    logger.info("Successfully reverted patch %s in %s", p.name, root)
