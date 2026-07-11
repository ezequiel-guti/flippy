# Pyplan MCP Skill
# SDAD v6 — .claude/skills/pyplan/mcp/SKILL.md
# G7 AI Development Methodology
# On-demand skill — loads when @mcp_tool, MCP tools, dynamic tools, §D, or
# mcp_tool decorator are detected in a Pyplan project context.

---

## Role

Pyplan MCP Engineer. Specialist in designing, implementing, and auditing
`@mcp_tool` nodes in Pyplan applications. Familiar with the Pyplan MCP server
(v1), OAuth 2.1 integration, dynamic tool discovery, and the constraints of
serializable return values.

Active during all phases where MCP tools are in scope: $spec (§D), $build
(MCP surface checklist), $qa (Layer 1 MCP security + Layer 5 MCP checks).

---

## Context

Pyplan MCP (v1) allows AI clients to connect to a running Pyplan instance,
discover application-specific tools, and execute them. Dynamic tools are
defined inside Pyplan nodes using the `@mcp_tool` decorator from
`pyplan_core.classes.ai.Agent`. They become visible to MCP clients only when
the target application is open.

**This is a v1 server.** Treat it as an external dependency that may change
across Pyplan updates. Flag it in §7 and $verify accordingly.

---

## §D — MCP Tools Catalog

§D is the gate section for Pyplan projects that expose MCP tools.
It must be approved before $build is allowed (same gate logic as §A).

### §D structure (one entry per @mcp_tool node)

| Field | Description |
|-------|-------------|
| Node identifier | The node name in the Pyplan application |
| Tool name | Human-readable name (also used as MCP identifier) |
| Description | What the tool does — written for an external LLM to understand |
| Parameters | Name, type, Annotated description for each parameter |
| Return type | Python type + serialization notes |
| Status | Draft / Approved |

### When to create §D

Ask during $spec: "Does this project expose any nodes as MCP tools (@mcp_tool)?"
- Yes → create §D, set gate, add to $build block check.
- No → skip §D entirely. Do not create the section.

---

## @mcp_tool Pattern

### Canonical implementation

```python
from pyplan_core.classes.ai.Agent import mcp_tool
from typing import Annotated

@mcp_tool
def _fn(
    param_one: Annotated[float, 'Clear description of what this parameter represents'],
    param_two: Annotated[str, 'Clear description — include format constraints if any'],
) -> dict:
    """
    One-paragraph docstring. Explain what the tool does, what it returns,
    and any business context an external LLM needs to invoke it correctly.
    This docstring is used by MCP clients to generate the tool schema.
    """
    # implementation
    return {
        'key': value,  # all values must be JSON-serializable
    }

result = _fn  # assign function, do not call it
```

### Rules (enforced by MCP surface checklist and QA Layer 5)

1. Import: `from pyplan_core.classes.ai.Agent import mcp_tool`
2. Decorator: `@mcp_tool` on the function definition
3. Parameters: every parameter must use `Annotated[type, 'description']`
4. Docstring: must explain what the tool does and what it returns — written for
   an external LLM, not just for a human reading the code
5. Return: plain Python dict, list, or scalar — must be JSON-serializable
   - No raw `xarray.DataArray` or `xarray.Dataset`
   - No bare `pandas.DataFrame` — use `.to_dict(orient='records')` or similar
   - No objects that require custom serialization
6. Assignment: `result = _fn` — assign the function, never call it
7. No side effects that depend on interactive agent state or session context

### Common mistakes

| Mistake | Correct |
|---------|---------|
| `result = _fn()` | `result = _fn` |
| `param: float` (no Annotated) | `param: Annotated[float, 'description']` |
| Returns a DataFrame directly | Returns `df.to_dict(orient='records')` |
| Vague docstring ("converts data") | Precise docstring with business context |
| Tool reads from mutable session state | Tool uses only its declared parameters |

---

## Build-via-AI Protocol

When using Pyplan MCP's build/modify capabilities (natural-language edits to
a running Pyplan instance), SDAD enforces the same discipline as $build:

1. Spec approved → build/modify allowed. Not approved → redirect to $spec.
2. Announce the modification as an increment before executing.
3. Wait for developer approval.
4. After execution: DECISIONS.md entry + §13 update.
5. Run $qa on the modified increment.
5.5. After $qa passes, export the Pyplan model snapshot (see Model Snapshot
   Convention below) and include it in the increment's atomic commit.
6. Run MCP surface checklist on any @mcp_tool node touched.
7. If the modification created or changed an HTML interface (the default
   interface type for AI-built screens), run the HTML interface surface
   checklist (pyplan-interfaces skill, section 11.8).

### Model Snapshot Convention

After $qa passes on a Build-via-AI increment, export the Pyplan model:

```
Path:    .sdad/pyplan-snapshots/YYYYMMDD-incN-slug.ppl
Naming:  date in YYYYMMDD - inc + zero-padded number - short feature slug
Example: .sdad/pyplan-snapshots/20260625-inc03-revenue-nodes.ppl
```

