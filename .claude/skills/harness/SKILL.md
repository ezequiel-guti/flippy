---
name: harness
description: >
  Activate this skill when the developer asks about SDAD's Control Layer, the
  harness model, the Governance Axiom, or how SDAD enforces each harness
  component. Use when the user says "control layer", "harness model",
  "governance axiom", "E T C S L V", "is this enforced in code or just the
  prompt", "what does $eval cover", "how does the spec-gate work", or asks why
  a gate is a hook/check rather than an instruction. Loaded on-demand so the
  full harness mapping stays out of CLAUDE.md's line budget (R4) while the
  one-line behavior rules there stay authoritative.
---

# SDAD Control Layer & Harness Model (v5)

SDAD v5 reframes the methodology against harness-engineering theory, where an
agent harness is **H = (E, T, C, S, L, V)**. The central axiom:

> **Governance Axiom** — structural constraints belong in *code*. A
> natural-language rule in the prompt is a suggestion a model can drift past;
> a hook or a check is a guarantee. Prompt rules are the fallback, not the
> contract. v5's identity change is moving SDAD's critical gates from prompt
> to code.

## Where SDAD enforces each component

| Comp | Name | What it governs | v5 enforcement (code vs prompt) |
|---|---|---|---|
| E | Execution | the build/test loop | `$build` runs real tests; on tool/test error -> stop clean + `.sdad/HOLD_AUTOCOMMIT`, no undefined retry loop (I6, prompt rule + sentinel honored by session-end) |
| T | Tools | tool surface & boundaries | PreToolUse spec-gate hook denies code `Write`/`Edit` without an approved Spec (I1, **code**) |
| C | Context | what the model sees | COMPACT ANCHOR: PreCompact snapshot + SessionStart re-inject (code); context-budget thresholds (prompt) |
| S | State | durable project state | SPEC.md + DECISIONS.md + §13; atomic single-commit per increment (I8); typed §13 schema (I5) |
| L | Lifecycle | session/agent liveness | lesson-to-guardrail ratchet `checks/` + git pre-commit (I2, **code**); `$agent` liveness wrapper `.sdad/lib/agent-run` with 600s timeout (I4, **code**) |
| V | Evaluation | regression of the methodology itself | `$eval` golden dataset `.sdad/eval/` — deterministic core + release-gate LLM smoke (I3, **code**) |

Pre-v5, SDAD was strong on C and S (the layers it owns) but governed E, T, L,
and V by instruction. v5 adds V (it was absent), moves the Spec gate (T) and
the lesson ratchet (L) into code, and pins liveness (L) and recovery (E).

## The two deliberate hard stops

Everything in SDAD fails **open** (a broken guard never freezes the developer)
except two intentional blocks:
1. The spec-gate's **deny** (exit 2) when a code file is written without an
   approved Spec.
2. The git **pre-commit** ASCII ratchet (`--no-verify` is an accepted Tier 1
   bypass; the SessionEnd path is the second net).

## Determinism & model pinning (I7)

Record the exact model string per release in SPEC §5 / `$verify` when
reproducibility matters — methodology behavior can shift across model releases,
so a pinned string makes a v5 result reproducible.

## What `$eval` actually checks

- **Deterministic core** (every CLAUDE.md/skill change + release gate): spec-gate
  decision tree, fail-open, ASCII ratchet (both engines), `$agent` timeout +
  empty-output, and CLAUDE.md structural asserts (language-first rule, §A/§D/§9
  gates, version stamp, +60 line budget).
- **LLM replay smoke** (release gate only, `$eval release`): 2-3 `claude --print`
  scenarios matched with lax regex — non-deterministic, never a per-change gate.

The runner stamps `.sdad/eval/last-run` with the CLAUDE.md blob hash on a green
run; SessionStart compares it and prints a one-line `$eval` reminder on drift.
