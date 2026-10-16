# DECISION.md — MIRA TV Decision Records & Codebase Understanding

> **Document Status**: Live & Mandatory for both **D** (Engine) and **V** (App/Report/Demo).  
> **Rule**: Append-only log. Every design decision, architectural choice, and code file added/modified must be documented here before PR merge and reviewed at integration checkpoints (CP0–CP5).

---

## 1. Executive Summary & Purpose

MIRA TV is an autonomous remote-control QA agent for Fire TV and Android TV applications. The project is built under strict hardware segregation, determinism guardrails, and role boundaries:
- **Teammate D (Engine)**: Operates without requiring an emulator on low-spec hardware using `FixtureDriver`, owning the core Python exploration engine (`mira_tv/`), test suites (`tests/`), validation schemas (`contracts/*.schema.json`), report compiler, and product feedback.
- **Teammate V (App/Integration)**: Operates the Android TV (1080p) emulator on high-spec hardware, owning the target React Native sample app (`app/`), the focus reporting instrumentation hook (`app/mira/reportFocus.ts`), bug injection and fix patches (`bugs/`, `fixes/`), scenario files, and report UI templates.

This document serves two primary functions:
1. **Architectural Decision Records (ADRs)**: Captures foundational design choices, tradeoffs, and rationale established during project initiation.
2. **Codebase Understanding & Ledger**: Detailed breakdown of all files initialized by Claude (Task D1/D2 skeleton and V contracts), their operational roles, and dependencies across team boundaries.

---

## 2. Architectural Decision Records (ADRs)

### ADR-001: Deterministic Defect Detection vs AI Explanation Layer
- **Status**: Accepted & Locked
- **Context**: Autonomous testing agents often suffer from non-deterministic evaluations or hallucinations when relying on LLMs/Vision models to judge test success or failure.
- **Decision**: Defect identification and test PASS/FAIL verdicts are **100% deterministic** and computed exclusively by algorithmic graph traversal and pixel-level comparison:
  1. `UNREACHABLE`: Set difference between expected element IDs and explored graph nodes.
  2. `TRAP`: BFS reverse-reachability analysis from designated exit targets.
  3. `NO_FOCUS_INDICATOR`: Mean absolute pixel difference across element bounding box below `MIRA_INDICATOR_DIFF_MIN`.
- **Role of AI (Amazon Bedrock)**: Claude Vision via Bedrock Converse API is strictly used as an **explanation layer** to produce plain-language developer summaries of already-proven defects. AI output can never alter or influence test verdicts.
- **Consequences**: Zero hallucinated failures; deterministic replayability across runs; meets strict hackathon truthfulness criteria.

### ADR-002: Hardware Isolation via Abstract Driver Interface
- **Status**: Accepted & Locked
- **Context**: Running Android Studio TV emulators requires high RAM and hardware virtualization (VT-x/Hyper-V). Teammate D has a lower-spec machine, while Teammate V has a high-spec development environment.
- **Decision**: Decouple the test engine from ADB via an abstract `Driver` base class (`mira_tv/driver.py`):
  - `AdbDriver`: Drives real emulator over ADB via subprocesses, keyevents, screencap, and logcat parsing. Runs exclusively on V's laptop.
  - `FixtureDriver`: Replays pre-recorded UI graph sessions and screenshots loaded from disk (`fixtures/`). Runs on D's laptop with zero emulator, zero Android SDK, and zero network requirement.
- **Consequences**: D can develop and unit-test the entire engine, exploration graph, AI caching, and report builder independently without ever booting an emulator.

