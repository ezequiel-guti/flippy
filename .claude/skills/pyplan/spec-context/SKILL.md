---
name: pyplan-spec-context
description: >
  Activate this skill for any task involving the SPEC.md of a Pyplan project:
  writing, reading, updating, interpreting, or validating it. Use when the user
  runs $spec, $specout, or $build on a Pyplan project, or when SPEC.md is loaded
  and the project declares PROJECT_PLATFORM: pyplan. This skill teaches Claude the
  Pyplan-specific SPEC structure (§0, §A, §B, §1–§13) and the rules for navigating
  it during requirements gathering, build approvals, and living-doc updates.
  Trigger whenever SPEC.md is the subject or the primary working artifact.
---

# SKILL: pyplan-spec-context
# Version: 1.1 | SDAD v4.3
# Layer: Pyplan Platform — Spec Structure & Navigation
# Activation: active whenever a Pyplan SPEC.md is being written, read, or used

---

## Purpose

This skill defines the Pyplan-specific SPEC structure and rules for using it.
Standard SDAD SPEC has 13 sections (§1–§13). Pyplan projects add three sections
at the front: **§0**, **§A**, and **§B**.

These three additions solve a Pyplan-specific problem: the standard SDAD flow
assumes a code project where every increment produces runnable output. Pyplan
models have a longer setup phase (data connections, dimension structures, user
roles) before anything is demonstrable. §0/§A/§B provide the scaffolding for that.

---

## Full Pyplan SPEC Structure

```
§0   — Platform Declaration
§A   — Build Gate (approval required before $build starts)
§B   — Living Model State (updated at each increment close)
§1   — Vision & Objective
§2   — Users & Roles
§3   — Functional Flows
§4   — Data Model
§5   — Technical Architecture (Pyplan-specific)
§6   — Business Rules
§7   — Integrations & Data Sources
§8   — Testing Strategy
§9   — Security & Compliance
§10  — Definition of Done
§11  — Out of Scope
§12  — Open Decisions
§13  — AI Authorship Log
```

---

## §0 — Platform Declaration

**Purpose:** Identifies this as a Pyplan project and locks platform-specific behavior.

**Required fields:**
```
PROJECT_PLATFORM: pyplan
PYPLAN_VERSION: [version if known, otherwise "current"]
DEPLOYMENT: [cloud / on-premise / hybrid]
CLIENT: [client name or codename]
COMPLIANCE_TIER: [1 / 2 / 3]
```

**Rules:**
- §0 is the first thing Claude reads at session start.
- If `PROJECT_PLATFORM: pyplan` is absent, Pyplan skills do not activate.
- If PYPLAN_VERSION is unknown, proceed — but flag any version-sensitive patterns.
- This section never changes after initial approval. To change platform context, start a new project.

---

## §A — Build Gate

**Purpose:** A checklist of conditions that must ALL be met before any `$build`
increment is approved. This replaces the ad-hoc "is this ready to build?" judgment.

**Standard §A checklist for Pyplan projects:**

```
§A — BUILD GATE
[ ] §0 complete and approved
[ ] §1 Vision approved — success criteria agreed with client
[ ] §2 Roles defined — who sees what confirmed
[ ] §3 at least one complete functional flow documented
[ ] §4 Data Model — source files or API connections identified
[ ] §5 Architecture — Pyplan module structure agreed
[ ] §6 Business Rules — at least core calculation logic defined
[ ] §7 Data sources accessible (credentials exist or are in plan)
[ ] §9 Compliance tier locked and requirements listed
[ ] §12 Open Decisions: none blocking implementation
[ ] Client sign-off on scope (documented or referenced here)
```

**Rules:**
- `$build` is blocked if any `[ ]` item in §A is unchecked.
- Partial unchecks are allowed only for items marked `[deferred]` with a documented reason.
- When `$build` is called, Claude reads §A first and reports status:
  - All checked → proceed
  - Any unchecked → block and list what needs resolution
- §A is sealed after first `$build` approval. New items cannot be added retroactively.
  Use §12 (Open Decisions) for new issues that arise mid-build.

---

## §B — Living Model State

**Purpose:** A running record of the model's current state. Updated at every increment close.
Replaces the need to re-read §13 (AI Authorship Log) to understand current status.

**Structure:**
```
§B — LIVING MODEL STATE
Last updated: [date] · Increment: [N]

MODULES COMPLETE:
  - [module name] — [one-line description of what it does]

MODULES IN PROGRESS:
  - [module name] — [what is done / what remains]

MODULES NOT STARTED:
  - [module name]

DATA CONNECTIONS:
  - [source name]: [connected / pending / blocked — reason]

OPEN ISSUES:
  - [issue description] — [owner or "unassigned"]

NEXT INCREMENT:
  [description of next planned increment]
```

