# DEMO_SCRIPT.md (owner: V, write before recording)

Target: 2:40 (hard limit: 3:00). Public, English, YouTube/Vimeo. No copyrighted music, no third-party logos.

---

## Pre-Recording Checklist
- [x] Android TV Emulator (`Android_TV_1080p`) booted and online (`adb devices`).
- [ ] Metro bundler running (`corepack yarn dev:android` in `app/`).
- [ ] `.env` configured with `MIRA_ADB_PATH=D:\Sdk\platform-tools\adb.exe` and `MIRA_BEDROCK_MODE`.
- [ ] Working tree clean (`git status`).
- [ ] Screen recorder set to 1080p 60fps / 30fps.

---

## Timed Narration & Action Script

### Part 1: The Problem & Amazon Fire TV Guidelines (0:00 – 0:20)
* **Visual**: Camera / Screen on title slide or repository README highlighting Amazon Fire TV Guidelines.
* **Spoken Narration (approx. 45 words)**:
  > *"Building apps for the 10-foot living room experience is tough. Amazon's official Fire TV guidelines require that every interactive control must be reachable via the remote D-pad, and every focused item must have an immediate, high-contrast visual indicator. Today, remote-control testing is manual and error-prone. Meet MIRA TV."*

### Part 2: The Application on the Emulator (0:20 – 0:35)
* **Visual**: Cut to the Android TV 1080p emulator running the Amazon React Native multi-TV sample app.
* **Spoken Narration (approx. 35 words)**:
  > *"Here is Amazon's React Native multi-TV sample app running on our Android TV 1080p emulator. MIRA TV drives the app autonomously over ADB, injecting D-pad keys and reading focus changes with sub-millisecond telemetry."*

### Part 3: Autonomous Exploration & Defect Discovery (0:35 – 1:20)
* **Visual**: Terminal running `python -m mira_tv demo`. Show the remote D-pad keys being pressed on the emulator (label on screen: *"Exploration sped up 2x"*).
* **Spoken Narration (approx. 90 words)**:
  > *"We launch MIRA's autonomous explorer. Using deterministic breadth-first search, MIRA traverses every screen, mapping the directional focus graph. In seconds, MIRA detects three critical defects:*
  > *First, an **UNREACHABLE** 'Add to List' button on the detail screen that never receives focus.*
  > *Second, a navigation **TRAP** in the movie card grid with no return path back to the menu.*
  > *And third, an invisible focus indicator (**NO_FOCUS_INDICATOR**) on movie card 2, where pixel difference math proves the focused state looks identical to unfocused."*

### Part 4: Amazon Bedrock Visual Explanation (1:20 – 1:45)
* **Visual**: Highlight the CLI / Report showing Bedrock Converse output and 6px red-annotated bounding-box screenshots.
* **Spoken Narration (approx. 55 words)**:
  > *"To help developers fix bugs fast, MIRA passes the proven defects and screenshot crops to the **Amazon Bedrock Converse API** using Claude Vision. Bedrock explains each defect in plain language—explaining what the remote user experiences on the couch and the architectural root cause—without ever altering the deterministic test verdict."*

### Part 5: Automated Patch Verification & Green Report (1:45 – 2:20)
* **Visual**: Engine applies vetted git patches, relaunches the app on the emulator, and re-explores the affected screens.
* **Spoken Narration (approx. 70 words)**:
  > *"MIRA doesn't just find defects—it verifies fixes. The engine applies vetted patch files from `fixes/`, re-explores the affected screen topology, and verifies that the defect is completely resolved with zero regressions introduced.*
  > *The before state fails with a red border; the re-explored state passes with a clean green focus indicator."*

### Part 6: Standalone HTML Report & Submission Wrap-Up (2:20 – 2:40)
* **Visual**: Open the generated `report.html` in a web browser. Scroll through the summary bar, interactive SVG focus navigation graph, and side-by-side red/green split-view cards.
* **Spoken Narration (approx. 45 words)**:
  > *"MIRA compiles everything into a standalone, single-file HTML report viewable offline. All code in this repository was built 100% fresh for the Amazon Developer Hackathon, combining deterministic test gating with AWS Bedrock visual intelligence. Thank you!"*
