"""Command-line interface. Exit codes: 0 ok, 1 defects found, 2 environment/usage error."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional

from . import __version__
from .config import load_config
from .driver import Driver, DriverError
from .telemetry import parse_lines


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


def _explore(
    mode: str,
    fixture_dir: Optional[str] = None,
    scenario_path: Optional[str] = None,
    expected_path: Optional[str] = None,
) -> int:
    cfg = load_config()

    from .demo import SYNTHETIC_EXPECTED_ELEMENTS, SYNTHETIC_SCENARIO
    from .detectors import detect_trap, detect_unreachable
    from .explore import explore_screen
    from .vision import detect_no_indicator

    # Resolve scenario
    if scenario_path and Path(scenario_path).is_file():
        try:
            scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"failed to parse scenario {scenario_path}: {e}", file=sys.stderr)
            return 2
    elif mode == "fixture" and not scenario_path:
        scenario = SYNTHETIC_SCENARIO
    else:
        scen_file = Path("contracts/scenario.json")
        if not scen_file.is_file():
            print("scenario file not found: contracts/scenario.json", file=sys.stderr)
            return 2
        try:
            scenario = json.loads(scen_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"failed to parse scenario: {e}", file=sys.stderr)
            return 2

    # Resolve expected elements
    if expected_path and Path(expected_path).is_file():
        try:
            expected_elements = json.loads(Path(expected_path).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"failed to parse expected elements: {e}", file=sys.stderr)
            return 2
    elif mode == "fixture" and not expected_path:
        expected_elements = SYNTHETIC_EXPECTED_ELEMENTS
    else:
        exp_file = Path("contracts/expected_elements.json")
        if not exp_file.is_file():
            print("expected elements file not found: contracts/expected_elements.json", file=sys.stderr)
            return 2
        try:
            expected_elements = json.loads(exp_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"failed to parse expected elements: {e}", file=sys.stderr)
            return 2

    # Initialize driver
    driver: Driver
    if mode == "fixture":
        from .fixture_driver import FixtureDriver
        fix_dir = Path(fixture_dir or "fixtures/synthetic_bugs")
        if not fix_dir.is_dir():
            print(f"fixture directory not found: {fix_dir}", file=sys.stderr)
            return 2
        try:
            driver = FixtureDriver(fix_dir)
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

    all_defects = []
    try:
        for screen_cfg in scenario.get("screens", []):
            screen_name = screen_cfg.get("screen", "")
            print(f"Exploring screen: {screen_name}...")
            res = explore_screen(driver, screen_cfg)
            print(f"  Probes: {res.probes}, elements visited: {len(res.graph.nodes)}")

            unreachable = detect_unreachable(res, expected_elements)
            trap = detect_trap(res, screen_cfg.get("exit_targets", []))
            no_ind = detect_no_indicator(res, diff_min=cfg.indicator_diff_min)

            defects = unreachable + trap + no_ind
            all_defects.extend(defects)

        all_defects.sort(key=lambda d: (d.screen, d.type, d.element_id))
        print(f"\nDefects found: {len(all_defects)}")
        for d in all_defects:
            print(f"  [{d.type}] {d.id} on {d.screen} - {d.detail}")

        return 1 if all_defects else 0
    except DriverError as e:
        print(f"driver error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"exploration error: {e}", file=sys.stderr)
        return 2
    finally:
        driver.close()


def _verify(
    mode: str,
    fixture_dir: Optional[str] = None,
    clean_fixture_dir: Optional[str] = None,
    scenario_path: Optional[str] = None,
    expected_path: Optional[str] = None,
    bug_map_path: Optional[str] = None,
    out_dir: Optional[str] = None,
) -> int:
    cfg = load_config()

    from .demo import SYNTHETIC_EXPECTED_ELEMENTS, SYNTHETIC_SCENARIO
    from .detectors import detect_trap, detect_unreachable
    from .explore import explore_screen
    from .verify import verify_defect
    from .vision import detect_no_indicator

    # Resolve scenario
    if scenario_path and Path(scenario_path).is_file():
        scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
    elif mode == "fixture" and not scenario_path:
        scenario = SYNTHETIC_SCENARIO
    else:
        scenario = json.loads(Path("contracts/scenario.json").read_text(encoding="utf-8"))

    # Resolve expected elements
    if expected_path and Path(expected_path).is_file():
        expected_elements = json.loads(Path(expected_path).read_text(encoding="utf-8"))
    elif mode == "fixture" and not expected_path:
        expected_elements = SYNTHETIC_EXPECTED_ELEMENTS
    else:
        expected_elements = json.loads(Path("contracts/expected_elements.json").read_text(encoding="utf-8"))

    # Resolve bug map
    bmap_file = Path(bug_map_path or "contracts/bug_map.json")
    if bmap_file.is_file():
        bug_map_raw = json.loads(bmap_file.read_text(encoding="utf-8"))
        bug_map = {k: v for k, v in bug_map_raw.items() if not k.startswith("_")}
    else:
        bug_map = {}

    run_out = Path(out_dir or "artifacts/verify_run")
    run_out.mkdir(parents=True, exist_ok=True)

    # Initialize driver
    driver: Driver
    if mode == "fixture":
        from .fixture_driver import FixtureDriver
        fix_dir = Path(fixture_dir or "fixtures/synthetic_bugs")
        if not fix_dir.is_dir():
            print(f"fixture directory not found: {fix_dir}", file=sys.stderr)
            return 2
        try:
            driver = FixtureDriver(fix_dir)
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

    try:
        screen_results_before = {}
        all_defects = []
        for screen_cfg in scenario.get("screens", []):
            screen_name = screen_cfg.get("screen", "")
            res = explore_screen(driver, screen_cfg)
            screen_results_before[screen_name] = res

            unreachable = detect_unreachable(res, expected_elements)
            trap = detect_trap(res, screen_cfg.get("exit_targets", []))
            no_ind = detect_no_indicator(res, diff_min=cfg.indicator_diff_min)
            all_defects.extend(unreachable + trap + no_ind)

        clean_fix_path = Path(clean_fixture_dir or "fixtures/synthetic_clean")
        verified_items = []
        for defect in all_defects:
            mapping = bug_map.get(defect.id)
            if not mapping:
                continue
            fix_patch = mapping.get("fix", "")
            s_res = screen_results_before[defect.screen]
            v_item = verify_defect(
                driver=driver,
                defect=defect,
                fix_patch=fix_patch,
                scenario=scenario,
                expected_elements=expected_elements,
                screen_result_before=s_res,
                out_dir=run_out,
                mode=mode,
                clean_fixture_dir=clean_fix_path,
                indicator_diff_min=cfg.indicator_diff_min,
                initial_defects=all_defects,
            )
            verified_items.append(v_item)
            status_tag = "PASS" if v_item.after == "PASS" else "FAIL"
            print(f"[{status_tag}] {v_item.defect_id} (fix: {v_item.fix}) -> {v_item.after} ({v_item.detail})")

        if not verified_items:
            print("No matching defects from bug_map found to verify.")
            return 0

        all_pass = all(v.after == "PASS" for v in verified_items)
        return 0 if all_pass else 1
    except DriverError as e:
        print(f"driver error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"verification error: {e}", file=sys.stderr)
        return 2
    finally:
        driver.close()


def _ai_ping() -> int:
    from .ai import ai_ping
    cfg = load_config()
    if cfg.bedrock_mode.lower() == "stub":
        print("OK (stub)")
        return 0
    ok = ai_ping(cfg)
    if ok:
        print("OK")
        return 0
    print("FAIL: Bedrock ping failed or credentials not configured", file=sys.stderr)
    return 2


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

    sub.add_parser("ai-ping", help="test Bedrock Converse connectivity or stub mode")

    exp = sub.add_parser("explore", help="explore screens and report discovered defects")
    exp.add_argument("--mode", choices=["fixture", "live"], default="fixture", help="driver mode")
    exp.add_argument("--fixture", default=None, help="fixture folder when mode is fixture")
    exp.add_argument("--scenario", default=None, help="path to scenario.json")
    exp.add_argument("--expected", default=None, help="path to expected_elements.json")

    ver = sub.add_parser("verify", help="verify defect fixes against scenario and bug map")
    ver.add_argument("--mode", choices=["fixture", "live"], default="fixture", help="driver mode")
    ver.add_argument("--fixture", default=None, help="fixture folder when mode is fixture")
    ver.add_argument("--clean-fixture", default=None, help="clean fixture folder when mode is fixture")
    ver.add_argument("--scenario", default=None, help="path to scenario.json")
    ver.add_argument("--expected", default=None, help="path to expected_elements.json")
    ver.add_argument("--bug-map", default=None, help="path to bug_map.json")
    ver.add_argument("--out", default=None, help="output directory for verify artifacts")

    dm = sub.add_parser("demo", help="run full QA demo (bugs -> explore -> explain -> verify -> report)")
    dm.add_argument("--mode", choices=["fixture", "live"], default="fixture", help="demo execution mode")
    dm.add_argument("--fixture", default=None, help="fixture folder for fixture mode")
    dm.add_argument("--scenario", default=None, help="path to scenario.json")
    dm.add_argument("--no-restore", action="store_true", help="do not restore patches in live mode")
    dm.add_argument("--out", default=None, help="output artifacts directory")

    rp = sub.add_parser("report", help="compile report.html from report.json in a run directory")
    rp.add_argument("--run-dir", required=True, help="path to run directory (e.g. artifacts/<run_id>)")

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
    if args.command == "ai-ping":
        return _ai_ping()
    if args.command == "explore":
        return _explore(
            mode=args.mode,
            fixture_dir=args.fixture,
            scenario_path=args.scenario,
            expected_path=args.expected,
        )
    if args.command == "verify":
        return _verify(
            mode=args.mode,
            fixture_dir=args.fixture,
            clean_fixture_dir=args.clean_fixture,
            scenario_path=args.scenario,
            expected_path=args.expected,
            bug_map_path=args.bug_map,
            out_dir=args.out,
        )
    if args.command == "report":
        from report.build_report import build_report
        try:
            out_file = build_report(args.run_dir)
            print(f"Report built: {out_file}")
            return 0
        except Exception as e:
            print(f"Report build failed: {e}", file=sys.stderr)
            return 2
    if args.command == "demo":
        from .demo import run_demo
        try:
            out_html = run_demo(
                mode=args.mode,
                fixture_dir=args.fixture,
                scenario_path=args.scenario,
                no_restore=args.no_restore,
                artifacts_dir=args.out,
            )
            print(f"Demo completed successfully. Report generated at: {out_html}")
            return 0
        except Exception as e:
            print(f"Demo failed: {e}", file=sys.stderr)
            return 2

    print(f"'{args.command}' is not implemented yet", file=sys.stderr)
    return 2
