"""Command-line interface. Exit codes: 0 ok, 1 defects found, 2 environment/usage error."""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .telemetry import parse_lines

NOT_YET = ["explore", "verify", "record", "report", "demo", "ai-ping"]


def _validate_events(path: str) -> int:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            events, bad = parse_lines(f)
    except OSError as e:
        print(f"cannot read {path}: {e}", file=sys.stderr)
        return 2
    print(f"valid MIRA_FOCUS events: {len(events)}")
    print(f"invalid MIRA_FOCUS lines: {bad}")
    if events:
        screens = sorted({e.screen for e in events})
        print(f"screens seen: {', '.join(screens)}")
    return 0 if events and bad == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mira_tv", description="MIRA TV remote-control QA agent")
    p.add_argument("--version", action="version", version=f"mira_tv {__version__}")
    sub = p.add_subparsers(dest="command")
    ve = sub.add_parser("validate-events", help="validate MIRA_FOCUS lines in a saved logcat dump")
    ve.add_argument("--file", required=True)
    for name in NOT_YET:
        sub.add_parser(name, help="(not implemented yet)")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "validate-events":
        return _validate_events(args.file)
    print(f"'{args.command}' is not implemented yet", file=sys.stderr)
    return 2
