# Eval scenario 17 -- I4 missing-result-assign ratchet: a clean node-graph passes
# (exit 0), a graph with a calculation node lacking result= fails (exit 1), and an
# interface node without result= is NOT flagged. Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$check = Join-Path $repo "checks\missing-result-assign.ps1"
$clean = Join-Path $repo ".sdad\audit\_fixtures\valid-node-graph.json"
$defect = Join-Path $repo ".sdad\audit\_fixtures\missing-result.node-graph.json"

$fails = 0

& powershell -NoProfile -ExecutionPolicy Bypass -File $check $clean | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "  clean fixture: exit $LASTEXITCODE (expected 0)"; $fails++ }

$out = & powershell -NoProfile -ExecutionPolicy Bypass -File $check $defect
$code = $LASTEXITCODE
$text = ($out | Out-String)
if ($code -ne 1) { Write-Host "  defect fixture: exit $code (expected 1)"; $fails++ }
# the offending function node must be named; the exempt interface node must not be
if ($text -notmatch 'margin') { Write-Host "  defect fixture: did not flag 'margin'"; $fails++ }
if ($text -match 'summary_screen') { Write-Host "  defect fixture: wrongly flagged interface node 'summary_screen'"; $fails++ }

if ($fails -eq 0) { Write-Host "PASS 17-missing-result-assign"; exit 0 }
Write-Host "FAIL 17-missing-result-assign ($fails subcases)"; exit 1
