# SDAD v6 -- Audit Evidence Schema and Acquisition Protocol (I1)

This file defines HOW the `$audit` lifecycle acquires a representation of a
server-side Pyplan model, where the evidence lands, and the exact structure of
the two evidence artifacts. It is the contract between the evidence-acquisition
layer (I1) and every downstream audit dimension.

A Pyplan application is not a file repo: it lives server-side (nodes,
interfaces, DB connections). A file-based agent cannot read it without an
evidence-acquisition step. The auditor NEVER assumes the model is inspectable
as code, and NEVER fabricates a node graph it could not acquire.

---

## 1. Acquisition paths (priority order)

| Order | Path | Status in v6 |
|-------|------|--------------|
| (a) | `.ppl` export parsed to `node-graph.json` | STUB (BR-17): the `.ppl` binary format is unverified and no real fixture exists, so the parser is documented but NOT implemented. Until a real `.ppl` is supplied and the parser validated, a supplied `.ppl` is declared `not_assessable` -- never parsed with a guessed format. |
| (b) | Pyplan MCP read endpoints | Performed by the auditor via the `pyplan-mcp` skill when the instance exposes read endpoints (per-instance; not universal). The result populates `node-graph.json`. |
| (c) | Manual fallback | The developer supplies `node-graph.json` directly (hand-built from the Pyplan UI / screenshots). Always available. |

`.ppl` export is the PRIMARY documented path and MCP read is the enhancement
(BR-01); but in v6 the deterministic, always-working path is (c) manual, which
the schema below validates.

---

## 2. Output location

```
.sdad/audit/<project>/evidence/
  node-graph.json   -- machine-readable model representation (validated by checks/audit-evidence)
  manifest.md       -- human-readable evidence manifest (what was acquired, how, gaps)
```

Local trusted files only (mirror the DOCUMENT INGESTION pattern). Evidence must
contain no OAuth tokens, credentials, or PII.

---

## 3. node-graph.json schema

```json
{
  "project": "string (project slug)",
  "acquired_at": "YYYY-MM-DD",
  "acquisition_path": "ppl-export | mcp-read | manual",
  "pyplan_version": "string | unknown",
  "nodes": [
    {
      "id": "string (non-empty node identifier)",
      "type": "data | function | interface | input",
      "has_result_assigned": true,
      "dependencies": ["node-id", "node-id"],
      "code_snippet": "string (first ~10 lines of node code)",
      "mcp_decorated": false
    }
  ],
  "gaps": [
    {
      "area": "string (what could not be acquired)",
      "reason": "string (why)",
      "status": "not_assessable"
    }
  ]
}
```

### Validation rules (enforced by `checks/audit-evidence`)
- All six top-level keys present.
- `acquisition_path` is one of `ppl-export | mcp-read | manual`.
- Each node carries all six keys; `type` is one of `data | function | interface | input`;
  `has_result_assigned` is a JSON boolean; `id` is non-empty.
- Each gap carries `area`, `reason`, and `status` exactly equal to `not_assessable`.
- `nodes` may be empty (an audit that acquired no nodes) -- in that case the
  `gaps` array must explain why (the missing-acquisition case).

The check is deterministic (BR-04): the LLM auditor consumes valid evidence; it
does not re-validate structure.

---

## 4. manifest.md

Human-readable header for the audit report. Required fields:
- **Project:** slug
- **Acquired At:** YYYY-MM-DD
- **Acquisition Path:** ppl-export | mcp-read | manual
- **Pyplan Version:** string | unknown
- **Node Count:** integer
- **App Access:** true | false (required for usability dimension, BR-12)
- **Usability:** convention-only (no live walkthrough performed) | live walkthrough performed
- **Gaps:** table listing un-acquired areas (area, reason, status: not_assessable)

Gaps are the areas the audit reports as "not assessable" -- they are findings, never
silent skips. `App Access: false` signals Tier B usability (convention-only) and must
appear explicitly; absent = declare it missing as a gap.

---

## 5. The not-assessable rule

When an area cannot be acquired (no `.ppl`, MCP read unavailable, format
unverified), it is recorded as a gap with `status: not_assessable` and surfaced
in the report. The audit never guesses, never fabricates, and never silently
omits an un-acquired area.

---

G7 AI Development Methodology | SDAD v6 | Audit Evidence Schema (I1)
