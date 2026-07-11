#!/bin/sh
# SDAD v4.3 -- cross-platform hook dispatcher (POSIX sh)
# Registered in .claude/settings.json as:  sh .../run-hook.sh <hook-name>
# Why this works on every platform (verified against the Claude Code hooks docs):
#   - macOS/Linux: shell-form hook commands run via `sh -c` -> this script -> <hook>.sh
#   - Windows: shell-form commands run via Git Bash when available -> this script
#     detects Windows (MINGW/MSYS/CYGWIN) and delegates to the tested <hook>.ps1,
#     so the existing Windows behavior is unchanged.
# stdin (the hook JSON) passes through exec untouched.

hook=$1
[ -n "$hook" ] || exit 0

dir="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks"

case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*)
    exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$dir/$hook.ps1"
    ;;
  *)
    exec sh "$dir/$hook.sh"
    ;;
esac