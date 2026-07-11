# Eval scenario 02 -- gate ALLOWS a code Write when SPEC.md is approved.
# Exit 0 = scenario pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$gate = Join-Path $repo ".claude\hooks\pre-tool-use-spec-gate.ps1"
if (-not (Test-Path $gate)) { $gate = Join-Path $repo "_staging_v5\hooks\pre-tool-use-spec-gate.ps1" }

$tmp = Join-Path $env:TEMP "sdad-eval-02-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    Set-Content -Path (Join-Path $tmp "SPEC.md") -Value "> SPEC STATUS: APPROVED (eval fixture)" -Encoding UTF8
    $env:CLAUDE_PROJECT_DIR = $tmp
    $json = '{"tool_name":"Write","tool_input":{"file_path":"' + ($tmp -replace '\\', '/') + '/app.py"}}'
    $json | powershell -NoProfile -ExecutionPolicy Bypass -File $gate 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "PASS 02-gate-allow-approved"; exit 0 }
    Write-Host "FAIL 02-gate-allow-approved (exit $LASTEXITCODE, expected 0)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:CLAUDE_PROJECT_DIR -ErrorAction SilentlyContinue
}
