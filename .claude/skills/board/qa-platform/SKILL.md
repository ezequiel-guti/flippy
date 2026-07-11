# SKILL: Board QA Platform
# On-demand skill — auto-activated by $qa on Board projects (Layer 5).
# Role: Board-specific QA checks — anti-patterns, syntax, placement rules, naming, security.
# Version: 5.2 | 2026

---

## Role

This skill runs as Layer 5 of the SDAD QA stack on Board projects.
It catches Board-specific issues that Layers 1-4 (general SDAD) do not cover.

Auto-activated when $qa runs on a project with PROJECT_PLATFORM: board.
All findings are numbered H-XX and classified by severity (P0 / P1 / P2).

Severity scale:
- P0 — 🚨 Must fix before increment is complete. Blocks DoD sign-off.
- P1 — ⚠️ Should fix before $build continues. Documented in DECISIONS.md if deferred.
- P2 — ℹ️ Improvement. Can be addressed in a later increment.

---

## Check Catalogue

Run all checks in priority order. Report each finding with: check ID, severity,
location (§E/§F section, artefact name), description, and recommended fix.

---

### DM-01 — Entity creation order (P0)

**What to check:** In the planned increment sequence (from SPEC §13 or the build plan),
verify that Entities are created before Relationships, and Relationships before Cubes.

**Finding:** Any Cube increment that precedes its dimension Entities or Relationships.

**Remediation:** Resequence increments. Entities → Relationships → Cubes is non-negotiable
in Board — attempting to create a Cube with an undefined Entity dimension will fail.

---

### DM-02 — Cube dimension validity (P0)

**What to check:** Every Cube in §E references only Entities that exist in the §E Entities table.

**Finding:** A Cube dimension that names an Entity not listed in §E.

**Remediation:** Either add the missing Entity to §E (preferred) or correct the Cube
definition. Block the increment until §E is consistent.

---

### DM-03 — Algorithm syntax (P0)

**What to check:** Every Algorithm spec uses block letters (a, b, c...) as operands,
not variable names or Cube names. Functions used are in the valid list:
`dt()`, `rt()`, `gt()`, `@DATE`, `@MONTH`, `@YEAR`.

**Finding examples:**
```
SalesValue / Budget * 100        -- P0: named references not valid in Board
a / b * 100                      -- PASS
a + unknownFn(b)                 -- P0: unknownFn not a valid Board function
```

**Remediation:** Replace named references with positional block letters.
Replace unrecognized functions with valid equivalents or flag for developer review.

---

### DM-04 — Division-by-zero in Algorithms (P1)

**What to check:** Any Algorithm that divides by a Cube operand (e.g. `a / b`).

**Finding:** Division by a Cube that may contain zero values.

**Remediation:** Confirm with the developer that zero-denominator behavior is acceptable
(Board returns 0, not an error). If it is not, document a conditional guard strategy —
Board does not have a native IF/ELSE in Algorithms; a workaround Cube may be needed.

---

### DM-05 — Cube sparsity risk (P1)

**What to check:** Any Cube with more than 5 Entity dimensions, or a Cube where
the combination of dimension member counts would yield > 1,000,000 potential cells.

**Estimate cell count:** multiply approximate member counts across all dimensions.
Example: Product(500) × Customer(2000) × Month(60) × Region(50) = 3,000,000,000 cells — flag immediately.

**Finding:** Cube with high dimension count or estimated high cell volume.

**Remediation:** Split into smaller Cubes, reduce dimension count, or use a Dataflow
step to pre-aggregate before storing in the high-cardinality Cube.

---

### DM-06 — Missing time Entity (P2)

**What to check:** If the project involves time-series data (sales, budget, actuals),
verify that a time Entity (Month, Week, or Day) is present in §E.

**Finding:** No time Entity declared despite the project description implying periodic data.

**Remediation:** Add a time Entity. Prefer Board's built-in time Entity type over
a custom-loaded date dimension.

---

### CP-01 — Procedure placement (P0)

**What to check:** Every Procedure in §F with Scheduleable: Yes is placed at
the Data Model level, not the Capsule level.

**Finding:** A Procedure marked Scheduleable: Yes placed at Capsule level.

**Remediation:** Move the Procedure to the Data Model. Capsule-level Procedures
cannot be scheduled — this will fail silently at go-live.

---

### CP-02 — Client-side Steps in server-side Procedures (P1)

