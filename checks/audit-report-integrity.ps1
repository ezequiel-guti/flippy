# SDAD v6 -- I7 audit-report-integrity ratchet: catch a deliberately weakened
# audit report. Deterministic meta-check over a (report.md + manifest.md) pair.
# It does NOT judge audit quality (that is the LLM auditor's job); it enforces the
# integrity invariants that a weakened/dishonest report would violate:
#   A. Reproducibility stamp (BR-13): the report must carry an SDAD version stamp
#      AND an exact model string. An audit is a point-in-time judgment; without the
#      stamp it is not reproducible/traceable.
#   B. No fabricated alignment finding (BR-09): when the manifest declares no owner
#      elicitation ("Elicitation: none"), the report's business-alignment (5a)
#      verdict MUST be "not assessable". A banded 5a finding (CRITICAL/HIGH/MEDIUM/
#      LOW) with no elicitation is a fabrication.
#   C. Evidence-gap surfacing: every gap area the manifest declares not_assessable
#      must appear in the report (gaps are findings, never silent omissions).
#
# Minimal report contract this check relies on (full template -> I8):
#   - somewhere a stamp line containing "SDAD v<n>" and a "claude-<model>" string
#   - a line "Business alignment (5a): <verdict>"
#   - each manifest gap area mentioned somewhere in the report text
#
# Mirror: checks/audit-report-integrity.sh (pure POSIX, no python needed).
# Usage: powershell -File checks/audit-report-integrity.ps1 -Dir path\to\report-dir
#   (the directory must contain report.md and manifest.md)
# Exit 0 = integrity intact, 1 = at least one violation or check error (fails
# closed, like the other checks). L-01: pure ASCII.
param([string]$Dir)
$ErrorActionPreference = "Stop"

try {
    if (-not $Dir) { Write-Host "audit-report-integrity: no -Dir argument"; exit 1 }
    $report = Join-Path $Dir "report.md"
    $manifest = Join-Path $Dir "manifest.md"
    if (-not (Test-Path $report)) { Write-Host "audit-report-integrity: report.md not found in $Dir"; exit 1 }
    if (-not (Test-Path $manifest)) { Write-Host "audit-report-integrity: manifest.md not found in $Dir"; exit 1 }

    $r = (Get-Content $report -Raw -Encoding UTF8) | Out-String
    $m = (Get-Content $manifest -Raw -Encoding UTF8) | Out-String
    $violations = New-Object System.Collections.ArrayList

    # Rule A -- reproducibility stamp (BR-13)
    if ($r -notmatch '(?i)SDAD v\d') {
        [void]$violations.Add("A: missing SDAD version stamp (BR-13 reproducibility)")
    }
    if ($r -notmatch '(?i)claude-[a-z0-9.\-]+') {
        [void]$violations.Add("A: missing exact model string (BR-13 reproducibility)")
    }

    # Rule B -- no fabricated alignment finding when elicitation is absent (BR-09)
    # Tolerate markdown around the field ("**Elicitation:** none"): any run of
    # non-alphanumerics may sit between the field name and the value.
    $elicitationNone = ($m -match '(?im)Elicitation[^A-Za-z0-9]*none') -or `
                       ($m -match '(?im)not.?assessable[^\n]*elicitation')
    if ($elicitationNone) {
        $line = $null
        foreach ($l in ($r -split "`n")) {
            if ($l -match '(?i)business alignment \(5a\):') { $line = $l; break }
        }
        if ($null -eq $line) {
            [void]$violations.Add("B: business-alignment (5a) verdict line missing")
        } elseif ($line -match '(?i)not assessable') {
            # honest: explicitly declared not assessable -- OK
        } elseif ($line -match '(?i)\b(CRITICAL|HIGH|MEDIUM|LOW)\b') {
            [void]$violations.Add("B: fabricated 5a finding with no elicitation input (BR-09)")
        } else {
            [void]$violations.Add("B: 5a verdict not declared not-assessable despite no elicitation")
        }
    }

    # Rule C -- every not_assessable gap area must be surfaced in the report
    $gapMatches = [regex]::Matches($m, '(?im)^\|\s*([A-Za-z0-9_\-]+)\s*\|.*not_assessable')
    foreach ($gm in $gapMatches) {
        $area = $gm.Groups[1].Value.Trim()
        if ($area -and ($r -notmatch [regex]::Escape($area))) {
            [void]$violations.Add("C: gap area '$area' declared in manifest but not surfaced in report")
        }
    }

    if ($violations.Count -gt 0) {
        Write-Host "audit-report-integrity: $($violations.Count) violation(s) in $Dir"
        foreach ($v in $violations) { Write-Host "  - $v" }
        exit 1
    }
    Write-Host "audit-report-integrity: OK ($Dir)"
    exit 0
}
catch {
    Write-Host "audit-report-integrity: check error: $($_.Exception.Message)"
    exit 1
}
