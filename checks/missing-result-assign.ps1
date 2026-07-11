# SDAD v6 -- I4 missing-result-assign ratchet: flag calculation nodes (type
# data|function) in a node-graph.json that do not have result= assigned
# (has_result_assigned == false). Deterministic (BR-04); the LLM auditor consumes
# the finding as pre-computed evidence and does not re-detect it.
# Mirror: checks/missing-result-assign.sh (python3 if available, else NOTE-skip).
# Usage:
#   powershell -File checks/missing-result-assign.ps1 path\to\node-graph.json
# Exit 0 = no offending nodes, 1 = at least one offending node or check error
# (fails closed, like audit-evidence / mcp-tool-audit).
param([string]$File)
$ErrorActionPreference = "Stop"

function Has($obj, $name) {
    if ($null -eq $obj) { return $false }
    return ($obj.PSObject.Properties.Name -contains $name)
}

try {
    if (-not $File) { Write-Host "missing-result-assign: no file argument"; exit 1 }
    if (-not (Test-Path $File)) { Write-Host "missing-result-assign: file not found: $File"; exit 1 }
    $raw = Get-Content -Path $File -Raw
    try { $j = $raw | ConvertFrom-Json }
    catch { Write-Host "missing-result-assign: invalid JSON: $($_.Exception.Message)"; exit 1 }

    $nodeList = @()
    if ((Has $j 'nodes') -and ($null -ne $j.nodes) -and ($j.nodes -isnot [string])) {
        $nodeList = @($j.nodes)
    }

    $offenders = New-Object System.Collections.ArrayList
    foreach ($n in $nodeList) {
        $type = if (Has $n 'type') { [string]$n.type } else { '' }
        # Only calculation nodes must carry result=; interface/input nodes are exempt.
        if ($type -ne 'data' -and $type -ne 'function') { continue }
        $assigned = $false
        if (Has $n 'has_result_assigned') { $assigned = [bool]$n.has_result_assigned }
        if (-not $assigned) {
            $id = if (Has $n 'id') { [string]$n.id } else { '<no-id>' }
            [void]$offenders.Add("$id ($type)")
        }
    }

    if ($offenders.Count -gt 0) {
        Write-Host "missing-result-assign: $($offenders.Count) node(s) without result= in $File"
        foreach ($o in $offenders) { Write-Host "  - $o" }
        exit 1
    }
    Write-Host "missing-result-assign: OK ($File)"
    exit 0
}
catch {
    Write-Host "missing-result-assign: check error: $($_.Exception.Message)"
    exit 1
}