### ADR-003: Contract-First Integration Architecture (C1–C5)
- **Status**: Accepted & Locked
- **Context**: Two developers working in parallel need strict interfaces to avoid merge conflicts and integration mismatches.
- **Decision**: Define five inviolable contracts:
  1. **C1 (Focus Telemetry)**: The TV app emits standard logcat events formatted as `MIRA_FOCUS {"seq":..., "screen":..., "element_id":..., "bounds":..., "ts":...}` on tag `ReactNativeJS`. Emitted only when `__DEV__` is true.
  2. **C2 (`report.json` v1)**: Strict JSON schema defining run metadata, explored screen graphs (`graph_before`, `graph_after`), discovered defect lists, and fix verification before/after proofs.
  3. **C3 (Unified Patch Format)**: Defects and repairs are represented as unified diffs (`bugs/BUG-0N-*.patch`, `fixes/FIX-0N-*.patch`) touching $\le 20$ lines only under `app/`. Reversible via `git apply -R`.
  4. **C4 (Scenarios & Expectations)**: `contracts/scenario.json` configures launch activities, entry sequences, and BFS depth/probe limits. `contracts/expected_elements.json` lists all interactive targets.
  5. **C5 (Report Template Token Injection)**: Report UI is a static offline HTML document. D's `build_report.py` injects compiled JSON into a single token (`/*__MIRA_REPORT_JSON__*/null`) and inlines `report/style.css`.
- **Consequences**: Changes to contracts require explicit agreement and PR commit prefix `CONTRACT-CHANGE:`.

### ADR-004: Strict Guardrails, Timeouts, and Reversibility
- **Status**: Accepted & Locked
- **Context**: Automated test engines driving real devices can hang, leak secrets, or leave test apps in broken states.
- **Decision**:
  - All ADB subprocess calls enforce a hard 20-second timeout.
  - Bedrock API calls default to `stub` mode, cache every successful response in `ai_cache/`, and enforce a hard cap of 12 calls (`MIRA_MAX_AI_CALLS`) with a 30-second timeout and 2 retries.
  - Test scripts (`demo`) must always execute `git apply -R` in a `finally` block to guarantee a clean git working tree on failure.
  - Telemetry is guarded by `__DEV__` to prevent overhead in production builds.

### ADR-005: Zero External Dependency Bloat
- **Status**: Accepted & Locked
- **Context**: Excessive dependencies increase vulnerability surface, setup friction, and cross-platform installation failures on Windows.
- **Decision**:
  - Python dependencies are strictly limited to `Pillow>=10`, `boto3`, and `pytest>=8`.
  - No `python-dotenv` package: custom robust `.env` parser in `mira_tv/config.py`.
  - No `jsonschema` package: hand-written deterministic schema validators in `mira_tv/validate.py`.
  - Report UI is 100% vanilla HTML/CSS/JS with zero CDNs, zero NPM packages, working offline from `file://`.

---

## 3. Codebase Understanding & File Ledger (Claude Init Audit)

This section documents every file generated during Claude's initialization phase (Task D1/D2 skeleton and initial contracts), explaining its technical design, responsibilities, and interactions.

