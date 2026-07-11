---
name: decision-architecture
description: >
  Activate this skill when any architectural decision needs to be made about
  how data is structured, stored, moved, or accessed in a project. Use when
  the user asks "how should we structure this data", "where should this live",
  "should we use a flat file or a database", "how do we handle this data flow",
  or any variant of choosing between data architecture options. Also activate
  when reviewing SPEC §4 (Data Model) or §5 (Technical Architecture), when a
  $build increment introduces a new data structure, or when a structural delta
  is flagged during build. Platform-agnostic — applies to Pyplan models,
  Python scripts, APIs, and any other stack.
---

# SKILL: decision-architecture
# Version: 1.0 | SDAD v4.2
# Layer: Transversal — Platform-Agnostic Data Architecture
# Activation: any project; triggered by architectural decision points

---

## Purpose

This skill provides a structured decision framework for data architecture choices.
It does not prescribe specific technologies — it guides the reasoning process that
leads to the right choice for the project's context.

Base version built from general best practices. Will be enriched with G7-specific
patterns after the first real client engagement (C-020 deferred input session).

---

## When This Skill Activates

This skill contributes to two types of situations:

**Decision point** — a new architectural choice must be made:
- Choosing between storage options (file, database, in-memory, platform-native)
- Choosing how to model a domain entity or dimension
- Choosing where transformation logic lives (source, intermediate, output)
- Choosing how data flows between modules or systems

**Review point** — an existing architecture must be evaluated:
- SPEC §4 or §5 review
- QA finding on data structure
- Structural delta during $build

---

## Decision Framework

### Step 1 — Characterize the data

Before choosing an architecture, answer these four questions:

| Question | Why it matters |
|----------|---------------|
| What is the read/write ratio? | High-read, low-write → optimize for read; frequent writes → optimize for mutation |
| How often does the structure change? | Stable → normalize; volatile → keep flexible |
| Who consumes it and how? | End-user report → flat; programmatic → normalized; both → two layers |
| What is the volume? | Rows × columns × refresh frequency → determines if file, DB, or platform-native |

Emit a CHARACTERIZATION block before recommending:

  📊 DATA CHARACTERIZATION
  Read/write ratio:     [read-heavy / write-heavy / balanced]
  Structure stability:  [stable / evolving / unknown]
  Consumers:           [end-user / programmatic / both]
  Volume:              [small <10k rows / medium 10k-1M / large >1M]

### Step 2 — Identify the decision category

| Category | Description | Typical signal |
|----------|-------------|---------------|
| Storage location | Where does the data physically live? | "Should this be a file or a table?" |
| Normalization level | How much should we split or flatten? | "Should accounts be a separate table?" |
| Transformation layer | Where does the calculation happen? | "Should we compute this in the source or in the model?" |
| Dimension design | How are shared dimensions structured? | "Time dimension — shared or per-module?" |
| Refresh strategy | When and how does data update? | "Should this recalculate on every open?" |
| Data contract | What is the interface between layers? | "What format does the model expect as input?" |

### Step 3 — Apply the relevant pattern

---

#### PATTERN: Storage Location

**Signals for file-based (CSV, XLSX, JSON):**
- Data is produced externally and delivered manually
- Volume is small (<50k rows)
- No concurrent writes
- Recipient system (Pyplan, Python script) reads once per session

**Signals for database:**
- Data is written by multiple sources or in real time
- Historical snapshots are required
- Concurrent read access
- Data is shared across multiple projects

**Signals for platform-native (Pyplan nodes, in-memory):**
- Data is computed, not stored
- Result depends on user selections (dynamic)
- Lifetime is session-scoped

**Decision rule:** use the simplest option that meets the access pattern. File → DB → platform-native in order of complexity. Don't add infrastructure that isn't needed today.

---

#### PATTERN: Normalization Level

**Normalize when:**
- The same entity appears in multiple places (accounts, cost centers, products)
- The entity will change over time (new accounts added, renamed)
- Multiple modules share the dimension

**Flatten when:**
- The data is consumed by a reporting tool that can't join
- Performance matters more than maintainability
- The structure will not change during the project lifetime

**For Pyplan specifically:** shared dimensions (time, accounts, org units) should always be defined in a single dimension module and referenced — never duplicated. Flat output views are acceptable at the presentation layer only.

---

#### PATTERN: Transformation Layer