**Rules:**
- §B is updated by Claude automatically at every `$build` increment close.
- §B is never edited manually mid-session — only at increment boundaries.
- If §B and §13 (AI Authorship Log) conflict, §B takes precedence for current state;
  §13 is the historical record.
- At session start, Claude reads §B first (before §1–§13) to reconstruct current state.
  This reduces context load on long-running projects.
- If §B is absent or empty, Claude must reconstruct state from §13 before proceeding.

---

## §5 — Technical Architecture (Pyplan-specific additions)

Standard §5 covers stack and components. For Pyplan projects, §5 must also include:

```
PYPLAN ARCHITECTURE:
  Module structure:     [list of top-level modules]
  Shared utility nodes: [nodes used across modules — list or "none"]
  Dimension catalog:    [time, accounts, cost centers, etc. — list]
  Driver nodes:         [user-adjustable inputs — list or "none at this stage"]
  Calculation layers:   [data → drivers → formulas → outputs]
  Interface entry point: [which module the user lands on first]
  Interface types:      [per screen: component / HTML - AI-built screens default to HTML]
```

If this information is not available at spec time, mark each field `[TBD]` and
add a corresponding item to §12 (Open Decisions). `$build` can proceed with
`[TBD]` fields only if the corresponding Open Decision is not on the §A gate.

---

## §7 — Integrations & Data Sources (Pyplan-specific additions)

Standard §7 covers APIs and external services. For Pyplan projects, §7 must also include:

```
DATA SOURCES:
  | Source | Type | Format | Refresh | Owner | Status |
  |--------|------|--------|---------|-------|--------|
  | [name] | [file/API/DB] | [xlsx/csv/json/etc] | [manual/scheduled] | [name] | [available/pending/blocked] |

KNOWN DATA QUALITY ISSUES:
  - [description] — [impact on model] — [mitigation or "none yet"]
```

Missing data sources with status `blocked` must appear in §A gate (unchecked) before `$build`.

---

## Reading Order for Claude at Session Start

When a Pyplan SPEC.md is loaded, read in this order:

1. **§0** — confirm PROJECT_PLATFORM: pyplan; load Pyplan skills
2. **§B** — reconstruct current model state without reading full history
3. **§A** — check build gate status
4. **§12** — note open decisions that may affect the session
5. **§1, §2, §3** — understand scope and user flows
6. **§5, §6, §7** — load architecture, rules, data sources
7. **§9** — compliance context
8. **§10** — DoD for QA reference
9. **§13** — only if §B is absent or a historical question arises

This order minimizes context consumption on large SPECs while ensuring the
most decision-relevant sections are loaded first.

---

## $spec Behavior for Pyplan Projects

When `$spec` runs on a Pyplan project, add these questions to the standard flow
(insert after basic scope, before compliance tier):

1. "What Pyplan modules will this model have? (e.g., Revenue, Cost, Headcount, Dashboard)"
2. "What are the main data sources? (file uploads, ERP connections, manual inputs?)"
3. "Who are the model users and what do they need to see? (roles and views)"
4. "Are there existing Pyplan conventions at this client we need to follow?"
5. "Which screens need a fully custom layout or will be built by an AI agent?
   (those become HTML interfaces - the agent default; standard dashboards
   stay as component interfaces)"

These answers populate §0, §A, §B, §5, and §7 automatically during `$specout`.

---

## $build Behavior for Pyplan Projects

At each increment close, Claude must:

1. Update §B (Living Model State) — modules, data connections, open issues, next increment
2. Update §13 (AI Authorship Log) — increment number, feature, model, date
3. Check §A gate — confirm no new blockers were introduced
4. Run the Pyplan QA checklist (from pyplan-qa-platform skill if active)

The §B update is the most important: it is what allows the next session to
start with full context from a single section read.

---

## Delta Handling During $build

Two types of changes arise during Pyplan builds:

**Small delta** — a requirement or data detail that clarifies but does not
change scope (e.g., a column name is different than expected):
- Resolve inline, log the change in §B under OPEN ISSUES or NEXT INCREMENT
- Note in §13: "Delta: [description]"
- Do NOT pause the build

**Structural delta** — a requirement that changes module structure, dimension
catalog, or cross-module logic (e.g., cost centers are shared across three
modules, not isolated per module):
- Pause `$build`
- Write a GAP REPORT to §12 (Open Decisions):
  ```
  OD-XX: [title]
  Impact: [what modules/nodes are affected]
  Options: [A / B / C — one line each]
  Recommendation: [Claude's recommendation and reason]
  Required: client / G7 decision before resuming
  ```
- Do not write code for the affected area until the decision is closed

---

## Key Constraints (carry into every session)

- §A is a hard gate — never let `$build` proceed with unchecked blocking items
- §B must be updated at every increment close — never skip it
- Pyplan models evolve slowly; a "complete" increment may only be one module
- Data source availability is the most common blocker — flag early, flag often
- Client sign-off on §1 (Vision) is required before any `$build` — no exceptions
