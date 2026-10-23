# FEEDBACK.md (owner: D) — Product Feedback for Hackathon Submission

This document records authentic product feedback from building MIRA TV for the Devpost submission and the **AWS Builder** mini-challenge.

---

## 1. Android Studio Emulator (Android TV 1080p Image)
- **What we used it for**: Running and visual testing of the React Native Fire TV sample application, testing remote control D-pad navigation over ADB, and capturing 1080p screenshots of focused UI states.
- **What worked well**: Once booted, the Android TV system image (API 34, Android 14) accurately rendered the 10-foot TV UI, responded faithfully to standard Android keycodes (`KEYCODE_DPAD_*`), and rendered high-resolution frame buffers accessible directly through `screencap -p`.
- **What needs work**: First-time initialization on Windows requires manual configuration of Windows Hypervisor Platform (WHPX) when Intel VT-x is managed across nested hypervisors. Cold boot on Windows can take 2–3 minutes before `sys.boot_completed` registers, requiring robust retry loops in automation scripts.
- **Onboarding experience**: Moderate. Finding the exact system image in `sdkmanager` (`system-images;android-34;android-tv;x86`) required filtering through numerous mobile and Google TV variants.
- **Would we build with it again?**: **Yes**. The emulator accurately reflects real living-room TV display densities and provides standard ADB access essential for automated QA agents.

---

## 2. ADB (Android Debug Bridge)
- **What we used it for**: Automated process lifecycle management (`am force-stop`, `am start`), real-time D-pad remote input injection (`input keyevent`), raw binary frame capture (`exec-out screencap -p`), and low-latency focus telemetry streaming via `logcat -v raw -s ReactNativeJS:V`.
- **What worked well**: Zero-dependency automation. `exec-out screencap -p` delivers uncompressed PNG streams directly to stdout without intermediate file writes on device storage. Background streaming of `ReactNativeJS` logs enabled instantaneous focus detection with sub-millisecond overhead.
- **What needs work**: Occasional device `offline` states during cold boot require polling checks on `getprop sys.boot_completed`. Windows PowerShell binary stdout redirection requires careful encoding handling (`Piped to python` rather than shell redirection).
- **Onboarding experience**: Excellent. Standardized CLI commands work identically across macOS, Linux, and Windows.
- **Would we build with it again?**: **Yes**. ADB is the gold standard for headless and automated Android TV testing.

---

## 3. Expo / React Native TV Sample App
- **What we used it for**: Target application under test, demonstrating real multi-screen TV navigation across catalog grids, navigation drawers, and detail pages.
- **What worked well**: Expo and `react-native-tvos` allow rapid cross-platform TV development with hot reloading via Metro. Bounding box calculation through `measureInWindow` scales cleanly to screenshot pixels when multiplied by `PixelRatio.get()`.
- **What needs work**: Heavy dependency tree (1,800+ packages in Yarn monorepo). On Windows, built-in Yarn 4 compatibility patches for TypeScript require careful path handling.
- **Onboarding experience**: Good. Clear configuration via `app.json` and straightforward TV orientation settings.
- **Would we build with it again?**: **Yes**. The React Native ecosystem for TV is maturing rapidly and provides exceptional development velocity.

---

## 4. React TV Space Navigation
- **What we used it for**: Directional spatial navigation management between focusable cards, buttons, and drawer menu items.
- **What worked well**: Declarative `<SpatialNavigationFocusableView>` and spatial event handling make building 10-foot directional grids intuitive. Provides clean `onFocus` and `onSelect` hooks that make instrumentation effortless.
- **What needs work**: Complex nested focus roots can occasionally produce subtle dead-ends or traps when transitioning between vertical lists and horizontal rows unless explicit edge anchors are declared.
- **Onboarding experience**: Very good. Well-documented API with intuitive focus delegation.
- **Would we build with it again?**: **Yes**. Highly recommended for any React Native TV app targeting Fire TV or Android TV.

---

## 5. Amazon Sample Repository (`AmazonAppDev/react-native-multi-tv-app-sample`)
- **What we used it for**: Real-world baseline application for demonstrating autonomous QA, bug injection, and patch verification.
- **What worked well**: Clean separation of `apps/expo-multi-tv` and `packages/shared-ui`. The UI components closely reflect production streaming apps with hero banners, metadata labels, and video detail layouts.
- **What needs work**: Monorepo Yarn workspace configuration contains some unfulfilled peer dependencies across Vega and Expo workspaces.
- **Onboarding experience**: Smooth. Good documentation in root README.
- **Would we build with it again?**: **Yes**. Serves as an ideal architectural reference for multi-platform TV applications.

---

## 6. Amazon Bedrock (Converse API) — AWS Builder Challenge
- **Which service used**: **Amazon Bedrock Converse API** (`bedrock-runtime`) utilizing Claude Vision.
- **How we used it**:
  - MIRA strictly separates **deterministic defect detection** from **AI explanation**. Pass/fail verdicts are computed 100% deterministically by algorithmic graph traversal and computer vision (Pillow pixel diffing).
  - Bedrock Converse is used exclusively as an **intelligent developer explanation layer**. When a defect is proven, MIRA sends the defect JSON and a 6px red-annotated bounding-box screenshot to Bedrock.
  - Bedrock generates a concise ($\le 60$ words), plain-language summary explaining what a remote-control user experiences on the couch and the most likely architectural root cause.
- **Three-Tier Architecture**:
  - `stub` *(default)*: Deterministic template explanations; requires zero AWS credentials or network access, ensuring judges can test offline.
  - `cache`: Replays genuine Bedrock responses saved in `ai_cache/` using SHA-256 content addressing.
  - `live`: Direct authenticated calls via AWS SDK (`boto3`) to Bedrock Converse API with exponential backoff and a hard cap of 12 calls (`MIRA_MAX_AI_CALLS`).
- **What worked well**: The Converse API unified multimodal schema makes sending text and PNG image blocks remarkably clean. Low latency and high visual reasoning quality from Claude Vision.
- **What needs work**: Better client-side SDK error typing for region-specific model availability.
- **Onboarding experience**: Excellent. Bedrock console setup and model access configuration was smooth and fast.
- **Would we build with it again?**: **Yes, absolutely**. The combination of deterministic test gating with Bedrock visual explanation represents the ideal paradigm for reliable, hallucination-free AI testing agents.
