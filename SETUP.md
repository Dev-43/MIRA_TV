# SETUP.md — MIRA TV prerequisites (D and V)

> Do this first, before any task in BUILD_D.md or BUILD_V.md. Every step has a check. If a check fails, stop, write it in `docs/FRICTION_LOG.md`, and message your teammate. Commands are PowerShell on Windows.
> Items marked **UNCLEAR** depend on files I have not seen. Do not guess them; read the source named in the step.

## 0. Who needs what
| Item | D (low-spec laptop) | V (high-spec laptop) |
|---|---|---|
| Git + GitHub account | Yes | Yes |
| Python 3.11/3.12 + venv | Yes | Yes (to run the engine live) |
| Node 20 LTS, JDK 17 | No | Yes |
| Android Studio + emulator | **No** | Yes |
| AWS account + Bedrock key | **Yes** | No |
| Devpost account | Yes (creates submission) | Yes (joins team) |
| YouTube or Vimeo account | No | Yes (uploads video) |
| Screen recorder | No | Yes |

## 1. Shared accounts (both, Oct 15)
1. **GitHub:** both have accounts. D creates the public repo `mira-tv` with an MIT license and adds V as a collaborator (Write). Check: both can `git push` to a test branch.
2. **Devpost:** both register for the hackathon at amazonappdev2026.devpost.com ("Join Hackathon"). One person (the Representative) creates the submission and adds the other as a team member. Decide who today. Check: both see the hackathon in their Devpost dashboard.
3. **Chat + daily sync:** one shared channel (WhatsApp or Discord) and one 10-minute sync time. Check: first post made.
4. **Screen sharing tool** (Meet, Discord, or Zoom): needed for live integration on V's laptop. Check: a 1-minute test share.

## 2. Both: Git and Python
1. Install Git (≥ 2.40): check `git --version`.
2. Install Python 3.11 or 3.12: check `python --version`.
3. Clone and create the venv:
```powershell
git clone https://github.com/<owner>/mira-tv.git
cd mira-tv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.
4. After D adds `requirements.txt` (Task D1): `pip install -r requirements.txt` (`Pillow`, `boto3`, `pytest`). Check: `pytest --version`.
5. Git identity: `git config user.name "<name>"`, `git config user.email "<email>"`.
6. Copy the env file: `Copy-Item .env.example .env`. Never commit `.env`.

## 3. D only: AWS Bedrock (do on Oct 15–16)
Account and model access can take time, so start now.
1. Sign in to (or create) an AWS account. Billing needs a payment card. The hackathon's AWS credit codes are gone, so assume a small real cost. Set a budget alert in AWS Billing at a low amount.
2. Open the Bedrock console in your chosen region. Enable access to a **vision-capable Claude model**. Note the exact model ID or inference profile ID the console shows.
3. Create a Bedrock API key in the console. Put it only in `.env`:
```
AWS_BEARER_TOKEN_BEDROCK=<your key>
AWS_REGION=<region from console>
BEDROCK_MODEL_ID=<id from console>
MIRA_BEDROCK_MODE=stub
```
4. After Task D6 exists: `python -m mira_tv ai-ping` prints OK. Then set `MIRA_BEDROCK_MODE=live` only when you want real calls.
5. Never share the key in chat, commits, or screenshots. If it leaks, delete it in the console immediately and create a new one.
**Check:** `ai-ping` returns OK, and the key does not appear in `git diff`.

## 4. V only: Android toolchain
1. **Virtualization:** enable VT-x/AMD-V in BIOS, and turn on the Windows feature "Windows Hypervisor Platform" (Hyper-V if the emulator asks). Reboot. Check: Task Manager → Performance → CPU shows "Virtualization: Enabled".
2. **Node 20 LTS:** check `node --version`. (Confirm the version the sample app requires in `app/package.json`; **UNCLEAR** until you read it.)
3. **JDK 17:** check `java -version`.
4. **Android Studio** (latest stable) with the Android SDK and platform-tools. Add `...\Android\Sdk\platform-tools` to PATH. Check: `adb version`.
5. **Emulator:** Device Manager → Create Device → **TV → Android TV (1080p)** → system image API 30–34 (pick the lowest the sample supports) → RAM ≥ 3 GB. Boot it. Check: `adb devices` lists `emulator-xxxx`.
6. **Remote check:** `adb shell input keyevent KEYCODE_DPAD_RIGHT` returns without error.
7. **Screenshot check:** `adb exec-out screencap -p > shot.png` creates a viewable image.

## 5. V only: the sample app
1. Clone `https://github.com/AmazonAppDev/react-native-multi-tv-app-sample` into a temp folder; copy its files into `app/` of `mira-tv`; delete `app/.git`; keep its license file.
2. `cd app; npm install`.
3. **Build and run on the emulator by following `app/README.md` exactly** (it uses Expo; the exact TV-prebuild and run commands are **UNCLEAR** until you read it). Do not improvise commands.
4. Keep Metro running in its own terminal for all live runs.
**Check (all four):** (a) app is visible on the emulator; (b) a D-pad key press moves focus visibly; (c) a screenshot is saved; (d) `adb logcat -d | findstr ReactNativeJS` prints output.
**Fallback:** if the sample will not build by the end of Oct 17, switch to `hello-world-fire-tv-react-native` and tell D the same day.

## 6. V only: recording and upload
1. Pick a screen recorder that exports MP4 (OBS Studio or the Windows Game Bar). Test a 20-second recording with audio off or your own voice.
2. Create or sign in to YouTube (or Vimeo). Test an **unlisted** upload, then confirm the final upload will be **public** later.
3. No copyrighted music, no Amazon or other third-party logos in the video.

## 7. Final readiness check (both, by Oct 16 evening)
| # | Check | Owner | Pass when |
|---|---|---|---|
| 1 | Repo is public, MIT visible, both can push | D | Both pushed a branch |
| 2 | `pytest -q` runs on a clean clone | D | Prints passed (even with 1 test) |
| 3 | `ai-ping` | D | OK (or `stub` mode confirmed if Bedrock is delayed) |
| 4 | Emulator + app + D-pad key moves focus | V | All four checks in section 5 |
| 5 | `docs/APP_MAP.md` exists | V | Package, activity, screens, element IDs filled |
| 6 | Screen share works | Both | Test share done |
| 7 | Both registered on Devpost | Both | Dashboard shows the hackathon |

## 8. Troubleshooting (log every hit in `docs/FRICTION_LOG.md`)
| Problem | Try |
|---|---|
| `adb` not recognized | PATH missing `platform-tools`; reopen PowerShell |
| Emulator will not start / very slow | Check virtualization (section 4); lower the AVD resolution or RAM; close heavy apps |
| `adb devices` shows `offline` | `adb kill-server; adb start-server`; restart the emulator |
| Gradle or Expo build fails | Check JDK 17 and Node version; read the sample's README and issues; try the fallback sample |
| `MIRA_FOCUS` never appears in logcat | Confirm the app is a dev build (`__DEV__` true), Metro is running, and the hook is wired to the element |
| Bedrock `AccessDenied` | Model access not enabled in that region, or wrong `BEDROCK_MODEL_ID` |
| PowerShell script blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Key accidentally committed | Delete the key in the AWS console first, then rewrite history only with your teammate's agreement |
