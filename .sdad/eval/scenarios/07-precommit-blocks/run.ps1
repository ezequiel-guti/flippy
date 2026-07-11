# Eval scenario 07 -- pre-commit ratchet blocks a commit staging a dirty .ps1
# in a temp git repo, and allows it once clean. Exit 0 = pass, 1 = fail. ASCII.
#
# Hermetic (H-02): the scenario CONSTRUCTS the pre-commit hook itself rather than
# copying an installed .git/hooks/pre-commit -- a clean CI runner has no installed
# hook. The constructed body mirrors the one install.ps1 writes (delegates to
# checks/ascii-ps1.sh). Cross-platform: OS temp dir + forward-slash paths + exec
# bit on POSIX, so it runs under pwsh on Linux/macOS too.
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot/../../../..").Path
$checkShSrc = Join-Path $repo "checks/ascii-ps1.sh"

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) "sdad-eval-07-$PID"
New-Item -ItemType Directory -Path (Join-Path $tmp "checks") -Force | Out-Null
try {
    Push-Location $tmp
    git init --quiet 2>$null
    git config user.email "eval@sdad.local" 2>$null
    git config user.name "SDAD Eval" 2>$null
    Copy-Item $checkShSrc (Join-Path $tmp "checks/ascii-ps1.sh")

    # Construct the pre-commit ratchet (mirror of install.ps1's body). LF only --
    # a CRLF shebang breaks sh ("bad interpreter"). No BOM.
    $hookBody = @'
#!/bin/sh
staged=$(git diff --cached --name-only --diff-filter=ACM -- '*.ps1' '*.sh' 2>/dev/null)
[ -n "$staged" ] || exit 0
repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
check="$repo_root/checks/ascii-ps1.sh"
[ -f "$check" ] || exit 0
if ! sh "$check" $staged; then
  echo "pre-commit: blocked by SDAD L-01 ratchet (non-ASCII .ps1/.sh staged)." >&2
  exit 1
fi
exit 0
'@
    $hookBody = $hookBody -replace "`r`n", "`n"
    $hookPath = Join-Path $tmp ".git/hooks/pre-commit"
    [System.IO.File]::WriteAllText($hookPath, $hookBody, (New-Object System.Text.UTF8Encoding($false)))
    # Executable bit is required for git to run the hook on POSIX (no-op on Windows).
    if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) {
        chmod +x $hookPath 2>$null
    }

    # dirty .ps1 (UTF-8 em dash E2 80 94)
    $bytes = [byte[]](36, 120, 32, 61, 32, 49, 32, 35, 32, 226, 128, 148)
    [System.IO.File]::WriteAllBytes((Join-Path $tmp "script.ps1"), $bytes)

    $ErrorActionPreference = "Continue"   # L-03: native stderr expected on block
    git add script.ps1 2>$null
    git commit -m "dirty" --quiet 2>$null
    $blocked = ($LASTEXITCODE -ne 0)

    Set-Content -Path (Join-Path $tmp "script.ps1") -Value '$x = 1 # clean' -Encoding ASCII
    git add script.ps1 2>$null
    git commit -m "clean" --quiet 2>$null
    $allowed = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = "Stop"

    if ($blocked -and $allowed) { Write-Host "PASS 07-precommit-blocks"; exit 0 }
    Write-Host "FAIL 07-precommit-blocks (blocked=$blocked expected True; allowed=$allowed expected True)"; exit 1
}
finally {
    Pop-Location
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
