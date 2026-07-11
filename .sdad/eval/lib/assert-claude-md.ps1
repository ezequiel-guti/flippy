# SDAD $eval -- structural asserts on a CLAUDE.md file (v5 I3, SPEC F3.3).
# Usage: assert-claude-md.ps1 <path-to-CLAUDE.md> [-SkipBudget]
# Exit 0 = all asserts pass, 1 = at least one failed (each failure printed).
# Shared by scenarios 08 (real CLAUDE.md) and 09 (planted regression).
# Pure ASCII (L-01): the section sign is built from its char code, never typed.
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [switch]$SkipBudget
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $Path)) {
    Write-Host "ASSERT FAIL: file not found: $Path"
    exit 1
}
$text = Get-Content $Path -Raw -Encoding UTF8
$S = [char]0x00A7   # section sign, kept out of this ASCII source

$failures = @()

# 1 -- language-first rule: $spec asks PROJECT_LANGUAGE before everything else.
if (-not ($text -match 'FIRST question' -and $text -match 'PROJECT_LANGUAGE')) {
    $failures += "language-first rule missing (FIRST question + PROJECT_LANGUAGE)"
}

# 2 -- Pyplan sA gate: build blocked until data architecture approved.
if (-not ($text -match [regex]::Escape("blocked if $($S)A is not marked as approved"))) {
    $failures += "sA gate rule missing"
}

# 3 -- Pyplan sD gate: build blocked while an MCP catalog is present and unapproved.
if (-not ($text -match [regex]::Escape("blocked if $($S)D is present and not marked as approved"))) {
    $failures += "sD gate rule missing"
}

# 4 -- Tier 3 s9 gate: build blocked until security section complete and approved.
if (-not ($text -match [regex]::Escape("blocked until SPEC.md $($S)9 is complete"))) {
    $failures += "s9 Tier 3 gate rule missing"
}

# 5 -- version stamp: header and footer carry the same SDAD vN.N.
$header = [regex]::Match($text, 'SDAD v(\d+\.\d+)')
$footer = [regex]::Match($text, 'SDAD v(\d+\.\d+)', 'RightToLeft')
if (-not $header.Success) {
    $failures += "version stamp missing (no 'SDAD vN.N' found)"
} elseif ($header.Groups[1].Value -ne $footer.Groups[1].Value) {
    $failures += "version stamp mismatch (header $($header.Groups[1].Value) vs footer $($footer.Groups[1].Value))"
}

# 6 -- line budget: current length <= previous-release baseline + 60 (R4 [LOCK]).
#      Uses the most recent git tag reachable from HEAD as the per-release baseline.
#      Skipped gracefully when no tag exists (downstream installs) or -SkipBudget.
if (-not $SkipBudget) {
    $baseline = $null
    try {
        Push-Location (Split-Path $Path -Parent)
        # Find the most recent release tag reachable from HEAD (dynamic baseline).
        $baseTag = git describe --tags --abbrev=0 2>$null
        if ($LASTEXITCODE -eq 0 -and $baseTag) {
            $leaf = Split-Path $Path -Leaf
            $tracked = @(git ls-tree -r --name-only $baseTag 2>$null) |
                Where-Object { (Split-Path $_ -Leaf) -ieq $leaf } | Select-Object -First 1
            if ($tracked) {
                $baseRaw = git show "${baseTag}:${tracked}" 2>$null
                if ($LASTEXITCODE -eq 0 -and $baseRaw) { $baseline = @($baseRaw).Count }
            }
        }
        Pop-Location
    } catch { try { Pop-Location } catch {} }
    if ($null -eq $baseline) {
        Write-Host "ASSERT NOTE: no release tag reachable -- line-budget assert skipped"
    } else {
        $current = @(Get-Content $Path -Encoding UTF8).Count
        $limit = $baseline + 60
        if ($current -gt $limit) {
            $failures += "line budget exceeded: $current lines vs limit $limit ($baseTag baseline $baseline + 60)"
        }
    }
}

if ($failures.Count -eq 0) { exit 0 }
foreach ($f in $failures) { Write-Host "ASSERT FAIL: $f" }
exit 1
