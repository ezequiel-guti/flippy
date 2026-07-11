# SDAD v6 -- I2 MCP tool audit check (wrapper over .sdad/audit/lib/mcp_lint.py).
# Audits @mcp_tool nodes in a Python file against the pyplan-mcp skill rules and
# reports findings tagged with BR-03 severities. ASCII (L-01).
# Mirror: checks/mcp-tool-audit.sh
# Requires python; if absent, NOTE-skips with exit 0 (Pyplan is Python, so python
# is expected on a Pyplan dev/audit machine; CI without python skips gracefully).
# Usage:
#   powershell -File checks/mcp-tool-audit.ps1 path\to\node.py
# Exit 0 = clean (or skipped), 1 = findings present or tool error.
param([string]$File)
$ErrorActionPreference = "Stop"
try {
    if (-not $File) { Write-Host "mcp-tool-audit: no file argument"; exit 1 }
    if (-not (Test-Path $File)) { Write-Host "mcp-tool-audit: file not found: $File"; exit 1 }

    $py = $null
    foreach ($cand in @('python', 'python3')) {
        $c = Get-Command $cand -ErrorAction SilentlyContinue
        if ($c) { $py = $c.Source; break }
    }
    if (-not $py) {
        Write-Host "mcp-tool-audit: NOTE python not available -- MCP lint skipped"
        exit 0
    }

    $lint = Join-Path $PSScriptRoot "..\.sdad\audit\lib\mcp_lint.py"
    & $py $lint $File
    exit $LASTEXITCODE
}
catch {
    Write-Host "mcp-tool-audit: check error: $($_.Exception.Message)"
    exit 1
}
