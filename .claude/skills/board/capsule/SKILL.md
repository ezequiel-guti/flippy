# SKILL: Board Capsule
# On-demand skill — loaded when capsule, screen, procedure, layout, mask, or §F is mentioned.
# Role: Screens, Procedures (types and steps), Layouts, Masks, Selectors, Data Entry.
# Version: 5.2 | 2026

---

## Role

This skill provides expertise for designing and building the Board Capsule layer.
It covers the full front-end of a Board project: Capsules, Screens, Procedures,
Layouts, Masks, Selectors, and Data Entry objects.

Triggered by keywords: capsule, screen, procedure, layout, mask, selector, data entry,
navigation, §F, DataView, chart, gauge, drill.

---

## Capsule Structure

A Capsule is a self-contained Board application. It contains Screens, Procedures,
and references one or more Data Models for its data.

### Design guidelines

- One Capsule = one logical application (e.g. Sales Dashboard, Budget Planning).
  Avoid putting unrelated workflows in the same Capsule — use separate Capsules instead.
- A Capsule can reference multiple Data Models, but each Screen's Data Blocks
  are bound to one Data Model at a time.
- Capsule-level Procedures are for interactive logic only (navigation, user-triggered
  calculations). Scheduled or shared logic belongs at the Data Model level.

---

## Screens

A Screen is a page within a Capsule. It contains data objects, controls, and navigation.

### Screen types

| Type | Use case |
|------|----------|
| Dashboard | Read-only KPIs, charts, tables — no user input |
| Input / Planning | Data Entry objects — users enter or modify Cube values |
| Report | Printable or exportable view — usually a DataView or pivot |
| Navigation | Landing page — menu objects linking to other Screens |

### Screen objects

| Object | Purpose | Key configuration |
|--------|---------|------------------|
| DataView | Tabular display of Cube data | Cube, axes (rows/columns), Entity selections |
| Chart | Visual chart (bar, line, pie...) | Cube, chart type, axes, series |
| Gauge | KPI indicator | Cube, target Cube (optional), thresholds |
| Label | Static or dynamic text | Text or reference to a Cube cell |
| Selector | Filter control | Entity, selection mode (single/multi), default |
| Button | Triggers a Capsule Procedure | Procedure name, label, style |
| DataEntry | Writeable cell/grid | Writeable Cube, locking rules |
| Menu Object | Navigation link | Target Screen name, icon |

### $build artefact: Layout XML spec

When a Screen layout is designed, generate a structured spec for the developer
to implement in the Board UI. Include:

```
Screen: [ScreenName]
Capsule: [CapsuleName]
Data Model: [DataModelName]
Mask: [MaskName or None]

Objects:
  1. [ObjectType] — [brief description]
     Cube/Entity: [reference]
     Position: [top-left / top-right / full-width / etc.]
     Configuration: [key settings — axes, filters, display options]

  2. [ObjectType] — ...

Navigation:
  [describe how users move from this Screen to others]
```

For complex layouts, generate the Board Layout XML definition:
- Use Board's XML schema for the target version (v14/v15)
- Include `<ScreenObjects>`, `<DataBlock>`, `<Cube>`, `<Entity>` tags as appropriate
- Mark the artefact as `[import via Board UI → Layout → Import XML]`

---

## Procedures

A Procedure is a sequence of Steps that executes logic in Board.
The placement of a Procedure determines its capabilities (BR-04).

### Procedure types and placement rules

| Placement | Type | Can be scheduled | Callable from other Capsules | Typical use |
|-----------|------|-----------------|------------------------------|-------------|
| Data Model level | Server-side | Yes | Yes | ETL, data loading, aggregation |
| Capsule level | Client-side (mostly) | No | No | Navigation, user-triggered logic |

**Critical rule:** A Procedure that needs to be scheduled (e.g. nightly data load)
MUST be placed at the Data Model level. A Capsule-level Procedure cannot be scheduled —
placing ETL logic there is a silent misconfiguration that will only surface at go-live.

