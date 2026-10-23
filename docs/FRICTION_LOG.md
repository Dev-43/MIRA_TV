# FRICTION_LOG.md (shared, append-only)

Entry template (copy, fill, append at the end):

### <short title> - <D or V> - <date>
- Task attempted:
- Steps taken:
- Expected vs actual:
- Severity: Low / Medium / High
- Workaround:
- Actionable suggestion:

---

### Windows Hypervisor Platform (WHPX) vs Firmware VT-x - V - 2026-10-16
- **Task attempted**: Boot Android TV 1080p AVD (`Android_TV_1080p`) from command line using `emulator.exe`.
- **Steps taken**: Ran `emulator -avd Android_TV_1080p` on Windows 11.
- **Expected vs actual**: Expected immediate emulator startup with HAXM/KVM acceleration. Actual: Failed with `emulator: ERROR: x86 emulation currently requires hardware acceleration!` because Intel VT-x firmware flag was disabled in BIOS despite Windows Hypervisor Platform feature being installed.
- **Severity**: High
- **Workaround**: Enabled Windows Hypervisor Platform (WHPX) via DISM, configured `hw.gpu.mode=auto`, and launched emulator with `-gpu swiftshader_indirect` fallback.
- **Actionable suggestion**: The Android Studio AVD creation wizard should explicitly verify both Windows hypervisor features and BIOS firmware virtualization flags before allowing x86 image selection.

### Yarn 4 Corepack Permission & TypeScript Patch Failure - V - 2026-10-17
- **Task attempted**: Install React Native sample app dependencies using `yarn install`.
- **Steps taken**: Executed `corepack enable` followed by `yarn install` in `app/`.
- **Expected vs actual**: Expected clean package extraction. Actual: `corepack enable` failed with `EPERM: operation not permitted` on `C:\Program Files\nodejs\yarnpkg.CMD`. Subsequent `corepack yarn install` raised `YN0066: Cannot apply hunk #1` for builtin TypeScript 5.7.3 patch due to Windows CRLF line ending differences.
- **Severity**: Medium
- **Workaround**: Invoked yarn directly through `corepack yarn` without global activation, and allowed optional patches to bypass non-blocking hunks.
- **Actionable suggestion**: Yarn 4 should default to permissive line-ending normalization for internal compatibility patches on Windows hosts.

### PixelRatio Scaling for Focus Bounding Boxes - D & V - 2026-10-18
- **Task attempted**: Calculate physical pixel coordinates for UI focus indicators so bounding box overlays match captured screenshot dimensions.
- **Steps taken**: Instrumented `reportFocus` to measure `(x, y, w, h)` via React Native's `measureInWindow`.
- **Expected vs actual**: Expected returned coordinates to align directly with 1920x1080 screenshots. Actual: Coordinates were reported in density-independent pixels (dp) (960x540 for 1080p TV at 320 dpi density, corresponding to a 2.0x scale factor), resulting in annotations drawn in the top-left quadrant.
- **Severity**: High
- **Workaround**: Multiplied all measured dimensions by `PixelRatio.get()` inside `app/mira/reportFocus.ts` prior to emitting `MIRA_FOCUS` JSON lines over logcat.
- **Actionable suggestion**: React Native TV documentation should explicitly highlight that screen measurements in `measureInWindow` require manual multiplication by `PixelRatio.get()` when correlating with ADB `screencap` output.

### Zero-Dependency Environment Variable Parsing - D - 2026-10-18
- **Task attempted**: Load `.env` configuration in `mira_tv/config.py` without introducing external dependencies like `python-dotenv`.
- **Steps taken**: Implemented line-by-line custom text parser in `load_dotenv()`.
- **Expected vs actual**: Expected standard KEY=VALUE lines to parse cleanly. Actual: Quoted values, inline whitespace, and Windows CRLF endings caused string comparison mismatches in boolean and numeric environment variables.
- **Severity**: Low
- **Workaround**: Added explicit stripping of single/double quotes and whitespace, with safe fallback type casters `_int()` and `_float()`.
- **Actionable suggestion**: Standardize on a minimal, single-function dotenv parser snippet across Python projects that prohibit third-party package bloat.

### ADB Subprocess Execution Hangs on Network Telemetry - D - 2026-10-19
- **Task attempted**: Read continuous ADB logcat streams to parse `MIRA_FOCUS` focus telemetry events in real time.
- **Steps taken**: Invoked `subprocess.Popen(["adb", "logcat"])` on the main testing thread.
- **Expected vs actual**: Expected logcat to yield lines as focus changed. Actual: Subprocess buffer deadlocked the Python test execution when no new focus events were emitted, causing test runs to hang indefinitely.
- **Severity**: High
- **Workaround**: Isolated logcat ingestion into a dedicated daemon background worker thread (`_logcat_thread`) that feeds a thread-safe `queue.Queue`, and enforced hard 20-second timeouts across all ADB command invocations.
- **Actionable suggestion**: ADB test tooling should always decouple continuous stream readers into asynchronous queues or threads rather than synchronous subprocess pipes.

### Bedrock Converse API Image Block Payload Schema - D - 2026-10-20
- **Task attempted**: Send annotated PNG screenshot evidence to Amazon Bedrock Converse API for plain-language developer explanations.
- **Steps taken**: Constructed multimodal message payload with base64 encoded image string.
- **Expected vs actual**: Expected Bedrock Converse API to accept standard base64 image strings. Actual: Received `ValidationException`: `converse` expects binary bytes passed directly under `{"image": {"format": "png", "source": {"bytes": <bytes>}}}` rather than base64 text strings.
- **Severity**: Medium
- **Workaround**: Passed raw PNG bytes directly into the `source.bytes` dictionary in `mira_tv/ai.py` and wrapped calls with automatic fallback to `stub` mode on any API exception.
- **Actionable suggestion**: AWS Boto3 documentation for the Converse API should explicitly contrast the `bytes` dictionary schema against the base64 convention used by Anthropic's native Messages API.