```
mira-tv/
├── .env.example                     # Environment template listing all configurable engine parameters
├── .gitignore                       # Repository exclusion rules (Python, Node, Android Gradle, IDEs)
├── .github/
│   ├── CODEOWNERS                   # GitHub path-based ownership enforcement matching OWNERSHIP.md
│   └── workflows/test.yml           # CI workflow running pytest on Python 3.12 (Ubuntu)
├── BUILD.md                         # Master specification, contracts C1-C5, guardrails, file structure
├── BUILD_D.md                       # Teammate D (Engine) task roadmap and deliverables (D1-D12)
├── BUILD_V.md                       # Teammate V (App/Demo) task roadmap and deliverables (V0-V9)
├── DECISION.md                      # Architecture Decision Records and Codebase Understanding (This file)
├── INTEGRATION.md                   # Daily sync, milestone checkpoints (CP0-CP5), git rules, risks
├── OWNERSHIP.md                     # File ownership boundaries enforced by scripts/check_ownership.py
├── README.md                        # Submission documentation outline and judge quickstart instructions
├── SETUP.md                         # Developer onboarding guide for D (low-spec) and V (high-spec)
├── requirements.txt                 # Pinned Python dependencies (Pillow, boto3, pytest)
├── contracts/
│   ├── bug_map.json                 # Mapping of defect IDs to corresponding bug/fix patch pairs
│   ├── expected_elements.json       # Interactive element inventory expected per screen
│   ├── focus_event.schema.json      # JSON Schema definition for C1 MIRA_FOCUS logcat lines
│   ├── report.schema.json           # JSON Schema definition for C2 report.json v1 format
│   └── scenario.json                # Test execution parameters (entry steps, exit targets, max probes)
├── app/
│   └── mira/
│       └── reportFocus.ts           # React Native hook emitting MIRA_FOCUS logcat events
├── mira_tv/
│   ├── __init__.py                  # Package root defining __version__ = "0.1.0"
│   ├── __main__.py                  # CLI entrypoint forwarding to mira_tv.cli.main()
│   ├── cli.py                       # CLI parser implementing validate-events and command stubs
│   ├── config.py                    # Handcrafted .env parser and Config dataclass with defaults
│   ├── keys.py                      # Remote control key codes, inverse mappings, and probe order
│   ├── validate.py                  # Hand-crafted validators for focus events and report.json
│   ├── telemetry.py                 # Robust logcat stream parser extracting MIRA_FOCUS payloads
│   ├── driver.py                    # Abstract Driver interface and FocusEvent dataclass
│   ├── adb_driver.py                # Live ADB driver skeleton (Task D2)
│   ├── fixture_driver.py            # Offline fixture replay driver skeleton (Task D2)
│   ├── make_synthetic.py            # Synthetic test fixture generator stub (Task D2)
│   ├── graph.py                     # Focus navigation graph data structure stub (Task D3)
│   ├── explore.py                   # Graph exploration algorithm stub (Task D3)
│   ├── detectors.py                 # UNREACHABLE and TRAP defect detector stubs (Task D4)
│   ├── vision.py                    # Focus indicator diffing and screenshot annotation stub (Task D5)
│   ├── ai.py                        # Bedrock Converse API explanation layer stub (Task D6)
│   ├── patches.py                   # Git patch apply and revert helper stub (Task D7)
│   ├── verify.py                    # Fix verification and regression detector stub (Task D7)
│   ├── demo.py                      # End-to-end demo execution orchestrator stub (Task D7)
│   └── record.py                    # Live exploration session recorder stub (Task D9)
├── report/
│   ├── build_report.py              # Single-file HTML compiler injecting report.json into template
│   ├── template.html                # Dark-themed report UI with split-view diff cards
│   └── style.css                    # Offline CSS styling for report.html
├── scripts/
│   ├── check_ownership.py           # Git status analyzer enforcing file ownership boundaries
│   ├── check_hook.ps1               # PowerShell test verifying React Native focus hook over ADB
│   ├── check_patches.ps1            # PowerShell test verifying git patch applicability and reversal
│   └── smoke.ps1                    # End-to-end smoke test runner (pytest + fixture demo)
├── tests/
│   ├── test_cli.py                  # Tests for CLI argument parsing and validate-events command
│   ├── test_config.py               # Tests for .env loading, defaults, and type casting
│   ├── test_keys.py                 # Tests for keycode mapping and inverse D-pad lookups
│   ├── test_ownership.py            # Tests for ownership validation and role restrictions
│   ├── test_schema.py               # Tests validating contracts against sample data
│   ├── test_telemetry.py            # Tests for logcat extraction, noise handling, and boundary cases
│   ├── test_validate.py             # Tests for focus event and report validation functions
│   └── [test_*.py stubs]           # Stubs for graph, explore, detectors, vision, ai, patches, report
└── docs/
    ├── APP_MAP.md                   # Application structure, package ID, activities, and element inventory
    ├── DEMO_SCRIPT.md               # Timed demo video script (target 2:40, max 3:00)
    ├── FEEDBACK.md                  # Hackathon product feedback for AWS Builder and Developer tools
    └── FRICTION_LOG.md              # Shared append-only engineering obstacle ledger
```

### Detailed Component Analysis

#### 1. Configuration & Keys (`mira_tv/config.py`, `mira_tv/keys.py`)
- **`config.py`**: Reads `.env` using a custom line-by-line parser without third-party dependencies. Implements hierarchical precedence: Operating System Environment Variables $>$ `.env` file $>$ Hardcoded Defaults in `Config` dataclass. Supports casting integers and floats safely with fallback defaults.
- **`keys.py`**: Maps TV remote keys (`UP`, `DOWN`, `LEFT`, `RIGHT`, `CENTER`, `BACK`) to standard Android ADB keycodes (`19`, `20`, `21`, `22`, `23`, `4`). Maps directional keys to their exact geometric inverses (`UP` $\leftrightarrow$ `DOWN`, `LEFT` $\leftrightarrow$ `RIGHT`). Defines the exploration probe sequence (`PROBE_KEYS = ["UP", "DOWN", "LEFT", "RIGHT", "BACK"]`).

