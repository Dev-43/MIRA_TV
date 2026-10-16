"""Ownership checker. Usage:
  python scripts/check_ownership.py --role D            # diff vs origin/main + working tree
  python scripts/check_ownership.py --role V --base main
  python scripts/check_ownership.py --role D --files mira_tv/cli.py tests/test_cli.py
  python scripts/check_ownership.py --role D --contract-change   # allow LOCKED files
Exit code 0 = ok, 1 = violations, 2 = could not read git state.
Keep the lists below identical to OWNERSHIP.md.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

D_OWNS = [
    "mira_tv/**", "tests/**",
    "fixtures/synthetic_clean/**", "fixtures/synthetic_bugs/**",
    "ai_cache/**", "report/build_report.py",
    "contracts/focus_event.schema.json", "contracts/report.schema.json",
    "scripts/smoke.ps1", "scripts/check_ownership.py",
    ".github/workflows/**", ".env.example", ".gitignore", "requirements.txt",
    "docs/FEEDBACK.md",
]
V_OWNS = [
    "app/**", "bugs/**", "fixes/**",
    "contracts/scenario.json", "contracts/expected_elements.json", "contracts/bug_map.json",
    "report/template.html", "report/style.css",
    "scripts/check_hook.ps1", "scripts/check_patches.ps1",
    "fixtures/real_clean/**", "fixtures/real_bugs/**",
    "docs/APP_MAP.md", "docs/DEMO_SCRIPT.md", "README.md", "LICENSE",
]
SHARED_APPEND = ["docs/FRICTION_LOG.md", "DECISION.md"]
LOCKED = [
    "BUILD.md", "BUILD_D.md", "BUILD_V.md", "INTEGRATION.md", "SETUP.md",
    "OWNERSHIP.md", ".github/CODEOWNERS",
]


def _norm(p: str) -> str:
    p = p.replace("\\", "/")
    return p[2:] if p.startswith("./") else p


def matches(path: str, patterns) -> bool:
    path = _norm(path)
    for pat in patterns:
        if pat.endswith("/**"):
            if path.startswith(pat[:-2]):
                return True
        elif path == pat:
            return True
    return False


def category(path: str) -> str:
    """Return D, V, SHARED, LOCKED or UNOWNED."""
    if matches(path, LOCKED):
        return "LOCKED"
    if matches(path, SHARED_APPEND):
        return "SHARED"
    if matches(path, D_OWNS):
        return "D"
    if matches(path, V_OWNS):
        return "V"
    return "UNOWNED"


def violations(role: str, files, contract_change: bool = False):
    """Return a list of (path, reason) for files the role may not touch."""
    out = []
    for f in files:
        cat = category(f)
        if cat == role or cat == "SHARED":
            continue
        if cat == "LOCKED":
            if not contract_change:
                out.append((f, "LOCKED (needs CONTRACT-CHANGE and agreement)"))
            continue
        if cat == "UNOWNED":
            out.append((f, "unowned path (ask first; add to OWNERSHIP.md via CONTRACT-CHANGE)"))
        else:
            out.append((f, f"owned by {cat}"))
    return out


def _git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "git failed")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def changed_files(base: str):
    files = set()
    try:
        files.update(_git("diff", "--name-only", f"{base}...HEAD"))
    except RuntimeError:
        pass  # base may not exist locally yet; fall back to working tree only
    files.update(_git("diff", "--name-only"))
    files.update(_git("diff", "--name-only", "--cached"))
    files.update(_git("ls-files", "--others", "--exclude-standard"))
    return sorted(files)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True, choices=["D", "V"])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--contract-change", action="store_true")
    a = ap.parse_args(argv)
    try:
        files = a.files if a.files is not None else changed_files(a.base)
    except (RuntimeError, OSError) as e:
        print(f"cannot read git state: {e}", file=sys.stderr)
        return 2
    bad = violations(a.role, files, a.contract_change)
    if not bad:
        print(f"OK: {len(files)} changed file(s), all allowed for {a.role}")
        return 0
    print(f"OWNERSHIP VIOLATIONS for {a.role}:")
    for f, why in bad:
        print(f"  {f}  -> {why}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
