# Pyplan Audit Report Template
# SDAD v6 | pyplan-audit skill | I8
# Usage: copy this template, replace every [PLACEHOLDER] marker, delete this header block.
# The audit-report-integrity ratchet enforces three invariants over this file
# (audit-report-integrity.ps1 / .sh -- see checks/): stamp present, 5a verdict
# present, all manifest gaps surfaced. Never remove or alter the stamp line.

---

# Pyplan Audit Report -- [PROJECT_SLUG]

<!-- reproducibility stamp (BR-13) -- REQUIRED: keep exactly this format -->
Stamp: SDAD v6 . Model: [claude-MODEL-STRING] . Date: [YYYY-MM-DD]

---

## Executive Summary

[2-4 sentences. State: (1) what model was audited and when, (2) acquisition path
used (manual / MCP read / ppl-export), (3) overall risk posture (number of
CRITICAL/HIGH findings), (4) single most important finding. Neutral tone -- state
intent vs delivered, never accusatory (BR-11).]

---

## Evidence Manifest

| Field | Value |
|-------|-------|
| Project | [project-slug] |
| Acquired At | [YYYY-MM-DD] |
| Acquisition Path | [ppl-export \| mcp-read \| manual] |
| Pyplan Version | [version string \| unknown] |
| Node Count | [N] |
| App Access | [true \| false] |
| Usability | [live walkthrough performed \| convention-only (no live walkthrough performed)] |
| Elicitation | [performed \| none] |

### Declared Gaps (not_assessable)

<!-- REQUIRED: every gap area declared in manifest.md must appear here AND in the
     relevant dimension section below. Gaps are findings, not silent omissions. -->

| Area | Reason | Status |
|------|--------|--------|
| [gap-area-slug] | [why this area could not be acquired] | not_assessable |

---

## Dimension 1 -- Development / Architecture

<!-- Source: code-reviewer agent + pyplan-qa-platform ratchets (missing-result-assign,
     circular-deps). The LLM reasons over what ratchets could not mechanize (intent,
     design choices, cohesion). Do NOT re-check what a ratchet already covers. -->

<!-- Finding format: BAND . [source-label] . [id] Description -->
<!-- Bands: CRITICAL | HIGH | MEDIUM | LOW | not assessable -->
<!-- source-label examples: ratchet:missing-result | agent:code-reviewer | platform:pyplan -->

[FINDINGS or "No findings." or "not assessable - [reason]"]

---

## Dimension 2 -- Security

<!-- Source: security-auditor agent + mcp-tool-audit ratchet.
     Severity mapping: P0 -> CRITICAL, P1 -> HIGH, P2 -> MEDIUM. -->

[FINDINGS or "No findings." or "not assessable - [reason]"]

---

## Dimension 3 -- Usability

<!-- Declare tier immediately; do not defer (BR-12). -->

<!-- TIER A (App Access: true): -->
<!-- Live walkthrough performed. [Summarize navigation, cognitive load, task success,
     error handling per declared user flows.] -->

<!-- TIER B (App Access: false): -->
<!-- Usability: convention-only -- live walkthrough not performed. -->
<!-- Convention checks (node graph + code only): -->
<!-- - Interface nodes: [present / absent] -->
<!-- - Input validation metadata: [present / absent / partial] -->
<!-- - Node identifier quality: [readable / cryptic] -->
<!-- - Dead interface nodes: [none / N found] -->
<!-- All Tier B findings are confidence: low -- capped at MEDIUM (BR-03 override). -->

[FINDINGS or "No findings." or the Tier B declaration]

---

## Dimension 4 -- Quality / Maintainability

<!-- Source: code-reviewer agent + pyplan-qa-platform (readability, duplication,
     naming, docs gaps). -->

[FINDINGS or "No findings." or "not assessable - [reason]"]

---

## Dimension 5 -- Business

### 5a -- Alignment (domain-agnostic)

<!-- REQUIRED LINE -- audit-report-integrity.ps1 Rule B matches this exact pattern:
     "Business alignment (5a): <verdict>"
     Valid verdicts:
       not assessable - no elicitation input       (BR-09: when Elicitation: none)
       CRITICAL -- [one-line finding]
       HIGH -- [one-line finding]
       MEDIUM -- [one-line finding]
       LOW -- [one-line finding]
     A CRITICAL/HIGH/MEDIUM/LOW verdict REQUIRES Elicitation: performed in the
     manifest. With Elicitation: none the only valid verdict is "not assessable". -->

Business alignment (5a): [verdict]

<!-- Detail (when assessable): measurable objective, traceable rules, value vs cost. -->
[DETAIL or omit when not assessable]

### 5b -- Domain Correctness

<!-- Source: domain-* profile(s) for PROJECT_DOMAIN. -->
<!-- When no profile exists: "not assessable - no domain profile" is itself a finding.
     Add a backlog entry: "Create domain-[domain] profile to enable 5b assessment." -->

[FINDINGS or "not assessable - no domain profile" or "not assessable - PROJECT_DOMAIN not detected"]

---

## Improvement Backlog

<!-- Sorted: CRITICAL first, then HIGH, MEDIUM, LOW.
     not-assessable gaps appear as LOW backlog items: "Supply X to enable Y assessment."
     Finding format: BAND . [id] . Short title -- dimension -- recommended action -->

<!-- CRITICAL -->
[CRITICAL items or omit section if none]

<!-- HIGH -->
[HIGH items or omit section if none]

<!-- MEDIUM -->
[MEDIUM items or omit section if none]

<!-- LOW / not-assessable gaps -->
[LOW items]

---

## Severity Reconciliation Reference (BR-03)

<!-- Inline table so any reader can verify band assignment without loading the skill. -->

| Band | Maps from |
|------|-----------|
| CRITICAL | P0 security; wrong-objective or misleading-output alignment finding |
| HIGH | P1 security; non-measurable objective; circular dependency; domain red flag |
| MEDIUM | P2 security; untraceable business rule; missing result=; value-cost inversion |
| LOW | Style; cosmetic objective wording; minor traceability gap |
| not assessable | Evidence/elicitation/profile not supplied -- surfaced as gap, never silent |

<!-- Tier B usability override: convention-only findings capped at MEDIUM regardless
     of the band the finding would receive under Tier A (BR-03). -->

---

G7 AI Development Methodology | SDAD v6 | Pyplan Audit Report Template (I8)
