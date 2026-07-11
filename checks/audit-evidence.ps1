# SDAD v6 -- I1 audit-evidence ratchet: validate a node-graph.json against the
# evidence schema (.sdad/audit/SCHEMA.md). Deterministic (BR-04); the LLM auditor
# consumes valid evidence, it does not re-validate structure. ASCII (L-01).
# Mirror: checks/audit-evidence.sh (python3 if available, else NOTE-skip).
# Usage:
#   powershell -File checks/audit-evidence.ps1 path\to\node-graph.json
# Exit 0 = valid, 1 = invalid or check error (fails closed, like ascii-ps1).
param([string]$File)
$ErrorActionPreference = "Stop"

function Has($obj, $name) {
    if ($null -eq $obj) { return $false }
    return ($obj.PSObject.Properties.Name -contains $name)
}

try {
    if (-not $File) { Write-Host "audit-evidence: no file argument"; exit 1 }
    if (-not (Test-Path $File)) { Write-Host "audit-evidence: file not found: $File"; exit 1 }
    $raw = Get-Content -Path $File -Raw
    try { $j = $raw | ConvertFrom-Json }
    catch { Write-Host "audit-evidence: invalid JSON: $($_.Exception.Message)"; exit 1 }

    $errors = New-Object System.Collections.ArrayList

    foreach ($k in @('project','acquired_at','acquisition_path','pyplan_version','nodes','gaps')) {
        if (-not (Has $j $k)) { [void]$errors.Add("missing top-level key: $k") }
    }

    $paths = @('ppl-export','mcp-read','manual')
    if ((Has $j 'acquisition_path') -and ($paths -notcontains $j.acquisition_path)) {
        [void]$errors.Add("acquisition_path not one of ppl-export|mcp-read|manual: $($j.acquisition_path)")
    }

    $types = @('data','function','interface','input')
    $nodeList = @()
    if ((Has $j 'nodes') -and ($null -ne $j.nodes) -and ($j.nodes -isnot [string])) {
        $nodeList = @($j.nodes)
    } elseif ((Has $j 'nodes') -and ($j.nodes -is [string]) -and ($j.nodes -ne '')) {
        [void]$errors.Add("nodes is a string, expected an array")
    }
    $i = 0
    foreach ($n in $nodeList) {
        foreach ($k in @('id','type','has_result_assigned','dependencies','code_snippet','mcp_decorated')) {
            if (-not (Has $n $k)) { [void]$errors.Add("node[$i] missing key: $k") }
        }
        if ((Has $n 'type') -and ($types -notcontains $n.type)) {
            [void]$errors.Add("node[$i] type not one of data|function|interface|input: $($n.type)")
        }
        if ((Has $n 'has_result_assigned') -and ($n.has_result_assigned -isnot [bool])) {
            [void]$errors.Add("node[$i] has_result_assigned not boolean")
        }
        if ((Has $n 'id') -and [string]::IsNullOrWhiteSpace([string]$n.id)) {
            [void]$errors.Add("node[$i] id empty")
        }
        $i++
    }

    $gapList = @()
    if ((Has $j 'gaps') -and ($null -ne $j.gaps) -and ($j.gaps -isnot [string])) {
        $gapList = @($j.gaps)
    }
    $g = 0
    foreach ($gap in $gapList) {
        foreach ($k in @('area','reason','status')) {
            if (-not (Has $gap $k)) { [void]$errors.Add("gap[$g] missing key: $k") }
        }
        if ((Has $gap 'status') -and ($gap.status -ne 'not_assessable')) {
            [void]$errors.Add("gap[$g] status not 'not_assessable': $($gap.status)")
        }
        $g++
    }

    if ($errors.Count -gt 0) {
        Write-Host "audit-evidence: $($errors.Count) violation(s) in $File"
        foreach ($e in $errors) { Write-Host "  - $e" }
        exit 1
    }
    Write-Host "audit-evidence: OK ($File)"
    exit 0
}
catch {
    Write-Host "audit-evidence: check error: $($_.Exception.Message)"
    exit 1
}
