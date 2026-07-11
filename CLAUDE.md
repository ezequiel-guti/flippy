# SDAD v6.0 — CLAUDE.md
# Spec-Driven AI Development for Claude Code
# G7 AI Development Methodology
# Version 6.0 | 2026
#
# INSTALLATION: Place this file at the root of your project repository.
# The .claude/ folder (skills, agents, hooks) is installed by the SDAD installer.
# Run: install.ps1 (Windows) or install.sh (Mac/Linux)

---

## Project Declaration

# PROJECT_PLATFORM: generic
# PROJECT_LANGUAGE: es
# PROJECT_DOMAIN: none

## Flippy — Referencia rápida del proyecto

**Qué es:** PWA RAG conversacional para la comunidad educativa inmobiliaria de Virgilio.
**Spec:** SPEC.md · Tier 2 Business · Hitos 1–4 · USD 4.300 · 6.5 semanas

### Estructura de servicios
- `flippy-web/` → Next.js 14 App Router + TypeScript (Railway)
- `flippy-api/` → FastAPI Python 3.11+ (Railway) — toda la lógica de negocio

### Reglas de arquitectura
- `services/api.ts` es el único punto de llamadas al backend desde el frontend
- Sin axios — fetch nativo del navegador
- Streaming del chat: SSE leído vía ReadableStream del body de fetch
- Sin multi-tenancy — un solo cliente, sin headers de tenant ni API key estática
- Sin Vercel — timeouts de serverless incompatibles con procesamiento de documentos

### Reglas de seguridad
- `SUPABASE_SERVICE_ROLE_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `MP_WEBHOOK_SECRET`: solo en `flippy-api`, nunca en el frontend ni en el repositorio
- Webhooks MP validados con firma HMAC antes de procesar cualquier evento
- Errores al cliente: código HTTP + mensaje genérico, nunca stack traces

### Reglas de producto
- Respuestas ancladas exclusivamente al corpus documental, sin citas visibles
- Streaming en todas las respuestas del chat (SSE)
- Estados de usuario: `activo` | `en_mora` | `gratuito` | `cancelado`
- Transiciones de estado solo por webhooks de Mercado Pago, nunca desde el frontend
- Sin micrófono/voz en esta fase · Sin modo oscuro en esta fase

### Identidad visual
- Fondo marfil `#F4F1EC`, vino `#8B2E3B` para acciones, gris carbón para texto
- Tipografías: Cormorant Garamond para títulos, Lato para UI y chat
- Nombre: "Flippy" (con doble P)

### Decisión abierta
- OD-01: Límite del plan gratuito (confirmar con Virgilio antes del Hito 3)

---

# ── SDAD v6.0 methodology below ───────────────────────────────────────────
# PROJECT_PLATFORM: pyplan       ← uncomment for Pyplan projects
# PROJECT_PLATFORM: board        ← uncomment for Board projects
# PROJECT_PLATFORM: generic      ← default (no platform-specific skills)
#
# PROJECT_LANGUAGE: en | es      ← set by the first $spec question (v4.3).
#   Governs ALL interaction and generated documents: $spec questions, SPEC.md,
#   DECISIONS.md entries, QA reports, lesson candidates, $doc output.
#   Code identifiers and comments stay in English regardless (industry convention).
#
# PROJECT_DOMAIN: finance | supply-chain | <other> | none   ← business domain.
#   Asked in $spec; inferred in $audit then confirmed with the owner. Loads the
#   matching domain-* profile on-demand (tool-minimalism: only the project's
#   domain). No profile for a detected domain -> "not assessable - no domain
#   profile" (a finding, never a silent skip).
# ──────────────────────────────────────────────────────────────────────────
#
# When PROJECT_PLATFORM: pyplan is set, the following activate automatically:
#   · $spec    → adds §0 (platform), §A (data architecture), §B (discovery log),
#                §D (MCP Tools Catalog — conditional, only when @mcp_tool nodes declared)
#   · $build   → adds Pyplan checklist at increment close (includes MCP surface)
#   · $qa      → adds Platform layer (Layer 5) to QA run (includes MCP tool checks)
#   · Skills   → pyplan-diagram, pyplan-interfaces, pyplan-qa-platform,
#                pyplan-spec-context, pyplan-mcp load on-demand by trigger
#                decision-architecture and data-discovery load on-demand by trigger
#
# When PROJECT_PLATFORM: board is set, the following activate automatically:
#   · $spec    → adds §E (Board Data Model — gate) and §F (Board Capsule Structure)
#                asks "new vs existing project" before standard sections
#   · $build   → adds Board increment checklist at increment close
#                generates Board artefacts (SQL, CSV, Layout XML, Procedure specs)
#   · $qa      → adds Platform layer (Layer 5 — Board) to QA run
#   · Skills   → board-spec-context, board-data-model, board-capsule,
#                board-qa-platform load on-demand by trigger

---

## Core Rules

- Never write production code before the developer approves a Spec.
  Exception: $docfinal operates without a Spec — it generates one retroactively.
- Always follow: Context Analysis → Requirements → Spec → Build → QA.
- Claude Code has direct filesystem and terminal access — use it.
  Read actual files. Run actual tests. Write directly to the repo.
  Never simulate what you can execute.
- §A (Data Architecture) must be complete before $build is allowed on Pyplan projects.
  Same gate logic as §9 Security on Tier 3 projects.
- §D (MCP Tools Catalog) must be complete before $build is allowed on Pyplan projects
  that declare at least one @mcp_tool node. Same gate logic as §A.
- §E (Board Data Model) must be complete before $build is allowed on Board projects.
  Existing projects: Draft §E enables analysis mode; Approved enables full $build.

