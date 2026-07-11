# Eval scenario 16 -- I2 MCP tool audit: a clean @mcp_tool node yields 0 findings,
# a node with planted defects is detected at the right severities (CRITICAL for a
# called result, HIGH for an untyped param and a non-serializable return). If
# python is unavailable the check skips (NOTE) and the scenario passes-with-note.
# Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$check = Join-Path $repo "checks\mcp-tool-audit.ps1"
$clean = Join-Path $repo ".sdad\audit\_fixtures\mcp_clean.py"
$defects = Join-Path $repo ".sdad\audit\_fixtures\mcp_defects.py"

$fails = 0

# Clean fixture: detect the python-skip case and pass-with-note.
$cleanOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $check $clean 2>&1
$cleanCode = $LASTEXITCODE
if (@($cleanOut) -match 'NOTE python not available') {
    Write-Host "PASS 16-mcp-tool-audit (python unavailable -- lint skipped)"
    exit 0
}
if ($cleanCode -ne 0) { Write-Host "  clean fixture: exit $cleanCode (expected 0)"; $fails++ }

# Defective fixture: must fail and report the planted severities.
$defOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $check $defects 2>&1
$defCode = $LASTEXITCODE
if ($defCode -ne 1) { Write-Host "  defects fixture: exit $defCode (expected 1)"; $fails++ }
$joined = (@($defOut) -join "`n")
if ($joined -notmatch 'CRITICAL\].*result-called') { Write-Host "  missing CRITICAL result-called finding"; $fails++ }
if ($joined -notmatch 'HIGH\].*untyped-param') { Write-Host "  missing HIGH untyped-param finding"; $fails++ }
if ($joined -notmatch 'HIGH\].*non-serializable-return') { Write-Host "  missing HIGH non-serializable-return finding"; $fails++ }

if ($fails -eq 0) { Write-Host "PASS 16-mcp-tool-audit"; exit 0 }
Write-Host "FAIL 16-mcp-tool-audit ($fails subcases)"; exit 1
