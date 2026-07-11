---
name: data-discovery
description: >
  Activate this skill when starting work on a project where data sources are
  unknown, incomplete, or unverified. Use when the user says "we don't know
  what data we have", "the client hasn't sent the files yet", "I need to
  understand what's in this dataset", "the data is messy", or any variant of
  exploring unfamiliar data before or during build. Also activate when §7
  (Integrations & Data Sources) is being defined in $spec, when a data source
  is flagged as "pending" or "blocked" in SPEC §B, or when the first increment
  of a Pyplan model involves connecting to a data source for the first time.
  Use this skill before writing any logic that depends on data whose structure
  has not been verified.
---

# SKILL: data-discovery
# Version: 1.0 | SDAD v4.2
# Layer: Transversal — Data Discovery & Contract Management
# Activation: any project with unverified or partially known data sources

---

## Purpose

This skill governs the process of discovering, characterizing, and contracting
data sources before they are used in build. It prevents the most common failure
mode in analytics projects: writing logic against assumptions about data that
turn out to be wrong.

Core principle: **no logic is written against a data source that has not been
characterized**. Discovery is not optional — it is a gate before $build.

---

## The Discovery Gate

Before any increment that reads from a data source, Claude checks:

```
DISCOVERY GATE — [source name]
[ ] Source is accessible (file received / API reachable / DB connected)
[ ] Structure is documented (columns, types, sample confirmed)
[ ] Volume is known (row count or size estimate)
[ ] Null / missing data strategy is defined
[ ] Refresh cadence is agreed with the client or data owner
[ ] Data contract written in SPEC §7
```

If any item is unchecked: the increment is blocked for that source.
Unblocking requires closing the missing item, not skipping it.

---

## Phase 1 — Source Inventory

At the start of any project, before $spec is complete, produce a source inventory.

Trigger: user mentions data sources or uploads files. Run silently, emit result.

```
📋 DATA SOURCE INVENTORY
Source: [name]
  Type:       [file / API / database / manual entry / platform-native]
  Format:     [CSV / XLSX / JSON / REST / SQL / Pyplan node / other]
  Status:     [available / pending / blocked]
  Owner:      [who provides this — client, G7, external system]
  Cadence:    [one-time / daily / monthly / on-demand / unknown]
  Notes:      [any known issues, size, or constraints]

[repeat for each source]

Sources ready for build: [N]
Sources blocking build:  [N — list them]
```

If sources are blocking: add them to §12 (Open Decisions) with status `blocked`
and add corresponding unchecked items to §A (Build Gate).

---

## Phase 2 — Source Characterization

When a source becomes available (file received, API accessible), characterize it
before writing any logic that depends on it.

### For file sources (CSV, XLSX, JSON)

Produce a characterization report:

```
📊 SOURCE CHARACTERIZATION — [source name]
File:         [filename and path]
Format:       [CSV / XLSX tab / JSON]
Rows:         [count or estimate]
Columns:      [N columns]

COLUMN CATALOG:
  [column_name] | [inferred type] | [nulls: N%] | [sample values] | [notes]
  ...

KEY FINDINGS:
  ✅ [what looks clean and usable]
  ⚠️  [anomalies, inconsistencies, or quality issues found]
  🔴 [blockers — data that cannot be used as-is]

DATA QUALITY SCORE: [HIGH / MEDIUM / LOW]
  HIGH:   usable as-is, minimal cleaning needed
  MEDIUM: usable after documented transformations
  LOW:    requires significant remediation or client correction before use

RECOMMENDED NEXT STEP: [use as-is / clean in staging / return to client]
```

### For API sources

```
📊 SOURCE CHARACTERIZATION — [API name]
Endpoint:     [URL pattern]
Auth:         [API key / OAuth / none]
Response:     [JSON / XML / other]
Pagination:   [yes — [method] / no]
Rate limits:  [requests/min or "unknown"]

FIELDS RETURNED:
  [field_name] | [type] | [nullable] | [notes]
  ...

KEY FINDINGS:
  ✅ [usable fields]
  ⚠️  [missing fields, inconsistencies]
  🔴 [blockers]

RECOMMENDED NEXT STEP: [proceed / clarify with provider / test error cases]
```

