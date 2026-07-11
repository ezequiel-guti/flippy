# Eval scenario 22 -- I8 severity determinism: two fixtures with equivalent findings
# but different wording must (a) both pass audit-report-integrity and (b) produce the
# same severity classification fingerprint (identical band counts + 5a verdict).
# This is the I8 SPEC-S8 gate: "equivalent findings -> identical classification."
# Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$check = Join-Path $repo "checks\audit-report-integrity.ps1"
$dirA = Join-Path $repo ".sdad\audit\_fixtures\equiv-A"
$dirB = Join-Path $repo ".sdad\audit\_fixtures\equiv-B"

$fails = 0

# Part 1 -- both reports must pass the integrity check (exit 0)
$ErrorActionPreference = "Continue"
& powershell -NoProfile -ExecutionPolicy Bypass -File $check -Dir $dirA 2>&1 | Out-Null
$codeA = $LASTEXITCODE
& powershell -NoProfile -ExecutionPolicy Bypass -File $check -Dir $dirB 2>&1 | Out-Null
$codeB = $LASTEXITCODE
$ErrorActionPreference = "Stop"

if ($codeA -ne 0) { Write-Host "  equiv-A integrity: exit $codeA (expected 0)"; $fails++ }
if ($codeB -ne 0) { Write-Host "  equiv-B integrity: exit $codeB (expected 0)"; $fails++ }

# Part 2 -- severity classification fingerprint must be identical
# Fingerprint = "5a:<verdict> CRITICAL:<n> HIGH:<n> MEDIUM:<n> LOW:<n>"
# Extracted from the Improvement Backlog section (band prefix on each backlog line).
function Get-Fingerprint([string]$dir) {
    $report = Get-Content (Join-Path $dir "report.md") -Encoding UTF8

    # Extract 5a verdict (the exact line "Business alignment (5a): <verdict>")
    $verdict5a = "missing"
    foreach ($line in $report) {
        if ($line -match '(?i)Business alignment \(5a\):\s*(.+)') {
            $verdict5a = ($Matches[1].Trim() -replace '\s+', ' ').ToLower()
            break
        }
    }

    # Count band labels in the Improvement Backlog section only.
    # Find the backlog section and count lines that start with a band keyword.
    $inBacklog = $false
    $counts = @{ CRITICAL = 0; HIGH = 0; MEDIUM = 0; LOW = 0 }
    foreach ($line in $report) {
        if ($line -match '##\s+Improvement Backlog') { $inBacklog = $true; continue }
        if ($inBacklog -and $line -match '^##') { $inBacklog = $false; continue }
        if ($inBacklog -and $line -match '^(CRITICAL|HIGH|MEDIUM|LOW)\s*\.') {
            $band = $Matches[1]
            $counts[$band]++
        }
    }

    return "5a:$verdict5a CRITICAL:$($counts.CRITICAL) HIGH:$($counts.HIGH) MEDIUM:$($counts.MEDIUM) LOW:$($counts.LOW)"
}

$fpA = Get-Fingerprint $dirA
$fpB = Get-Fingerprint $dirB

if ($fpA -ne $fpB) {
    Write-Host "  severity fingerprint mismatch:"
    Write-Host "    equiv-A: $fpA"
    Write-Host "    equiv-B: $fpB"
    $fails++
}

if ($fails -eq 0) { Write-Host "PASS 22-severity-determinism"; exit 0 }
Write-Host "FAIL 22-severity-determinism ($fails subcases)"; exit 1
