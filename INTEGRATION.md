# INTEGRATION.md — MIRA TV

> ⚠️ AGENT INSTRUCTIONS: This file defines how D's engine and V's app/report connect. Do not change contracts. If something is unclear, output `UNCLEAR: [question]` and stop.

## Integration Flow
```
V's app (emulator) --C1 MIRA_FOCUS logcat lines--> D's AdbDriver/telemetry
D's engine explores --> detectors --> AI explanation (Bedrock/cache/stub)
D's verify applies V's fixes/*.patch (C3) --> re-explore --> report.json (C2)
D's build_report.py + V's template.html (C5) --> report.html --> demo video
```
D never needs the emulator: `FixtureDriver` replays recorded sessions. V never needs D to finish: V can check the hook and patches with their own scripts.

## Contracts (summary; BUILD.md is authoritative)
| # | Contract | Producer | Consumer | Verified by |
|---|---|---|---|---|
| C1 | `MIRA_FOCUS {json}` logcat line | V (hook) | D (telemetry) | `scripts/check_hook.ps1` + `validate-events` |
| C2 | `report.json` v1 | D | V (template) | `tests/test_schema.py` + template check |
| C3 | `bugs/*.patch`, `fixes/*.patch`, `bug_map.json` | V | D (patches/verify) | `scripts/check_patches.ps1` + `tests/test_patches.py` |
| C4 | `scenario.json`, `expected_elements.json` | V | D (explore/detectors) | `validate.py` + fixture explore on `real_*` |
| C5 | `template.html` token | V | D (build_report) | `tests/test_report.py` |

## Git Rules
- Repo: public, MIT license, name `mira-tv`. Public removes any reviewer-permission question; judges can read it directly.
- Branches: `main` (always green), `d/<topic>`, `v/<topic>`. Merge through pull requests. Each person merges their own branches after tests pass.
- Contract changes (C1–C5, env vars, folder structure, key names, ID formats): commit message starts with `CONTRACT-CHANGE:`, and the change needs the other person's explicit "ok" in chat first. Update BUILD.md in the same PR.
- Never force-push `main`. Never commit `.env`, keys, `artifacts/`, `node_modules/`.
- Ownership: do not edit the other person's folders (see BUILD.md table). Ask them in chat.

## Daily Sync (10 minutes, same time each day, voice or chat)
Each person posts: (1) done since yesterday, (2) blocked by, (3) next 24 hours. Anything blocked for more than 4 hours gets escalated in chat immediately and logged in `docs/FRICTION_LOG.md`.

## Timeline (IST) and Checkpoints
| Date | D | V | Checkpoint |
|---|---|---|---|
| Thu Oct 15 | repo skeleton, config, contracts schemas, Bedrock account | emulator + sample app build | — |
| Fri Oct 16 | telemetry, drivers, synthetic fixtures, `record`, `validate-events` | V0 done, APP_MAP, contract drafts | **CP0 (evening):** emulator moves focus on key press; `record` exists |
| Sat Oct 17 | graph + explore + UNREACHABLE/TRAP detectors | hook wired, real fixtures recorded | **CP1:** `fixtures/real_clean` explores to a full graph on D's machine |
| Sun Oct 18 | indicator check, AI layer, tuning on real fixtures | bug and fix patches, final contracts | **CP2:** first live `explore` on V's laptop finds the 3 planted defects |
| Mon Oct 19 | patches/verify, `demo`, report builder | report template | **CP3:** `demo --mode live` end to end |
| Tue Oct 20 | polish, cache real Bedrock responses, friction log | template polish, demo script | AI cache filled for the demo run |
| Wed Oct 21 | README engine section, FEEDBACK.md; **feature freeze 18:00** | record and edit demo, README | **CP4:** demo video draft < 3:00 |
| Thu Oct 22 | clean-clone checks, submission form, **submit by evening** | final video upload, clean-clone test | **CP5:** submitted |
| Fri Oct 23 | buffer only; no new work | buffer only | Deadline is 12:00 pm PT = Oct 24 00:30 IST |

