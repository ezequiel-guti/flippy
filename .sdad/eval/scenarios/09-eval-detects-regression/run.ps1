# Eval scenario 09 -- self-test (SPEC s8): plant a methodology regression by
# stripping the language-first rule from a CLAUDE.md copy; the structural
# assert MUST catch it (exit 1 naming the rule). A green result here proves
# $eval can actually detect regressions, not just rubber-stamp.
# Exit 0 = pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$assert = Join-Path $repo ".sdad\eval\lib\assert-claude-md.ps1"

$tmp = Join-Path $env:TEMP "sdad-eval-09-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    # Planted regression: drop every line carrying the language-first anchor.
    $copy = Join-Path $tmp "CLAUDE.md"
    Get-Content (Join-Path $repo "CLAUDE.md") -Encoding UTF8 |
        Where-Object { $_ -notmatch 'FIRST question' } |
        Set-Content -Path $copy -Encoding UTF8

    # -SkipBudget: the temp copy lives outside the repo, no v4.3 tag there.
    $ErrorActionPreference = "Continue"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $assert -Path $copy -SkipBudget 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = "Stop"

    $named = (@($out) -join "`n") -match 'language-first'
    if ($code -eq 1 -and $named) { Write-Host "PASS 09-eval-detects-regression"; exit 0 }
    foreach ($line in @($out)) { Write-Host "  | $line" }
    Write-Host "FAIL 09-eval-detects-regression (exit $code, named=$named; expected 1 + 'language-first')"
    exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
