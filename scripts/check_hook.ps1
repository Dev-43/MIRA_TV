# Verifies the app hook emits valid MIRA_FOCUS events. Run on V's laptop with the emulator + app running.
$adb = if ($env:MIRA_ADB_PATH) { $env:MIRA_ADB_PATH } else { "adb" }
$serial = @()
if ($env:MIRA_ADB_SERIAL) { $serial = @("-s", $env:MIRA_ADB_SERIAL) }
& $adb @serial logcat -c
foreach ($k in @("KEYCODE_DPAD_RIGHT", "KEYCODE_DPAD_DOWN", "KEYCODE_DPAD_LEFT", "KEYCODE_DPAD_UP")) {
  & $adb @serial shell input keyevent $k
  Start-Sleep -Milliseconds 700
}
$dump = Join-Path $env:TEMP "mira_logcat.txt"
& $adb @serial logcat -d | Out-File -Encoding utf8 $dump
$count = (Select-String -Path $dump -Pattern "MIRA_FOCUS" -SimpleMatch | Measure-Object).Count
Write-Host "MIRA_FOCUS lines: $count"
if ($count -lt 4) { Write-Host "CHECK_HOOK FAIL: expected at least 4 MIRA_FOCUS lines"; exit 1 }
python -m mira_tv validate-events --file $dump
if ($LASTEXITCODE -ne 0) { Write-Host "CHECK_HOOK FAIL: validate-events reported problems"; exit 1 }
Write-Host "CHECK_HOOK PASS"
exit 0
