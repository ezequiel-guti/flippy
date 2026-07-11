# SDAD v5 -- SessionStart hook (Windows / PowerShell)  [v5 I3 eval reminder]
# Purpose:
#   1) Inject the COMPACT ANCHOR ([LOCK] decisions from DECISIONS.md) into context.
#      Because SessionStart fires AFTER compaction (source=compact), this is what makes
#      the anchor SURVIVE compaction -- PreCompact's own injection does not persist.
#   2) Guarded fast-forward git pull.
#   3) v5 I3 (OD-2): one-line $eval reminder when CLAUDE.md changed since the
#      last green eval run (stamp written by .sdad/eval/run-eval.ps1 on all-pass).
# Safety: must NEVER block session start. Always exits 0. All git ops are guarded.
# Pure ASCII (L-01).

$ErrorActionPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

try { $raw = [Console]::In.ReadToEnd() } catch { $raw = '' }
$src = 'startup'
if ($raw) {
  try { $j = $raw | ConvertFrom-Json; if ($j.source) { $src = $j.source } } catch {}
}

$root = $env:CLAUDE_PROJECT_DIR
if (-not $root) { $root = (Get-Location).Path }

$notes = @()

# --- Guarded git pull: fast-forward only, and only if no TRACKED files are modified ---
Push-Location $root
try {
  $porcelain = @(git status --porcelain 2>$null)
  $trackedDirty = $false
  foreach ($line in $porcelain) {
    if ($line -and ($line -notmatch '^\?\?')) { $trackedDirty = $true; break }
  }
  if ($trackedDirty) {
    $notes += 'git pull skipped (tracked files modified)'
  } else {
    $pullOut = git pull --ff-only 2>$null
    if ($LASTEXITCODE -eq 0) { $notes += 'git pull ok (up-to-date or fast-forwarded)' }
    else { $notes += 'git pull skipped (no upstream or not fast-forwardable)' }
  }
} catch { $notes += 'git pull skipped (error)' }
finally { Pop-Location }

# --- $eval reminder (v5 I3, OD-2): fires when CLAUDE.md hash differs from the
#     last green-run stamp (or no stamp exists). Fail-open: any error -> no note.
$evalNote = ''
try {
  $runner = Join-Path $root '.sdad/eval/run-eval.ps1'
  if ((Test-Path $runner) -and (Test-Path (Join-Path $root 'CLAUDE.md'))) {
    Push-Location $root
    $cur = git hash-object CLAUDE.md 2>$null
    Pop-Location
    if ($cur) {
      $last = ''
      $stampPath = Join-Path $root '.sdad/eval/last-run'
      if (Test-Path $stampPath) { $last = [string](Get-Content $stampPath | Select-Object -First 1) }
      if (([string]$cur).Trim() -ne $last.Trim()) {
        $evalNote = 'CLAUDE.md changed since the last green $eval -- run: powershell -ExecutionPolicy Bypass -File .sdad/eval/run-eval.ps1'
      }
    }
  }
} catch {}

# --- Build the anchor: prefer PreCompact snapshot on compact, else DECISIONS.md [LOCK] ---
$anchor = ''
$snapPath = Join-Path $root '.sdad/compact_anchor.md'
if (($src -eq 'compact') -and (Test-Path $snapPath)) {
  try { $anchor = (Get-Content $snapPath -Raw -Encoding UTF8) } catch {}
}
if (-not $anchor) {
  $decPath = Join-Path $root 'DECISIONS.md'
  if (Test-Path $decPath) {
    $inLock = $false
    $lockLines = @()
    foreach ($l in (Get-Content $decPath -Encoding UTF8)) {
      if ($l -match '^\#\#\s+\[LOCK\] decisions') { $inLock = $true; continue }
      if ($inLock) {
        if (($l -match '^\#\#\s') -or ($l -match '^---')) { break }
        if ($l.Trim()) { $lockLines += $l.Trim() }
      }
    }
    if ($lockLines.Count -gt 0) { $anchor = ($lockLines -join "`n") }
  }
}

$ctx = "SDAD session restored (source=$src). " + ($notes -join '; ') + "."
if ($anchor) {
  $ctx += "`n`nCOMPACT ANCHOR - [LOCK] decisions that must not be reopened:`n" + $anchor
}
if ($evalNote) {
  $ctx += "`n`n" + $evalNote
}

$out = @{ hookSpecificOutput = @{ hookEventName = 'SessionStart'; additionalContext = $ctx } }
$out | ConvertTo-Json -Depth 6 -Compress
exit 0