### Step types

| Step type | Side | Description |
|-----------|------|-------------|
| Data Reader | Server | Runs a Data Reader to load Cube data |
| Dataflow | Server | Runs a Dataflow aggregation between Cubes |
| Algorithm Recalculation | Server | Forces recalculation of Algorithm Cubes |
| Clear Cube | Server | Clears data from a Cube (optionally filtered) |
| Go to Screen | Client | Navigates to another Screen |
| Apply Selection | Client | Sets the Entity selection context |
| Set Variable | Client/Server | Sets a Board variable value |
| Send Mail | Server | Sends an email notification |
| Execute Procedure | Both | Calls another Procedure |
| Lock/Unlock Cube | Server | Controls write access to a Cube |

**Client-side vs server-side placement check:**
Steps like "Go to Screen" and "Apply Selection" are client-side — they require
a user session. Placing them inside a scheduled (server-side) Procedure will
fail at runtime. Flag any Procedure that mixes scheduled intent with client-side Steps.

### $build artefact: Procedure spec

```
Procedure name: [name]
Location: [Data Model: ModelName / Capsule: CapsuleName]
Type: [Server-side / Client-side / Mixed — if mixed, flag as risk]
Scheduleable: [Yes / No]
Trigger: [scheduled (cron) / button click / called by another Procedure]

Steps:
  1. [StepType] — [description]
     Parameters: [key config]
  2. [StepType] — [description]
     ...

Notes: [any ordering constraints, error handling, or known risks]
```

---

## Masks

A Mask is a reusable template applied to multiple Screens within a Capsule.
It typically contains navigation elements, headers, and branding.

### Design guidelines

- Use a Mask when 3 or more Screens share the same chrome (nav, logo, footer).
- A Mask cannot contain data objects that need a specific Data Model binding —
  use it for structural/navigational elements only.
- Changes to a Mask propagate to all Screens using it — test on all affected Screens.

### $build artefact: Mask spec

```
Mask name: [name]
Applied to: [All Screens / specific Screen list]
Contents:
  - [Object type]: [description, position]
  - Menu Object: links to [Screen1, Screen2, Screen3...]
  - Logo: [position]
  - [other elements]
```

---

## Selectors

A Selector is a filter control on a Screen that sets the Entity selection context
for all Data Blocks on that Screen (or a specified subset).

### Design guidelines

- Each Selector is bound to one Entity.
- Selection mode: Single (one member at a time) or Multi (multiple members).
- Default selection: always define a default — an empty Selector shows no data.
- Cascading Selectors: when one Selector drives another (e.g. Region → Country),
  the child Selector must be configured with a "from parent" dependency.
  Incorrect cascading produces data inconsistencies that are hard to debug.

---

## Data Entry

Data Entry objects allow users to write values directly into writeable Cubes.

### Design guidelines

- The target Cube must be configured as writeable in the Data Model.
- Locking rules control who can edit which cells — always define locking rules
  for planning/budgeting use cases to prevent accidental overwrites.
- After a Data Entry save, trigger an Algorithm Recalculation Step if any
  downstream Algorithm Cubes depend on the written Cube.
- Data Entry with version control (Scenario Cubes) requires additional
  Cube configuration — document in §E if applicable.

---

## §F Completeness Check

Before closing a Capsule increment, verify:

- [ ] All Capsules listed with primary Data Model reference
- [ ] All Screens listed with type and key objects
- [ ] All Procedures listed with correct placement (Data Model vs Capsule) and scheduleable flag
- [ ] No scheduleable Procedure placed at Capsule level (BR-04)
- [ ] No client-side Steps (Go to Screen, Apply Selection) inside server-side Procedures
- [ ] All Screen Data Blocks bound to a valid Data Model (§E Approved or Draft)
- [ ] Masks listed with Screen coverage
- [ ] Selectors have default selections defined
- [ ] Writeable Cubes have locking rules documented
