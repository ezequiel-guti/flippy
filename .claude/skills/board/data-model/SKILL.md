# SKILL: Board Data Model
# On-demand skill — loaded when entity, cube, relationship, dimension, or §E is mentioned.
# Role: Entities, Relationships, Cubes, Data Readers, Algorithm syntax, SQL generation.
# Version: 5.2 | 2026

---

## Role

This skill provides expertise for designing and building the Board Data Model layer.
It covers the full back-end of a Board project: Entities, Relationships, Cubes,
Data Readers, and Algorithms.

Triggered by keywords: entity, cube, relationship, dimension, §E, data model, data reader,
algorithm, SQL reader, dataflow, hierarchy.

---

## Creation Order — Enforced Rule (BR-05)

Board enforces a strict creation order. Violating it causes dimension binding errors
that surface only when a Cube is created, making them hard to trace back.

```
1. Entities        — define dimensions first
2. Relationships   — define hierarchies between existing Entities
3. Cubes           — reference Entities as dimensions; source from Data Readers or Algorithms
```

Always verify this order before announcing a $build increment. If an increment would
create a Cube before its Entities exist, block the increment and resequence.

---

## Entities

An Entity is a dimension — the "who, what, when" axis of a Cube.

### Design guidelines

- **Time Entity:** almost every Board Data Model needs a time Entity (Month, Week, or Day).
  Board has a built-in time Entity type — prefer it over custom-loading date members.
- **Member count:** estimate members per Entity. High member counts (>10,000) increase
  Cube density and memory use — flag when this threshold is approached.
- **Source:** each Entity loads members from one source: SQL query, CSV file, or manual entry.
  Document source type and connection in §E.
- **Naming:** use singular nouns (Product, Customer, Month) — not plurals or abbreviations.

### $build artefact: Entity load CSV

When a CSV is needed to load Entity members:
```
Column 1: member code (unique identifier)
Column 2: member description
Additional columns: attributes (optional, for use in Relationships or display)
```
Validate that member codes are unique and non-empty before delivering the artefact.

### $build artefact: SQL Entity loader

When members load from SQL:
```sql
-- Entity: [EntityName]
-- Source: [database / schema / table or view]
SELECT
    [code_column]   AS MemberCode,
    [desc_column]   AS MemberDescription
    [, attribute_columns as needed]
FROM [source_table_or_view]
WHERE [filter_condition if any]
ORDER BY [sort_column]
```
Always include an ORDER BY — Board loads members in the order returned.

---

## Relationships (Hierarchies)

A Relationship defines a parent-child hierarchy between two Entities.

### Design guidelines

- A Relationship requires both Entities to exist first.
- Direction: child Entity → parent Entity (e.g. Product → Category).
- Multi-level: a single Relationship can chain multiple levels
  (e.g. Product → Category → Division → All).
- **Fan-out:** a single Entity can participate in multiple Relationships
  (e.g. Product → BrandHierarchy and Product → ChannelHierarchy).
  This is valid but increases Cube complexity — note it in DECISIONS.md.
- Circular relationships are not allowed — flag immediately.

### $build artefact: Relationship load CSV

```
Column 1: child member code
Column 2: parent member code
```
Validate: no orphan children (parent code must exist in parent Entity),
no circular chains, no duplicate child entries within the same Relationship.

---

## Cubes

A Cube stores numeric data at the intersection of one or more Entity dimensions.

### Design guidelines

- **Dimension count:** keep dimensions ≤ 5 per Cube where possible.
  Each added dimension multiplies the potential cell count — sparsity grows exponentially.
- **Sparsity:** if most cells would be empty (e.g. not every Product sells in every Region
  every Month), consider splitting into smaller Cubes or using Dataflow aggregation.
- **Data type:** Numeric (default), Text (limited use — no aggregation), or Date.
- **Writeable Cubes:** Cubes used for Data Entry must be explicitly marked as writeable
  in the Data Model configuration.

