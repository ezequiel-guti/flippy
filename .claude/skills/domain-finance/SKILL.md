---
name: domain-finance
description: >
  Domain-correctness profile for financial planning & analysis (FP&A). Activate
  when PROJECT_DOMAIN is finance / FP&A / budgeting / consolidation, or when the
  model deals with revenue, COGS, margin, cash flow, budget vs actual, or group
  consolidation. Loaded by $audit (dimension 5b) when PROJECT_DOMAIN resolves to
  finance, and on-demand in $build when a finance calculation needs domain review.
  Checklist level (BR-05): KPIs, formulas to validate, trap assumptions, red flags
  — not a full FP&A methodology. Pairs with the domain-agnostic business-alignment
  skill, which handles objective measurability and rule traceability.
---

# SKILL: domain-finance
# Version: 1.0 | SDAD v6
# Layer: Domain profile (audit dimension 5b) — FP&A
# Depth: checklist (BR-05). Confidence labelling per BR-10. Not a substitute for the client's SME.

---

## Scope

Domain-correctness checklist for FP&A models: budgeting, forecasting, management
reporting, and group consolidation. It tells the auditor *what to check and what
typically goes wrong*, not how to build an FP&A practice. Domain findings carry a
confidence level (BR-10); high-stakes numbers still require SME sign-off.

If `PROJECT_DOMAIN` is finance but no input lets these checks run, mark the
dimension "not assessable - no domain profile input" — never fabricate a finding.

---

## KPIs / metrics to recognize

| Metric | Definition to verify | Common mistake |
|--------|----------------------|----------------|
| Gross margin | (Revenue - COGS) / Revenue | COGS missing a cost component; margin on net vs gross revenue inconsistent |
| EBITDA | Operating profit + D&A | D&A added back twice, or financing items left in |
| Cash flow (indirect) | Net income +/- non-cash +/- working-capital change | Sign error on working-capital delta |
| Budget vs actual variance | Actual - Budget (and % of budget) | Variance sign flips favorable/unfavorable across cost vs revenue lines |
| Consolidated revenue | Sum of entity revenues MINUS intercompany | Intercompany not eliminated (see red flags) |
| Working capital | Current assets - current liabilities | Cash or debt items misclassified as operating |

## Formulas to validate

- Margin and ratio nodes divide by the correct base (gross vs net revenue) consistently across the model.
- Period logic: YTD = sum of periods to date; rolling forecast does not double-count the actuals already closed.
- Currency: each entity converted at the correct rate (closing vs average) for its line type (balance sheet = closing, P&L = average).
- Allocation drivers sum to 100% — no orphaned or double-allocated cost.

## Trap assumptions

- "Revenue" is unambiguous → it is not. Gross vs net, billed vs recognized, with/without intercompany all differ — check which one each node means.
- Actuals are frozen → late adjustments reopen closed periods; verify the forecast does not re-add them.
- One currency → multi-entity models almost always need FX; absence of FX logic in a multi-entity model is itself a flag.
- Time periods align → fiscal year != calendar year for many entities; check the calendar dimension.

## Red flags (flag immediately, with confidence + BR-03 band)

| Red flag | Why it matters | Typical band |
|----------|----------------|--------------|
| **Consolidation double-count** | A consolidated total ADDS intercompany / inter-entity lines instead of ELIMINATING them, or sums entities whose figures already roll up into a parent. Group revenue is overstated. | HIGH / CRITICAL |
| COGS omits a cost component | Margin overstated; pricing and profitability decisions wrong | HIGH |
| Working-capital sign error | Cash flow direction inverted | HIGH |
| Hardcoded FX rate or fiscal year | Breaks next period; silent staleness | MEDIUM |
| Variance sign inconsistent across lines | Favorable/unfavorable mislabeled in reports | MEDIUM |
| Double-counted D&A in EBITDA | Profit overstated | MEDIUM |

**Worked example of the consolidation double-count (the canonical FP&A trap):**
`consolidated_revenue = group_revenue + intercompany_sales`, where
`group_revenue = sub_a_revenue + sub_b_revenue` and `intercompany_sales` is
already inside `sub_b_revenue`. Intercompany is added a second time instead of
being eliminated (subtracted). Correct form:
`consolidated_revenue = group_revenue - intercompany_eliminations`.
This is the planted defect in the `finance-double-count` audit fixture.

---

## Cross-domain seams

When this profile loads alongside another (e.g. [[domain-supply-chain]]), flag the
boundary as high-risk and check it explicitly. The classic finance <-> supply-chain
seam is **COGS / inventory**: the value supply chain computes (unit cost x volume)
must reconcile with the COGS finance books; a mismatch double-counts or drops cost.
The `business-alignment` skill owns the seam-flagging rule; this profile supplies
the finance side of the reconciliation.

---

G7 AI Development Methodology | SDAD v6 | domain-finance (I3b)