Weekend (Oct 17–18) is the heavy build. After the Oct 21 freeze, only bug fixes and documentation are allowed.

## If-Late Rules
- V's emulator/app not working by end of Oct 17 → V switches to `hello-world-fire-tv-react-native` (BUILD_V V0). D keeps using synthetic fixtures.
- Hook not working by end of Oct 18 → D implements the screenshot-diff fallback (compare screenshots after each key press to infer focus movement), V pairs for at most one day. This lowers precision; mention it in the README.
- Real fixtures late → D continues on synthetic fixtures; integration moves to CP2.
- Bedrock not working by Oct 19 → ship with `stub` plus whatever responses are cached, and describe the integration honestly in FEEDBACK.md. Do not claim live calls that did not run.
- Demo run flaky → record from `fixtures`-driven explore plus one clean live clip; label clearly which is which.
- Anything not done by the freeze is cut, in this order: graph SVG, Open Source PR, third defect polish.

## Demo Path (what judges see)
1. Emulator shows the Fire TV app. 2. Engine presses the D-pad and explores. 3. Three defects found: unreachable button, trap, invisible focus. 4. AI explains each in plain words. 5. Fix applied, path replayed, defect disappears. 6. Report with red→green split view. 7. Closing: repo, how to run, AWS Bedrock, what is new.

## End-to-End Acceptance Tests
1. `scripts/smoke.ps1` passes on a clean clone (no emulator).
2. On V's laptop: `python -m mira_tv demo --mode live` finds exactly 3 defects (one per type), verifies 3 fixes, builds `report.html`, and restores the app. Run twice; results identical.
3. `report.json` validates against `contracts/report.schema.json`.
4. `report.html` opens from `file://` and shows 3 cards with red/green split views.
5. `git status` clean after `demo` (bugs and fixes fully reverted).
6. `git log -p` contains no keys or `.env`.

## Submission Checklist (Devpost)
- [ ] Hackathon joined; submission created before Oct 22 evening IST (draft saves allowed).
- [ ] Track: **Fire TV**. Mini challenge: **AWS Builder** (and Open Source only if D12 was completed).
- [ ] Text description: what it does, how it works, who it helps, what is new in the window (new repo; fresh code).
- [ ] Code repo URL, public, MIT license visible in the About section.
- [ ] Demo video URL: YouTube or Vimeo, public, English, < 3:00, shows the app running on the emulator.
- [ ] Product feedback (from `docs/FEEDBACK.md`): per tool used — what it was for, what worked, what needs work, onboarding, build again yes/no. Bedrock usage described here for AWS Builder.
- [ ] Friction log entries pasted from `docs/FRICTION_LOG.md` (optional, up to 10% bonus).
- [ ] Optional feature requests (priority labels: Critical / Important / Nice-to-have).
- [ ] If Open Source: contribution URL, repo URL, GitHub username, description of what/how/why.
- [ ] No third-party trademarks or copyrighted music in the video.
- [ ] Re-check the official rules page for changes before submitting.

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| Expo/Gradle build trouble on Windows | High | V0 first; fallback sample on Oct 17; log in friction log |
| Sample's focus library state differs from what the hook sees | Medium | Hook reports from the focus callback; fallback screenshot-diff |
| Bounds are wrong (dp vs px) | Medium | `PixelRatio` scaling; zero bounds skip the indicator check with a note; tune on real fixtures |
| Probe time too long for demo | Medium | `max_probes` caps; inverse-press optimization; fixture replay and a labeled sped-up clip |
| Bedrock access/billing delay | Medium | Set up Oct 15–16; `stub`/`cache` modes keep everything working |
| Metro not running during live demo | Medium | Checklist item in V7; `demo` aborts with a clear message |
| Time shortage (≈ 4–5 h/day each) | High | Freeze on Oct 21; cut order above |
