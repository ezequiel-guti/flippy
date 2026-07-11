---
name: pyplan-audit
description: >
  Activate this skill to audit an existing Pyplan application and produce a
  client-facing audit report. Auto-activates on the $audit command. Use when the
  user says "audit this Pyplan model", "review this client app", "what is wrong
  with this model", "is this model production-ready", or asks for a structured,
  multi-dimension assessment of a model SDAD did not build. It orchestrates the
  five-dimension audit (development, security, usability, quality, business),
  composing existing SDAD skills and agents — it does not rewrite them. Consumes
  the I1 evidence layer and the deterministic ratchet checks as pre-computed
  evidence; reconciles severities into one 4-band scheme; declares not-assessable
  wherever evidence or elicitation is missing rather than fabricating findings.
---

# SKILL: pyplan-audit
# Version: 1.0 | SDAD v6
# Layer: Audit orchestrator -- the engine behind the $audit command
# Activation: auto on $audit; on-demand when an audit of an existing Pyplan model is requested

---

## Purpose

The technical engine for assessing a Pyplan model already exists across SDAD's
skills and agents. What was missing is the **orchestration**, the **five-dimension
model**, and the **client-facing report deliverable**. This skill is that
orchestrator. It composes existing capabilities; when a composed skill improves,
the audit improves for free (no rewrite, no duplication).

The audit is a point-in-time, evidence-based judgment of a model SDAD did not
necessarily build. It is liability- and relationship-aware: it reports intent
versus delivered **neutrally**, never accusatorially, and never fabricates.

This skill orchestrates; it owns no detection logic of its own. Detection lives in
the composed skills, agents, and ratchet checks listed below.

---

## The five-dimension model

| # | Dimension | What it judges | Composed from |
|---|-----------|----------------|---------------|
| 1 | Development / architecture | Node design, data flow, architecture consistency | `pyplan-qa-platform` (Layer 7) + `code-reviewer` agent (structure) |
| 2 | Security | Secrets, token/PII exposure, MCP tool surface | `security-auditor` agent + `mcp-tool-audit` ratchet |
| 3 | Usability | Navigation clarity, cognitive load, task success | `pyplan-qa-platform` 7.3 (convention-compliance) + I6 live-walkthrough sub-protocol |
| 4 | Quality / maintainability | Readability, duplication, naming, docs gaps | `pyplan-qa-platform` (Layers) + `code-reviewer` agent |
| 5 | Business | Does the model serve its declared objective, correctly for its domain? | 5a + 5b below |
| 5a | -- Alignment (domain-agnostic) | Measurable objective, traceable rules, value vs cost | `business-alignment` skill via the `business-analyst` agent |
| 5b | -- Domain correctness (domain-specific) | KPIs, formulas, trap assumptions, red flags | the `domain-*` profile(s) loaded for `PROJECT_DOMAIN` |

Dimension 5b runs only where a domain profile exists. No profile -> the dimension
is **"not assessable - no domain profile"** (a finding recommending profile
creation, never a silent skip). See `business-alignment` and the `domain-*` skills.

---

## Evidence inputs (consume, do not re-detect -- BR-04)

Before reasoning, the orchestrator gathers pre-computed evidence:

1. **Model representation** -- `.sdad/audit/<project>/evidence/node-graph.json`,
   acquired per `.sdad/audit/SCHEMA.md` (I1). Acquisition path: `.ppl` export
   (primary, stub in v6) / MCP read (enhancement) / manual (always available).
   Un-acquired areas are declared gaps with `status: not_assessable`.
2. **Deterministic ratchet output** -- run and read, do NOT re-detect by LLM:
   - `checks/audit-evidence` -- evidence is structurally valid before use
   - `checks/missing-result-assign` -- calculation nodes without `result=`
   - `checks/circular-deps` -- dependency cycles in the node graph
   - `checks/mcp-tool-audit` -- `@mcp_tool` defects (untyped params, called `result`, non-serializable return)

The LLM auditor reasons over what the ratchets could not mechanize (intent,
alignment, usability, domain judgment); it never re-checks what a ratchet already
covers deterministically.

---

## Orchestration (via the agent-run wrapper)

Specialist roles run in isolated context through `.sdad/lib/agent-run`
(`.ps1` / `.sh`, 600s timeout, fails loud on empty/timeout -- never proceeds
silently). Each role returns an AGENT HANDOFF block (see
`.claude/agents/HANDOFF_TEMPLATE.md`):

