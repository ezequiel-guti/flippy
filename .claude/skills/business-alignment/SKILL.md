---
name: business-alignment
description: >
  Activate this skill to judge whether a project's logic actually serves its
  declared business objective — not whether it runs. Use when the user says
  "is this aligned with the goal", "does this rule make business sense", "what
  is the business value here", "are these objectives measurable", or any variant
  of evaluating business worth rather than technical correctness. Auto-activates
  on $audit (business dimension, 5a). In $spec / $build it activates when a §1
  objective is vague / non-measurable or a §6 business rule has no traceable
  business reason. Domain-agnostic — the domain-* profiles handle domain-specific
  correctness; this skill handles alignment, measurability, and value-vs-cost.
---

# SKILL: business-alignment
# Version: 1.0 | SDAD v6
# Layer: Transversal — Business dimension (audit 5a), shared by $build and $audit
# Activation: on-demand. $audit (always); $spec/$build (vague §1 objective or untraceable §6 rule). BR-02.

---

## Purpose

SDAD already covers technical correctness ($qa Layers 1-4), platform correctness
(Layer 5), and delivery. It has had no specialist for the question a client
actually pays for: **does this model do the right business thing, and can anyone
prove it?** This skill is that specialist.

It judges alignment, not execution. A model can calculate flawlessly and still be
worthless — wrong objective, untraceable rules, value swamped by cost. This skill
flags that gap. Domain-specific correctness (is this the right COGS formula?) is
delegated to the `domain-*` profile loaded for `PROJECT_DOMAIN`; this skill stays
domain-agnostic.

---

## The three alignment checks

### Check 1 — Objective is measurable (SPEC §1)

A business objective is assessable only if a third party could decide, from the
text alone, whether it was met. Apply the two-person test (CLAUDE.md success
criterion): if two reasonable people could disagree about whether the objective
was achieved, it is not measurable.

| Verdict | Signal |
|---------|--------|
| Measurable | Names a metric, a direction, and a reference point. "Cut month-end close from 10 days to 5 by Q4." |
| Non-measurable | Adjective with no metric. "Improve visibility", "optimize planning", "better decisions". |

When non-measurable in `$spec` / `$build`: flag and propose a measurable rewrite —
do not invent the target number; ask the owner. When auditing: record as an
alignment finding, severity per BR-03 (typically HIGH — an unmeasurable objective
makes the whole model unauditable for value).

### Check 2 — Business rules are traceable (SPEC §6)

Every business rule (§6) must trace back to a stated business reason and, ideally,
to the objective in §1. A rule with no "why" is either dead logic or an
undocumented assumption — both are findings.

For each §6 rule ask: *which objective or external requirement forces this rule?*
- Traceable → reason recorded, links to §1 or a named regulation/policy.
- Untraceable → flag. In `$audit`, this is an alignment finding; recommend the
  owner confirm the rule still reflects intent (rules outlive their reason).

### Check 3 — Value exceeds cost (SPEC §12)

For each significant capability, weigh business value against build + run +
maintenance cost. Flag inversions: heavy machinery for marginal value
(e.g. a real-time pipeline feeding a report read once a month). This is a
recommendation-level finding (usually MEDIUM/LOW per BR-03), never a hard block —
the owner decides. Record the trade-off; do not silently accept or silently kill.

---

## Elicitation protocol (the gate — BR-09)

Alignment cannot be judged against an objective the auditor invented. Before any
alignment finding, the declared business objective must come from an input the
owner provided:

- **$spec / $build** — the objective is in SPEC §1 (the developer declared it).
- **$audit** — the auditor must elicit it from the model owner. Structured
  elicitation: *What decision does this model support? What metric moves if it
  works? Who acts on the output, and when?*

**If no elicitation input exists → mark the business dimension
"not assessable - no elicitation input" and stop. Never fabricate an objective,
never infer one from node names and then audit against it (BR-09).** A fabricated
alignment finding is the failure mode eval scenario I7 is built to catch.

The not-assessable verdict is itself a finding: the report recommends the owner
supply the objective so the dimension can be assessed.

---

## Confidence labelling (BR-10)

Every business finding carries a confidence level — `high | medium | low`.
- Direct from owner elicitation + explicit §1/§6 text → high.
- Inferred from partial input, or judged via an LLM-seeded domain profile → medium/low.
An LLM or provisional domain profile raises the floor of what can be checked; it
does **not** replace the client's SME for high-stakes validation. Surface the
confidence so the owner knows what still needs human sign-off.

---

## Severity mapping (BR-03)

Business findings join the unified 4-band scheme. Each finding shows band + source
label `alignment`:

| Band | Typical alignment trigger |
|------|---------------------------|
| CRITICAL | Model optimizes the wrong objective — output actively misleads decisions |
| HIGH | Objective non-measurable; a §6 rule contradicts the declared objective |
| MEDIUM | Untraceable §6 rule; value-vs-cost inversion on a significant capability |
| LOW | Minor traceability gap; cosmetic objective wording |

---

## Integration

**$spec / $build:** when §1 reads non-measurable or a §6 rule lacks a reason, this
skill activates, flags it, and proposes a rewrite — it does not block the build
(alignment is advisory in build; only platform/security gates block).

**$audit (dimension 5a):** always runs. Elicit → apply the three checks → emit
findings with band + `alignment` source + confidence. Hands off domain-specific
correctness to the loaded `domain-*` profile (5b); flags cross-domain seams as
high-risk when multiple profiles are loaded.

**Relationship to other skills:** pairs with `decision-architecture` (which judges
*how* data is structured) — this skill judges *whether the structure serves the
goal*. Domain profiles ([[domain-finance]], [[domain-supply-chain]]) supply the
domain-correctness layer this skill deliberately leaves out.

---

G7 AI Development Methodology | SDAD v6 | business-alignment (I3a)
