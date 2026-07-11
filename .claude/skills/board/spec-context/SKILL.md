# SKILL: Board Spec Context
# On-demand skill — auto-activated by $spec and $specout on Board projects.
# Role: Board-specific $spec questions, §E/§F generation, file ingestion, API ingestion.
# Version: 5.2 | 2026

---

## Role

This skill drives the $spec and $specout phases for Board projects.
It replaces the generic requirements questions with Board-specific ones,
populates §E (Board Data Model) and §F (Board Capsule Structure),
and handles two ingestion paths: file-based (XML, CFG, CSV) and API-based (Board Public API).

Activated automatically when $spec or $specout is run on a project with PROJECT_PLATFORM: board.

---

## Phase 0 — First Question

Before the standard PROJECT_LANGUAGE question, ask:

> "Is this a **new Board project** or an **existing one** you want to document/extend?
>  (1) New project — I will ask setup questions to define §E and §F from scratch
>  (2) Existing project — I will ingest your exported files and reconstruct §E and §F"

The answer determines which flow to follow. All subsequent questions use the
PROJECT_LANGUAGE established in the first $spec exchange.

---

## Flow A — New Project

Ask these questions one at a time, in order, with a proposed default each time.
Read any files already present in the repo before asking — infer what is already defined.

### Question sequence

**1. Board version**
> "Which Board version is this project targeting? [default: 15]"
Accepted: 15, 14, 13, or other (ask to specify).

**2. Deployment environment**
> "Cloud or on-premises? [default: Cloud]"
Accepted: Cloud, On-premises.

**3. Data Model name(s)**
> "What is the name of the primary Data Model? [default: infer from project name if clear]"
If multiple Data Models are needed, ask after the first is confirmed.

**4. Entities (dimensions)**
> "Which Entities (dimensions) does this Data Model need?
>  Example: Product, Customer, Month, Geography.
>  [default: Month is almost always needed — suggest it as a starting point]"
Ask about Members count and source for each Entity.

**5. Relationships (hierarchies)**
> "Are there any hierarchies between Entities?
>  Example: Product → Category → Division.
>  [default: none, unless entities suggest a natural parent-child]"

**6. Cubes (measures)**
> "Which Cubes (measures) does this project need?
>  Example: SalesValue, Quantity, Budget.
>  For each: which Entities are dimensions, what is the data type, what is the source?"

**7. Capsule structure**
> "What Capsules does this project need? For each Capsule:
>  - Name and purpose
>  - Which Data Model(s) it uses
>  - Approximate number of Screens"

**8. Procedures needed**
> "Are there any Procedures needed? For each:
>  - Name and purpose
>  - Location: Data Model level (scheduleable) or Capsule level (interactive only)
>  - Approximate steps (e.g. SQL Data Reader → Dataflow, or Go to Screen → Apply Selection)"

**9. Data sources**
> "Where does the data come from?
>  (1) SQL database — specify DB type and table/view names
>  (2) CSV / flat files — specify file names and update frequency
>  (3) SAP / ERP connector
>  (4) Board Public API
>  (5) Manual entry via Data Entry objects
>  [multiple sources allowed]"

**10. Board API access (optional)**
> "Does this project have access to the Board Public API?
>  (OAuth2 Bearer token available?)
>  [default: No — skip API integration unless confirmed]"
If yes: record the Board instance URL in §7. Do NOT record credentials anywhere.
If no: skip API-related questions entirely.

---

## Flow B — Existing Project (Ingestion)

### Step 1 — Collect available files

Ask once:
> "What files can you provide from the existing Board project?
>  (1) Layout XMLs — exported via Board UI (Export Layout to XML)
>  (2) CFG files — Data Reader configurations
>  (3) CSV or TXT exports — Entity members or Cube data
>  (4) Screenshots of Screens
>  (5) Board API access (OAuth Bearer token)
>  Share what you have — I will infer as much as possible and ask only about gaps."

### Step 2 — Parse provided files

Process each file type as follows:

**Layout XML**
Extract: Cube names, Entity names, Data Block configurations, Algorithm text,
Screen names, object types (DataView, Chart, Selector, Gauge, Label).
Note: XML structure varies by Board version — focus on tag names containing
`Cube`, `Entity`, `DataBlock`, `Algorithm`, `Screen`, `Object`.

