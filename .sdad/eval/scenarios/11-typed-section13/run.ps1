# Eval scenario 11 -- typed s13 AI Authorship Log schema (I5 / SPEC R5, s4).
# Asserts the repo SPEC.md s13 table carries the 8-column schema in order and
# that every data row has 8 cells. Locks the structured form so a future free-
# form edit regresses visibly. Exit 0 = pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$spec = Join-Path $repo "SPEC.md"
$cols = @('Increment', 'Feature', 'Model', 'Effort', 'Files', 'Tests', 'QA findings', 'Date')

$lines = Get-Content $spec -Encoding UTF8
$S = [char]0x00A7

# Find the s13 heading, then the first markdown table header below it.
$start = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match ([regex]::Escape("$($S)13") + '.*AI Authorship Log')) { $start = $i; break }
}
if ($start -lt 0) { Write-Host "FAIL 11-typed-section13 (s13 heading not found)"; exit 1 }

$headerIdx = -1
for ($i = $start + 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*\|.*\|\s*$') { $headerIdx = $i; break }
}
if ($headerIdx -lt 0) { Write-Host "FAIL 11-typed-section13 (no table under s13)"; exit 1 }

function Split-Row($row) {
    $t = $row.Trim() -replace '^\|', '' -replace '\|$', ''
    return ($t -split '\|' | ForEach-Object { $_.Trim() })
}

$fails = @()
$headerCells = Split-Row $lines[$headerIdx]
if ($headerCells.Count -ne 8) { $fails += "header has $($headerCells.Count) columns (expected 8)" }
for ($c = 0; $c -lt $cols.Count -and $c -lt $headerCells.Count; $c++) {
    if ($headerCells[$c] -notmatch [regex]::Escape($cols[$c])) {
        $fails += "column $c is '$($headerCells[$c])' (expected '$($cols[$c])')"
    }
}

# Data rows: skip the separator (|---|---|) line; each must have 8 cells.
$dataRows = 0
for ($i = $headerIdx + 2; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -notmatch '^\s*\|.*\|\s*$') { break }
    $cells = Split-Row $lines[$i]
    if ($cells.Count -ne 8) { $fails += "data row $($i+1) has $($cells.Count) cells (expected 8)" }
    $dataRows++
}
if ($dataRows -lt 1) { $fails += "no data rows found under s13" }

if ($fails.Count -eq 0) { Write-Host "PASS 11-typed-section13"; exit 0 }
foreach ($f in $fails) { Write-Host "  | $f" }
Write-Host "FAIL 11-typed-section13 ($($fails.Count) issues)"; exit 1
