# Eval scenario 08 -- structural asserts hold on the repo's real CLAUDE.md
# (language-first rule, sA/sD/s9 gates, version stamp, +60 line budget).
# Exit 0 = pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$assert = Join-Path $repo ".sdad\eval\lib\assert-claude-md.ps1"
$claudeMd = Join-Path $repo "CLAUDE.md"

$ErrorActionPreference = "Continue"
$out = & powershell -NoProfile -ExecutionPolicy Bypass -File $assert -Path $claudeMd 2>&1
$code = $LASTEXITCODE
$ErrorActionPreference = "Stop"

if ($code -eq 0) { Write-Host "PASS 08-claude-md-structural"; exit 0 }
foreach ($line in @($out)) { Write-Host "  | $line" }
Write-Host "FAIL 08-claude-md-structural (exit $code)"
exit 1