**CFG files**
Extract: Data Reader type (SQL, CSV, SAP), source connection parameters,
target Cube name, field mappings.

**CSV / TXT exports**
Infer: Entity member names and count, Cube data structure (column = Entity, row = member).

**Screenshots**
Describe: Screen layout, visible object types, navigation elements, filter controls.
Mark all visual inferences as `[inferred — confirm]`.

**Board API** (if credentials provided)
Ask the developer to share the Bearer token only in this message — do not echo it back,
do not log it, do not include it in any generated file (see Security Rules below).
Call these endpoints using WebFetch with the Bearer token:
- `GET {instance_url}/public/{dbName}/schema/Entities` → populate §E Entities
- `GET {instance_url}/public/{dbName}/schema/Cubes` → populate §E Cubes
- `GET {instance_url}/public/capsules/{capsuleName}` → populate §F Capsules
Rate limits: 500 req/day, 10 req/s. Verify the token with a lightweight call first
(e.g. `/public/search/test`) to avoid burning quota on an expired credential.

### Step 3 — Populate §E and §F with [inferred] tags

Every field populated from file ingestion or API data is tagged `[inferred]`.
Every field confirmed by the developer removes the `[inferred]` tag.

Example:
```
| SalesValue | Gross sales amount [inferred] | Product, Customer, Month [inferred] | Numeric [inferred] | SQL Data Reader [inferred] |
```

### Step 4 — Targeted gap questions

After ingestion, ask only about what could not be inferred:
- Missing Entity sources
- Relationship definitions not visible in XML
- Procedure step logic not inferable from configuration
- Time range and granularity if not in the data

### Step 5 — Generate SPEC_RETROACTIVE.md

For existing projects, write SPEC_RETROACTIVE.md (not SPEC.md) using the $docfinal pattern.
Never overwrite an existing SPEC.md.

---

## §E Generation Template

After all Data Model questions are answered, generate §E with this structure:

```markdown
## §E — Board Data Model
**Board version:** [N]
**Environment:** [Cloud / On-premises]
**Data Model name(s):** [names]
**Time Range:** [start – end, granularity]

### Entities
| Entity name | Description | Members (approx.) | Source |
|-------------|-------------|-------------------|--------|

### Relationships (Hierarchies)
| Hierarchy name | Base Entity → Parent → ... → Top |
|----------------|-----------------------------------|

### Cubes
| Cube name | Description | Dimensions | Data type | Source |
|-----------|-------------|------------|-----------|--------|

**§E Status:** Draft
```

Set status to Draft initially. Developer changes to Approved before full $build.
For existing projects with complete ingestion, propose Approved if developer confirms all fields.

---

## §F Generation Template

After Capsule questions are answered, generate §F:

```markdown
## §F — Board Capsule Structure

### Capsules
| Capsule name | Purpose | Primary Data Model | Screens (approx.) |
|--------------|---------|-------------------|-------------------|

### Screens (per Capsule)
| Screen name | Type | Objects | Data Model |
|-------------|------|---------|------------|

### Procedures
| Procedure name | Location | Type | Steps summary | Scheduleable |
|----------------|----------|------|---------------|--------------|

### Masks
| Mask name | Applied to Screens | Contents |
|-----------|-------------------|----------|

**§F Status:** Draft
```

---

## §E Gate Enforcement

Before ending $spec, check §E status:

- **§E empty or missing** → flag: "$build is blocked until §E has at least Draft status."
- **§E Draft** → flag: "$build available in analysis/optimization mode. Full $build requires Approved."
- **§E Approved** → full $build available.

Always surface the gate status explicitly at the end of $spec.

---

## Security Rules (BR-06)

Board API credentials (OAuth client secret, Bearer token) are **never** written to:
- SPEC.md or SPEC_RETROACTIVE.md
- DECISIONS.md
- Any file in the repository

The Board instance URL (non-sensitive) may be recorded in §7.
If a developer accidentally pastes credentials in chat, do not echo them back or store them.
Instruct the developer to use environment variables for any persistent use.
