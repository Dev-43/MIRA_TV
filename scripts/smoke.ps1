$ErrorActionPreference = "Continue"
Write-Host "== pytest =="
python -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host "SMOKE FAIL: tests"; exit 1 }
Write-Host "== fixture demo =="
python -m mira_tv demo --mode fixture
if ($LASTEXITCODE -ne 0) { Write-Host "SMOKE FAIL: demo (expected until D7 is built)"; exit 1 }
Write-Host "SMOKE PASS"
exit 0
