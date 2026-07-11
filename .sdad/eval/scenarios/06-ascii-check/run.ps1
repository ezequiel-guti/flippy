# Eval scenario 06 -- L-01 ratchet check: dirty .ps1 fails, clean .ps1 passes,
# on BOTH engines (ps1 and sh mirror). Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$checkPs = Join-Path $repo "checks\ascii-ps1.ps1"
$checkSh = Join-Path $repo "checks\ascii-ps1.sh"

$tmp = Join-Path $env:TEMP "sdad-eval-06-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    # dirty fixture: 'x = 1 <em-dash> comment' with UTF-8 em dash bytes E2 80 94
    $dirty = Join-Path $tmp "dirty.ps1"
    $bytes = [byte[]](36, 120, 32, 61, 32, 49, 32, 35, 32, 226, 128, 148, 32, 99)
    [System.IO.File]::WriteAllBytes($dirty, $bytes)
    $clean = Join-Path $tmp "clean.ps1"
    Set-Content -Path $clean -Value '$x = 1 # plain ascii' -Encoding ASCII

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

    # .sh subcases: the check must flag a non-ASCII .sh and pass a clean one.
    # Guards the v5.2 scope extension (.ps1 + .sh) against silent reversion.
    $dirtySh = Join-Path $tmp "dirty.sh"
    [System.IO.File]::WriteAllBytes($dirtySh, [byte[]](35, 33, 32, 226, 128, 148))  # '#! <em-dash>'
    $cleanSh = Join-Path $tmp "clean.sh"
    Set-Content -Path $cleanSh -Value '#!/bin/sh' -Encoding ASCII
    & powershell -NoProfile -ExecutionPolicy Bypass -File $checkPs $dirtySh | Out-Null
    if ($LASTEXITCODE -ne 1) { Write-Host "  ps1 engine dirty .sh: exit $LASTEXITCODE (expected 1)"; $fails++ }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $checkPs $cleanSh | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "  ps1 engine clean .sh: exit $LASTEXITCODE (expected 0)"; $fails++ }

    # default-scan coverage: a tracked dirty .sh must make the no-arg scan fail
    # (proves the git ls-files glob now includes *.sh, not only *.ps1).
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $gitTmp = Join-Path $tmp "gitrepo"
        New-Item -ItemType Directory -Path $gitTmp -Force | Out-Null
        [System.IO.File]::WriteAllBytes((Join-Path $gitTmp "d.sh"), [byte[]](35, 33, 32, 226, 128, 148))
        Push-Location $gitTmp
        git init --quiet 2>$null
        git add d.sh 2>$null
        & powershell -NoProfile -ExecutionPolicy Bypass -File $checkPs | Out-Null
        if ($LASTEXITCODE -ne 1) { Write-Host "  default-scan tracked dirty .sh: exit $LASTEXITCODE (expected 1)"; $fails++ }
        Pop-Location
    } else {
        Write-Host "  NOTE git not available -- default-scan .sh subcase skipped"
    }

    if ($fails -eq 0) { Write-Host "PASS 06-ascii-check"; exit 0 }
    Write-Host "FAIL 06-ascii-check ($fails subcases)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
