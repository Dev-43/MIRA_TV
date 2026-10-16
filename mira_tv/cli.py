"""Command-line interface. Exit codes: 0 ok, 1 defects found, 2 environment/usage error."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .config import load_config
from .driver import DriverError
from .telemetry import parse_lines

NOT_YET = ["explore", "verify", "report", "demo", "ai-ping"]


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


def _record(out_dir: str, scenario_path: str, driver_type: str, fixture_dir: str | None) -> int:
    p = Path(scenario_path)
    if not p.is_file():
        print(f"scenario file not found: {scenario_path}", file=sys.stderr)
        return 2

    try:
        with open(p, "r", encoding="utf-8") as f:
            scenario = json.load(f)
    except Exception as e:
        print(f"failed to parse scenario {scenario_path}: {e}", file=sys.stderr)
        return 2

    cfg = load_config()

    if driver_type == "fixture":
        if not fixture_dir:
            print("--fixture path is required when --driver is fixture", file=sys.stderr)
            return 2
        from .fixture_driver import FixtureDriver
        try:
            driver = FixtureDriver(fixture_dir)
        except DriverError as e:
            print(f"driver error: {e}", file=sys.stderr)
            return 2
    else:
        from .adb_driver import AdbDriver
        try:
            driver = AdbDriver(cfg, scenario)
        except DriverError as e:
            print(f"driver error: {e}", file=sys.stderr)
            return 2

    from .record import record_fixture
    try:
        data = record_fixture(driver, scenario, out_dir)
        el_count = len(data.get("elements", {}))
        print(f"Recorded {el_count} elements to {out_dir}")
        return 0
    except DriverError as e:
        print(f"recording failed: {e}", file=sys.stderr)
        return 2
    finally:
        driver.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mira_tv", description="MIRA TV remote-control QA agent")
    p.add_argument("--version", action="version", version=f"mira_tv {__version__}")
    sub = p.add_subparsers(dest="command")

    ve = sub.add_parser("validate-events", help="validate MIRA_FOCUS lines in a saved logcat dump")
    ve.add_argument("--file", required=True)

    rec = sub.add_parser("record", help="record live screen exploration session into a fixture folder")
    rec.add_argument("--out", required=True, help="output directory for fixture")
    rec.add_argument("--scenario", default="contracts/scenario.json", help="path to scenario.json")
    rec.add_argument("--driver", choices=["adb", "fixture"], default="adb", help="driver to use")
    rec.add_argument("--fixture", default=None, help="fixture folder when --driver is fixture")

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
    if args.command == "record":
        return _record(args.out, args.scenario, args.driver, args.fixture)
    print(f"'{args.command}' is not implemented yet", file=sys.stderr)
    return 2
