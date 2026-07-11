#!/bin/sh
# SDAD v5 -- $agent liveness wrapper (macOS/Linux, POSIX sh), I4 / SPEC F5.
# 1:1 port of agent-run.ps1: wraps a `claude --print` delegation with a timeout
# and an empty-output check, so a hung or silent sub-agent fails fast.
#
# Usage (real delegation):
#   sh .sdad/lib/agent-run.sh "<system context + task>" [outfile] [timeout_sec]
#
# Exit codes (surfaced to the caller -- never proceed silently on non-zero):
#   0  success: outfile written and non-empty
#   1  empty/missing output
#   2  timeout (process killed)
#   3  claude CLI not found / failed to start
#
# OD-3: default timeout 600s (10 min). The SDAD_AGENT_EXE env var overrides the
# executable ONLY for the eval scenario, which points it at a self-contained
# stand-in that ignores the extra args. Real callers leave it unset (claude).
prompt=$1
outfile=${2:-.sdad/agent_output.tmp}
timeout_sec=${3:-600}
exe=${SDAD_AGENT_EXE:-claude}

if [ "$exe" = "claude" ] && ! command -v claude >/dev/null 2>&1; then
  echo "agent-run: claude CLI not found -- cannot delegate (install it or check PATH)"
  exit 3
fi

outdir=$(dirname "$outfile")
[ -d "$outdir" ] || mkdir -p "$outdir" 2>/dev/null
rm -f "$outfile" "$outfile.err" 2>/dev/null

# Launch in background, then poll up to timeout (portable: no `timeout` dep).
"$exe" --print "$prompt" >"$outfile" 2>"$outfile.err" &
pid=$!

elapsed=0
while kill -0 "$pid" 2>/dev/null; do
  if [ "$elapsed" -ge "$timeout_sec" ]; then
    kill "$pid" 2>/dev/null
    wait "$pid" 2>/dev/null
    echo "agent-run: TIMEOUT after ${timeout_sec}s -- delegation killed, not proceeding silently"
    rm -f "$outfile.err" 2>/dev/null
    exit 2
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
wait "$pid" 2>/dev/null

rm -f "$outfile.err" 2>/dev/null
if [ ! -s "$outfile" ]; then
  echo "agent-run: empty/missing output from delegation -- surfacing error, not proceeding"
  exit 1
fi
exit 0
