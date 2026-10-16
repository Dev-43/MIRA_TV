# BUILD.md — MIRA TV (Master)

> ⚠️ AGENT INSTRUCTIONS: Build ONLY what is listed here. Do not add features, do not infer requirements, do not improve on the spec. If something is unclear, output a comment `// UNCLEAR: [question]` (or `# UNCLEAR: [question]` in Python/Markdown) and stop. Do not proceed past unclear points.

## Project Overview
MIRA TV is an autonomous remote-control QA agent for Fire TV apps. A Python engine drives a Fire TV–compatible app on an Android TV emulator over `adb`, presses the D-pad, maps where focus can and cannot go, and deterministically detects exactly three defect types: `UNREACHABLE` (control cannot be focused), `TRAP` (focus cannot get back out), `NO_FOCUS_INDICATOR` (focused element looks identical to unfocused). A Bedrock vision model only EXPLAINS each defect in plain language; the deterministic detectors decide pass/fail. Vetted patch files fix each defect, the affected screen is re-explored, and a static HTML report shows red (before) vs green (after).

Hackathon: Build, Ship, Shape — Amazon Developer Hackathon. Track: **Fire TV**. Mini challenge: **AWS Builder** (Bedrock). Stretch: **Open Source** (PR to Amazon's sample repo). Submission deadline: Oct 23, 2026 12:00 pm PT (= Oct 24, 00:30 IST). Internal target: submitted by evening of Oct 22 IST.

## Team Overview
| Teammate | Role | Owns | Integrates With |
|---|---|---|---|
| **D** | Engine | `mira_tv/`, `tests/`, `fixtures/` (format + synthetic), `ai_cache/`, `report/build_report.py`, `contracts/*.schema.json`, `scripts/`, `.github/`, `.env.example`, `docs/FEEDBACK.md`, `docs/FRICTION_LOG.md` | V via C1 (focus events), C2 (report.json), C3 (patch files), C4 (scenario/expected files), C5 (report template) |
| **V** | App + Report + Demo | `app/`, `bugs/`, `fixes/`, `contracts/scenario.json`, `contracts/expected_elements.json`, `contracts/bug_map.json`, `report/template.html`, `report/style.css`, `docs/APP_MAP.md`, `docs/DEMO_SCRIPT.md`, `README.md`, `LICENSE`, demo video | D via the same contracts |

**Hardware rule:** only V's laptop runs the emulator. D develops and tests with `FixtureDriver` (no emulator). All live runs and the demo recording happen on V's laptop.

## Tech Stack (exact)
- Python 3.11 or 3.12; packages (in `requirements.txt`): `Pillow>=10`, `boto3` (latest), `pytest>=8`. Nothing else.
- Node.js 20 LTS (confirm against `app/package.json` engines; record in `docs/APP_MAP.md`), JDK 17, Git ≥ 2.40.
- Android Studio (latest stable) with SDK platform-tools; AVD: **Android TV (1080p)**, API level 30–34 (lowest the sample supports; record choice in `docs/APP_MAP.md`), RAM ≥ 3 GB.
- Target app: `AmazonAppDev/react-native-multi-tv-app-sample` (React Native + Expo + TypeScript, focus via React TV Space Navigation), copied into `app/` as plain files (no nested `.git`).
- AI: Amazon Bedrock Converse API (`bedrock-runtime`), vision-capable Claude model. Exact model ID is set by D in `.env` after checking the Bedrock console (`BEDROCK_MODEL_ID`). `UNCLEAR` until D confirms.
- Report: one static HTML file, plain HTML/CSS/JS, no framework, no CDN, works offline from `file://`.

## Shared Contracts (ALL agents must honor these)

### Glossary
- Keys (exact strings): `UP`, `DOWN`, `LEFT`, `RIGHT`, `CENTER`, `BACK`. ADB keycodes: UP=19, DOWN=20, LEFT=21, RIGHT=22, CENTER=23, BACK=4. Inverse keys: UP↔DOWN, LEFT↔RIGHT. `CENTER` and `BACK` have no inverse.
- Element ID format: `<screen>.<region>.<n>` lowercase, e.g. `home.drawer.1`, `home.card.2`, `details.btn.play`. IDs are globally unique. The first segment is the screen name. Screens in scope: `home`, `details` (exact final set fixed by V in `docs/APP_MAP.md` by end of Oct 16; at most 3 screens).
- Defect ID format: `<TYPE>:<element_id>`, e.g. `UNREACHABLE:details.btn.addlist`.
- Run ID: UTC timestamp `YYYYMMDDTHHMMSSZ`.

### C1 — Focus event (App → Engine) via logcat
The app prints one line per focus change using `console.log`:
```
MIRA_FOCUS {"seq":1,"screen":"home","element_id":"home.card.1","bounds":{"x":0,"y":0,"w":0,"h":0},"ts":1760000000000}
```
- `seq`: integer, starts at 1 after every app launch, increments by 1 per event.
- `bounds`: integer pixels in **screenshot coordinates** (window dp × `PixelRatio.get()`); all zeros = unknown.
- Only emitted when `__DEV__` is true.
- Engine reads `adb logcat` (tag `ReactNativeJS`). Parser rule: find the substring `MIRA_FOCUS `, take from the first `{` after it to the last `}` on the line, `json.loads` it. Lines that fail to parse are counted and ignored (never crash).
- Schema file: `contracts/focus_event.schema.json` (D).

### C2 — report.json v1 (Engine → Report)
Written to `artifacts/<run_id>/report.json`. Exact shape:
```json
{
  "schema_version": "1",
  "run_id": "20261018T101500Z",
  "mode": "live | fixture",
  "app": {"package": "string", "git_commit": "string"},
  "screens": [
    {
      "screen": "home",
      "probes": 0,
      "elements_seen": ["home.drawer.1"],
      "graph_before": {"nodes": [{"id": "", "x": 0, "y": 0, "w": 0, "h": 0}], "edges": [{"from": "", "key": "RIGHT", "to": "id-or-null"}]},
      "graph_after": null
    }
  ],
  "defects": [
    {
      "id": "UNREACHABLE:details.btn.addlist",
      "type": "UNREACHABLE | TRAP | NO_FOCUS_INDICATOR",
      "screen": "details",
      "element_id": "details.btn.addlist",
      "path": ["RIGHT", "DOWN"],
      "evidence": {"detail": "string", "screenshot": "relative/path.png"},
      "ai_explanation": "string or null",
      "ai_source": "bedrock | cache | stub | none"
    }
  ],
  "verify": [
    {
      "defect_id": "UNREACHABLE:details.btn.addlist",
      "fix": "fixes/FIX-01-unreachable.patch",
      "before": "FAIL",
      "after": "PASS | FAIL",
      "before_screenshot": "relative/path.png",
      "after_screenshot": "relative/path.png"
    }
  ],
  "summary": {"defects_found": 0, "fixed_verified": 0, "ai_calls": 0}
}
```
All screenshot paths are relative to the run directory. Schema file: `contracts/report.schema.json` (D).

### C3 — Patch files (App ↔ Engine)
- `bugs/BUG-0N-<slug>.patch` injects a bug; `fixes/FIX-0N-<slug>.patch` repairs it. Unified diffs generated with `git diff` at repo root (paths start `a/app/...`), applied from repo root with `git apply`, reversed with `git apply -R`.
- Each patch changes ≤ 20 lines and touches only files under `app/`.
- `contracts/bug_map.json`: `{"<defect_id>": {"screen": "details", "bug": "bugs/BUG-01-....patch", "fix": "fixes/FIX-01-....patch"}}`. Exactly 3 entries: one per defect type.
- After applying a patch the engine relaunches the app (`am force-stop` + start) so the dev bundle reloads from Metro. Metro (`npx expo start`) must be running on V's laptop for live demo runs.

### C4 — Scenario files (App → Engine)
`contracts/scenario.json`:
```json
{
  "package": "UNCLEAR-V-fills-from-APP_MAP",
  "launch_activity": "UNCLEAR-V-fills-from-APP_MAP",
  "screens": [
    {"screen": "home", "entry_steps": [], "exit_targets": ["home.drawer.1"], "max_probes": 80, "max_depth": 8},
    {"screen": "details", "entry_steps": ["RIGHT", "CENTER"], "exit_targets": ["home.drawer.1"], "max_probes": 60, "max_depth": 8}
  ]
}
```
- `entry_steps` = keys pressed after a fresh launch to reach the screen (the app's first focus must be on the `home` entry element).
- `exit_targets` = element IDs that must be reachable from every element of the screen (used by TRAP detection). An element on a different screen than the one being explored counts as an exit target too.

`contracts/expected_elements.json`: `{"home": ["home.drawer.1", "..."], "details": ["details.btn.play", "..."]}` — every interactive element that must be focusable. V owns the content.

### C5 — Report template (Report ↔ Engine)
- V writes `report/template.html` + `report/style.css`. The template contains exactly one token: `/*__MIRA_REPORT_JSON__*/null` inside a `<script>` tag, as `window.MIRA_REPORT = /*__MIRA_REPORT_JSON__*/null;`.
- The template also contains exactly one stylesheet tag: `<link rel="stylesheet" href="style.css">`.
- D's `report/build_report.py` replaces that tag with an inline `<style>` block holding `report/style.css`, replaces the token with the report.json content, and writes `artifacts/<run_id>/report.html`. It fails with a clear error if either the tag or the token is missing. Screenshot paths in the JSON resolve relative to `report.html`.

### Environment Variables
| Name | Purpose | Default | Set by |
|---|---|---|---|
| `MIRA_ADB_PATH` | adb executable | `adb` | each person |
| `MIRA_ADB_SERIAL` | emulator serial | unset (single device) | V |
| `MIRA_KEY_DELAY_MS` | gap between key presses | `400` | each |
| `MIRA_SETTLE_MS` | wait after a key before reading focus | `600` | each |
| `MIRA_RESET_WAIT_MS` | wait after app relaunch | `4000` | each |
| `MIRA_INDICATOR_DIFF_MIN` | mean abs pixel diff (0–255) below which an element has no visible focus indicator | `4.0` | D (tuned Oct 18) |
| `MIRA_ARTIFACTS_DIR` | output dir | `artifacts` | each |
| `MIRA_BEDROCK_MODE` | `stub` \| `cache` \| `live` | `stub` | each |
| `AWS_REGION` | Bedrock region | `us-east-1` | D |
| `BEDROCK_MODEL_ID` | model/inference-profile ID | unset | D |
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock API key | unset | D only |
| `MIRA_MAX_AI_CALLS` | hard cap per run | `12` | D |
`.env.example` (D) lists all of these. Real `.env` is git-ignored. Only D holds the Bedrock key.

### File Structure (root) — exact, and the owner of every path
```
mira-tv/
├─ LICENSE                          V
├─ README.md                        V (D supplies engine section text)
├─ BUILD.md BUILD_D.md BUILD_V.md INTEGRATION.md SETUP.md OWNERSHIP.md   LOCKED
├─ DECISION.md                                                           shared, append-only
├─ .env.example  .gitignore  requirements.txt                            D
├─ .github/
│  ├─ CODEOWNERS                    LOCKED
│  └─ workflows/test.yml            D
├─ contracts/
│  ├─ focus_event.schema.json  report.schema.json                        D
│  └─ scenario.json  expected_elements.json  bug_map.json                V
├─ mira_tv/                                                              D (all files)
│  ├─ __init__.py __main__.py cli.py config.py keys.py validate.py
│  ├─ driver.py adb_driver.py fixture_driver.py make_synthetic.py telemetry.py
│  ├─ graph.py explore.py detectors.py vision.py
│  ├─ ai.py patches.py verify.py record.py demo.py
├─ tests/                                                                D (all files)
│  ├─ test_keys.py test_config.py test_telemetry.py test_validate.py test_cli.py
│  ├─ test_graph.py test_explore.py test_detectors.py test_vision.py
│  ├─ test_ai.py test_patches.py test_report.py test_schema.py test_ownership.py
├─ fixtures/
│  ├─ synthetic_clean/  synthetic_bugs/                                  D
│  └─ real_clean/  real_bugs/                                            V
├─ ai_cache/                                                             D
├─ report/
│  ├─ build_report.py                                                    D
│  └─ template.html  style.css                                           V
├─ scripts/
│  ├─ smoke.ps1  check_ownership.py                                      D
│  └─ check_hook.ps1  check_patches.ps1                                  V
├─ app/                             V  (sample app files + app/mira/reportFocus.ts)
├─ bugs/  fixes/                    V
├─ docs/
│  ├─ APP_MAP.md  DEMO_SCRIPT.md                                         V
│  ├─ FEEDBACK.md                                                        D
│  └─ FRICTION_LOG.md                                                    shared, append-only
└─ artifacts/                       git-ignored output, nobody commits it
```
The full per-person "may touch" lists are in `OWNERSHIP.md` and are enforced by `python scripts/check_ownership.py --role D|V`.

## Decision Record & Code Understanding Protocol (Mandatory for D & V)
Both teammates (D and V) must document all technical decisions and provide an explicit understanding of every code file created or modified in `DECISION.md`. This is required for seamless integration checkpoints (CP0–CP5):
1. **Decision Tracking:** Every architectural choice, algorithm adaptation, detector threshold calibration, UI layout rule, and prompt iteration must be logged in `DECISION.md` under the designated ADR format before PR merge.
2. **Codebase Understanding Ledger:** Every code file or contract file added/updated must have a corresponding entry explaining its operational purpose, core methods/interfaces, inputs, outputs, and dependencies across the D/V boundary.
3. **Pre-Integration Review:** At each integration checkpoint (CP0 through CP5 defined in `INTEGRATION.md`), both teammates must review each other's additions in `DECISION.md`. No integration run or contract modification proceeds without mutual sign-off on documented decisions.
4. **Ownership & Permissions:** `DECISION.md` is shared and append-only (`OWNERSHIP.md`). Neither teammate may overwrite or delete the other's decision history.

## Guardrails (apply to everyone)
1. **Deterministic gate:** defect detection and PASS/FAIL come only from the detectors. AI text never changes a result.
2. **No AI-written code changes:** fixes are only the vetted patches in `fixes/`.
3. **Bedrock:** default mode `stub`; `live` requires `MIRA_BEDROCK_MODE=live`; hard cap `MIRA_MAX_AI_CALLS`; 30 s timeout; 2 retries; every response cached in `ai_cache/`.
4. **Timeouts everywhere:** every `adb` subprocess call has a 20 s timeout; any wait loop has a maximum; no unbounded loops.
5. **Secrets:** never commit `.env`, keys, or tokens. Never print the Bedrock key.
6. **Reversibility:** the `demo` command always restores the app (`git apply -R`) even on failure.
7. **No telemetry in release:** hook runs only when `__DEV__`.
8. **No third-party trademarks or copyrighted media** in the demo or repo (no Amazon logos, no music).
9. **Truthfulness:** cached Bedrock responses are real responses to real screenshots; the video and README say "cached" where used. Nothing is faked.

## Test Gates
- Before every push: `python scripts/check_ownership.py --role D` (or `--role V`) must print OK.
- D: `pytest -q` must pass before every push (runs with no emulator).
- V: `scripts/check_patches.ps1` and `scripts/check_hook.ps1` must pass before every push touching `app/`, `bugs/`, `fixes/`.
- Both: `scripts/smoke.ps1` (fixture mode) passes on `main` at all times.

## DO NOT (all agents)
- Do not add any feature not listed in this document.
- Do not change shared contract definitions (C1–C5, env vars, file structure).
- Do not rename files or folders.
- Do not install packages not listed in the tech stack.
- Do not use your own judgment to "improve" the code.
- Do not touch another teammate's owned files.
- Out of scope (will be rejected): voice control, Vega OS, other apps, multi-agent orchestration, AI-written fixes, extra defect types, a web server or database.