### $build artefact: Cube load CSV

When a CSV loads initial Cube data:
```
Columns: one column per Entity dimension (member codes), one column for the value
```
Example for SalesValue [Product, Month]:
```
ProductCode,MonthCode,SalesValue
P001,2024-01,12500.00
P001,2024-02,11800.00
```

---

## Data Readers

A Data Reader loads data from an external source into one or more Cubes.
It runs as a Step inside a Procedure (typically a Data Model-level Procedure).

### Data Reader types

| Type | Use case | Key parameters |
|------|----------|---------------|
| SQL Data Reader | Relational database | Connection string, SQL query, target Cube, field mappings |
| CSV Data Reader | Flat file import | File path, delimiter, header row, target Cube |
| SAP Data Reader | SAP ERP | RFC connection, function module, field mappings |
| Dataflow | In-memory aggregation from other Cubes | Source Cube(s), aggregation logic, target Cube |

### $build artefact: SQL Data Reader spec

```
Data Reader name: [name]
Type: SQL
Target Cube: [CubeName]
Source: [database type] — [server/schema]

SQL query:
  SELECT
      [entity_col_1]  AS [EntityName1],
      [entity_col_2]  AS [EntityName2],
      [measure_col]   AS Value
  FROM [source_table]
  WHERE [filter]

Field mappings:
  [entity_col_1] → Entity: [EntityName1]
  [entity_col_2] → Entity: [EntityName2]
  Value          → Cube: [CubeName]

Procedure location: Data Model level — [ProcedureName]
Scheduleable: [Yes / No]
```

---

## Algorithms

An Algorithm is a formula assigned to a Cube that computes its values from
other Cubes, constants, or built-in Board functions.

### Syntax rules (BR-03)

Board Algorithms use **positional block letters** as operands. The letters map to
Cubes referenced in the Algorithm definition, in the order they are listed.

```
a  →  first referenced Cube
b  →  second referenced Cube
c  →  third referenced Cube
... and so on
```

**Valid formula examples:**
```
a + b                    -- sum of two Cubes
a - b                    -- difference
a / b * 100              -- percentage (note: always guard against division by zero)
dt(a, b)                 -- Board time function (see built-in functions below)
```

**Common mistake — do NOT use variable names:**
```
SalesValue / Budget * 100   -- WRONG: Board does not recognize named references
a / b * 100                 -- CORRECT
```

### Built-in Board functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `dt()` | `dt(cube, periods)` | Delta over time: value minus value N periods ago |
| `rt()` | `rt(cube, periods)` | Running total over N periods |
| `gt()` | `gt(cube)` | Grand total across all members of a dimension |
| `@DATE` | `@DATE` | Current date (system) |
| `@MONTH` | `@MONTH` | Current month number |
| `@YEAR` | `@YEAR` | Current year number |

Flag any function not in this list — it may be version-specific or invalid.
Always validate Algorithm syntax before marking an increment complete.

### Division-by-zero guard

When an Algorithm divides by a Cube (operand b, c, etc.), always flag the risk:
> "This Algorithm divides by [CubeName]. If [CubeName] contains zero values,
> Board will return zero (not an error) — verify this is the intended behavior."

### $build artefact: Algorithm spec

```
Cube: [TargetCubeName]
Algorithm formula: a / b * 100
Operand mapping:
  a → [SourceCube1]
  b → [SourceCube2]
Business meaning: [one-line description]
Division-by-zero risk: [Yes / No — if Yes, note expected behavior]
```

---

## §E Completeness Check

Before approving §E, verify:

- [ ] All Entities listed with source and approximate member count
- [ ] All Relationships defined with full chain (child → ... → top)
- [ ] All Cubes listed with dimensions, data type, and source
- [ ] No Cube references an Entity not listed in the Entities table
- [ ] Creation order respected in the build sequence: Entities before Relationships before Cubes
- [ ] Time Entity present (flag if absent and project involves time-series data)