Export mechanism (Pyplan MCP v1):
- If the MCP exposes an export/snapshot endpoint: use it and note the endpoint
  name in §7.
- If not (v1 current behavior): export manually from the Pyplan UI before
  committing. The step is still mandatory.

The snapshot is committed in the same atomic commit as DECISIONS.md and the §13
update. One commit = one increment = one known model state.

Recovery: to restore a prior increment's model state, load the corresponding
.ppl file in Pyplan. Git history gives the full restore timeline. No GitHub
required — local git commits are sufficient for recovery.

---

## $qa Integration

### Layer 1 — Security (MCP-specific checks)
- P0: OAuth token not logged or stored in node results
- P1: @mcp_tool parameters validated — no path to arbitrary code execution
- P2: Exposed tools have minimum necessary scope per §D contract

### Layer 5 — Platform (MCP-specific checks)
- All nodes in §D have @mcp_tool decorator and result = _fn
- All parameters use Annotated[...] with non-empty descriptions
- Docstrings precise enough for an external LLM to invoke correctly
- Return values verified serializable
- No tool depends on interactive agent behavior or mutable session state
- Snapshot: .sdad/pyplan-snapshots/ contains a .ppl file for this Build-via-AI
  increment, named correctly (YYYYMMDD-incN-slug.ppl), present in the staged commit

---

## $verify — MCP Server Dependency

Always include in §7 when §D is present:

```
| Pyplan MCP server | /ai/mcp | Dynamic tool execution — v1 (first release,
  API may change across Pyplan updates). Lock Pyplan version in §5 if
  MCP stability is critical. |
```

Export capability: check whether the installed Pyplan version exposes a model
export endpoint via MCP. If yes, document it in §7 and use it in the snapshot
step. If not, the export is manual (Pyplan UI) — the snapshot step is still
mandatory.

---

## Lesson Capture Triggers (MCP-specific)

Propose a lesson candidate after $qa when:
- A serialization error was found in a return value
- A parameter description was too vague and caused incorrect tool invocation
- A `result = _fn()` vs `result = _fn` mistake caused a silent failure
- A tool exposed more data than its declared contract (scope creep)

Category for all Pyplan MCP findings: **Pyplan**

---

## MCP Read-Access — Evidence Acquisition for $audit (v6, I1)

Beyond the producer role above, the MCP also serves as a **read path** for the
`$audit` lifecycle. A Pyplan model is server-side; the auditor cannot read it as
files. When the client instance exposes MCP read endpoints, this skill is the
defined way to acquire model evidence (acquisition path (b) in
`.sdad/audit/SCHEMA.md`; `.ppl` export is the primary path (a), MCP read is the
enhancement — BR-01).

Read-access protocol:
- Discover the model graph via the instance's MCP read endpoints (node ids,
  types, dependencies, `result=` presence, `@mcp_tool` decoration).
- Map each node into the `node-graph.json` schema (id, type, has_result_assigned,
  dependencies, code_snippet, mcp_decorated).
- Whatever the MCP does not expose (e.g. interface internals, DB credentials) is
  declared as a gap with `status: not_assessable` — never inferred.
- MCP availability is per-instance and not guaranteed. If read endpoints are
  absent, fall back to `.ppl` export or manual acquisition and record the path
  used in the evidence manifest.

Security on read: the auditor never logs or stores OAuth tokens in the evidence
(Layer 1, P0). Evidence under `.sdad/audit/<project>/evidence/` must be free of
tokens, credentials, and PII.

---

## Auditing Exposed MCP Tools — $audit Producer Context (v6, I2)

In `$audit`, the producer-context checks above are run against a model the team
did **not** build. The deterministic detections are mechanized in
`.sdad/audit/lib/mcp_lint.py` (invoked via `checks/mcp-tool-audit`), so the
auditor consumes findings rather than re-detecting them by eye (BR-04). The lint
parses the Python with an AST — the checks are real, not regex guesses.

Unified severity mapping (BR-03):

| Finding | Band | Rule |
|---------|------|------|
| `result = fn()` — function called, not assigned | CRITICAL | 6 (silent failure of the whole tool) |
| OAuth token logged or surfaced in a node result | CRITICAL | Layer 1 P0 |
| Parameter untyped, or typed but not via `Annotated[...]` | HIGH | 3 |
| Likely non-serializable return (DataFrame/xarray, no conversion) | HIGH | 5 (medium confidence — labeled) |
| Tool exposes more than its declared §D contract (scope creep) | MEDIUM | Layer 1 P2 |
| Missing or trivial docstring | MEDIUM | 4 |

`mcp_lint.py` covers the mechanical rows (CRITICAL result-called, HIGH untyped /
non-annotated param, HIGH non-serializable return, MEDIUM weak docstring). Token
exposure and scope creep require reading the node logic + §D contract and are
judged by the auditor, not the lint. Every non-serializable-return finding
carries a confidence label — a static heuristic raises the floor, it does not
replace a human read for a borderline case.

---

G7 AI Development Methodology | SDAD v6
Pyplan MCP Skill — .claude/skills/pyplan/mcp/SKILL.md
