"""Tests for git patch apply and revert logic (Task D7)."""
from pathlib import Path
import subprocess
import pytest

from mira_tv.patches import PatchError, apply, revert


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Creates a temporary git repository with initial commit."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True)

    app_dir = tmp_path / "app"
    app_dir.mkdir(parents=True)
    sample_file = app_dir / "Button.tsx"
    sample_file.write_text("export const Button = () => <button>Click</button>;\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(tmp_path), check=True)
    return tmp_path


def test_apply_and_revert_success(temp_git_repo: Path) -> None:
    sample_file = temp_git_repo / "app" / "Button.tsx"
    orig_content = sample_file.read_text(encoding="utf-8")

    # Create unified patch that changes Button
    patch_content = (
        "--- a/app/Button.tsx\n"
        "+++ b/app/Button.tsx\n"
        "@@ -1 +1 @@\n"
        "-export const Button = () => <button>Click</button>;\n"
        "+export const Button = () => <button disabled>Click</button>;\n"
    )
    patch_file = temp_git_repo / "test.patch"
    patch_file.write_text(patch_content, encoding="utf-8")

    # 1. Apply patch
    apply(patch_file, repo_root=temp_git_repo)
    modified_content = sample_file.read_text(encoding="utf-8")
    assert "<button disabled>" in modified_content

    # 2. Revert patch
    revert(patch_file, repo_root=temp_git_repo)
    restored_content = sample_file.read_text(encoding="utf-8")
    assert restored_content == orig_content


def test_apply_missing_file(temp_git_repo: Path) -> None:
    with pytest.raises(PatchError, match="Patch file not found"):
        apply("nonexistent.patch", repo_root=temp_git_repo)


def test_apply_corrupt_patch(temp_git_repo: Path) -> None:
    bad_patch = temp_git_repo / "bad.patch"
    bad_patch.write_text("THIS IS NOT A VALID UNIFIED DIFF\n", encoding="utf-8")
    with pytest.raises(PatchError, match="git apply --check failed"):
        apply(bad_patch, repo_root=temp_git_repo)


def test_revert_unapplied_patch(temp_git_repo: Path) -> None:
    patch_content = (
        "--- a/app/Button.tsx\n"
        "+++ b/app/Button.tsx\n"
        "@@ -1 +1 @@\n"
        "-export const Button = () => <button>Click</button>;\n"
        "+export const Button = () => <button disabled>Click</button>;\n"
    )
    patch_file = temp_git_repo / "unapplied.patch"
    patch_file.write_text(patch_content, encoding="utf-8")

    # Attempting to revert a patch that was never applied should fail
    with pytest.raises(PatchError, match="git apply --reverse --check failed"):
        revert(patch_file, repo_root=temp_git_repo)
