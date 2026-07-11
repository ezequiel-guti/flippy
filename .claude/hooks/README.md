# .claude/hooks/

Claude Code lifecycle scripts that run automatically at defined points in the workflow.

## Status in SDAD v4.3

**ACTIVE (cross-platform).** Three hooks are wired in `.claude/settings.json` through the
`run-hook.sh` dispatcher (see Platform below). Each hook has two 1:1 implementations:
`.ps1` (Windows) and `.sh` (macOS/Linux).

| Hook | Scripts | What it does | Safeguards |
|---|---|---|---|
| `SessionStart` | `session-start.ps1` / `.sh` | Injects the COMPACT ANCHOR ([LOCK] decisions from `DECISIONS.md`) into context, and does a fast-forward `git pull`. Fires after compaction too — this is what makes the anchor survive compaction. | Pull only if no tracked file is modified and only `--ff-only`; never blocks session start; always exits 0. |
| `PreCompact` | `pre-compact.ps1` / `.sh` | Writes a compaction-time anchor snapshot to `.sdad/compact_anchor.md` so `SessionStart(compact)` can re-inject it. | Never blocks compaction (never exits 2); exits 0. |
| `SessionEnd` | `session-end.ps1` / `.sh` | Batch auto-commit of SDAD docs at session end. | Whitelist: ONLY `DECISIONS.md` + `LESSON_LIBRARY.md`, never code; skips if `.sdad/HOLD_AUTOCOMMIT` exists; no empty commit; standardized message. |

### Design note (verified against Claude Code docs)
A `PreCompact` hook **cannot** inject context that survives compaction — its `additionalContext`
is discarded by the compaction. The durable mechanism is `PreCompact` writing the anchor to disk +
`SessionStart` (matcher includes `compact`) re-injecting it **after** compaction. This corrects the
original roadmap assumption that PreCompact alone would persist the anchor.

### Autocommit hold
To pause autocommit (e.g. an open P0 QA finding or a failing increment), create an empty file
`.sdad/HOLD_AUTOCOMMIT`. Delete it to resume. `.sdad/` is gitignored (runtime state only).

## Platform
Cross-platform since the macOS port. `settings.json` registers ONE shell-form command per hook:
`sh .../run-hook.sh <hook-name>`. Per the Claude Code hooks docs, shell-form commands run via
`sh -c` on macOS/Linux and via **Git Bash** on Windows (when available). The dispatcher detects
Windows (`MINGW`/`MSYS`/`CYGWIN`) and delegates to the original, tested `.ps1` scripts unchanged;
everywhere else it runs the `.sh` ports. The `.sh` scripts are POSIX sh, use `jq` for JSON
output when available (manual escaping fallback otherwise), and passed the same test gate as
the Windows versions (valid JSON, unicode round-trip without mojibake, pull guard, hold
sentinel, whitelist, no empty commits, real-session integration).
Known limit: a Windows machine WITHOUT Git for Windows falls back to PowerShell, which cannot
run the `sh` command — hooks then fail non-blocking (the session still works). Git Bash ships
with Git for Windows, which the SDAD workflow already requires.

## Reference
Claude Code hooks: https://code.claude.com/docs/en/hooks
Any hook here activates for all developers using this repo. Test in a branch before merging to main.
