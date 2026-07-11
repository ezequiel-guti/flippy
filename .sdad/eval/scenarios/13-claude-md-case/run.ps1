# Eval scenario 13 -- L-04 ratchet: a code/config file referencing the wrong-case
# methodology filename fails; the correct all-caps form passes. Both engines
# (ps1 + sh mirror). Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$checkPs = Join-Path $repo "checks\claude-md-case.ps1"
$checkSh = Join-Path $repo "checks\claude-md-case.sh"

$tmp = Join-Path $env:TEMP "sdad-eval-13-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    # dirty fixture: an installer-style line with the wrong-case reference.
    $wrong = "Claude" + ".md"
    $right = "CLAUDE" + ".md"
    $dirty = Join-Path $tmp "dirty.ps1"
    Set-Content -Path $dirty -Value "Invoke-WebRequest `"`$REPO/$wrong`"" -Encoding ASCII
    $clean = Join-Path $tmp "clean.ps1"
    Set-Content -Path $clean -Value "Invoke-WebRequest `"`$REPO/$right`"" -Encoding ASCII

    $fails = 0
    & powershell -NoProfile -ExecutionPolicy Bypass -File $checkPs $dirty | Out-Null
    if ($LASTEXITCODE -ne 1) { Write-Host "  ps1 engine dirty: exit $LASTEXITCODE (expected 1)"; $fails++ }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $checkPs $clean | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "  ps1 engine clean: exit $LASTEXITCODE (expected 0)"; $fails++ }

    if (Get-Command sh -ErrorAction SilentlyContinue) {
        $dirtyU = $dirty -replace '\\', '/'
        $cleanU = $clean -replace '\\', '/'
        & sh $checkSh $dirtyU | Out-Null
        if ($LASTEXITCODE -ne 1) { Write-Host "  sh engine dirty: exit $LASTEXITCODE (expected 1)"; $fails++ }
        & sh $checkSh $cleanU | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "  sh engine clean: exit $LASTEXITCODE (expected 0)"; $fails++ }
    } else {
        Write-Host "  NOTE sh not available -- sh engine subcases skipped"
    }

    if ($fails -eq 0) { Write-Host "PASS 13-claude-md-case"; exit 0 }
    Write-Host "FAIL 13-claude-md-case ($fails subcases)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