| Role | Agent file | Feeds dimension |
|------|-----------|-----------------|
| Security audit | `.claude/agents/security-auditor.md` | 2 |
| Structure / quality review | `.claude/agents/code-reviewer.md` | 1, 4 |
| Business alignment | `.claude/agents/business-analyst.md` (elicitation-fed) | 5a |

Domain correctness (5b) and the Pyplan platform checks (1, 3, 4) are applied by the
main auditor with the relevant skills loaded (`domain-*`, `pyplan-qa-platform`) --
they are knowledge, not isolated-context delegations.

Sub-agents run in isolated context and do not consume the main session budget.
Surface any `agent-run` non-zero exit to the developer; do not proceed silently.

---

## Usability dimension sub-protocol (dimension 3, BR-12)

Usability is the only dimension that requires **live app access** to assess fully.
The sub-protocol has two tiers:

### Tier A — Live walkthrough (app accessible)
1. Request the running Pyplan app URL or instance from the owner.
2. Walk through each declared user flow (§3 / business objective):
   - Navigation: does the user reach the right screens without dead ends?
   - Cognitive load: are filters, indexes, and inputs labeled clearly?
   - Task success: can the target user complete the declared task end-to-end?
   - Error handling: do invalid inputs surface a clear message (not a crash/blank)?
3. For each interface node in the node graph: check it renders data (not empty/error).
4. Screenshot or describe evidence for each finding. Severity per BR-03.

### Tier B — Convention-compliance only (app NOT accessible, BR-12)
When the live app is not accessible during the audit:
1. **Declare the limitation immediately** — do not defer or omit. Use exact wording:
   `"Usability: convention-only — live walkthrough not performed."`
2. Run convention checks only (what is inspectable from the node graph + code):
   - Interface nodes present? (`type: interface` in the node graph)
   - Input nodes have validation metadata? (range, type in code snippet)
   - Node identifiers are human-readable? (no `node_12`, no single-letter ids)
   - No dead interface nodes (declared but 0 dependencies, never referenced)
3. Every finding is marked `confidence: low` — these are structural proxies, not
   observed behavior. A convention-compliance finding cannot be CRITICAL or HIGH;
   cap at MEDIUM (BR-03 override for Tier B findings).
4. Add to the report backlog: `"Recommend a live-walkthrough session to close the
   usability gap. Current findings are convention-only."` (LOW band, for the owner).

### Manifest field
The evidence manifest (`manifest.md`) must declare `App Access: true | false`.
When `false`, the report automatically applies Tier B and records
`Usability: convention-only (no live walkthrough performed)` in the evidence
manifest header. This field is required — absence = declare it missing as a gap.

---

## Domain detection and loading

`PROJECT_DOMAIN` is declared in `$spec` (developer) or inferred in `$audit` from
data sources, node/KPI naming, interfaces, and ingested discovery docs, then
**confirmed with the owner**. Load every matching `domain-*` profile.
- Multi-domain model -> load multiple profiles and flag cross-domain seams as
  high-risk (e.g. the finance <-> supply-chain COGS/inventory seam).
- No profile for a detected domain -> not-assessable finding + creation-path
  backlog entry (BR-07/08). Never improvise a profile mid-audit.

Ingested sales/discovery docs, blueprints, and POCs are **declared-intent /
claims-to-verify, timestamped -- not ground truth** (markitdown ingestion, local
trusted files only). The audit verifies claims against acquired evidence.

---

## Severity reconciliation (BR-03 -- detailed template in I8)

Findings arrive from heterogeneous sources (H-XX technical, PP-XX platform, domain,
alignment, ratchet exits). Reconcile them into ONE 4-band scheme. Each finding
shows `band + source label`:

| Band | Source mapping |
|------|----------------|
| CRITICAL | P0 security; wrong-objective/misleading-output alignment |
| HIGH | P1; non-measurable objective; circular dependency; domain red flag (CRITICAL/HIGH) |
| MEDIUM | P2; untraceable rule; missing `result=`; value-cost inversion |
| LOW | style; cosmetic objective wording; minor traceability gap |

The full reconciliation + report template lands in I8; this skill defines the
contract the report consumes.

---

## The not-assessable rule (epistemic honesty)

