---
name: pyplan-diagram
description: >
  Pyplan influence diagram expertise. Use when working on the code side of a
  Pyplan application: designing or reviewing nodes, writing node definitions,
  managing dependencies between nodes, using wizards or the Code Assistant,
  structuring modules, or debugging calculation errors. Covers node types,
  the result= convention, pandas and xarray patterns, and diagram best
  practices. Does not cover interface components or dashboard layout —
  use pyplan-interfaces for that.
license: G7 proprietary
metadata:
  author: G7 AI Development
  version: "4.2"
  platform: pyplan
---

# Pyplan Diagram Skill

You are an expert Pyplan developer focused on the code side of a Pyplan
application: the influence diagram, nodes, Python definitions, and
data transformation logic.

---

## 1. Core Mental Model

A Pyplan application has two distinct surfaces:

- **Code surface** — the influence diagram with nodes containing Python logic.
- **Interface surface** — dashboards with components that display node results.

This skill covers the code surface exclusively. When the task involves
components, filters, or visual layout, switch to pyplan-interfaces.

The influence diagram is a **dependency graph**: each node is one step in
a data pipeline. Arrows represent data dependencies — a node can only use
the result of another node if there is an arrow connecting them.

---

## 2. Node Types

| Type | Purpose | Returns |
|------|---------|---------|
| **Variable** | Generic Python logic, most common type | Any Python object |
| **Data Reading** | Connects to external sources (CSV, DB, Excel, API) | DataFrame or xarray |
| **Input — Scalar** | Single user-editable value (rate, flag, threshold) | int, float, str, bool |
| **Input — Selector** | User selects from a list | str or list |
| **Input — Form** | Tabular editable data stored in DB | DataFrame |
| **Input — Cube** | Multidimensional editable data stored in DB | xarray DataArray |
| **Index** | Stores a dimension list (Product, Region, Year) | pandas.Index |
| **Report** | Combines multiple nodes into a structured output | xarray or DataFrame |
| **Button** | Executes code on click (refresh, process trigger) | None (side effects) |
| **Module** | Container grouping other nodes hierarchically | — |
| **Text** | Documentation label only — no code | — |

**Node color in diagram (visual convention):**
- Blue/gray — standard variable or data node
- Red — node with a calculation error
- Green — node evaluated and clean
- Orange — input node awaiting user value

---

## 3. The result= Convention

Every codable node must assign its final output to `result`.
Pyplan uses the value of `result` as the node's output for downstream nodes
and for interface components.

```python
# Correct — all local variables prefixed with _
_columns = ["product", "region", "sales"]
_data = [
    ["Product A", "North", 1200],
    ["Product B", "South", 850],
]
_df = pd.DataFrame(_data, columns=_columns)

result = _df
```

**Rules:**
- Local variables always start with `_` (e.g. `_df`, `_data`, `_mask`).
- The last meaningful line must be `result = <variable>`.
- Never assign `result` mid-function and then continue — it will be
  overwritten or cause confusion.
- Nodes that produce no output (Button) set `result = None`.

**Common error:** forgetting `result =` entirely. The node evaluates but
returns `None`, and downstream nodes fail silently or show empty data.
Always verify `result =` is present on QA.

---

## 4. Dependency Design

### 4.1 Declaring dependencies
A node can reference another node's result directly by its node ID:

```python
# Node "sales_filtered" references node "sales_raw"
_mask = sales_raw["region"] == "North"
result = sales_raw[_mask]
```

The arrow in the diagram is drawn automatically when you reference another
node's ID in the code. If no arrow exists, the reference will fail at runtime.

### 4.2 Dependency best practices
- Keep the dependency graph **acyclic** — circular dependencies cause
  infinite recalculation loops and crash the model.
- Keep node logic **focused** — one transformation per node, not a
  monolithic node that does everything.
- Name nodes with **snake_case** that describes their output content
  (e.g. `sales_by_region`, `cost_variance_ytd`), not their operation
  (e.g. `calculate_stuff`).
- Use **Module nodes** to group related nodes — it reduces diagram clutter
  and makes navigation easier for the next developer.

### 4.3 Detecting circular dependencies
Symptoms: the model freezes on evaluation, or a node shows a "circular
reference" error. Resolution: trace the dependency chain backwards from
the failing node. Remove the cycle by introducing an intermediate input
node that breaks the loop.

---

## 5. Data Types: pandas vs xarray

### 5.1 pandas DataFrame
Use for: tabular data with rows and columns (transaction records,
flat exports from DB, form inputs).

```python
import pandas as pd

_df = pd.read_csv("data/sales.csv")
_df["date"] = pd.to_datetime(_df["date"])
_df = _df[_df["year"] == 2025]

result = _df
```

### 5.2 xarray DataArray / Dataset
Use for: multidimensional data with named dimensions and coordinates
(sales by Product × Region × Month, budget cubes, planning matrices).

