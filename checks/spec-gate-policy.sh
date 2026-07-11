#!/bin/sh
# SDAD v5.1 -- shared spec-gate decision policy (POSIX engine).
# Single source of truth for "may this path be written without an approved SPEC?".
# Consumed by:
#   - the local PreToolUse hook (.claude/hooks/pre-tool-use-spec-gate.sh), per tool call
#   - the CI gate runner (checks/spec-gate-ci.sh), per changed file in a pull request
# One module means local and server enforcement cannot drift (SPEC F4).
# Mirror: checks/spec-gate-policy.ps1 -- keep the two in sync.
#
# Usage: sh checks/spec-gate-policy.sh <path> [project_dir]
#   <path>        file path (absolute or repo-relative) the caller wants to write
#   [project_dir] repo root (default: $CLAUDE_PROJECT_DIR, else current dir)
# Exit codes: 0 = allow, 2 = deny (reason on stderr).
# Deterministic: this module does NOT fail open. Callers decide the error policy
# (the local hook wraps it and fails open; CI fails closed). L-01: pure ASCII.

target=$1
proj=${2:-${CLAUDE_PROJECT_DIR:-$(pwd)}}

[ -z "$target" ] && exit 0

# Path normalization via POSIX parameter expansion -- no sed (BSD/GNU parity, L-05
# sibling) and safe for paths containing spaces (INC-2 P2 hardening).
proj_norm=${proj%/}
rel=${target#"$proj_norm/"}
rel_low=$(printf '%s' "$rel" | tr 'A-Z' 'a-z')
name=$(basename "$rel_low")

# R1 allowlist: methodology state + docs are never blocked
case "$name" in
  spec.md|spec_retroactive.md|decisions.md|lesson_library.md|changelog.md|readme.md) exit 0 ;;
esac
case "$rel_low" in
  *.md) exit 0 ;;
  docs/*|.sdad/*|.claude/*|hub/*) exit 0 ;;
esac

# $docfinal legitimately runs without a Spec (sentinel file)
[ -f "$proj_norm/.sdad/DOCFINAL_ACTIVE" ] && exit 0

# $audit also runs without a Spec (sentinel file, mirrors $docfinal -- BR-14)
[ -f "$proj_norm/.sdad/AUDIT_ACTIVE" ] && exit 0

# R2 code-file denylist; unknown extensions default to allow
case "$rel_low" in
  *.py|*.js|*.ts|*.jsx|*.tsx|*.ps1|*.psm1|*.sh|*.bat|*.cmd|*.sql|*.html|*.css|*.json|*.yaml|*.yml|*.toml|*.ini|*.cs|*.java|*.go|*.rs|*.rb|*.php) ;;
  *) exit 0 ;;
esac

# The gate
if [ ! -f "$proj_norm/SPEC.md" ]; then
  echo "SDAD gate: no SPEC.md in this project -- code writes are blocked until a Spec is approved. Run \$spec (or \$docfinal for retroactive documentation)." >&2
  exit 2
fi
if ! grep -q "SPEC STATUS: APPROVED" "$proj_norm/SPEC.md" 2>/dev/null; then
  echo "SDAD gate: SPEC.md is not approved (missing 'SPEC STATUS: APPROVED' marker). Get developer approval before writing code." >&2
  exit 2
fi
exit 0
