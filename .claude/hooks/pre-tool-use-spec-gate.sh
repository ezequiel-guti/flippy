#!/bin/sh
# SDAD v5.1 -- PreToolUse spec gate (POSIX). Thin adapter: parse the stdin JSON,
# then delegate the allow/deny decision to checks/spec-gate-policy.sh, the module
# shared with the CI gate (SPEC F4). Decision logic lives in the policy, not here.
# STATUS: the .sh path-extraction edge cases (BSD sed, spaces) are validated on
# macOS/Linux in INC-2 (see docs/TASK_HOOKS_MACOS_PORT.md).
# Exit codes: 0 = allow, 2 = deny (stderr fed back to the model).
# Fail-open: internal errors allow the action and log to .sdad/gate.log. L-01: ASCII.

proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"

log_warn() {
  mkdir -p "$proj/.sdad" 2>/dev/null
  echo "$(date '+%Y-%m-%d %H:%M:%S') WARN spec-gate failed open: $1" >> "$proj/.sdad/gate.log" 2>/dev/null
}

raw=$(cat 2>/dev/null) || { log_warn "stdin read failed"; exit 0; }
[ -n "$raw" ] || exit 0

if command -v jq >/dev/null 2>&1; then
  target=$(printf '%s' "$raw" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
  [ $? -eq 0 ] || { log_warn "jq parse failed"; exit 0; }
else
  target=$(printf '%s' "$raw" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
fi
[ -n "$target" ] || exit 0

# Locate the shared policy relative to this hook (.claude/hooks -> repo/checks).
hookdir=$(cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || { log_warn "hookdir resolve failed"; exit 0; }
policy="$hookdir/../../checks/spec-gate-policy.sh"
[ -f "$policy" ] || exit 0   # policy missing -> fail open

sh "$policy" "$target" "$proj"
exit $?