**What to check:** Every Procedure spec is reviewed for client-side Steps
(Go to Screen, Apply Selection) placed inside a Procedure that is either
server-side or scheduleable.

**Finding:** A Step of type "Go to Screen" or "Apply Selection" inside a
Data Model-level or scheduleable Procedure.

**Remediation:** Move client-side Steps to a Capsule-level Procedure.
Create a separate Capsule Procedure for the interactive logic and call it
from a Button on the relevant Screen.

---

### CP-03 — Screen Data Block binding (P1)

**What to check:** Every Screen in §F has all its Data Blocks bound to a
Data Model that exists in §E.

**Finding:** A Screen references a Data Model name not declared in §E.

**Remediation:** Correct the Data Model reference in §F, or add the missing
Data Model to §E.

---

### CP-04 — Selector without default (P2)

**What to check:** Every Selector in the increment spec has a defined default selection.

**Finding:** A Selector with no default defined.

**Remediation:** Define a default member (e.g. current year, first product, all customers).
A Selector with no default will cause all bound Data Blocks to show no data on first load.

---

### CP-05 — Writeable Cube without locking rules (P1)

**What to check:** Any Cube marked as writeable (used in a Data Entry object)
has locking rules documented in §F or the increment spec.

**Finding:** A writeable Cube with no locking rules.

**Remediation:** Define who can write to which cells, under which conditions.
Unprotected writeable Cubes are a data integrity risk in multi-user planning scenarios.

---

### NM-01 — Naming conventions (P2)

**What to check:** All Board objects follow consistent naming across the increment:

| Object | Convention | Example |
|--------|-----------|---------|
| Entity | PascalCase, singular noun | `Product`, `Month`, `CostCenter` |
| Relationship | PascalCase + "Hierarchy" or descriptive | `ProductHierarchy`, `GeoRegion` |
| Cube | PascalCase, noun or noun+noun | `SalesValue`, `BudgetAmount`, `QuantitySold` |
| Data Reader | PascalCase, action + source | `LoadSalesSQL`, `ImportProductCSV` |
| Procedure | PascalCase, verb + object | `LoadSalesData`, `NavigateToDashboard` |
| Screen | PascalCase, descriptive | `SalesDashboard`, `BudgetInput` |
| Capsule | PascalCase, application name | `SalesAnalysis`, `BudgetPlanning` |

**Finding:** Objects using snake_case, ALL_CAPS, spaces, or inconsistent style
within the same increment.

**Remediation:** Rename before implementing. Renaming in Board after use breaks
existing references — it is expensive to fix post-build.

---

### SEC-01 — Board API credentials in Procedures (P0)

**What to check:** Review all Procedure specs, Algorithm specs, and any generated
SQL or configuration artefacts for embedded credentials:
OAuth client secrets, Bearer tokens, passwords, connection string passwords.

**Finding:** Any credential string in a generated artefact or SPEC section.

**Remediation:** Remove immediately. Replace with a placeholder `[CREDENTIAL — use
environment variable]`. Credentials must never appear in Board Procedure steps,
SQL queries, or SDAD documents.

---

## QA Run Format

When Layer 5 runs, report findings in this format:

```
=== Layer 5 — Board Platform QA ===

[H-01] DM-03 — P0 — Algorithm syntax error
  Location: §E Cubes > MarginPct Algorithm
  Finding: Formula uses named reference "SalesValue / CostValue * 100"
  Fix: Replace with block letters: "a / b * 100"
        Operand a → SalesValue, Operand b → CostValue

[H-02] CP-01 — P0 — Scheduleable Procedure at Capsule level
  Location: §F Procedures > LoadMonthlyData
  Finding: Procedure marked Scheduleable: Yes but placed at Capsule level
  Fix: Move LoadMonthlyData to Data Model level

No further findings.
```

If no findings: `=== Layer 5 — Board Platform QA: no findings ===`

---

## Interaction with Other QA Layers

Layer 5 runs after Layers 1–4. Cross-layer notes:

- **Layer 1 (Security):** SEC-01 above overlaps with Layer 1. If Layer 1 already
  flagged a credential, do not duplicate — reference the existing finding.
- **Layer 2 (Structure):** DM-01 (creation order) and CP-03 (binding) relate to
  structural consistency. If already flagged by Layer 2, mark as "confirmed by Layer 5."
- **$qa auto mode:** Never auto-fix P0 findings. Surface to developer and require
  explicit approval before any remediation is applied.
