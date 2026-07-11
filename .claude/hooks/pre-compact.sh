#!/bin/sh
# SDAD v4.3 -- PreCompact hook (macOS/Linux, POSIX sh)
# 1:1 port of pre-compact.ps1.
# Purpose: snapshot the COMPACT ANCHOR to .sdad/compact_anchor.md at compaction time,
#   so the SessionStart(compact) hook can re-inject it AFTER compaction. PreCompact's own
#   additionalContext does NOT survive compaction (verified against Claude Code docs), so
#   the durable hand-off is this file, not an inline injection.
# Safety: must NOT block compaction. Always exits 0 (never 2).

cat >/dev/null 2>&1 || true

root=${CLAUDE_PROJECT_DIR:-$(pwd)}

mkdir -p "$root/.sdad" 2>/dev/null

# Extract [LOCK] decisions from DECISIONS.md
locks=''
if [ -f "$root/DECISIONS.md" ]; then
  locks=$(awk '
    /^##[[:space:]]+\[LOCK\] decisions/ { inlock = 1; next }
    inlock && (/^##[[:space:]]/ || /^---/) { exit }
    inlock {
      line = $0
      gsub(/^[[:space:]]+/, "", line)
      gsub(/[[:space:]]+$/, "", line)
      if (line != "") print line
    }' "$root/DECISIONS.md" 2>/dev/null)
fi

branch=$(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null)

{
  printf 'COMPACT ANCHOR (snapshot at compaction)\n'
  printf 'Branch: %s\n' "$branch"
  printf '[LOCK] decisions:\n'
  if [ -n "$locks" ]; then
    printf '%s\n' "$locks" | sed 's/^/  /'
  else
    printf '  (none recorded)\n'
  fi
} > "$root/.sdad/compact_anchor.md" 2>/dev/null

exit 0