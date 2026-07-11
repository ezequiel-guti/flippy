#!/bin/sh
# SDAD v5 -- L-01 ratchet check: every .ps1 and .sh must be pure ASCII (POSIX engine).
# Installers/init scripts break on fresh machines with non-ASCII bytes (L-01,
# extended to .sh in the v5.2 versioning patch). Name kept as ascii-ps1 for
# hook/eval/install compatibility; scope is .ps1 + .sh.
# Mirror of checks/ascii-ps1.ps1 -- keep the two in sync.
# Usage: sh checks/ascii-ps1.sh [files...]   (default: all git-tracked .ps1/.sh)
# Exit 0 = clean, 1 = violations (commit-time guard fails CLOSED, see SPEC R3).

# Build the file list as positional params so paths with spaces survive (INC-2 P2).
if [ $# -eq 0 ]; then
  oldIFS=$IFS
  IFS='
'
  set -- $(git ls-files -- '*.ps1' '*.sh' 2>/dev/null)
  IFS=$oldIFS
fi

bad=0
for f in "$@"; do
  [ -f "$f" ] || continue
  n=$(LC_ALL=C tr -d '\000-\177' < "$f" | wc -c | tr -d ' ')
  if [ "$n" -gt 0 ]; then
    echo "ASCII VIOLATION: $f ($n non-ASCII bytes)"
    bad=$((bad + 1))
  fi
done

if [ "$bad" -gt 0 ]; then
  echo "ascii-ps1: $bad file(s) violate L-01 (pure-ASCII .ps1/.sh)"
  exit 1
fi
exit 0
