# AGENT HANDOFF TEMPLATE

When a sub-agent ($agent review / test / audit, or any delegated task) finishes, its final
message — which IS its return value — must follow this structure. The gap SDAD closes here is
the **return** (handoff), not the delegation: Claude Code already delegates natively and returns
the sub-agent's final message, so SDAD does NOT add custom orchestration — only this convention
for what that final message contains.

```
── AGENT HANDOFF ───────────────────────────────────────
Agent: [name] | Task: [one line]
Result: [max 5 lines — the answer, not the process]
Files changed: [list, or "none — read-only"]
Decisions made: [→ record in DECISIONS.md, or "none"]
Critical findings: [P0/P1 with severity, or "none"]
────────────────────────────────────────────────────────
```

## Rules
- Keep Result to 5 lines max — the main session reads this, not the full transcript.
- Any decision listed must also be written to DECISIONS.md by the main session.
- P0/P1 findings are surfaced immediately (🚨 security / 🔒 compliance) per the Behavior Rules.
- If the sub-agent produced structured data, prefer a schema so the return is machine-parseable.

## Note on native capability (C-010 evaluation, 2026-06-07)
Claude Code provides native sub-agent delegation with a returned final message (and schema-based
structured output via workflows). Custom return infrastructure is therefore unnecessary; this
template is the lightweight convention layered on top.
