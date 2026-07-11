---
name: domain-supply-chain
description: >
  Domain-correctness profile for supply chain planning. Activate when
  PROJECT_DOMAIN is supply-chain / S&OP / inventory / demand planning /
  procurement / logistics, or when the model deals with demand forecast, safety
  stock, reorder points, lead times, inventory cover, or fill rate. Loaded by
  $audit (dimension 5b) when PROJECT_DOMAIN resolves to supply chain, and
  on-demand in $build when a supply-chain calculation needs domain review.
  Checklist level (BR-05): KPIs, formulas to validate, trap assumptions, red flags
  — not a full supply-chain methodology. Pairs with the domain-agnostic
  business-alignment skill and reconciles with domain-finance at the COGS seam.
---

# SKILL: domain-supply-chain
# Version: 1.0 | SDAD v6
# Layer: Domain profile (audit dimension 5b) — Supply chain / S&OP
# Depth: checklist (BR-05). Confidence labelling per BR-10. Not a substitute for the client's SME.

---

## Scope

Domain-correctness checklist for supply chain and S&OP models: demand planning,
inventory policy, replenishment, and capacity. It tells the auditor *what to check
and what typically goes wrong*, not how to run a planning practice. Findings carry
a confidence level (BR-10); high-stakes parameters still need SME sign-off.

If `PROJECT_DOMAIN` is supply-chain but no input lets these checks run, mark the
dimension "not assessable - no domain profile input" — never fabricate a finding.

---

## KPIs / metrics to recognize

| Metric | Definition to verify | Common mistake |
|--------|----------------------|----------------|
| Safety stock | z x sigma_demand x sqrt(lead time) | Lead-time and demand units mismatched; sigma over wrong horizon |
| Reorder point | (avg demand x lead time) + safety stock | Lead-time demand omitted; uses period demand instead of lead-time demand |
| Inventory cover (days) | Inventory / avg daily demand | Monthly demand divided by daily inventory or vice versa (unit mismatch) |
| Fill rate / service level | Demand met from stock / total demand | Backorders counted as fulfilled |
| Forecast accuracy (MAPE/bias) | abs(actual - forecast) / actual | Bias hidden by symmetric error metric; zero-demand periods divide by zero |
| Inventory turns | COGS / average inventory | COGS basis differs from the finance books (see cross-domain seam) |

## Formulas to validate

- Unit consistency end to end: demand, lead time, and stock all expressed on the same time base (days vs weeks vs months).
- Safety stock scales with sqrt(lead time), not lead time linearly.
- Lead-time demand (demand x lead time) is included in the reorder point, not just safety stock.
- Aggregation: family/category forecast equals the sum of its SKUs (no top-down/bottom-up drift).
- Capacity constraints actually bind the plan — an "optimized" plan that exceeds capacity is unflagged is a defect.

## Trap assumptions

- Lead time is constant → it varies; using a point estimate understates safety stock.
- Demand is stationary → seasonality and trend break naive sigma-based safety stock.
- One unit of measure → cases vs eaches vs pallets; conversion errors are silent and large.
- Forecast = plan → the consumed plan may override forecast; verify which one drives replenishment.

## Red flags (flag immediately, with confidence + BR-03 band)

| Red flag | Why it matters | Typical band |
|----------|----------------|--------------|
| Unit-of-measure mismatch | Reorder points and cover off by orders of magnitude | HIGH / CRITICAL |
| Lead-time demand omitted from reorder point | Systematic stockouts | HIGH |
| Safety stock scales linearly with lead time | Over/understocking | MEDIUM |
| Capacity constraint not binding the plan | Infeasible plan presented as optimal | HIGH |
| Forecast bias masked by MAPE only | Persistent over/under-forecast undetected | MEDIUM |
| Top-down vs bottom-up forecast drift | Aggregate != sum of SKUs | MEDIUM |

---

## Cross-domain seams

When this profile loads alongside [[domain-finance]], flag the boundary as
high-risk. The canonical seam is **COGS / inventory valuation**: the unit cost x
consumed volume this model computes must reconcile with the COGS finance books. A
mismatch means cost is double-counted or dropped between the operational and
financial views. Check that inventory valuation method (FIFO / average) and the
cost rates match across the two domains. `business-alignment` owns the
seam-flagging rule; this profile supplies the supply-chain side of the reconciliation.

---

G7 AI Development Methodology | SDAD v6 | domain-supply-chain (I3b)