Every dimension that cannot be assessed is reported as such, with the reason:
- No evidence acquired -> "not assessable - evidence not acquired" (I1 gap).
- No elicitation input -> "not assessable - no elicitation input" (BR-09).
- No domain profile -> "not assessable - no domain profile" (BR-07).
- Live app unavailable -> usability "convention-only, live walkthrough not performed" (I6).

The audit never guesses, never fabricates, and never silently omits an un-assessed
area. A not-assessable verdict is itself a finding that tells the owner what to
supply to close the gap.

---

## External dependency

The Pyplan MCP server (used for the MCP read acquisition path) is a **v1 external
dependency -- API may change across Pyplan updates**. Flag its maturity in the
report when the MCP read path was used. See the `pyplan-mcp` skill.

---

## The `$audit` command (lifecycle)

`$audit` is the command that drives this orchestrator. It is a **sibling of
`$docfinal`**: both run on a model SDAD did not necessarily build, and both run
**without an approved `SPEC.md`**. Where `$docfinal` *documents* retroactively,
`$audit` *judges and recommends* — its deliverable is a client-facing audit report,
and it is itself a `$QA` Standalone run extended with the five-dimension model and
the evidence/severity contract above.

### Modes
- `$audit` — full five-dimension lifecycle (all steps below).
- `$audit [dimension]` — run a single dimension (1..5, or `5a`/`5b`); the others are
  reported `not_assessable - not requested`, never silently dropped.
- `$audit report` — (re)generate the report from already-acquired evidence and the
  reconciled findings, without re-running acquisition.

### Spec-gate: runs without a Spec (BR-14)
`$audit` legitimately writes audit artifacts with no approved Spec. The spec-gate
allows this via the `.sdad/AUDIT_ACTIVE` sentinel (mirrors `$docfinal`'s
`.sdad/DOCFINAL_ACTIVE`; both are allowlisted in `checks/spec-gate-policy.{ps1,sh}`,
the single source of truth shared by the local hook and CI):
1. On `$audit` start, create `.sdad/AUDIT_ACTIVE` (empty sentinel; it is runtime
   state — `.sdad/*` is git-ignored, never committed).
2. On completion **or abort**, remove it, so the gate returns to enforcing the Spec
   for normal `$build`. Always remove it on the way out, including error paths.

The sentinel only lifts the *no-Spec* block; it grants no other allowance. Security
and compliance findings still require explicit developer approval before any fix.

### Pre-audit ingestion (runs before the five-dimension run)
1. **Evidence (I1).** Acquire the model representation per `.sdad/audit/SCHEMA.md`
   into `.sdad/audit/<project>/evidence/` — `.ppl` export (primary, stub in v6) /
   MCP read (enhancement) / manual (always available). Emit the evidence manifest
   (acquisition path, timestamp, Pyplan version if known, declared gaps). Un-acquired
   areas become `status: not_assessable`, never assumptions.
2. **Declared intent.** Ingest prior sales/discovery docs, blueprints, and POCs via
   markitdown (`convert_local`, local trusted files only) into
   `.sdad/audit/<project>/ingest/`. This material is **declared-intent /
   claims-to-verify, timestamped — not ground truth.** The audit verifies these
   claims against acquired evidence; it never treats a sales claim as delivered fact.
3. **Domain.** Detect `PROJECT_DOMAIN`, confirm with the owner, load matching
   `domain-*` profile(s) (see "Domain detection and loading" above).
4. **Elicitation.** Run the `business-alignment` elicitation for the declared
   objective; with no owner input, dimension 5a is `not_assessable - no elicitation
   input` (BR-09) — never fabricated.

Then run the five-dimension audit, reconcile severities (BR-03), and generate the
report. The report states intent vs delivered **neutrally** (BR-11) — liability- and
relationship-aware, never accusatory.

(The `$audit` command is registered in CLAUDE.md `Commands` / `$sdad` in I9, with the
rest of the v6 CLAUDE.md wiring, to keep that edit atomic against the line budget.
The skill auto-activates on `$audit` regardless, so the command works before then.)

---

## Report shape (full template -> I8)

Executive summary -> evidence manifest (acquisition path, gaps, SDAD version +
exact model string for reproducibility) -> one section per dimension (1, 2, 3, 4,
5a, 5b) -> prioritized improvement backlog (by band). Modes: `$audit` (full) /
`$audit [dimension]` / `$audit report`.

---

G7 AI Development Methodology | SDAD v6 | pyplan-audit (I4)