| Layer | Put here | Avoid here |
|-------|----------|-----------|
| Source (raw data) | Nothing — preserve as received | Any transformation |
| Staging | Type casting, null handling, standard column names | Business logic |
| Business logic | Calculations, allocations, derived metrics | UI formatting |
| Presentation | Formatting, aggregation for display | Recalculation |

**Rule:** each layer should be independently testable. If a transformation can't be explained without referencing another layer, it's in the wrong place.

---

#### PATTERN: Dimension Design

| Dimension type | Design recommendation |
|----------------|----------------------|
| Time | Single source, ISO format, never hardcoded year ranges |
| Accounts / chart of accounts | Hierarchical structure; leaf nodes for transactions, parent nodes for aggregation |
| Org units (cost centers, entities) | Same as accounts — hierarchical, single source |
| Product / SKU | Flat if stable; hierarchical if categorization is used in reporting |
| Custom (project-specific) | Define at spec time; document any hierarchy |

**Red flags:**
- Time dimension defined per-module (causes calendar drift)
- Account codes hardcoded in formula nodes (breaks when chart of accounts changes)
- Org hierarchy duplicated in multiple modules (maintenance nightmare)

---

#### PATTERN: Data Contract

A data contract defines the expected format at a layer boundary.
It must be documented in SPEC §7 (for external sources) or §4 (for internal).

Minimum contract definition:
```
CONTRACT: [name]
Direction:   [source → target]
Format:      [CSV / XLSX / JSON / DataFrame / Pyplan node]
Columns:     [name | type | nullable | example]
Refresh:     [manual / scheduled / on-demand]
Owner:       [who produces this data]
Validated:   [yes / no — if yes, how]
```

If a data contract is missing at $build time, add it to §12 (Open Decisions)
and flag as a potential blocker before writing code that depends on it.

---

### Step 4 — Document the decision

Every architectural decision made using this skill must be logged.

In SDAD projects: write to `DECISIONS.md` (CC) or `DECISIONS_[CLIENT].md` (hub).

Entry format:
```
## DA-XX — [Decision title]
Date: [YYYY-MM-DD]
Status: APPROVED / SUPERSEDED / DEFERRED

Context:
  [One paragraph — what situation forced this decision]

Options considered:
  A. [description] — [tradeoff]
  B. [description] — [tradeoff]
  C. [description] — [tradeoff]

Decision: Option [X]

Rationale:
  [Why this option for this project. Reference the characterization step.]

Consequences:
  [What this decision makes easier / harder downstream]

Review trigger:
  [Condition that should reopen this decision — e.g., "volume exceeds 500k rows"]
```

Findings numbered DA-01, DA-02... independently from H-XX and PP-XX.

---

## Anti-Patterns to Flag

Flag these immediately when detected, regardless of phase:

| Anti-pattern | Signal | Risk |
|---|---|---|
| Hardcoded dimension values | Year, account code, or org unit as a literal string in logic | Breaks when structure changes |
| Transform-at-source | Business logic applied before data enters the model | Untestable, invisible to QA |
| Shared mutation | Two modules write to the same data object | Race conditions, unexpected state |
| Missing null strategy | No documented handling for missing data | Silent wrong results |
| Implicit contract | Layer boundary with no documented expected format | Breaks on data change, hard to debug |
| Single flat file for everything | All data concatenated in one file/table | Performance degrades, no layer separation |

---

## Integration with $spec and $build

**During $spec:**
- When §4 (Data Model) is being defined: apply the characterization step to each entity
- When §7 (Integrations) is being defined: require a data contract for each source
- Flag any dimension that will be shared across modules — recommend centralization early

**During $build:**
- When a new data structure is introduced: check against the documented contract
- When a structural delta occurs: apply this framework to evaluate options before reopening §12
- When a Pyplan node reads from multiple sources: verify dimension alignment

**During $qa:**
- Check that every layer boundary has a documented contract (PP or H finding if missing)
- Check that shared dimensions are not duplicated (PP finding if they are)
- Check that no hardcoded dimension values exist in logic nodes

---

## Note on G7 Enrichment (C-020)

This skill is built from general best practices. The following areas are intentionally
left as placeholders until the G7 input session runs:

- G7 standard naming conventions for data layers
- Preferred stack choices per project type (specific technology recommendations)
- Client-specific patterns observed across engagements
- Reusable dimension templates from completed projects

When the G7 input session runs, enrich this skill with those patterns and bump to v1.1.