```python
import xarray as xr
import pandas as pd

_df = sales_by_region  # upstream node result (DataFrame)
_da = xr.DataArray(
    _df.pivot(index="month", columns="region", values="sales"),
    dims=["month", "region"]
)

result = _da
```

**Decision rule:** if the data has more than two natural dimensions,
use xarray. If it's a flat table or the downstream node is a Form,
use DataFrame.

### 5.3 Index nodes and xarray alignment
Index nodes store dimension lists used across the model. When a DataArray
uses an Index node as a dimension, changes to the index (adding a new
region, changing a year range) propagate automatically to all dependent
DataArrays. This is the primary reason to use Index nodes rather than
hardcoding dimension lists.

---

## 6. Data Reading Nodes

### 6.1 Wizard-based setup (preferred)
For CSV, Excel, and common DB connections, use the **Data Reading Wizard**:
1. Create a Data Reading node.
2. Right-click → Wizard → select source type.
3. Configure connection parameters.
4. The wizard generates the Python code automatically.

Always review the generated code — wizards produce correct but sometimes
verbose code. Simplify if the pattern is cleaner.

### 6.2 Manual DB connection pattern
```python
import pandas as pd

_query = """
    SELECT product_id, region, SUM(amount) as total_sales
    FROM sales_fact
    WHERE year = 2025
    GROUP BY product_id, region
"""
# Connection object defined in a parent module node (connection_db)
result = pd.read_sql(_query, connection_db)
```

**Data contract alignment:** the fields selected in the query must match
what is documented in §A (Data Architecture) of the SPEC. If a field
is missing or has a different name, log it in §B (Discovery Log) before
proceeding. See CLAUDE.md data delta handling rules.

### 6.3 Performance considerations
- Always filter at the source (WHERE clause in SQL, not post-load in Python).
- Avoid loading entire tables when only aggregates are needed.
- For large DataFrames (>500k rows), prefer xarray aggregation over
  pandas groupby chains — xarray is vectorized and significantly faster.

---

## 7. Wizards and Code Assistant

### 7.1 DataFrame Wizards
Available when a node returns a DataFrame. Access via node toolbar →
**Handling Data**. Available wizards:

| Wizard | What it does |
|--------|-------------|
| Select columns | Keep only specified columns |
| Filter rows | Apply condition-based row filter |
| Group / Aggregate | groupby + aggregation function |
| Calculated field | Add a new computed column |
| Sort | Order by one or more columns |
| Join / Merge | Merge two DataFrames |
| Pivot / Unpivot | Reshape table structure |

Wizards generate Python code in the node definition. Always review the
generated code and remove any redundant steps.

### 7.2 Code Assistant
The Code Assistant (available in the node toolbar) generates node code
from a natural language description. Use it for:
- Complex transformations where the pandas/xarray syntax is unclear.
- Generating boilerplate for new node types.

**Important:** the Code Assistant does not know the context of other nodes
in the diagram. Always review generated code to ensure it references the
correct upstream node IDs and uses the project's naming conventions.

---

## 8. Module Structure Best Practices

Organize nodes into modules by functional area. Recommended structure:

```
App root
├── 00_connections      ← DB connections, file paths, credentials
├── 01_inputs           ← all Input nodes (scalar, selector, form, cube)
├── 02_indexes          ← all Index nodes
├── 03_data             ← Data Reading nodes and raw data processing
├── 04_calculations     ← business logic transformations
├── 05_outputs          ← Report nodes and final outputs for interfaces
└── 99_utilities        ← helper functions, constants, shared logic
```

**Rule:** no node in `04_calculations` should connect directly to a DB
or file source — that is the responsibility of `03_data`. This separation
makes debugging and data source changes significantly easier.

---

## 9. QA Checklist — Diagram Surface

Run these checks on every $qa for Pyplan projects (contributes to Layer 5):

- [ ] All new nodes have `result =` assigned as the final line
- [ ] No circular dependencies introduced (verify with diagram inspection)
- [ ] Node naming follows snake_case and describes the output content
- [ ] Local variables use `_` prefix consistently
- [ ] Data Reading nodes align with §A data contract (field names, source)
- [ ] Any data delta from §A is logged in §B and DECISIONS.md
- [ ] Module organization follows the project's established structure
- [ ] No monolithic nodes — each node has a single, focused responsibility
- [ ] Index nodes are used for dimensions instead of hardcoded lists
- [ ] Large data operations filter at source, not post-load

---

## 10. Common Errors and Fixes

| Error | Likely cause | Fix |
|-------|-------------|-----|
| Node result is None | Missing `result =` line | Add `result = <variable>` as last line |
| Downstream node shows KeyError | Column name mismatch vs upstream | Check actual column names with `.columns` |
| Model freezes on evaluation | Circular dependency | Trace dependency chain, break cycle with input node |
| xarray dimension mismatch | Index node changed, DataArray not updated | Re-evaluate affected DataArrays |
| DB connection fails | Credentials or connection string changed | Check `00_connections` module node |
| Wizard generates incorrect groupby | Multi-level aggregation | Review and simplify generated code manually |
