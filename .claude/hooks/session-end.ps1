# SDAD v5 -- SessionEnd hook (Windows / PowerShell)  [v5 I2 ratchet wired]
# Purpose: batch auto-commit at session end of ONLY the SDAD doc files.
# Safeguards (all mandatory):
#   - Whitelist: commits ONLY DECISIONS.md and LESSON_LIBRARY.md. Never code, never `git add .`.
#   - Hold sentinel: if .sdad/HOLD_AUTOCOMMIT exists (open P0 / failing increment), do nothing.
#   - No empty commit: commits only if a whitelisted file actually changed.
#   - Standardized commit message.
#   - v5 I2: L-01 ratchet at the session boundary -- if any tracked .ps1 violates
#     pure-ASCII, skip the autocommit and log a warning. The autocommit itself only
#     touches .md files; skipping it is the visibility mechanism, not data protection.
# Safety: always exits 0.

$ErrorActionPreference = 'SilentlyContinue'
try { $null = [Console]::In.ReadToEnd() } catch {}

$root = $env:CLAUDE_PROJECT_DIR
if (-not $root) { $root = (Get-Location).Path }

# Guard: hold sentinel blocks all autocommit
if (Test-Path (Join-Path $root '.sdad/HOLD_AUTOCOMMIT')) { exit 0 }

Push-Location $root
try {
  # v5 I2 -- L-01 ratchet (child process: the check script uses exit codes)
  $check = Join-Path $root 'checks/ascii-ps1.ps1'
  if (Test-Path $check) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $check | Out-Null
    if ($LASTEXITCODE -ne 0) {
      $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
      if (-not (Test-Path (Join-Path $root '.sdad'))) {
        New-Item -ItemType Directory -Path (Join-Path $root '.sdad') -Force | Out-Null
      }
      Add-Content -Path (Join-Path $root '.sdad/gate.log') -Encoding UTF8 -Value "$stamp WARN session-end: ascii-ps1 ratchet failed -- autocommit skipped (L-01)"
      Pop-Location
      exit 0
    }
  }

  $whitelist = @('DECISIONS.md', 'LESSON_LIBRARY.md')
  $changed = @()
  foreach ($f in $whitelist) {
    if (Test-Path $f) {
      $st = @(git status --porcelain -- $f 2>$null)
      if ($st.Count -gt 0) { $changed += $f }
    }
  }
  if ($changed.Count -gt 0) {
    git add -- $changed 2>$null
    git diff --cached --quiet -- $changed 2>$null
    if ($LASTEXITCODE -ne 0) {
      git commit -m "docs: auto-commit SDAD docs at session end" -- $changed 2>$null | Out-Null
    }
  }
} catch {}
finally { Pop-Location }
exit 0
