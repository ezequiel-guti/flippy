# SDAD v6 -- I4 circular-deps ratchet: detect a dependency cycle in a
# node-graph.json (each node's `dependencies` lists the node ids it reads).
# Deterministic (BR-04); the LLM auditor consumes the finding as pre-computed
# evidence and does not re-detect it.
# Mirror: checks/circular-deps.sh (python3 if available, else NOTE-skip).
# Usage:
#   powershell -File checks/circular-deps.ps1 path\to\node-graph.json
# Exit 0 = no cycle, 1 = a cycle was found or check error (fails closed).
param([string]$File)
$ErrorActionPreference = "Stop"

function Has($obj, $name) {
    if ($null -eq $obj) { return $false }
    return ($obj.PSObject.Properties.Name -contains $name)
}

try {
    if (-not $File) { Write-Host "circular-deps: no file argument"; exit 1 }
    if (-not (Test-Path $File)) { Write-Host "circular-deps: file not found: $File"; exit 1 }
    $raw = Get-Content -Path $File -Raw
    try { $j = $raw | ConvertFrom-Json }
    catch { Write-Host "circular-deps: invalid JSON: $($_.Exception.Message)"; exit 1 }

    $nodeList = @()
    if ((Has $j 'nodes') -and ($null -ne $j.nodes) -and ($j.nodes -isnot [string])) {
        $nodeList = @($j.nodes)
    }

    # Build adjacency: id -> [dependency ids]
    $adj = @{}
    foreach ($n in $nodeList) {
        if (-not (Has $n 'id')) { continue }
        $id = [string]$n.id
        $deps = @()
        if ((Has $n 'dependencies') -and ($null -ne $n.dependencies) -and ($n.dependencies -isnot [string])) {
            $deps = @($n.dependencies | ForEach-Object { [string]$_ })
        }
        $adj[$id] = $deps
    }

    # Iterative DFS with WHITE/GRAY/BLACK coloring; record the back-edge cycle.
    $color = @{}                       # 0 = unvisited, 1 = in-stack, 2 = done
    foreach ($k in $adj.Keys) { $color[$k] = 0 }
    $cyclePath = $null

    function Visit($node, $adj, $color, $stack) {
        $color[$node] = 1
        $stack.Add($node) | Out-Null
        foreach ($dep in $adj[$node]) {
            if (-not $adj.ContainsKey($dep)) { continue }   # dep not a known node -> external/leaf
            if ($color[$dep] -eq 1) {
                # back-edge: cycle from $dep down the current stack to $node
                $idx = $stack.IndexOf($dep)
                $cyc = @($stack.GetRange($idx, $stack.Count - $idx)) + @($dep)
                return ($cyc -join ' -> ')
            }
            if ($color[$dep] -eq 0) {
                $r = Visit $dep $adj $color $stack
                if ($r) { return $r }
            }
        }
        $color[$node] = 2
        $stack.RemoveAt($stack.Count - 1) | Out-Null
        return $null
    }

    foreach ($start in $adj.Keys) {
        if ($color[$start] -eq 0) {
            $stack = New-Object System.Collections.Generic.List[string]
            $r = Visit $start $adj $color $stack
            if ($r) { $cyclePath = $r; break }
        }
    }

    if ($cyclePath) {
        Write-Host "circular-deps: cycle detected in $File"
        Write-Host "  - $cyclePath"
        exit 1
    }
    Write-Host "circular-deps: OK ($File)"
    exit 0
}
catch {
    Write-Host "circular-deps: check error: $($_.Exception.Message)"
    exit 1
}
