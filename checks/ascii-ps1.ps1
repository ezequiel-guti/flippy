# SDAD v5 -- L-01 ratchet check: every .ps1 and .sh must be pure ASCII.
# Windows PowerShell 5.1 misreads non-ASCII and installers/init scripts break on
# fresh machines (L-01, extended to .sh in the v5.2 versioning patch).
# Mirror: checks/ascii-ps1.sh (POSIX contexts: git pre-commit, macOS hooks).
# Name kept as ascii-ps1 for hook/eval/install compatibility; scope is .ps1 + .sh.
# Usage:
#   powershell -File checks/ascii-ps1.ps1                  -> scan all git-tracked .ps1/.sh
#   powershell -File checks/ascii-ps1.ps1 f1.ps1 f2.sh     -> scan specific files
# Exit 0 = clean, 1 = violations or check error (commit-time guard fails CLOSED --
# the deliberate exception to the fail-open rule; see SPEC R3).
param([string[]]$Files)
$ErrorActionPreference = "Stop"
try {
    if (-not $Files -or $Files.Count -eq 0) {
        $Files = @(git ls-files -- '*.ps1' '*.sh' 2>$null)
    }
    $bad = 0
    foreach ($f in $Files) {
        if (-not (Test-Path $f)) { continue }
        $bytes = [System.IO.File]::ReadAllBytes($f)
        for ($i = 0; $i -lt $bytes.Length; $i++) {
            if ($bytes[$i] -gt 127) {
                Write-Host "ASCII VIOLATION: $f (first at byte offset $i, value $($bytes[$i]))"
                $bad++
                break
            }
        }
    }
    if ($bad -gt 0) {
        Write-Host "ascii-ps1: $bad file(s) violate L-01 (pure-ASCII .ps1/.sh)"
        exit 1
    }
    exit 0
}
catch {
    Write-Host "ascii-ps1: check error: $($_.Exception.Message)"
    exit 1
}
