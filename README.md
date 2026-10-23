# MIRA TV — Autonomous Remote-Control QA Agent for Fire TV

[![tests](https://github.com/Dev-43/MIRA_TV/actions/workflows/test.yml/badge.svg)](https://github.com/Dev-43/MIRA_TV/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11 | 3.12](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Track: Fire TV](https://img.shields.io/badge/Track-Fire%20TV-orange.svg)](https://developer.amazon.com/apps-and-games/fire-tv)
[![Challenge: AWS Builder](https://img.shields.io/badge/Challenge-AWS%20Builder-yellow.svg)](https://aws.amazon.com/bedrock/)

**MIRA TV** is an autonomous remote-control QA agent engineered specifically for Fire TV and Android TV applications. Operating directly over ADB (or an offline synthetic fixture driver), MIRA systematically presses D-pad directional keys, maps the application's spatial focus graph, and deterministically detects the three most critical 10-foot UI defects: **`UNREACHABLE`** controls, navigation **`TRAP`**s, and missing focus indicators (**`NO_FOCUS_INDICATOR`**). Proven defects are explained in plain language using **Amazon Bedrock (Claude Vision)**, automatically repaired using vetted patch files, and verified via screen re-exploration to generate a standalone, split-view (Red/FAIL vs. Green/PASS) HTML verification report.

---

## Table of Contents
- [Why MIRA TV: Amazon Fire TV Guidelines](#why-mira-tv-amazon-fire-tv-guidelines)
- [Architecture & Flow](#architecture--flow)
- [How Detection Works (Deterministic Engine)](#how-detection-works-deterministic-engine)
- [AWS Bedrock Integration (AWS Builder Challenge)](#aws-bedrock-integration-aws-builder-challenge)
- [Guardrails & Safety Protocols](#guardrails--safety-protocols)
- [Setup & Quickstart for Judges](#setup--quickstart-for-judges)
- [Running Live with Android TV Emulator](#running-live-with-android-tv-emulator)
- [What Was Built During the Hackathon Window](#what-was-built-during-the-hackathon-window)
- [Credits & Licenses](#credits--licenses)

---

## Why MIRA TV: Amazon Fire TV Guidelines

Building applications for TV requires a fundamentally different mental model than mobile or web: the **10-foot experience**. Users navigate exclusively using a remote control D-pad (`UP`, `DOWN`, `LEFT`, `RIGHT`, `CENTER`, `BACK`) from across the living room.

Amazon's official [Fire TV Design and User Experience Guidelines](https://developer.amazon.com/docs/fire-tv/design-and-user-experience-guidelines.html) and [Focus and Navigation Guidelines](https://developer.amazon.com/docs/fire-tv/focus-and-navigation.html) enforce two non-negotiable rules:

> 1. *"Every interactive control must be reachable using only directional keys on the remote control. Users must never encounter navigation dead-ends or unreachable buttons."*
> 2. *"It must be immediately clear which item has focus at all times. The focused element must have a distinct visual treatment (such as a border, scale, or color change) that differentiates it from unfocused elements."*

Manual remote-control testing across dozens of screen paths is tedious, slow, and prone to human oversight. MIRA TV automates this process end-to-end with mathematical precision.

---

## Architecture & Flow

```
                      ┌────────────────────────────────────────┐
                      │   Fire TV / Android TV App (Expo)      │
                      │   app/mira/reportFocus.ts (__DEV__)    │
                      └──────────────────┬─────────────────────┘
                                         │ C1: adb logcat MIRA_FOCUS {json}
                                         ▼
                      ┌────────────────────────────────────────┐
                      │          MIRA Python Engine            │
                      │  ┌──────────────────────────────────┐  │
                      │  │  Driver: AdbDriver / Fixture     │  │
                      │  │  Graph: BFS Spatial Explorer     │  │
                      │  └──────────────────┬───────────────┘  │
                      │                     │ Defect Candidates│
                      │  ┌──────────────────▼───────────────┐  │
                      │  │   Deterministic Defect Gate      │  │
                      │  │   • UNREACHABLE  • TRAP          │  │
                      │  │   • NO_FOCUS_INDICATOR (Pillow)  │  │
                      │  └──────────────────┬───────────────┘  │
                      └─────────────────────┼──────────────────┘
                                            │ Defect JSON + Annotated Shot
                                            ▼
                      ┌────────────────────────────────────────┐
                      │ Amazon Bedrock Converse API (Vision)   │
                      │ • Claude Vision Plain-Text Explanation │
                      │ • Caches response in ai_cache/         │
                      └─────────────────────┬──────────────────┘
                                            │
                                            ▼
                      ┌────────────────────────────────────────┐
                      │ Verification & Patch Engine            │
                      │ • Apply vetted patch (fixes/FIX-*.patch│
                      │ • Re-explore affected screen topology  │
                      │ • Enforce regression-free PASS/FAIL    │
                      └─────────────────────┬──────────────────┘
                                            │ C2: report.json
                                            ▼
                      ┌────────────────────────────────────────┐
                      │ Static Single-File Report Compiler     │
                      │ • report/build_report.py (Contract C5) │
                      │ • artifacts/<run_id>/report.html       │
                      │ • Split-view Red/Before vs Green/After │
                      └────────────────────────────────────────┘
```

---

## How Detection Works (Deterministic Engine)

MIRA TV strictly separates **deterministic defect detection** from **AI explanation**. Pass/fail verdicts are never hallucinated and are calculated purely through algorithmic graph traversal and computer vision:

| Defect Type | Deterministic Detection Rule | Verification Rule |
|---|---|---|
| **`UNREACHABLE`** | Target elements cataloged in `contracts/expected_elements.json` that never appear in the explored focus graph nodes after BFS exploration ($V_{expected} \setminus V_{visited}$). | Fix restores focusability; element is successfully visited and focused during re-exploration. |
| **`TRAP`** | Reverse reachability analysis from designated exit targets (e.g., navigation drawer or parent screen). Any node with no directed path returning to an exit target is flagged as a navigation trap. | Fix restores exit path back to drawer/home; reverse reachability from exit targets covers all screen nodes. |
| **`NO_FOCUS_INDICATOR`** | Mean absolute pixel difference across the element's bounding box comparing its focused state against an unfocused neighbor state:$$\Delta_{px} = \frac{1}{3 \cdot W \cdot H}\sum_{c \in \{R,G,B\}}\sum_{x,y}|I_{\text{focused}}(x,y,c) - I_{\text{neighbor}}(x,y,c)|$$If $\Delta_{px} < \text{MIRA\_INDICATOR\_DIFF\_MIN}$ (default 4.0), it is flagged as invisible focus. | Fix restores visible border/scale; pixel delta rises significantly above threshold. |

---

## AWS Bedrock Integration (AWS Builder Challenge)

MIRA TV leverages the **Amazon Bedrock Converse API** (`bedrock-runtime`) using a vision-capable Claude model to bridge the gap between automated test graphs and developer actionability:

1. **Role of Bedrock**:
   - Accepts the deterministic defect payload and the 6px annotated bounding-box screenshot.
   - Generates a concise, plain-language developer summary ($\le 60$ words) explaining what a remote-control user experiences and the root architectural cause.
2. **Three Operational Modes**:
   - `stub` *(default)*: Deterministic template explanations; requires **zero** AWS keys or network access (ideal for offline judge testing).
   - `cache`: Replays genuine Bedrock responses saved in `ai_cache/` using SHA-256 content addressing:
     $$\text{Key} = \text{SHA256}(\text{PROMPT\_VERSION} + \text{model\_id} + \text{defect\_id} + \text{SHA256}(\text{image\_bytes}))$$
   - `live`: Direct authenticated calls via AWS SDK (`boto3`) to Amazon Bedrock Converse API.
3. **Guardrails**:
   - **Hard Cap**: Max 12 AI calls per run (`MIRA_MAX_AI_CALLS = 12`).
   - **Resilience**: 30-second timeout, 2 retries, and automatic fallback to `stub` on any network failure (never aborts a QA run).
   - **Verdict Isolation**: Bedrock output is strictly explanatory; it cannot alter the deterministic PASS/FAIL verdict.

---

## Guardrails & Safety Protocols

- **Deterministic Gate**: Defect verdicts come exclusively from the deterministic detectors. AI text never influences pass/fail results.
- **Vetted Patches Only**: Fixes are strictly verified unified diffs in `fixes/`. No unconstrained or AI-generated code edits are ever applied.
- **Subprocess & Network Timeouts**: Every ADB subprocess enforces a strict 20-second timeout. No command can hang indefinitely.
- **Guaranteed Reversibility**: The demo runner restores all applied patches via `git apply -R` inside a `finally` block, ensuring working trees remain pristine even upon test termination.
- **Secrets Protection**: `.env` and API credentials are git-ignored; CLI ping commands never leak keys or tokens to stdout/stderr.
- **Zero Production Overhead**: The focus reporting hook is compiled inside `if (!__DEV__) return;` guaranteeing zero runtime impact in production releases.

---

## Setup & Quickstart for Judges

Judges can execute and verify the full MIRA TV QA cycle on any machine (Windows, macOS, or Linux) in **under 2 minutes** without installing Android Studio, Node.js, or an emulator, using our pre-recorded synthetic fixtures.

### 1. Prerequisites
- Python 3.11 or 3.12
- Git

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/Dev-43/MIRA_TV.git
cd MIRA_TV

# Create and activate a virtual environment
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# Install exact dependencies (only Pillow, boto3, and pytest)
pip install -r requirements.txt
```

### 3. Run Automated Tests
Verify that all 97 offline unit and integration tests pass:
```bash
python -m pytest -q
```

### 4. Run the Full QA Demo (Fixture Mode)
Run the autonomous demo runner in fixture mode:
```bash
python -m mira_tv demo --mode fixture
```

**What this does automatically:**
1. Loads the TV screen navigation space (`home` and `details`).
2. Explores the UI topology and flags all 3 defect types (`UNREACHABLE`, `TRAP`, `NO_FOCUS_INDICATOR`).
3. Generates plain-language explanations using Bedrock Converse (stub/cache mode).
4. Verifies fixes one-by-one by re-exploring the screens.
5. Captures 6px red (before/FAIL) and green (after/PASS) bounding-box screenshots.
6. Generates a standalone single-file HTML report at `artifacts/<run_id>/report.html`.

Open the generated `report.html` directly in any web browser to view the interactive cards, SVG focus visualizer, and split-view evidence.

---

## Running Live with Android TV Emulator

To run live against the instrumented React Native TV sample on an Android TV emulator:

### 1. Requirements
- Android Studio with **Android TV (1080p)** AVD (API level 30–34, RAM $\ge 3$ GB).
- Node.js 20 LTS & JDK 17.
- ADB added to system PATH.

### 2. Launch App & Metro
```bash
cd app
npm install
npx expo start
```
Run the application on the booted Android TV emulator following `app/README.md`.

### 3. Run Live Engine Demo
From the repository root:
```bash
# Verify focus telemetry stream over ADB
powershell -ExecutionPolicy Bypass -File scripts/check_hook.ps1

# Execute live QA demo
python -m mira_tv demo --mode live
```

---

## What Was Built During the Hackathon Window

This repository is **100% brand-new code** authored during the Amazon Developer Hackathon (October 15–23, 2026):

1. **Autonomous Remote-Control Engine (`mira_tv/`)**:
   - Spatial graph representation and BFS D-pad probe algorithms with automatic reset-and-replay recovery.
   - Deterministic detectors for `UNREACHABLE` controls and navigation `TRAP`s.
   - Computer vision focus indicator difference engine (`vision.py`) and high-resolution bounding-box annotator.
   - Abstract driver architecture (`Driver`, `AdbDriver`, `FixtureDriver`, `SessionRecorder`).
2. **Amazon Bedrock Converse Integration (`mira_tv/ai.py`)**:
   - Claude Vision integration with caching, retry logic, call limits, and fallback safety.
3. **React Native TV Telemetry (`app/mira/reportFocus.ts`)**:
   - PixelRatio-scaled coordinate calculation streaming live focus state over ADB logcat without frame drops.
4. **Offline Single-File Report Compiler (`report/`)**:
   - High-contrast, accessible dark theme HTML/CSS report with client-side SVG focus graph visualizer.
5. **Contract System & Test Suite (`contracts/`, `tests/`)**:
   - 97 deterministic unit and integration tests covering drivers, telemetry parser, graph BFS, detectors, vision math, AI engine, and patch verifiers.

---

## Credits & Licenses

- **License**: MIT License ([LICENSE](LICENSE)) — © 2026 Devesh Laxman Dolas.
- **Sample TV Application**: Based on [`AmazonAppDev/react-native-multi-tv-app-sample`](https://github.com/AmazonAppDev/react-native-multi-tv-app-sample), licensed under the MIT-0 License (preserved in [app/LICENSE](app/LICENSE)).
- **Focus Engine**: Powered by `react-tv-space-navigation`.
