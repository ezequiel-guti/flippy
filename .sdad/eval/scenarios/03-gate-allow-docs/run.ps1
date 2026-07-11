# Eval scenario 03 -- gate ALLOWS docs/markdown writes even with no SPEC.md
# (allowlist R1: docs/, *.md). Exit 0 = pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$gate = Join-Path $repo ".claude\hooks\pre-tool-use-spec-gate.ps1"
if (-not (Test-Path $gate)) { $gate = Join-Path $repo "_staging_v5\hooks\pre-tool-use-spec-gate.ps1" }

$tmp = Join-Path $env:TEMP "sdad-eval-03-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    $env:CLAUDE_PROJECT_DIR = $tmp
    $base = $tmp -replace '\\', '/'
    $fails = 0
    foreach ($rel in @('docs/guide.md', 'NOTES.md', 'docs/page.html')) {
        $json = '{"tool_name":"Edit","tool_input":{"file_path":"' + $base + '/' + $rel + '"}}'
        $json | powershell -NoProfile -ExecutionPolicy Bypass -File $gate 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Host "  subcase $rel exit $LASTEXITCODE (expected 0)"; $fails++ }
    }
    if ($fails -eq 0) { Write-Host "PASS 03-gate-allow-docs"; exit 0 }
    Write-Host "FAIL 03-gate-allow-docs ($fails subcases)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:CLAUDE_PROJECT_DIR -ErrorAction SilentlyContinue
}
