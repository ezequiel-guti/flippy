# Eval scenario 10 -- $agent liveness wrapper (I4 / SPEC F5):
#   (a) a hung delegation hits the timeout and exits 2 (not silently)
#   (b) a delegation that produces no output exits 1
# The stand-in is injected via SDAD_AGENT_EXE -- a self-contained script that
# ignores the wrapper's `--print <prompt>` args. Checked on the ps1 engine; the
# sh mirror runs when sh is present. Exit 0 = pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$wrapPs = Join-Path $repo ".sdad\lib\agent-run.ps1"
$wrapSh = Join-Path $repo ".sdad\lib\agent-run.sh"

$tmp = Join-Path $env:TEMP "sdad-eval-10-$PID"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    $fails = 0
    $out = Join-Path $tmp "out.txt"

    # Windows stand-ins: a hanging one (~30s) and an instant silent one.
    $sleeper = Join-Path $tmp "sleeper.bat"
    Set-Content -Path $sleeper -Value '@ping -n 31 127.0.0.1 >nul' -Encoding ASCII
    $empty = Join-Path $tmp "empty.bat"
    Set-Content -Path $empty -Value '@exit /b 0' -Encoding ASCII

    # (a) ps1 timeout: stand-in hangs, timeout 2s -> expect exit 2.
    $env:SDAD_AGENT_EXE = $sleeper
    & powershell -NoProfile -ExecutionPolicy Bypass -File $wrapPs -Prompt "x" -OutFile $out -TimeoutSec 2 | Out-Null
    if ($LASTEXITCODE -ne 2) { Write-Host "  ps1 timeout: exit $LASTEXITCODE (expected 2)"; $fails++ }

    # (b) ps1 empty output: stand-in exits at once writing nothing -> expect exit 1.
    $env:SDAD_AGENT_EXE = $empty
    & powershell -NoProfile -ExecutionPolicy Bypass -File $wrapPs -Prompt "x" -OutFile $out -TimeoutSec 10 | Out-Null
    if ($LASTEXITCODE -ne 1) { Write-Host "  ps1 empty: exit $LASTEXITCODE (expected 1)"; $fails++ }
    Remove-Item Env:SDAD_AGENT_EXE -ErrorAction SilentlyContinue

    if (Get-Command sh -ErrorAction SilentlyContinue) {
        $sleeperSh = Join-Path $tmp "sleeper.sh"
        Set-Content -Path $sleeperSh -Value "#!/bin/sh`nsleep 30" -Encoding ASCII
        $emptySh = Join-Path $tmp "empty.sh"
        Set-Content -Path $emptySh -Value "#!/bin/sh`nexit 0" -Encoding ASCII
        $wrapShU = $wrapSh -replace '\\', '/'
        $outU = $out -replace '\\', '/'

        # (a) sh timeout -> expect exit 2.
        $env:SDAD_AGENT_EXE = ($sleeperSh -replace '\\', '/')
        & sh $wrapShU "x" $outU 2 | Out-Null
        if ($LASTEXITCODE -ne 2) { Write-Host "  sh timeout: exit $LASTEXITCODE (expected 2)"; $fails++ }
        # (b) sh empty -> expect exit 1.
        $env:SDAD_AGENT_EXE = ($emptySh -replace '\\', '/')
        & sh $wrapShU "x" $outU 10 | Out-Null
        if ($LASTEXITCODE -ne 1) { Write-Host "  sh empty: exit $LASTEXITCODE (expected 1)"; $fails++ }
        Remove-Item Env:SDAD_AGENT_EXE -ErrorAction SilentlyContinue
    } else {
        Write-Host "  NOTE sh not available -- sh engine subcases skipped"
    }

    if ($fails -eq 0) { Write-Host "PASS 10-agent-timeout"; exit 0 }
    Write-Host "FAIL 10-agent-timeout ($fails subcases)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:SDAD_AGENT_EXE -ErrorAction SilentlyContinue
}
