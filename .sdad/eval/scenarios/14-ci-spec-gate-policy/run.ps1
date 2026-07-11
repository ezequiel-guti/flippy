# Eval scenario 14 -- shared spec-gate policy: deny/allow on both engines.
# Proves the single-source-of-truth module (checks/spec-gate-policy.*), consumed
# by the local hook and the CI gate, agrees across cases. Exit 0 = pass, 1 = fail.
# Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$polPs = Join-Path $repo "checks\spec-gate-policy.ps1"
$polSh = Join-Path $repo "checks\spec-gate-policy.sh"

$tmp = Join-Path $env:TEMP "sdad-eval-14-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

function Check-Exit($label, $expected, $actual, [ref]$fails) {
    if ($actual -ne $expected) {
        Write-Host "  ${label}: exit $actual (expected $expected)"
        $fails.Value++
    }
}

try {
    $fails = 0
    $code = $tmp -replace '\\', '/'
    $app = "$code/app.py"
    $specFile = Join-Path $tmp "SPEC.md"

    $ErrorActionPreference = "Continue"

    # PowerShell engine -------------------------------------------------------
    & powershell -NoProfile -ExecutionPolicy Bypass -File $polPs -Path $app -ProjectDir $tmp 2>$null
    Check-Exit "ps no-spec" 2 $LASTEXITCODE ([ref]$fails)

    Set-Content -Path $specFile -Value "# draft, no marker" -Encoding UTF8
    & powershell -NoProfile -ExecutionPolicy Bypass -File $polPs -Path $app -ProjectDir $tmp 2>$null
    Check-Exit "ps not-approved" 2 $LASTEXITCODE ([ref]$fails)

    Set-Content -Path $specFile -Value "SPEC STATUS: APPROVED" -Encoding UTF8
    & powershell -NoProfile -ExecutionPolicy Bypass -File $polPs -Path $app -ProjectDir $tmp 2>$null
    Check-Exit "ps approved" 0 $LASTEXITCODE ([ref]$fails)

    Remove-Item $specFile -Force
    & powershell -NoProfile -ExecutionPolicy Bypass -File $polPs -Path "$code/docs/extra.md" -ProjectDir $tmp 2>$null
    Check-Exit "ps docs-allow" 0 $LASTEXITCODE ([ref]$fails)

    # POSIX engine (if sh available) -----------------------------------------
    if (Get-Command sh -ErrorAction SilentlyContinue) {
        $polShU = $polSh -replace '\\', '/'
        & sh $polShU $app $code 2>$null
        Check-Exit "sh no-spec" 2 $LASTEXITCODE ([ref]$fails)

        Set-Content -Path $specFile -Value "SPEC STATUS: APPROVED" -Encoding UTF8
        & sh $polShU $app $code 2>$null
        Check-Exit "sh approved" 0 $LASTEXITCODE ([ref]$fails)
    } else {
        Write-Host "  NOTE sh not available -- sh engine subcases skipped"
    }

    $ErrorActionPreference = "Stop"

    if ($fails -eq 0) { Write-Host "PASS 14-ci-spec-gate-policy"; exit 0 }
    Write-Host "FAIL 14-ci-spec-gate-policy ($fails subcases)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
