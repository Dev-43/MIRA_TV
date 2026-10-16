# Verifies every bug/fix patch applies and reverses cleanly. Run from the repo root with a clean working tree.
$ErrorActionPreference = "Continue"
$status = git status --porcelain
if ($status) { Write-Host "CHECK_PATCHES FAIL: working tree not clean"; exit 1 }
$bugs = Get-ChildItem bugs -Filter "BUG-*.patch" -ErrorAction SilentlyContinue
if (-not $bugs -or $bugs.Count -ne 3) { Write-Host "CHECK_PATCHES FAIL: expected exactly 3 BUG-*.patch files"; exit 1 }
$failed = $false
foreach ($b in $bugs) {
  $n = ($b.Name -split "-")[1]
  $fix = Get-ChildItem fixes -Filter "FIX-$n-*.patch" -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $fix) { Write-Host "FAIL: no fix for $($b.Name)"; $failed = $true; continue }
  git apply --check $b.FullName; if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: bug does not apply: $($b.Name)"; $failed = $true; continue }
  git apply $b.FullName
  git apply --check $fix.FullName; if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: fix does not apply after bug: $($fix.Name)"; $failed = $true; git apply -R $b.FullName; continue }
  git apply $fix.FullName
  git apply -R $fix.FullName
  git apply -R $b.FullName
  Write-Host "OK: $($b.Name) / $($fix.Name)"
}
$status = git status --porcelain
if ($status) { Write-Host "CHECK_PATCHES FAIL: tree dirty after reversing"; $failed = $true }
if ($failed) { exit 1 }
Write-Host "CHECK_PATCHES PASS (reminder: confirm manually that the app still reloads after each bug)"
exit 0
