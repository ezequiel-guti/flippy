# SDAD $eval -- deterministic runner (v5 I3, SPEC F3.1).
# Runs every scenario under .sdad/eval/scenarios/NN-name/run.ps1 and reports
# one line per scenario: PASS/FAIL + name. Exit 0 only when all pass.
#
#   powershell -ExecutionPolicy Bypass -File .sdad\eval\run-eval.ps1            # core
#   powershell -ExecutionPolicy Bypass -File .sdad\eval\run-eval.ps1 -Release   # + LLM smoke
#
# Gate cadence (R8): core on any CLAUDE.md/skill change; -Release before tagging.
# On all-pass the runner stamps .sdad/eval/last-run with the git blob hash of
# CLAUDE.md -- the SessionStart hook compares it to decide the $eval reminder (OD-2).
# Pure ASCII (L-01).
param(
    [switch]$Release
)
$ErrorActionPreference = "Stop"
$evalRoot = $PSScriptRoot
$repo = (Resolve-Path "$evalRoot\..\..").Path

$dirs = @(Get-ChildItem -Path (Join-Path $evalRoot "scenarios") -Directory | Sort-Object Name)
if ($dirs.Count -eq 0) {
    Write-Host "FAIL eval: no scenarios found under .sdad/eval/scenarios/"
    exit 1
}

$passed = 0
$failed = 0
Write-Host "=== SDAD eval -- deterministic core ($($dirs.Count) scenarios) ==="
foreach ($d in $dirs) {
    $script = Join-Path $d.FullName "run.ps1"
    if (-not (Test-Path $script)) {
        Write-Host "FAIL $($d.Name) (no run.ps1)"
        $failed++
        continue
    }
    # PS 5.1 + EAP Stop turns child stderr into a terminating error (L-03);
    # relax EAP around the native call and judge by exit code only.
    $ErrorActionPreference = "Continue"
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $script 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    if ($code -eq 0) {
        Write-Host "PASS $($d.Name)"
        $passed++
    } else {
        Write-Host "FAIL $($d.Name) (exit $code)"
        foreach ($line in @($out)) { Write-Host "  | $line" }
        $failed++
    }
}
Write-Host "=== core: $passed passed, $failed failed ==="

$smokeFailed = 0
if ($Release) {
    $smoke = Join-Path $evalRoot "llm-smoke.ps1"
    Write-Host ""
    Write-Host "=== SDAD eval -- LLM replay smoke (release gate) ==="
    $ErrorActionPreference = "Continue"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $smoke
    if ($LASTEXITCODE -ne 0) { $smokeFailed = 1 }
    $ErrorActionPreference = "Stop"
}

if ($failed -eq 0 -and $smokeFailed -eq 0) {
    # Stamp the CLAUDE.md state this green run covered (consumed by OD-2 reminder).
    try {
        Push-Location $repo
        $hash = git hash-object CLAUDE.md 2>$null
        if ($LASTEXITCODE -eq 0 -and $hash) {
            Set-Content -Path (Join-Path $evalRoot "last-run") -Value $hash -Encoding ASCII
        }
        Pop-Location
    } catch { try { Pop-Location } catch {} }
    Write-Host ""
    Write-Host "EVAL PASS"
    exit 0
}
Write-Host ""
Write-Host "EVAL FAIL"
exit 1
