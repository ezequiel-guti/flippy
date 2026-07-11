---
name: pyplan-qa-platform
description: >
  Activate this skill for any QA, review, or validation task on a Pyplan project.
  Use when the user runs $qa on a Pyplan increment, asks to review a node, module,
  diagram, or interface built in Pyplan, needs to validate that a model follows
  platform conventions, or wants to confirm that a Pyplan build is client-ready.
  This skill extends the SDAD base QA protocol with Pyplan-specific checks.
  Trigger even when the user says "review this", "check this", or "does this look
  right" inside a Pyplan project context.
---

# SKILL: pyplan-qa-platform
# Version: 1.1 | SDAD v4.3
# Layer: Pyplan Platform — QA & Validation
# Activation: always active when pyplan-qa-platform is loaded; complements base SDAD $qa

---

## Purpose

This skill extends the SDAD base QA protocol with Pyplan-specific checks.
It does not replace the base 6-layer QA — it adds a 7th layer and injects
platform-specific rules into the existing layers.

Base QA layers (from SDAD core):
  🔐 Security · 🏗️ Structure · ⚡ Efficiency · ✅ DoD · 📄 Documentation · 🧪 Functional Coverage

This skill adds:
  🟣 Pyplan Platform — node design, data flow, interface, performance, and delivery conventions

---

## LAYER 7 — Pyplan Platform Checks

Run this layer after all base SDAD QA layers complete.
Report findings with prefix PP-01, PP-02... (independent numbering from H-XX).

### 7.1 Node Design

- [ ] Each node has a single, clearly named responsibility (no multi-purpose nodes)
- [ ] Node names follow the project naming convention (ask if no convention established)
- [ ] No node directly modifies another node's output — transformations are explicit
- [ ] Circular dependencies absent or intentional and documented
- [ ] Nodes that are reused across modules are factored into shared utility nodes
- [ ] No "dead" nodes (nodes with no downstream consumers and no deliberate output)

### 7.2 Data Flow

- [ ] Data source nodes are clearly identified and isolated from transformation nodes
- [ ] Currency/date assumptions are explicit (e.g., hard-coded year in a filter node flagged)
- [ ] Dimension structures (accounts, cost centers, time) are consistent across the model
- [ ] Driver nodes (inputs, parameters) are separated from formula nodes
- [ ] Missing-data handling is explicit — no silent NaN propagation
- [ ] Array shape assumptions are documented when non-obvious

### 7.3 Interface & Presentation

- [ ] All user-facing dashboards follow the interface conventions in SKILL pyplan-interfaces
  (if interfaces skill is active — otherwise note: "interfaces skill not loaded")
- [ ] No raw data shown directly to end users without formatting
- [ ] Navigation is linear and matches the use-case flow defined in SPEC §3
- [ ] Selector nodes (filters, dropdowns) are visually grouped, not scattered
- [ ] Error or edge-case states have a visible presentation (no blank/broken views)

### 7.4 Performance

- [ ] Heavy computation nodes are not recalculated on every selector change
  (check: are expensive nodes downstream of volatile inputs?)
- [ ] Nodes that can be precomputed (fixed reference data) are separated from live nodes
- [ ] No nested loops in Python nodes that could be vectorized with numpy/pandas
- [ ] File imports are not inside nodes that run repeatedly — imported once at init
- [ ] Model loads in a reasonable time for the client environment (flag if >30s is expected)

### 7.5 Pyplan Delivery Conventions

- [ ] SPEC §A gate conditions met (all items checked before declaring increment done)
- [ ] Model version is noted in the AI Authorship Log (SPEC §13)
- [ ] Client-visible text (labels, titles, tooltips) is in the correct language for the client
- [ ] No development scaffolding left visible (debug nodes, test selectors, placeholder text)
- [ ] Export / download functions tested with real data, not just structure
- [ ] Permissions model matches the client's role structure (if multi-user)

---

### 7.6 HTML Interfaces (when the project has any)

- [ ] All page-model traffic goes through window.pyplan.callback - no direct fetch/XHR
- [ ] Getter callbacks return JSON-friendly data; no raw DataFrames or xarray
- [ ] Mutator callbacks return stale-widget lists from get_nodes_to_refresh(...)
- [ ] Model writes only via set_input / set_form_values
- [ ] No cookie/localStorage dependence - state persists through model callbacks
- [ ] Node-backed headings carry data-pyplan-nodes for diagram traceability
- [ ] External JS modules loaded via window.pyplan.import; no iframe embeds
- [ ] Brand Token Sheet applied if active (cross-check pyplan-interfaces section 11)

---

## Reporting Format

Findings are numbered PP-01, PP-02...
Classify each as:
  🔴 must fix — blocks delivery or causes incorrect results
  🟡 should improve — degrades UX or maintainability, not a blocker
  🔵 style/convention — alignment with platform standards

Report format per finding:
  PP-XX [🔴/🟡/🔵] [layer] — [finding title]
  What: [one sentence describing the issue]
  Where: [node name, module, or interface element]
  Fix: [concrete action]

After all PP findings, emit:

  ─── PYPLAN QA SUMMARY ─────────────────────────────────
  PP findings:  [N total] · 🔴 [n] · 🟡 [n] · 🔵 [n]
  Base H findings: [carry over from base QA]
  Delivery status: [READY / BLOCKED — reason]
  ────────────────────────────────────────────────────────

Delivery is BLOCKED if any 🔴 finding is unresolved or SPEC §A gate is not fully cleared.

---

## Integration with $qa

When $qa runs on a Pyplan project (detected via PROJECT_PLATFORM: pyplan in SPEC §0):

1. Run all 6 base SDAD QA layers as normal.
2. Append Layer 7 (this skill) immediately after.
3. If the interfaces skill (pyplan-interfaces) is active, cross-reference §7.3 against it.
4. If the diagram skill (pyplan-diagram) is active, cross-reference §7.1 (node design) against architecture decisions made during diagramming.
5. Emit the combined report: H-XX findings first, then PP-XX findings, then combined summary.

---

## Lesson Capture — Pyplan-specific triggers

In addition to the base SDAD lesson capture triggers, propose a lesson entry when:
- A Pyplan platform behavior caused an unexpected result (e.g., recalculation order, node scope)
- A dimension mismatch caused silent errors that were hard to detect
- A performance issue was traced to a structural decision made early in the model
- A client delivery was blocked by a presentation or permissions issue not caught earlier

Category for Pyplan platform findings: ⚙️ Environment

---

## Key Pyplan Constraints (carry into every QA session)

- Pyplan's native Analyst Agent is immature — never assume it will catch issues automatically
- Nodes are the unit of version control — changes to shared nodes propagate immediately
- The model runs server-side; heavy client-side fallbacks are not available
- Selector state does not persist across sessions by default — design for stateless views
- Array operations follow numpy semantics; pandas DataFrames need explicit dimension labeling
