# SKILL: Board Platform
# Always-active skill for PROJECT_PLATFORM: board sessions.
# Role: Board mental model, glossary, artefact orientation, sub-skill routing.
# Version: 5.2 | 2026

---

## Role

This skill is the foundation for all Board-platform work in SDAD.
It provides the mental model, glossary, and artefact orientation needed
before any $spec, $build, or $qa activity on a Board project.

It is always active when PROJECT_PLATFORM: board is declared. It does not need
to be invoked manually.

Four sub-skills extend this foundation on demand:
- **board/spec-context** — $spec questions and §E/§F generation
- **board/data-model**   — Entities, Relationships, Cubes, Data Readers, Algorithms
- **board/capsule**      — Screens, Procedures, Layouts, Masks, Selectors
- **board/qa-platform**  — Layer 5 QA checks (anti-patterns, syntax, placement rules)

---

## Board Mental Model

Board is a BI & Planning platform built around two distinct layers.
Understanding this separation is essential before any design or build work.

### Layer 1 — Data Model (back-end)

The Data Model is the calculation and storage engine. It contains:

| Object | Purpose |
|--------|---------|
| **Entity** | A dimension — the "who, what, when" of the data (e.g. Product, Month, Customer) |
| **Relationship** | A hierarchy between Entities (e.g. Product → Category → Division) |
| **Cube** | A measure at the intersection of dimensions (e.g. SalesValue by Product × Month) |
| **Data Reader** | A connector that loads data into Cubes from SQL, CSV, SAP, or API sources |
| **Procedure (DM)** | A server-side sequence of Steps that can be scheduled and called from any Capsule |
| **Algorithm** | A formula assigned to a Cube that computes values from other Cubes or functions |

Creation order is enforced by Board: **Entities → Relationships → Cubes**.
Violating this order causes downstream dimension errors that are hard to diagnose.

### Layer 2 — Capsule (front-end)

The Capsule is the presentation and interaction layer. It contains:

| Object | Purpose |
|--------|---------|
| **Capsule** | A self-contained application bound to one or more Data Models |
| **Screen** | A page within a Capsule containing data objects and controls |
| **Procedure (Capsule)** | A client-side sequence of Steps — cannot be scheduled, cannot be called externally |
| **Layout** | The visual definition of a Screen — exported/imported as XML |
| **Mask** | A reusable template applied to multiple Screens (navigation, branding) |
| **Selector** | A filter control that sets the selection context for data objects on a Screen |
| **Data Entry** | A writable DataView that allows users to input or modify Cube values |

---

## Key Distinctions (common mistake sources)

**Procedure placement:**
A Procedure placed at the **Data Model level** can be scheduled and called from any Capsule.
A Procedure placed at the **Capsule level** cannot be scheduled and cannot be called externally.
Placing a scheduleable ETL Procedure at Capsule level is a common misconfiguration — it will
fail silently or be inaccessible from other Capsules.

**Algorithm syntax:**
Board Algorithms use **positional block letters** (a, b, c...) as operands, not variable names.
Valid built-in functions: `dt()`, `rt()`, `gt()`, `@DATE`, `@MONTH`, `@YEAR`.
Using SQL-style variable names or unsupported functions will fail at runtime without clear errors.

**Cube sparsity:**
A Cube with many dimensions and sparse data causes memory and performance issues.
Prefer fewer dimensions per Cube and use Procedures to pre-aggregate where possible.

---

## What $build Generates on Board Projects

Board development does not produce traditional code files. SDAD $build generates:

| Artefact | Format | Purpose |
|----------|--------|---------|
| SQL Data Reader | `.sql` + configuration spec | Loads data into Cubes from a database |
| Entity/Cube CSV | `.csv` | Bulk-loads dimension members or Cube data |
| Layout XML | `.xml` | Defines the visual structure of a Screen (importable via Board UI) |
| Procedure spec | Structured markdown | Step-by-step Procedure logic for implementation in Board UI |
| Algorithm spec | Inline in SPEC or DECISIONS.md | Formula logic for Cube Algorithms |

There are no unit tests in the traditional sense. The Definition of Done for Board increments
uses artefact validation against Board syntax rules (see board/qa-platform for checks).

---

## SPEC Sections for Board Projects

Two sections are added to SPEC.md when PROJECT_PLATFORM: board:

**§E — Board Data Model** (gate section)
Documents Entities, Relationships, and Cubes. Must be at least Draft before $build.
Approved = full $build. Draft = analysis/optimization mode only (used for existing projects).

**§F — Board Capsule Structure**
Documents Capsules, Screens, Procedures, and Masks. Not a gate — informational.

---

## Sub-Skill Routing

| Trigger keyword | Sub-skill loaded |
|-----------------|-----------------|
| $spec, $specout (Board project) | board/spec-context — auto |
| entity, cube, relationship, dimension, §E | board/data-model — on demand |
| capsule, screen, procedure, layout, mask, §F | board/capsule — on demand |
| $qa (Board project) | board/qa-platform — auto |

---

## Out of Scope for This Skill Set

Board administration (user management, licensing, SCIM API), add-ins (Power BI, Excel),
XBRL export, BEAM/Predictive Analysis, NEXEL and Substitution Formula full references,
Board Collaboration Services, and Board MCP connector development are out of scope.
See SPEC §11 for the full exclusion list.