### For Pyplan-native sources (nodes, existing models)

```
📊 SOURCE CHARACTERIZATION — [node/module name]
Node type:    [data / formula / selector / output]
Dimensions:   [list of dimensions this node carries]
Shape:        [describe the array structure]
Dependencies: [what upstream nodes it reads from]

KEY FINDINGS:
  ✅ [what is stable and well-defined]
  ⚠️  [assumptions in this node that downstream logic depends on]
  🔴 [risks if upstream changes]
```

---

## Phase 3 — Data Contract

After characterization, formalize the contract. This is the artifact that
governs how this source is used in the rest of the project.

Write to SPEC §7.

```
CONTRACT: [contract name — descriptive, not just the filename]
Version:      1.0
Date:         [YYYY-MM-DD]
Status:       ACTIVE / PENDING / SUPERSEDED

SOURCE:
  Owner:      [who produces and maintains this data]
  Location:   [file path / API endpoint / node name]
  Format:     [format]
  Refresh:    [cadence and trigger]

SCHEMA:
  | Column / Field | Type     | Nullable | Constraints       | Notes |
  |----------------|----------|----------|-------------------|-------|
  | [name]         | [type]   | yes/no   | [unique, range…]  | [any] |

QUALITY GUARANTEES:
  [What the data owner commits to — or "none documented"]

KNOWN ISSUES:
  [Any anomalies documented during characterization]

TRANSFORMATION REQUIRED:
  [What must be done before this source can be used in logic — or "none"]

DOWNSTREAM CONSUMERS:
  [Which modules or nodes depend on this contract]

REVIEW TRIGGER:
  [Condition that should reopen this contract — e.g., "client changes ERP"]
```

---

## Phase 4 — Ongoing Monitoring

After a data source is in use, this skill contributes to ongoing sessions:

**At session start:** if §B (Living Model State) lists a data connection as
`pending` or `blocked`, surface it before any $build work.

**At $build increment close:** if the increment touched a data source, confirm
the contract is still accurate. If not, flag a contract drift finding:

```
⚠️  CONTRACT DRIFT — [source name]
What changed: [description]
Impact:       [which nodes or modules are affected]
Action:       update contract in SPEC §7 and review dependent logic
```

**At $qa:** check that every data source used in the increment has a documented
contract. Missing contract = PP finding (🟡 should improve) or 🔴 (if the
source was supposed to be contracted before build started).

---

## Integration with Pyplan

For Pyplan projects, data discovery maps to the model's setup phase:

| Discovery phase | Pyplan equivalent |
|---|---|
| Source inventory | List all input nodes before building any formula nodes |
| Characterization | Verify dimension structure matches the expected catalog |
| Contract | Document in §7 what format each input module expects |
| Monitoring | Check §B at each session — data connection status |

The most common Pyplan data discovery failures:

**Dimension mismatch** — the time dimension in the source file uses a different
calendar structure than the model expects (fiscal vs calendar, week vs month).
Discovery catch: check time grain and calendar type during characterization.

**Account code format** — account codes in the source use a format (e.g., `4.1.001`)
that doesn't match the model's node names (e.g., `account_4100`).
Discovery catch: document code format in the contract; build a mapping node.

**Missing entities** — the source file doesn't contain all cost centers or
entities the model was designed for. Silent result: some rows return zero.
Discovery catch: cross-reference source entities against the dimension catalog.

**Refresh gap** — the model is refreshed monthly but the source file is updated
only quarterly. Discovery catch: document cadence in the contract; flag the gap.

---

## Escalation Rules

| Situation | Action |
|---|---|
| Source is unavailable at spec time | Add to §A gate (unchecked); block $build for dependent modules |
| Source is available but quality is LOW | Write contract, document known issues, recommend client correction before $build |
| Source changes after $build starts | Flag CONTRACT DRIFT; review dependent logic before continuing |
| Source is available but schema changed from contract | Treat as structural delta; pause $build; update contract and review impact |
| Source owner is unresponsive | Escalate in §12 as Open Decision with `owner: client`; do not proceed silently |