#### 2. Validation & Telemetry (`mira_tv/validate.py`, `mira_tv/telemetry.py`)
- **`validate.py`**: Pure Python schema validation without `jsonschema`.
  - `validate_focus_event()`: Verifies integer sequence $\ge 1$, valid screen/element strings, timestamp, and integer bounds (`x`, `y`, `w`, `h`).
  - `validate_report()`: Validates `schema_version == "1"`, mode (`live` or `fixture`), app metadata, screens list, defect structure, and verify block consistency.
- **`telemetry.py`**: Parses incoming ADB logcat streams. Scans for marker `MIRA_FOCUS `, extracts inner JSON substring between the first `{` and last `}`, runs `json.loads`, and constructs immutable `FocusEvent` dataclasses. Non-conforming lines are counted in `bad_count` and safely discarded without raising exceptions.

#### 3. Driver Architecture (`mira_tv/driver.py`, `adb_driver.py`, `fixture_driver.py`)
- **`driver.py`**: Declares abstract methods `reset_to_screen()`, `press()`, `screenshot()`, and `close()`.
- **`adb_driver.py`** (D2): Target for live device execution. Manages background logcat worker thread, executes `screencap -p` for screenshots, and issues `input keyevent` commands with settling delays.
- **`fixture_driver.py`** (D2): Offline replay driver. Consumes `fixture.json` and static screenshot PNGs, updating internal graph state and returning synthetic `FocusEvent` instances.

#### 4. React Native Instrumentation Hook (`app/mira/reportFocus.ts`)
- Implements `reportFocus(screen, elementId, bounds?)`.
- Guarded by `if (!__DEV__) return;` to guarantee zero production performance impact.
- Uses `PixelRatio.get()` to scale coordinates into actual physical screenshot pixel coordinates so bounding boxes directly overlay captured PNGs.

#### 5. Ownership Policy & CI (`scripts/check_ownership.py`, `.github/workflows/test.yml`)
- **`check_ownership.py`**: Inspects git diffs against `origin/main`, staged files, and untracked files. Maps files to categories (`D`, `V`, `SHARED`, `LOCKED`, `UNOWNED`). Fails with non-zero exit code if a teammate touches files outside their designated role without a `CONTRACT-CHANGE` exception.
- **`test.yml`**: GitHub Actions runner executing `pytest -q` across all unit tests on every push and pull request.

---

## 4. Teammate Protocol & Future Decision Template

### Decision Logging Rules
1. Any modification affecting shared contracts (C1–C5), algorithms, AI prompts, detector parameters, or file layouts must be logged below before creating a PR.
2. Commit messages impacting contracts must begin with `CONTRACT-CHANGE:`.
3. Checkpoint reviews require verifying this ledger against the code diffs.

### Decision Template (Copy and append below)

```markdown
### [ADR-00X] <Title of Decision>
- **Date**: YYYY-MM-DD
- **Author**: D (Engine) | V (App/Integration)
- **Scope / Component**: (e.g., mira_tv/explore.py, contracts/scenario.json)
- **Context & Problem**: Brief explanation of the situation, trade-offs, or issue encountered.
- **Decision Taken**: Specific approach, parameter, or architectural pattern chosen.
- **Files Modified / Added**: Exact paths to affected files.
- **Integration Impact**: What the other teammate needs to know or adjust.
```

---

## 5. Team Decision Ledger (Append-Only)

