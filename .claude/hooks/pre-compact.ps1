# SDAD v5 -- PreCompact hook (Windows / PowerShell)  [v5 I3 ascii-clean]
# Purpose: snapshot the COMPACT ANCHOR to .sdad/compact_anchor.md at compaction time,
#   so the SessionStart(compact) hook can re-inject it AFTER compaction. PreCompact's own
#   additionalContext does NOT survive compaction (verified against Claude Code docs), so
#   the durable hand-off is this file, not an inline injection.
# Safety: must NOT block compaction. Always exits 0 (never 2).
# v5 I3: header normalized to pure ASCII (L-01) -- logic unchanged from v4.2.

$ErrorActionPreference = 'SilentlyContinue'
try { $null = [Console]::In.ReadToEnd() } catch {}

$root = $env:CLAUDE_PROJECT_DIR
if (-not $root) { $root = (Get-Location).Path }

$sdad = Join-Path $root '.sdad'
if (-not (Test-Path $sdad)) { New-Item -ItemType Directory -Path $sdad | Out-Null }

# Extract [LOCK] decisions from DECISIONS.md
$lockLines = @()
$decPath = Join-Path $root 'DECISIONS.md'
if (Test-Path $decPath) {
  $inLock = $false
  foreach ($l in (Get-Content $decPath -Encoding UTF8)) {
    if ($l -match '^\#\#\s+\[LOCK\] decisions') { $inLock = $true; continue }
    if ($inLock) {
      if (($l -match '^\#\#\s') -or ($l -match '^---')) { break }
      if ($l.Trim()) { $lockLines += $l.Trim() }
    }
  }
}

Push-Location $root
$branch = git rev-parse --abbrev-ref HEAD 2>$null
Pop-Location

$snap = "COMPACT ANCHOR (snapshot at compaction)`nBranch: $branch`n[LOCK] decisions:`n"
if ($lockLines.Count -gt 0) {
  $snap += (($lockLines | ForEach-Object { "  $_" }) -join "`n")
} else {
  $snap += "  (none recorded)"
}

Set-Content -Path (Join-Path $sdad 'compact_anchor.md') -Value $snap -Encoding UTF8
exit 0
