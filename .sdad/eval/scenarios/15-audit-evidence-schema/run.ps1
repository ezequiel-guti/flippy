# Eval scenario 15 -- I1 audit-evidence ratchet: a valid node-graph passes, an
# invalid one fails, and the acquire-evidence stub declares a gap (no crash) when
# no .ppl is supplied, producing output that itself validates. Exit 0 = pass,
# 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$check = Join-Path $repo "checks\audit-evidence.ps1"
$valid = Join-Path $repo ".sdad\audit\_fixtures\valid-node-graph.json"
$invalid = Join-Path $repo ".sdad\audit\_fixtures\invalid-node-graph.json"
$acquire = Join-Path $repo ".sdad\audit\lib\acquire-evidence.ps1"

$fails = 0

& powershell -NoProfile -ExecutionPolicy Bypass -File $check $valid | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "  valid fixture: exit $LASTEXITCODE (expected 0)"; $fails++ }

& powershell -NoProfile -ExecutionPolicy Bypass -File $check $invalid | Out-Null
if ($LASTEXITCODE -ne 1) { Write-Host "  invalid fixture: exit $LASTEXITCODE (expected 1)"; $fails++ }

# stub: no .ppl supplied -> node-graph.json with a declared gap, exit 0, no crash.
$tmp = Join-Path $env:TEMP "sdad-eval-15-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $acquire -Project "evaltest" -OutDir $tmp | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "  acquire stub (no ppl): exit $LASTEXITCODE (expected 0)"; $fails++ }
    $graph = Join-Path $tmp "node-graph.json"
    if (-not (Test-Path $graph)) {
        Write-Host "  acquire stub: node-graph.json not produced"; $fails++
    } else {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $check $graph | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "  acquire stub output invalid: exit $LASTEXITCODE (expected 0)"; $fails++ }
        $j = (Get-Content $graph -Raw | ConvertFrom-Json)
        if (@($j.gaps).Count -lt 1) { Write-Host "  acquire stub: no gap declared (expected >=1)"; $fails++ }
    }
} finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

if ($fails -eq 0) { Write-Host "PASS 15-audit-evidence-schema"; exit 0 }
Write-Host "FAIL 15-audit-evidence-schema ($fails subcases)"; exit 1
