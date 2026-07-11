# Eval scenario 01 -- gate DENIES a code Write when SPEC.md is absent.
# Exit 0 = scenario pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$gate = Join-Path $repo ".claude\hooks\pre-tool-use-spec-gate.ps1"
if (-not (Test-Path $gate)) { $gate = Join-Path $repo "_staging_v5\hooks\pre-tool-use-spec-gate.ps1" }

$tmp = Join-Path $env:TEMP "sdad-eval-01-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    $env:CLAUDE_PROJECT_DIR = $tmp
    $json = '{"tool_name":"Write","tool_input":{"file_path":"' + ($tmp -replace '\\', '/') + '/app.py"}}'
    # PS 5.1: stderr of a native call under EAP Stop becomes a terminating
    # NativeCommandError -- relax EAP around the call (the deny message IS stderr).
    $ErrorActionPreference = "Continue"
    $json | powershell -NoProfile -ExecutionPolicy Bypass -File $gate 2>$null
    $ErrorActionPreference = "Stop"
    if ($LASTEXITCODE -eq 2) { Write-Host "PASS 01-gate-deny-no-spec"; exit 0 }
    Write-Host "FAIL 01-gate-deny-no-spec (exit $LASTEXITCODE, expected 2)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:CLAUDE_PROJECT_DIR -ErrorAction SilentlyContinue
}
