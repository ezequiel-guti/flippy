# Eval scenario 21 -- I7 audit-report-integrity ratchet: the honest report passes
# (exit 0) and the deliberately weakened report is caught (exit 1 -- fabricated 5a
# finding with no elicitation, missing reproducibility stamp, un-surfaced gaps).
# This is the I7 SPEC-S8 test: "the runner catches a deliberately weakened audit."
# Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$check = Join-Path $repo "checks\audit-report-integrity.ps1"
$honest = Join-Path $repo ".sdad\audit\_fixtures\honest-report"
$weakened = Join-Path $repo ".sdad\audit\_fixtures\weakened-report"

$fails = 0

# honest report must PASS the integrity check (exit 0)
& powershell -NoProfile -ExecutionPolicy Bypass -File $check -Dir $honest | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "  honest report: exit $LASTEXITCODE (expected 0)"; $fails++ }

# weakened report must be CAUGHT (exit 1)
& powershell -NoProfile -ExecutionPolicy Bypass -File $check -Dir $weakened | Out-Null
if ($LASTEXITCODE -ne 1) { Write-Host "  weakened report: exit $LASTEXITCODE (expected 1 -- weakening not caught)"; $fails++ }

if ($fails -eq 0) { Write-Host "PASS 21-audit-report-integrity"; exit 0 }
Write-Host "FAIL 21-audit-report-integrity ($fails subcases)"; exit 1
