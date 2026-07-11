#!/bin/sh
# SDAD v5 -- SessionEnd hook (macOS/Linux, POSIX sh)  [v5 I2 ratchet wired]
# 1:1 port of session-end.ps1.
# Purpose: batch auto-commit at session end of ONLY the SDAD doc files.
# Safeguards (all mandatory):
#   - Whitelist: commits ONLY DECISIONS.md and LESSON_LIBRARY.md. Never code, never `git add .`.
#   - Hold sentinel: if .sdad/HOLD_AUTOCOMMIT exists (open P0 / failing increment), do nothing.
#   - No empty commit: commits only if a whitelisted file actually changed.
#   - Standardized commit message.
#   - v5 I2: L-01 ratchet at the session boundary -- if any tracked .ps1 violates
#     pure-ASCII, skip the autocommit and log a warning.
# Safety: always exits 0.

cat >/dev/null 2>&1 || true

root=${CLAUDE_PROJECT_DIR:-$(pwd)}

# Guard: hold sentinel blocks all autocommit
[ -f "$root/.sdad/HOLD_AUTOCOMMIT" ] && exit 0

cd "$root" 2>/dev/null || exit 0

# v5 I2 -- L-01 ratchet
if [ -f "$root/checks/ascii-ps1.sh" ]; then
  if ! sh "$root/checks/ascii-ps1.sh" >/dev/null 2>&1; then
    mkdir -p "$root/.sdad" 2>/dev/null
    echo "$(date '+%Y-%m-%d %H:%M:%S') WARN session-end: ascii-ps1 ratchet failed -- autocommit skipped (L-01)" >> "$root/.sdad/gate.log" 2>/dev/null
    exit 0
  fi
fi

changed=''
for f in DECISIONS.md LESSON_LIBRARY.md; do
  if [ -f "$f" ]; then
    if [ -n "$(git status --porcelain -- "$f" 2>/dev/null)" ]; then
      changed="$changed $f"
    fi
  fi
done

if [ -n "$changed" ]; then
  # $changed is intentionally unquoted: whitelist names contain no spaces
  git add -- $changed >/dev/null 2>&1
  if ! git diff --cached --quiet -- $changed 2>/dev/null; then
    git commit -m 'docs: auto-commit SDAD docs at session end' -- $changed >/dev/null 2>&1
  fi
fi
exit 0
