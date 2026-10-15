# BUILD_V.md — V: App, Report, Demo

> ⚠️ AGENT INSTRUCTIONS: Build ONLY what is listed here and in BUILD.md. Do not add features or infer requirements. If something is unclear, output `// UNCLEAR: [question]` and stop. Read BUILD.md first; the shared contracts (C1–C5) there are law.

## Your Scope
You own the app under test (Amazon's TV sample), the focus-reporting hook, the three injected bugs and three vetted fixes, the scenario/expected files, the HTML report design, the demo recording, and the final README. Only your laptop runs the emulator, so you also run every live integration with D (screen share).

## Your Files
`app/*`, `bugs/*`, `fixes/*`, `contracts/scenario.json`, `contracts/expected_elements.json`, `contracts/bug_map.json`, `report/template.html`, `report/style.css`, `scripts/check_hook.ps1`, `scripts/check_patches.ps1`, `fixtures/real_clean`, `fixtures/real_bugs`, `docs/APP_MAP.md`, `docs/DEMO_SCRIPT.md`, `README.md`, `LICENSE`.
You must NOT edit: `mira_tv/`, `tests/`, `contracts/*.schema.json`, `ai_cache/`, `report/build_report.py`, `.github/`, `docs/FEEDBACK.md`.

## Setup (Windows, your high-spec laptop)
1. Install Git, Node.js 20 LTS, JDK 17, Python 3.11+, Android Studio (with SDK + platform-tools).
2. Add `platform-tools` to PATH. Check: `adb version`.
3. Turn on virtualization: BIOS VT-x/AMD-V, and Windows features "Windows Hypervisor Platform" (and Hyper-V if the emulator asks).
4. Android Studio → Device Manager → Create Device → **TV → Android TV (1080p)** → API 30–34 image (use the lowest that the sample supports) → RAM ≥ 3 GB. Boot it. Check: `adb devices` shows `emulator-xxxx`.
5. Clone the repo (`mira-tv`). Copy the sample into `app/`: clone `https://github.com/AmazonAppDev/react-native-multi-tv-app-sample` to a temp folder, copy its files into `app/`, and delete `app/.git`. Keep the license text of the sample (`app/LICENSE`).
6. `cd app; npm install`. Then **follow `app/README.md` exactly** for building the TV-optimized native project and running on Android (it uses Expo). `UNCLEAR` — I have not seen the exact commands; do not guess, read the README.
7. Python: `python -m venv .venv`, activate, `pip install -r requirements.txt` (needed only to run D's engine for integration).
8. Copy `.env.example` to `.env`; leave `MIRA_BEDROCK_MODE=stub`. You do NOT need an AWS key.

## Tasks (in order)

### V0 — Emulator + app running (Oct 15–16) — CRITICAL PATH
**Acceptance (all four):** (1) sample app visible on the emulator; (2) `adb shell input keyevent KEYCODE_DPAD_RIGHT` visibly moves focus; (3) `adb exec-out screencap -p > shot.png` produces an image; (4) `adb logcat -d | findstr ReactNativeJS` shows output.
**Fallback (your decision, by end of Oct 17):** if the sample will not build, switch to Amazon's `hello-world-fire-tv-react-native` (same stack) and tell D immediately. Log the problem in `docs/FRICTION_LOG.md` either way.

### V1 — `docs/APP_MAP.md` (Oct 16)
Record, from the real code: package id; launch activity; AVD API level; Node version used; the screens (max 3; names must be lowercase, e.g. `home`, `details`); for each screen the file that renders it; which file renders the drawer/menu, the content cards, and the detail buttons; the exact name of the focus component/prop in the focus library used by the sample (e.g. the `onFocus` equivalent); how Back behaves. Include the final list of element IDs (format `<screen>.<region>.<n>`).
**Acceptance:** D can read it and fill in nothing by guessing.

### V2 — Contract files (Oct 16 draft, Oct 18 final)
Create `contracts/scenario.json` (C4 shape; real `package`, `launch_activity`, `entry_steps`, `exit_targets`), `contracts/expected_elements.json` (every interactive element per screen), `contracts/bug_map.json` (3 entries, filled after V4).
**Acceptance:** valid JSON; every ID in these files exists in `APP_MAP.md`.

### V3 — Focus hook (Oct 17)
Create `app/mira/reportFocus.ts` (copy exactly; adjust only imports if needed):
```ts
import { PixelRatio } from 'react-native';

let seq = 0;

export type Bounds = { x: number; y: number; w: number; h: number };

export function reportFocus(screen: string, elementId: string, bounds?: Bounds): void {
  if (!__DEV__) return;
  seq += 1;
  const r = PixelRatio.get();
  const b = bounds ?? { x: 0, y: 0, w: 0, h: 0 };
  console.log(
    'MIRA_FOCUS ' +
      JSON.stringify({
        seq,
        screen,
        element_id: elementId,
        bounds: {
          x: Math.round(b.x * r),
          y: Math.round(b.y * r),
          w: Math.round(b.w * r),
          h: Math.round(b.h * r),
        },
        ts: Date.now(),
      }),
  );
}
```
Wire it into **every** interactive element listed in `expected_elements.json`: in that element's focus handler, call `ref.measureInWindow((x, y, w, h) => reportFocus(screen, id, { x, y, w, h }))`; if measuring is not available, call `reportFocus(screen, id)` (zero bounds). `UNCLEAR` — the exact focus callback name comes from `APP_MAP.md`. Do not change app behavior or styling beyond this call.
**Acceptance:** pressing keys prints `MIRA_FOCUS` lines in `adb logcat`; `seq` restarts at 1 after the app is force-stopped and relaunched; `scripts/check_hook.ps1` passes.
`scripts/check_hook.ps1`: clears logcat, sends RIGHT/DOWN/LEFT/UP, dumps `adb logcat -d`, counts `MIRA_FOCUS` lines (must be ≥ 4), then runs `python -m mira_tv validate-events --file <dump>` (D's command) and prints PASS/FAIL.
**If it fails by end of Oct 18:** tell D; D switches to the screenshot-diff fallback and you pair for at most one day. Log it in the friction log.

### V4 — Bugs and fixes (Oct 18)
Create three bug patches and three matching fix patches. Each ≤ 20 changed lines, only under `app/`, generated with `git diff` at repo root.
| # | Type | Required effect | Fix |
|---|---|---|---|
| BUG-01 | `UNREACHABLE` | One visible action button on a detail screen can no longer receive focus from any direction | Restores focusability/position in the focus order |
| BUG-02 | `TRAP` | After entering the content grid, focus cannot return to the drawer/menu by any D-pad key or BACK | Restores the exit |
| BUG-03 | `NO_FOCUS_INDICATOR` | One card keeps identical appearance when focused | Restores a visible focused style (border/scale/color) |
Name them `bugs/BUG-01-unreachable.patch`, `fixes/FIX-01-unreachable.patch`, etc. Each fix must be a clean reverse-compatible change: applying bug then fix leaves the app functionally identical to the original. Fill `contracts/bug_map.json` with the three real defect IDs (`<TYPE>:<element_id>`).
**Acceptance:** `scripts/check_patches.ps1` passes: for each bug/fix it runs `git apply --check`, applies, reverses, and confirms a clean working tree; it also confirms that after applying a bug the app still builds/reloads (manual check, noted in the script output as a reminder).
Rule: a bug patch must break only its target; the other two defects and normal navigation stay intact.

### V5 — Record real fixtures (Oct 17 and Oct 18)
When D announces `record` is ready (target Oct 16 evening): with Metro and the emulator running, run `python -m mira_tv record --out fixtures/real_clean` on the clean app, then apply all three bug patches and run `... --out fixtures/real_bugs`; reverse the bugs. Commit both folders and tell D.
**Acceptance:** `python -m mira_tv explore --mode fixture --fixture fixtures/real_bugs` runs on D's machine and finds the three planted defects.

### V6 — Report template (Oct 19–20)
`report/template.html` + `report/style.css`. Contract C5: exactly one script line `window.MIRA_REPORT = /*__MIRA_REPORT_JSON__*/null;`. No external fonts, CDNs, or images; works from `file://`; dark theme; base font ≥ 18 px so it reads in a 1080p screen recording.
Required content (in this order): (1) header with run id, mode, app package; (2) summary bar: defects found / fixes verified / AI calls; (3) one card per defect: type badge, element ID, screen, key path as chips, `ai_explanation` with a small label showing `ai_source`; (4) inside each card a **split view**: left = `before_screenshot` with a red border and a FAIL badge, right = `after_screenshot` with a green border and a PASS badge; (5) footer text: "Pass/fail decided by deterministic tests; AI only explains."
Stretch only after everything else works: draw the focus graph from `screens[].graph_before` / `graph_after` as SVG (nodes at their bounds, red for trapped/unreachable nodes, green after fix).
**Acceptance:** renders correctly with `report.json` from `fixtures/synthetic_*` and from the real run; defect with `after = FAIL` shows red and does not claim success.

### V7 — Demo recording (Oct 20–21)
Write `docs/DEMO_SCRIPT.md` before recording. Required structure (target 2:40, hard limit 3:00):
- 0:00–0:20 the problem in one sentence: remote-control focus bugs; quote that Amazon's own guidelines require reachable elements and visible focus (read from the sources D lists in the README).
- 0:20–0:30 app running on the emulator.
- 0:30–2:20 live run: engine explores, finds the three defects (red), AI explanation appears, fix applied, replay, green. (You may speed up the exploring; say "sped up" on screen.)
- 2:20–2:40 the report and what is new during the hackathon window; mention AWS Bedrock (state if responses are cached).
Rules: public, English, YouTube or Vimeo, under 3:00, lead with the strongest part, no copyrighted music, no third-party logos. Test the upload while logged out.

### V8 — README + LICENSE (Oct 21)
`LICENSE`: MIT. `README.md` sections: what it is; why (quote the two Amazon guideline statements with links); architecture diagram (simple text); **setup for judges** (exact commands: clone, `pip install -r requirements.txt`, `python -m mira_tv demo --mode fixture`, plus the live emulator path); how detection works; guardrails; **what was built/updated during the submission window** (new repo; MIRA idea from earlier work, all code new); AWS usage (Bedrock Converse for explanations); credits (Amazon sample app license). D supplies the engine section text.
**Acceptance:** a clean clone on another machine runs the fixture demo in under 5 minutes using only the README.

### V9 — Clean-clone test (Oct 22)
Fresh clone in a new folder, follow the README exactly, run the fixture demo, then the live demo once. Fix only documentation, not code, unless it is a blocker.

## Test Suites (V)
- `scripts/check_hook.ps1` — hook emits valid events (see V3).
- `scripts/check_patches.ps1` — every bug/fix applies and reverses cleanly (see V4).
- Manual template check: open `report.html` built from synthetic and real runs.
- Pass criteria are in each task; run both scripts before every push that touches `app/`, `bugs/`, `fixes/`.

## Integration Points
| From D to you | Needed by | If late |
|---|---|---|
| `python -m mira_tv record`, `validate-events` | Oct 16 evening | Keep working on V0–V2 |
| `demo --mode live` | Oct 19 | Run `explore` + `verify` manually |
| `report/build_report.py` | Oct 19 | Hand-edit a test JSON into your template |
| **From you to D** | Needed by | |
| `docs/APP_MAP.md`, draft contract files | Oct 16 | D uses placeholders |
| `fixtures/real_clean`, `fixtures/real_bugs` | Oct 17–18 | D keeps using synthetic fixtures |
| Final `scenario.json`, `bug_map.json` | Oct 18 | — |
| `report/template.html` | Oct 19 | D uses a test template |

## Definition of Done (V)
- Emulator + app run; hook verified; three bugs and three fixes verified.
- Real fixtures committed.
- Report template renders real data.
- Demo video public and < 3:00.
- README + LICENSE complete; clean-clone test passed.

## DO NOT
- Do not add features, screens, bugs, or UI beyond what is listed.
- Do not edit engine code, schemas, or D's files; message D instead.
- Do not guess Expo/React Native commands or focus-callback names; read the sample's README/code or write `UNCLEAR`.
- Do not use copyrighted music, logos, or footage in the video.
- Do not commit `.env`, keystores, or personal data.