### [ADR-006] Repository Baseline Stabilization and Proper .gitignore Setup
- **Date**: 2026-10-16
- **Author**: D (Engine)
- **Scope / Component**: Root repository hygiene, `.gitignore`, `BUILD.md`, `INTEGRATION.md`, `OWNERSHIP.md`, `scripts/check_ownership.py`
- **Context & Problem**: Initial repository contained temporary zip backups (`mira-tv.zip`) and redundant duplicate directories (`Trash/`), along with a minimal `.gitignore` missing Android Gradle, Expo, and system artifacts. Teammate integration needed a formal decision tracking protocol.
- **Decision Taken**:
  1. Purged temporary `Trash/` and `mira-tv.zip` archives.
  2. Implemented a comprehensive, production-grade `.gitignore` covering Python venv/pytest/bytecode, Node/Expo artifacts, Android/Gradle build caches and keystores, and OS/IDE metadata.
  3. Formulated and integrated the Decision Record and Codebase Understanding protocol into `BUILD.md` and `INTEGRATION.md`.
  4. Added `DECISION.md` to `OWNERSHIP.md` and `scripts/check_ownership.py` under `SHARED_APPEND` to permit collaborative documentation without ownership check violations.
  5. Established granular, structured commit history reflecting each subsystem rather than bulk commits.
- **Files Modified / Added**: `.gitignore`, `BUILD.md`, `INTEGRATION.md`, `OWNERSHIP.md`, `scripts/check_ownership.py`, `.github/CODEOWNERS`, `tests/test_ownership.py`, `DECISION.md`.
- **Integration Impact**: Both D and V now have clear guidelines and clean working trees for Task D2 and Task V0/V1 milestones.

### [ADR-007] Drivers, Synthetic Fixtures, Exploration Graph & Session Recorder (CP0 Milestone)
- **Date**: 2026-10-16
- **Author**: D (Engine)
- **Scope / Component**: `mira_tv/make_synthetic.py`, `mira_tv/fixture_driver.py`, `mira_tv/adb_driver.py`, `mira_tv/graph.py`, `mira_tv/explore.py`, `mira_tv/record.py`, `mira_tv/cli.py`, `tests/test_*`
- **Context & Problem**: To achieve Checkpoint CP0 by Oct 16 evening, the engine must support offline fixture replay, live ADB driving with 20s timeouts, deterministic exploration graph mapping, and the `record` CLI tool so Teammate V can record real device fixtures on Oct 17.
- **Decision Taken**:
  1. Implemented `make_synthetic.py` with Pillow generating `synthetic_clean` and `synthetic_bugs` fixtures (~8 elements on `home`, ~4 on `details`, 1920x1080 screenshots with 6px focus borders, planted UNREACHABLE, TRAP, and missing focus indicator).
  2. Unignored `fixtures/**/shots/` in `.gitignore` to guarantee offline test replayability in CI.
  3. Implemented `FixtureDriver` replaying pre-recorded paths, screenshots, and sequence increments from `fixture.json`.
  4. Implemented `AdbDriver` enforcing 20s timeouts on all subprocess calls, background raw logcat telemetry stream ingestion, and application relaunch sequence (`am force-stop` followed by `am start -n` and sequence counter reset).
  5. Implemented `Graph` data structure supporting BFS shortest-path derivation, forward reachability, and reverse-reachability for exit target verification.
  6. Implemented deterministic `explore_screen` following the exact BFS probe loop from `BUILD_D.md`, with automatic reset-and-replay recovery on focus loss.
  7. Implemented `record_fixture` and wired `record` sub-command into `mira_tv/cli.py`, allowing V to capture live emulator sessions into standard fixture packages.
- **Files Modified / Added**: `mira_tv/make_synthetic.py`, `fixtures/synthetic_clean/**`, `fixtures/synthetic_bugs/**`, `mira_tv/fixture_driver.py`, `mira_tv/adb_driver.py`, `mira_tv/graph.py`, `mira_tv/explore.py`, `mira_tv/record.py`, `mira_tv/cli.py`, `tests/test_fixture_driver.py`, `tests/test_adb_driver.py`, `tests/test_graph.py`, `tests/test_explore.py`, `tests/test_record.py`, `tests/test_cli.py`, `tests/test_telemetry.py`, `DECISION.md`.
- **Integration Impact**: Milestone CP0 requirement ("record exists") is met. V can now execute `python -m mira_tv record --out fixtures/real_clean` on their laptop to capture real Android TV app fixtures.

