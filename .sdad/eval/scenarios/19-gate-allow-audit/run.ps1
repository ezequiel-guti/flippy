# Eval scenario 19 -- gate ALLOWS code writes during $audit (sentinel file
# .sdad/AUDIT_ACTIVE) even with no SPEC.md. Mirrors scenario 04 ($docfinal).
# Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$gate = Join-Path $repo ".claude\hooks\pre-tool-use-spec-gate.ps1"
if (-not (Test-Path $gate)) { $gate = Join-Path $repo "_staging_v5\hooks\pre-tool-use-spec-gate.ps1" }

$tmp = Join-Path $env:TEMP "sdad-eval-19-$PID"
New-Item -ItemType Directory -Path (Join-Path $tmp ".sdad") -Force | Out-Null
try {
    Set-Content -Path (Join-Path $tmp ".sdad\AUDIT_ACTIVE") -Value "" -Encoding ASCII
    $env:CLAUDE_PROJECT_DIR = $tmp
    $json = '{"tool_name":"Write","tool_input":{"file_path":"' + ($tmp -replace '\\', '/') + '/app.py"}}'
    $json | powershell -NoProfile -ExecutionPolicy Bypass -File $gate 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "PASS 19-gate-allow-audit"; exit 0 }
    Write-Host "FAIL 19-gate-allow-audit (exit $LASTEXITCODE, expected 0)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:CLAUDE_PROJECT_DIR -ErrorAction SilentlyContinue
}
