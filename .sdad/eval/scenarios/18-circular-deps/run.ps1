# Eval scenario 18 -- I4 circular-deps ratchet: an acyclic node-graph passes
# (exit 0) and a graph whose dependencies form a cycle fails (exit 1), naming the
# nodes on the cycle. Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$check = Join-Path $repo "checks\circular-deps.ps1"
$clean = Join-Path $repo ".sdad\audit\_fixtures\valid-node-graph.json"
$defect = Join-Path $repo ".sdad\audit\_fixtures\circular-deps.node-graph.json"

$fails = 0

& powershell -NoProfile -ExecutionPolicy Bypass -File $check $clean | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "  clean fixture: exit $LASTEXITCODE (expected 0)"; $fails++ }

$out = & powershell -NoProfile -ExecutionPolicy Bypass -File $check $defect
$code = $LASTEXITCODE
$text = ($out | Out-String)
if ($code -ne 1) { Write-Host "  defect fixture: exit $code (expected 1)"; $fails++ }
if ($text -notmatch 'cycle detected') { Write-Host "  defect fixture: did not report a cycle"; $fails++ }
if ($text -notmatch 'cash_flow') { Write-Host "  defect fixture: cycle path did not name the nodes"; $fails++ }

if ($fails -eq 0) { Write-Host "PASS 18-circular-deps"; exit 0 }
Write-Host "FAIL 18-circular-deps ($fails subcases)"; exit 1