---

## Environment

DIRECT WRITE: yes — always. Claude Code writes files directly to the repo.
State is always the actual filesystem + SPEC.md + git log.

---

## Model & Effort Routing
# Added in v4.3 — extends the $build model line (C-015) to every SDAD phase.

CAPABILITY (verified against Claude Code, 2026-06):
  The main session never auto-switches model or effort. Changes happen only via
  /model + /effort (manual, Vía A) or pinned model/effort in the frontmatter of
  .claude/agents/*.md (delegated work, Vía B).

MODEL TIERS (agnostic — map to whatever is installed; survives model releases):
  FRONTIER → best reasoning model available (e.g. fable, opus)
  STANDARD → balanced cost/capability model (e.g. sonnet)
  ECONOMY  → fastest, cheapest model (e.g. haiku)

ROUTING TABLE (recommended model + effort per phase):
  $spec / $specout            → FRONTIER · high    — open decisions, requirements design
  $build (per increment)      → STANDARD · low when executing already-specified work;
                                FRONTIER · high when increment has medium/high risk
                                or an open decision (existing per-increment rule)
  $qa (incremental)           → STANDARD · medium  — bounded review of one increment
  $qa full / $QA / $docfinal  → FRONTIER · high    — whole-codebase judgment
  $verify / $doc              → ECONOMY–STANDARD · low — mechanical, delegable
  $agent review / audit       → pinned in agent frontmatter (FRONTIER · high)
  $agent test                 → pinned in agent frontmatter (STANDARD · medium)
  $pause / $lesson / $flow    → current model · low — never switch for these

ANNOUNCEMENT RULE (generalizes the $build 🧠 MODEL line):
  At the start of $spec, $specout, $qa full, and $docfinal emit:
    🧠 MODEL: [recommended] · effort [level] — [reason, ~4 words]
       If the active session differs:  /model [model]   and   /effort [level]
  $build keeps its gate: a mismatch blocks code writing until the developer
  switches. All other phases flag the mismatch once and continue — routing
  recommendations never block non-build phases.

---

## Active Skills

# Skills load from .claude/skills/ using SKILL.md progressive disclosure.
# Two loading modes:

### Always-on (loaded every session, declared here)
- **AI Architect** (.claude/skills/ai-architect/SKILL.md)
  Architecture decisions, LLM integration patterns, cost modeling, red flags.
  Active in all phases. Adds Architecture layer to QA.

- **AI Engineer** (.claude/skills/ai-engineer/SKILL.md)
  Implementation quality, tooling setup, developer experience, UI detection, docs standards.
  Active in all phases. Detects UI in Phase 0.

### On-demand (loaded when description trigger matches task)
- **Security Reviewer** — trigger: security, API keys, PII, auth, vulnerabilities (Phases 3–4)
- **QA Engineer** — trigger: QA, testing, code review, Phase 4, coverage
- **Compliance Reviewer** — trigger: auto-activated on Tier 2/3 confirmation
- **Frontend / UI** — trigger: user interface, components, React, Vue, dashboard, screen design
- **Brand Design** — trigger: brand, visual identity, brand tokens, logo, color palette, §C
- **Pyplan Diagram** — trigger: nodes, influence diagram, result=, module, wizard, xarray (Pyplan projects)
- **Pyplan Interfaces** — trigger: interface, component, dashboard, filter, index, chart, KPI (Pyplan projects)
- **Pyplan QA Platform** — trigger: auto-activated by $qa on Pyplan projects (Layer 5)
- **Pyplan Spec Context** — trigger: auto-activated by $spec / $specout on Pyplan projects
- **Pyplan MCP** — trigger: @mcp_tool, MCP tools, dynamic tools, OAuth MCP, §D, mcp_tool decorator (Pyplan projects)
- **Decision Architecture** — trigger: data architecture, DW, staging, data sources, §A
- **Data Discovery** — trigger: data delta, field mismatch, source discrepancy, data gap
- **Dev Setup** — trigger: onboarding, dev setup, which Claude Code features complement SDAD (links to live docs)
- **Harness** — trigger: control layer, harness model, governance axiom, E/T/C/S/L/V, enforcement in code vs prompt, $eval
- **Pyplan Audit** — trigger: auto-activated by $audit; audit an existing Pyplan model, five-dimension client report (Pyplan projects)
- **Business Alignment** — trigger: measurable objective, traceable rule, value vs cost, alignment, §1/§6 (auto in $audit dimension 5a)
- **Domain Profiles** (domain-finance, domain-supply-chain) — trigger: PROJECT_DOMAIN match; load on-demand for domain-correctness (5b)
- **Board Spec Context** — trigger: auto on $spec/$specout on Board projects
- **Board Data Model**   — trigger: entity, cube, relationship, dimension, §E (Board projects)
- **Board Capsule**      — trigger: capsule, screen, procedure, layout, mask, §F (Board projects)
- **Board QA Platform**  — trigger: auto by $qa on Board projects (Layer 5)

Use $skills to view details or activate additional skills manually.

---

## Compliance Tiers

Tier is detected in Phase 0 and confirmed in Phase 1.
Claude recommends a tier based on repo context — developer confirms or overrides.

TIER 1 — STANDARD
  For: internal tools, POCs, productivity scripts, personal projects
  Auto-activates: nothing additional
  DoD additions: none

TIER 2 — BUSINESS
  For: customer-facing products, SaaS, apps handling user data
  Auto-activates: Compliance Reviewer
  DoD additions: audit logging present, PII handling documented, auth reviewed, sanitized errors
  SPEC.md additions: §9 expanded with data classification and retention policy

TIER 3 — ENTERPRISE / REGULATED
  For: cloud deployments to corporate IT, healthcare, finance, government, ISO/SOC2
  Auto-activates: Compliance Reviewer (full profile) + regulation-specific skill
  DoD additions: threat model documented, data flow diagram present, control matrix in SPEC.md
  SPEC.md additions: §9 mandatory — must be complete and approved before $build
  $build is blocked until SPEC.md §9 is complete and approved.
  External skills: add gdpr-compliance / hipaa-compliance / soc2-compliance as applicable

TIER DETECTION (Phase 0, automatic):
  Payment integration, health data, government → recommend Tier 3
  User accounts, external data, client deployment → recommend Tier 2
  Internal script, no user data, no external exposure → recommend Tier 1
  Always confirm with developer in Phase 1 before locking tier.

---

## Context Budget

MONITORING: Estimate context usage after every response, starting from Phase 0.

AT 50% — ⚠️ SOFT WARNING (informational, continue normally):
  "⚠️ CONTEXT ~50% — Extended session. Consider starting a new session after
   completing the current increment."

AT 65% — 🔴 HARD WARNING (action required):
  "🔴 CONTEXT ~65% — Blocking $build after current increment.
   When done: run $pause compress, save state, start a new session."
  → Finish the current increment fully (including tests and $qa).
  → Block any new $build until session is restarted.
  → $pause, $spec, $verify, $lesson, $doc, $flow remain available.

RULES:
  Emit context warnings only at the defined thresholds — never otherwise.
  Hard warning never interrupts mid-increment — always finish cleanly.
  Sub-agents run in isolated context — they do not consume the main session budget.

---

## Sub-Agent Delegation ($agent — automatic)

Delegate automatically when ALL three conditions are true:
  1. The task operates on files already committed to the filesystem.
  2. The task does not require knowledge of decisions made in this session.
  3. The task is expensive in context (doc generation, architectural review, test suite).

Always delegate:  $doc (all variants) · $agent review · $agent test · $agent audit
Never delegate:   $qa after $build · $spec / $specout · $build

EXECUTION:
  Agent files live in .claude/agents/ (code-reviewer.md, test-generator.md, security-auditor.md)
  claude --print "[system context + isolated task]" > .sdad/agent_output.tmp
  Read .sdad/agent_output.tmp and incorporate the result. Delete temp file after.
  WHEN agent_output.tmp is empty or missing → surface error to developer, do not proceed silently.
  Developer sees only the final result — sub-agent mechanics are silent.

---

## Commands

**$sdad** — Show SDAD v6.0 methodology overview: phases, descriptions, command list (incl. $eval, $audit).

**$spec** (or $spec [section]) — Phase 1: Guided Requirements.
ONE question at a time with proposed default.
FIRST question (always, before everything else, unless PROJECT_LANGUAGE is already set):
  "Project language — should all documents and our interaction be in
   (1) English or (2) Spanish? [default: the language you are writing in]"
  Lock the answer as PROJECT_LANGUAGE in the project declaration and switch
  immediately. Code identifiers/comments stay in English regardless.
Standard order: scope, user flows, data model, integrations, business rules,
performance, security, compliance tier, testing.
Before asking, read existing files in the repo — infer what is already defined.

DOCUMENT INGESTION (all projects — $spec, §A client diagnosis, $docfinal inputs):
  When source material arrives as binary office documents (PDF, docx, xlsx, pptx,
  Outlook .msg, images), convert to Markdown first with markitdown, then read the
  Markdown — it preserves headings/tables/lists and is far more token-efficient:
    pip install 'markitdown[all]'   →   markitdown file.pdf -o file.md
  Security: convert local, trusted files only (convert_local) — never feed
  untrusted paths or URLs (markitdown performs I/O with process privileges).
  Keep converted .md files in .sdad/ingest/ — they are working copies, not deliverables.

PYPLAN PROJECTS (when PROJECT_PLATFORM: pyplan):
  Run §0 (platform context) first, then §A (data architecture) before standard sections.
  §A gate: flag explicitly when §A is incomplete — $build is blocked until approved.
  §B (discovery log) is initialized empty — it fills during $build.
  §D gate (conditional): ask "Does this project expose any nodes as MCP tools (@mcp_tool)?"
    If yes: run §D (MCP Tools Catalog) before moving to standard sections.
    §D gate: flag explicitly when §D is incomplete — $build is blocked until approved.
    If no: skip §D entirely — do not create the section.

BOARD PROJECTS (when PROJECT_PLATFORM: board):
  Ask "New project or existing?" before standard sections.
  New: run Board questions in order (version, cloud/on-prem, entities, relationships,
    cubes, capsule structure, procedures, data sources, Board API available?).
  Existing: file ingestion flow (Layout XML, CFG, CSV, screenshots) → auto-populate §E/§F.
    Mark all inferred fields as [inferred] — developer confirms before §E approved.
  §E gate: flag when empty — $build blocked. Draft = analysis mode for existing projects.

COMPLIANCE QUESTION (always ask, never skip):
  "What's the deployment context?
   (1) Internal tool / POC — Tier 1 Standard
   (2) Customer-facing product / SaaS — Tier 2 Business
   (3) Regulated environment / corporate IT / cloud enterprise — Tier 3 Enterprise
   Based on what I see in this repo, I recommend: [Tier N — reason]"
  Lock the tier on confirmation. Activate tier-specific skills and DoD immediately.
Suggest $specout when all areas are covered.

**$specout** — Phase 2: Generate full Spec Document.

Standard sections (all projects):
  §1  Vision & Objective
  §2  Users & Roles
  §3  Functional Flows
  §4  Data Model
  §5  Technical Architecture
  §6  Business Rules
  §7  Integrations & APIs
  §8  Testing Strategy
  §9  Security & Compliance (depth depends on tier)
  §10 Definition of Done
  §11 Out of Scope
  §12 Open Decisions
  §13 AI Authorship Log (Increment / Feature / Model / Date / Notes)

Additional sections for Pyplan projects (prepended before §1):
  §0  Platform Context (Pyplan version, workspace, permissions, data types, conventions)
  §A  Data Architecture (client diagnosis, architecture decision, data contract per source)
  §B  Discovery Log (initialized empty — updated during $build when data deltas are found)
  §D  MCP Tools Catalog (conditional — include only when the project declares at least one
      @mcp_tool node. Documents each tool: node identifier, tool name, description,
      parameter names + types + Annotated descriptions, return type, serialization notes.
      §D is a gate section: must be approved before $build when present.)

Additional sections for Board projects (prepended before §1):
  §E  Board Data Model (gate: approved before $build; Draft allows analysis mode for existing projects)
  §F  Board Capsule Structure

§7 — MCP vs CLI rule (consumer context only):
  When §7 documents a third-party integration SDAD will consume during $build,
  evaluate wrapping a CLI over invoking the MCP directly when ALL hold:
    (a) the task hits a single endpoint,
    (b) context is near the budget threshold, AND
    (c) the CLI adds no greater security risk than the MCP
        (shell injection, credentials in argv/env, fragile parsing).
  If (c) fails, keep the vetted MCP. Record the choice and its security
  rationale in §7 of SPEC.md. Cross-check $qa Layer 1 (Security).
  Does NOT apply in producer context (Pyplan §D / @mcp_tool — MCP is the
  correct architecture; no CLI preference).

After generating, write the Spec to SPEC.md in the repo root automatically.
For Tier 2/3: §9 is mandatory and must be complete before approval.
For Tier 3 and Pyplan: respective gate sections (§9 / §A) block $build until approved.
For Pyplan projects with MCP tools: §D blocks $build until approved.
For Board projects: §E blocks $build until Draft or Approved (empty §E = full block).
Ask for developer approval before allowing $build.

**$build** (or $build [feature]) — Phase 3: Guided Development.
Requires approved SPEC.md.
WHEN SPEC.md not found: read the repo, then offer $spec or $docfinal — do not proceed.
WHEN no test command found: flag before writing code.
Blocked if Context Budget hard warning (65%) was triggered.
ON PYPLAN PROJECTS: blocked if §A is not marked as approved in SPEC.md.
ON PYPLAN PROJECTS: blocked if §D is present and not marked as approved in SPEC.md.
ON BOARD PROJECTS: blocked if §E is empty (not present, not Draft, not Approved) in SPEC.md.

Before each increment announce:

  🔨 INCREMENT [N]: [feature name]
  🧠 MODEL: [model] · effort [low|high] — [reason, ~4 words]
     (per Model & Effort Routing table — low = executing already-specified work ·
      high = medium/high risk or open decision)
     If the active session differs:  /model [model]   and   /effort [low|high]
  Files: [list of files to create or modify]
  Tests: [unit / integration / E2E — will be executed after writing]
  Docs: [README update / API doc / inline comments required]
  Dependencies: [what must be done first]
  ──────────────────────────────────────────────────────
  [If model/effort matches the recommendation, confirm and proceed; if it differs, flag and wait
   for the developer to switch before writing code. The session does not auto-switch. Then run tests.]

After writing code for an increment:
  1. Run the project's test command. Report actual result — pass count, failures, errors.
  2. Run $qa on the increment.
  3. Write DECISIONS.md entry for this increment (see HUB BLOCK below).
  4. Update SPEC.md §13 AI Authorship Log.
  5. ON PYPLAN PROJECTS: run Pyplan increment checklist (see below).
     ON BOARD PROJECTS: run Board increment checklist (see below).
  5.5. Project CLAUDE.md sync — if this increment changed structure, propose an update to the
       project's own CLAUDE.md (see PROJECT CLAUDE.md PROTOCOL below).

PROJECT CLAUDE.md PROTOCOL (the developer's own repo CLAUDE.md — not this methodology file):
  Contains: stack/architecture conventions, project commands, hard rules, lasting structural
    decisions. Excludes: increment status and anything already in SPEC.md (no duplication — the
    main control). Update on structural-increment close or at session end. Soft guide ~150–200 lines.

PYPLAN INCREMENT CHECKLIST (runs after step 4 on Pyplan projects):
  Diagram surface:
    □ All new nodes have result= assigned and calculate without error
    □ No circular dependencies introduced
    □ Data source of read nodes matches §A data contract
  Interface surface:
    □ All new indexes are synchronized
    □ Inputs have type and range validations configured
    □ Visualization components display calculated data (not empty)
  HTML interface surface (only when the increment touches an HTML interface):
    □ All page↔model traffic goes through window.pyplan.callback — no direct fetch/XHR
    □ Getters return JSON-friendly data; mutators return get_nodes_to_refresh(...) lists
    □ Model writes use set_input / set_form_values — never touch model internals directly
    □ No cookie/localStorage reliance — state persists via callbacks to the model
    □ Node-backed headings carry data-pyplan-nodes; in-app navigation uses plain anchors
    □ External JS modules load via window.pyplan.import — no <iframe> embeds (unsupported)
  Discovery:
    □ Any data deltas found during this increment recorded in §B and DECISIONS.md
    □ If structural delta found: $build paused, data gap report generated for consultant
  MCP surface (only when project has §D):
    □ Each new @mcp_tool node: docstring explains the business action precisely
    □ All parameters use Annotated[type, 'description'] — no untyped parameters
    □ Return value is serializable (no raw xarray, no bare DataFrames — use .to_dict())
    □ result = _fn assigned — not result = _fn() (function assigned, not called)
    □ Tool does not depend on interactive agent behavior or session state
    □ §D entry created or updated for this tool (identifier, name, description, parameter schema)
  Versioning (only when the increment modified the Pyplan model):
    □ Model exported to .sdad/pyplan-snapshots/ named YYYYMMDD-incN-slug.ppl
    □ Snapshot included in this increment's atomic commit

BOARD INCREMENT CHECKLIST (runs after step 4 on Board projects):
  Data Model surface:
    □ Entity creation order respected: Entities → Relationships → Cubes
    □ All Cubes reference only valid Entities as dimensions
    □ Algorithm formulas use block letters (a, b, c...) and Board functions only: dt(), rt(), gt(), @DATE, @MONTH, @YEAR
    □ No circular dependencies in Relationships
  Capsule surface:
    □ Scheduleable Procedures placed at Data Model level — not Capsule level
    □ Client-side Steps (navigation, selection) not placed in server-side Procedures
    □ All Screen Data Blocks bound to a valid Data Model
  Artefact validation:
    □ SQL Data Readers validated against declared source type in §E
    □ CSV imports match Entity structure defined in §E
    □ Layout XML follows Board element and attribute naming conventions
  Discovery:
    □ Any schema or source deltas found during this increment recorded in §B and DECISIONS.md

DATA DELTA HANDLING (Pyplan projects):
  Small delta (format error, nulls, unexpected volume, wrong field name):
    → Resolve in the node.
    → Record in §B: what was assumed, what was found, how resolved, impact on other nodes.
    → $build continues.
  Structural delta (data does not exist, wrong granularity, source completely different):
    → Pause $build immediately.
    → Generate data gap report: assumption from §A, finding, decision needed.
    → Surface to developer — consultant takes report to client.
    → $build does not resume until consultant records approved resolution in §B.

BUILD-VIA-AI GUARDRAILS (Pyplan MCP — when using Pyplan MCP's build/modify capabilities):
  Pyplan MCP allows AI clients to modify application logic and interfaces directly in a
  running Pyplan instance. SDAD treats each AI-driven modification as an increment.
  Interfaces built via AI (Pyplan agents or Pyplan MCP) are HTML interfaces by default —
  each generated or modified HTML interface is itself an increment under these rules,
  and closes with the HTML interface surface checklist.
  Rules:
    1. Spec must be approved before any build/modify action — same gate as $build.
       If Spec is not approved, block the modification and redirect to $spec / $specout.
    2. Each AI-driven modification is announced as an increment before execution
       (same format as the $build increment announcement block).
    3. Wait for developer approval before executing the modification.
    4. After execution: write DECISIONS.md entry and update §13 AI Authorship Log.
    5. Run $qa on the modified increment — no increment is complete without QA.
    5.5. PYPLAN MODEL SNAPSHOT: after $qa passes, export the model to
         .sdad/pyplan-snapshots/YYYYMMDD-incN-slug.ppl (MCP export endpoint if available,
         else Pyplan UI); include it in this increment's atomic commit.
    6. Run MCP surface checklist for any node modified or created via AI.
  Note: Pyplan MCP is a v1 server (first release). Document it as an external
  dependency in §7 and flag its maturity level in $verify.

**$qa** (or $qa [mode]) — Phase 4: Quality Assurance.

  $qa           → incremental QA on last $build increment (auto mode)
  $qa review    → manual QA — per-finding approval
  $qa full      → full project audit
  $QA           → full standalone audit (SDAD-Aware or Standalone)

QA LAYERS (run in priority order):
  Layer 1 — 🔐 Security: API key exposure, unprotected endpoints, PII in logs (P0),
            missing input sanitization, weak auth (P1), rate limiting, missing headers (P2)
            MCP (Pyplan projects with §D): OAuth token not logged or exposed in node results (P0),
            @mcp_tool parameters validated before use — no path to arbitrary code execution (P1),
            exposed tools have minimum necessary scope — no tool exposes more than its declared contract (P2)
            MCP vs CLI (consumer context): a CLI wrapper chosen over a vetted MCP
            must not add shell-injection, credentials-in-argv/env, or fragile-parsing risk (P1) — see $specout §7 rule
  Layer 2 — 🏗️ Structure: architecture consistency, separation of concerns, error handling,
            context flow, tight coupling
  Layer 3 — ⚡ Efficiency: token usage, redundant calls, conversation history management,
            unbounded loops, latency bottlenecks
  Layer 4 — ✅ Best Practices: readability, maintainability, duplication, naming, docs gaps
  Layer 5 — 🟠 Platform (Pyplan and Board projects):
    Pyplan checks: nodes missing result=, unsynchronized indexes,
            inputs without validations, circular dependencies, Analyst Agent context gaps
            MCP tools (when §D present):
              □ All nodes registered in §D are decorated with @mcp_tool and have result = _fn
              □ All parameters have Annotated[...] with non-empty descriptions
              □ Docstrings are precise enough for an external LLM to invoke correctly
              □ Return values verified serializable — no DataFrames, no xarray without conversion
              □ No tool depends on interactive agent behavior or mutable session state
              □ Build-via-AI: model snapshot present in .sdad/pyplan-snapshots/ for this increment (YYYYMMDD-incN, committed)
            HTML interfaces (when the project has any):
              □ Page↔model traffic only via window.pyplan.callback — no direct requests
              □ Mutator callbacks report stale widgets via get_nodes_to_refresh
              □ No cookie/localStorage dependence — state persisted through model callbacks
    Board checks (Board projects only): Entity creation order, Cube dimension validity,
            Algorithm syntax (block letters, Board functions: dt(), rt(), gt(), @DATE, @MONTH, @YEAR),
            Procedure level (scheduleable → Data Model level only, not Capsule level),
            Step type misplacement (client-side Steps in server-side Procedures),
            naming convention consistency, Board API credentials not logged in Procedures (P0)

$qa auto never touches security, compliance, or Spec deviations without human approval.
Security and compliance findings always require explicit developer approval before any fix.

**$verify** — Check dependency documentation currency.
Runs automatically when $build introduces a new external dependency.
When Context 7 MCP is active, $verify uses it automatically.

  $verify         → reactive (default): triggered when $build adds a new dependency.
  $verify audit   → proactive: read package.json / requirements.txt / dep tree and verify
                    each dependency against current docs (Context 7 MCP, else WebSearch).
                    Trigger: Phase 0 when the project went >30 days without $build (date
                    source: last §13 entry / git log), or on demand. Not automatic per session.
ON PYPLAN PROJECTS WITH §D: $verify always includes the Pyplan MCP server as an external
dependency. Flag in §7: "Pyplan MCP server — v1 (first release, API may change across
Pyplan updates)." Recommend locking to a specific Pyplan version in §5 if MCP stability
is critical for the project.

**$eval** — Methodology self-evaluation (V component). Replays the `.sdad/eval/` golden
dataset (deterministic core: spec-gate hook, ASCII ratchet, $agent liveness, CLAUDE.md asserts;
`$eval release` adds non-deterministic LLM smoke before tagging) to catch regressions before
release. Run on any CLAUDE.md/skill change and as the release gate; SessionStart reminds when
CLAUDE.md drifts from the last green run. See the Harness skill.

**$pause** — Show current session state.
  Current Phase | Spec Status | Compliance Tier | Platform | Context Budget %
  Last increment + test result | Open QA findings (H-XX) | Active Skills
  Decisions log: [N entries — last entry title and date]
  Project CLAUDE.md: last modified [date]
  Flows defined: [N] | Next step recommendation

**$pause compress** — Generate Session Snapshot for next session.
  Compact state block for pasting at the start of the next conversation.
  Includes: phase, spec status per section, compliance tier, platform,
  completed increments summary, open QA findings (H-XX), open decisions,
  AI Authorship Log summary, Lesson Library summary (N new entries),
  active skills, context budget %, flows defined, exact next step.
  When a Session Snapshot is detected at conversation start:
  acknowledge and restore all state without asking developer to re-explain.
  Emit a COMPACT ANCHOR within the snapshot: active phase/tier/platform, approved spec sections,
  active increment, [LOCK] decisions only, open QA (H-XX), and constraints that must not be lost.

**$docfinal** — Retroactive Documentation. For projects built without SDAD.
No Spec required. Infers everything from the codebase. Runs 4 steps in sequence.

  $docfinal         → run all 4 steps (default)
  $docfinal spec    → Step 1 only — retroactive SPEC
  $docfinal log     → Step 2 only — AI Authorship Log
  $docfinal qa      → Step 3 only — QA standalone audit
  $docfinal lessons → Step 4 only — lesson candidates

STEP 1 — RETROACTIVE SPEC: Read entire codebase. Write SPEC_RETROACTIVE.md to repo root.
  Never overwrite SPEC.md. Include only sections reliably inferred from code:
  §1, §2, §3, §4, §5, §9, §11, §12. Skip §6, §7, §8, §10.

STEP 2 — AI AUTHORSHIP LOG: Generate §13 table — one row per detected module or feature.
  Increment / Feature / Model: "Pre-SDAD / unknown" / Date from git log / Notes.
  Append to SPEC_RETROACTIVE.md.

STEP 3 — QA STANDALONE AUDIT: Full $QA Standalone mode. All layers including Platform
  if Pyplan or Board is detected. Mark P0 findings with 🚨. Number H-01, H-02...
  Do NOT apply any fixes — report only.
  Close with: "Which fixes would you like me to apply? (H-XX, 'all', or 'none')"

STEP 4 — LESSON CANDIDATES: Evaluate findings and codebase. Propose up to 3 candidates.
  For each: title / Category / Signal / Principle / Add to Lesson Library? (yes/skip/edit)

**$audit** (or $audit [dimension] | $audit report) — Pyplan Audit. Sibling of $docfinal:
runs on a model SDAD did not build, without an approved SPEC.md. Where $docfinal documents,
$audit judges and recommends — deliverable is a client-facing five-dimension report
(development, security, usability, quality, business). Auto-activates the pyplan-audit skill,
which owns the lifecycle, evidence contract, and severity reconciliation.
  Spec-gate: writes audit artifacts with no Spec via .sdad/AUDIT_ACTIVE (mirrors $docfinal's
  DOCFINAL_ACTIVE; allowlisted in checks/spec-gate-policy). Create on start, remove on
  completion or abort. Security/compliance findings still need explicit approval.
  Evidence first: acquire per .sdad/audit/SCHEMA.md; un-acquirable areas are "not assessable"
  gaps, never assumptions. Report intent vs delivered neutrally — never accusatory.

**$agent** — Sub-Agent Delegation. Each agent returns an AGENT HANDOFF block — see .claude/agents/HANDOFF_TEMPLATE.md.

  $agent review [module]  → architectural review (uses .claude/agents/code-reviewer.md)
  $agent test [module]    → generate test suite (uses .claude/agents/test-generator.md)
  $agent audit [path]     → security audit (uses .claude/agents/security-auditor.md)

**$doc** — Technical Documentation Generator. Delegates to sub-agent automatically.

  $doc            → full documentation set
  $doc readme     → update README.md
  $doc api        → generate or update API reference
  $doc arch       → generate architecture document
  $doc compliance → compliance summary (Tier 2/3 only)

All $doc outputs written directly to /docs in the repo.

**$flow** — Project Flow Manager.

  $flow [name]       → define a new flow for this project
  $flow list         → list all flows in .claude/flows/
  $flow [name] run   → execute a saved flow
  $flow [name] edit  → update an existing flow

**$lesson** — Lesson Library management.

  $lesson            → show all entries grouped by category
  $lesson search [kw] → filter by keyword, category, stack, or #stack/#phase tag
  $lesson [L-XX]     → show full entry
  $lesson new        → guided entry creation — writes to LESSON_LIBRARY.md on approval

**$skills** — Show active and available AI specialist skills.
  Always active: AI Architect, AI Engineer.
  On-demand: Security Reviewer, QA Engineer, Compliance Reviewer, Frontend,
             Brand Design, Pyplan x5 (diagram, interfaces, qa-platform, spec-context, mcp),
             Board x4 (spec-context, data-model, capsule, qa-platform),
             Decision Architecture, Data Discovery.

---

## HUB BLOCK — auto-generated after each $build increment

After every completed increment, generate and display this block:

  ════════════════════════════════════════════════════════
  📋 HUB BLOCK — DECISIONS_[PROJECT].md
  ════════════════════════════════════════════════════════
  Date: [YYYY-MM-DD]
  Increment: [N] — [feature name]
  Model: [model used]
  Decision: [one-line summary of the main architectural or implementation decision]
  Rationale: [one-line rationale]
  Alternatives considered: [brief — or "none"]
  Impact: [files changed, dependencies added, patterns introduced]
  ════════════════════════════════════════════════════════
  → Copy this block to: hub/DECISIONS_[PROJECT].md

Also write the decision entry directly to DECISIONS.md in the repo root.

---

## Lesson Capture — triggered after $qa

Evaluate after every $qa run. Trigger only when the increment reveals:
  - a bug or failure pattern likely to recur in other projects
  - an integration quirk not documented in official docs
  - an architectural or prompt pattern that significantly simplified the solution
  - a Pyplan-specific pattern (node design, interface structure, data handling)

If triggered, propose ONE entry (most valuable finding only):

  📚 LESSON CANDIDATE — [short title]
  Category: [LLM Design | Architecture | Data & Debugging | Environment | Workflow | Pyplan]
  Signal: [one line — how would another developer recognize this applies to them?]
  Principle: [one transferable sentence]

  Add to Lesson Library? (yes / skip / edit)

If yes: write the full L-XX entry directly to LESSON_LIBRARY.md.
        Also generate HUB BLOCK for LESSONS_RAW.md (Google Drive).
Also evaluate: should this finding become a rule in this project's CLAUDE.md?
If nothing is lesson-worthy: skip silently — never mention it.

---

## Behavior Rules

- Read actual files before asking questions — never ask what you can infer.
- Run actual tests after every $build increment — never skip execution.
- Write SPEC.md to the repo on $specout — never keep the Spec only in chat.
- Write lesson entries to LESSON_LIBRARY.md directly — never ask developer to paste.
- Ask the compliance tier question in Phase 1 — never skip it.
- Honor PROJECT_LANGUAGE in every interaction and generated document; if unset, ask it
  as the first $spec question. Code identifiers and comments stay in English.
- Activate Compliance Reviewer automatically on Tier 2/3 confirmation.
- Ask one question at a time in $spec — never present a questionnaire.
- Always propose a default — interrupt only when data cannot be inferred.
- Announce increments before coding — never skip the announcement.
- Announce a recommended model + effort in every $build increment; if the active session differs, flag and wait for the developer to switch before writing code.
- Route model + effort per the Model & Effort Routing table; emit the 🧠 MODEL line at the start of $spec, $specout, $qa full, and $docfinal. Only $build blocks on mismatch — other phases flag once and continue.
- After a structural increment, propose an update to the project's own CLAUDE.md (step 5.5); never duplicate SPEC.md content into it.
- Include docs update in every $build increment announcement.
- Mark critical security issues with 🚨 regardless of current phase.
- Mark compliance violations with 🔒 regardless of current phase.
- Distinguish clearly: "must fix" / "should improve" / "style suggestion".
- Lesson capture is silent when nothing is worth capturing — never force an entry.
- $qa auto never touches security, compliance, or Spec deviations without human approval.
- Update SPEC.md §13 after every completed increment.
- In Phase 0, detect UI presence and suggest frontend skill if applicable.
- In Phase 0, surface 2-3 relevant lessons from LESSON_LIBRARY.md (match by #stack/#phase); embeddings only past ~50 entries.
- $agent delegation is automatic — never ask developer which tasks to delegate.
- $verify runs automatically when $build introduces a new external dependency.
- $verify audit is the proactive mode — run it in Phase 0 when >30 days elapsed since the last $build.
- In consumer context, weigh CLI-vs-MCP per the $specout §7 rule; if the CLI adds security risk, keep the vetted MCP. Never applies in producer context (§D active).
- $pause always includes Context Budget status, Decisions log count, platform, flows count, and project CLAUDE.md mod date.
- Write DECISIONS.md entry and HUB BLOCK after each completed increment.
- Mark non-reopenable decisions [LOCK] in DECISIONS.md; $pause compress carries only [LOCK] decisions into the COMPACT ANCHOR.
- ON PYPLAN PROJECTS: run increment checklist before marking any increment complete.
- ON BOARD PROJECTS: run Board increment checklist before marking any increment complete.
- ON BOARD PROJECTS: Entity creation order enforced — Entities → Relationships → Cubes (BR-05).
- ON BOARD PROJECTS: Algorithm syntax validated before increment closes — block letters and valid Board functions only (BR-03).
- ON BOARD PROJECTS: Procedure placement enforced — scheduleable Procedures at Data Model level only, not Capsule level (BR-04).
- ON BOARD PROJECTS: existing project ingestion marks all inferred §E/§F fields as [inferred] — developer confirms before §E approved (BR-07).
- ON PYPLAN PROJECTS: never rely on the Pyplan Analyst Agent — SDAD is self-sufficient.
- ON PYPLAN PROJECTS: structural data deltas pause $build — never improvise a workaround.
- ON PYPLAN PROJECTS WITH MCP: Build-via-AI requires approved Spec — Pyplan MCP does not bypass the Spec gate.
- ON PYPLAN PROJECTS WITH MCP: each AI-driven modification via Pyplan MCP is announced and approved as an increment before execution.
- ON PYPLAN PROJECTS WITH MCP: §D is a gate section when present — $build blocked until §D is approved.
- ON PYPLAN PROJECTS WITH MCP: flag Pyplan MCP as a v1 external dependency in §7 — API may change across Pyplan updates.
- ON PYPLAN PROJECTS: AI-built interfaces default to HTML interfaces; each one is announced,
  approved, and QA'd as an increment, closing with the HTML interface surface checklist.
- ON PYPLAN PROJECTS WITH MCP: after each Build-via-AI increment's $qa passes, export the model
  snapshot to .sdad/pyplan-snapshots/ before committing — increment is not complete without it.
- Convert binary source documents (PDF/docx/xlsx/pptx) to Markdown with markitdown before
  reading them — see DOCUMENT INGESTION under $spec. Local trusted files only.
- Before session end or $pause compress, resolve any pending commits using git log.
- All .ps1 AND .sh scripts must be pure ASCII — Windows PowerShell 5.1 misreads UTF-8 without
  BOM and fresh-machine installers break on non-ASCII bytes; ratcheted for both in
  checks/ascii-ps1 (L-01, .sh added in the v5.2 versioning patch).
- Governance Axiom: hard gates live in code (PreToolUse spec-gate, checks/ ratchet, git pre-commit); prompt rules are the fallback, not the guarantee. See the Harness skill.
- $eval runs on any CLAUDE.md/skill change and as the release gate; a captured lesson with a mechanically verifiable pattern gets a check in checks/, not only a prose rule.
- $agent delegation goes through .sdad/lib/agent-run (600s timeout) — fails loud on timeout or empty output, never proceeds silently.
- On a tool/test error mid-increment: stop the increment cleanly, set .sdad/HOLD_AUTOCOMMIT, never enter an undefined retry loop — recovery clears when the developer resumes.
- Commit DECISIONS.md + §13 + SPEC.md for one increment as a single atomic commit; record the exact model string per release (§5 / $verify) when reproducibility matters.
- ON PYPLAN PROJECTS: $audit judges an existing model without a Spec (.sdad/AUDIT_ACTIVE sentinel); never assume the model is inspectable as code — acquire evidence per .sdad/audit/SCHEMA.md, declare un-acquirable areas "not assessable".
- Business dimension never fabricates: no owner elicitation -> alignment (5a) "not assessable - no elicitation input"; no domain profile -> domain correctness (5b) "not assessable - no domain profile". Both are findings, never silent skips.
- Every domain-correctness finding carries a confidence level — an LLM domain profile raises the floor, it does not replace the client's SME for high-stakes validation.
- $audit reports intent vs delivered neutrally — evidence-based, liability- and relationship-aware, never accusatory.
- PROJECT_DOMAIN loads only the matching domain-* profile(s) on-demand (tool-minimalism); multi-domain models load multiple and flag cross-domain seams as high-risk.

---

## Required Environment Tool

ccstatusline provides a real-time status bar inside Claude Code: model, thinking effort,
context %, session cost, git branch. Configure once per machine (interactive TUI — enable
the Model, Thinking Effort, Context %, Session Cost and Git Branch widgets; writes statusLine into
~/.claude/settings.json):

  npx ccstatusline@latest

The bar then renders automatically in every session.
Use as primary context budget indicator — shows the 50% / 65% thresholds.

---

## Complementary Tools
# Developer reference — does not affect Claude behavior.
#
# Warp                    AI-native terminal                   https://warp.dev
# Context 7 MCP           Up-to-date API docs in session       /plugin → "Context 7"
# Sequential Thinking MCP Chain-of-thought reasoning           type "install sequential thinking MCP"
# Happy Engineering        Remote Claude Code control (mobile)  https://happy.engineering
# MarkItDown              Office/PDF → Markdown for ingestion  https://github.com/microsoft/markitdown
#
# Note: when Context 7 MCP is active, $verify uses it automatically.
# Note: hooks (.claude/hooks/) are ACTIVE since v4.2 (Windows/PowerShell): SessionStart (anchor +
#       guarded ff-pull), PreCompact (anchor snapshot), SessionEnd (whitelisted autocommit). See README.

---

G7 AI Development Methodology | SDAD v6.0 | CLAUDE.md
Spec-Driven AI Development for Claude Code
