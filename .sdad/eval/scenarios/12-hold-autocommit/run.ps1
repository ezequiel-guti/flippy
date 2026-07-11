# Eval scenario 12 -- $build E-termination contract (I6 / SPEC F4):
# session-end autocommit MUST be suppressed while .sdad/HOLD_AUTOCOMMIT exists,
# and MUST resume once it is removed. Tests the staged session-end.ps1 against a
# temp git repo. Exit 0 = pass, 1 = fail. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$seSrc = Join-Path $repo "_staging_v5\hooks\session-end.ps1"
if (-not (Test-Path $seSrc)) { $seSrc = Join-Path $repo ".claude\hooks\session-end.ps1" }
$checkSrc = Join-Path $repo "checks\ascii-ps1.ps1"

$tmp = Join-Path $env:TEMP "sdad-eval-12-$PID"
New-Item -ItemType Directory -Path (Join-Path $tmp "checks") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tmp ".sdad") -Force | Out-Null
try {
    Copy-Item $checkSrc (Join-Path $tmp "checks\ascii-ps1.ps1")
    Set-Content -Path (Join-Path $tmp "DECISIONS.md") -Value "# decisions" -Encoding ASCII
    # L-03: native git stderr (e.g. CRLF warning) under EAP Stop terminates -- relax it.
    $ErrorActionPreference = "Continue"
    Push-Location $tmp
    git init --quiet 2>$null
    git config user.email "eval@sdad.local" 2>$null
    git config user.name "SDAD Eval" 2>$null
    git config core.autocrlf false 2>$null
    git add -A 2>$null
    git commit -m "seed" --quiet 2>$null
    Pop-Location

    $env:CLAUDE_PROJECT_DIR = $tmp
    function Count-Commits { Push-Location $tmp; $n = (git rev-list --count HEAD 2>$null); Pop-Location; return [int]$n }

    $before = Count-Commits

    # Case A: HOLD present + dirty whitelisted file -> no autocommit.
    Add-Content -Path (Join-Path $tmp "DECISIONS.md") -Value "change A" -Encoding ASCII
    New-Item -ItemType File -Path (Join-Path $tmp ".sdad\HOLD_AUTOCOMMIT") -Force | Out-Null
    '' | & powershell -NoProfile -ExecutionPolicy Bypass -File $seSrc | Out-Null
    $afterHold = Count-Commits
    $caseA = ($afterHold -eq $before)

    # Case B: HOLD removed, same dirty file -> autocommit resumes (one new commit).
    Remove-Item (Join-Path $tmp ".sdad\HOLD_AUTOCOMMIT") -Force
    '' | & powershell -NoProfile -ExecutionPolicy Bypass -File $seSrc | Out-Null
    $afterClear = Count-Commits
    $caseB = ($afterClear -eq $before + 1)

    $env:CLAUDE_PROJECT_DIR = ''
    if ($caseA -and $caseB) { Write-Host "PASS 12-hold-autocommit"; exit 0 }
    Write-Host "FAIL 12-hold-autocommit (HOLD-suppresses=$caseA expected True; resumes=$caseB expected True; commits $before->$afterHold->$afterClear)"; exit 1
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Env:CLAUDE_PROJECT_DIR -ErrorAction SilentlyContinue
}
