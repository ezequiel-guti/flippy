# Eval scenario 05 -- gate FAILS OPEN on internal error: garbage (non-JSON)
# stdin must exit 0 (allow) and leave a warning in .sdad/gate.log.
# Exit 0 = pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$gate = Join-Path $repo ".claude\hooks\pre-tool-use-spec-gate.ps1"
if (-not (Test-Path $gate)) { $gate = Join-Path $repo "_staging_v5\hooks\pre-tool-use-spec-gate.ps1" }

$tmp = Join-Path $env:TEMP "sdad-eval-05-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    $env:CLAUDE_PROJECT_DIR = $tmp
    "this is not json {{{" | powershell -NoProfile -ExecutionPolicy Bypass -File $gate 2>$null
    $code = $LASTEXITCODE
    $logExists = Test-Path (Join-Path $tmp ".sdad\gate.log")
    if ($code -eq 0 -and $logExists) { Write-Host "PASS 05-gate-fail-open"; exit 0 }
    Write-Host "FAIL 05-gate-fail-open (exit $code, expected 0; gate.log present: $logExists)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:CLAUDE_PROJECT_DIR -ErrorAction SilentlyContinue
}
