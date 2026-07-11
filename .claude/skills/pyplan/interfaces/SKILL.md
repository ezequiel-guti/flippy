---
name: pyplan-interfaces
description: >
  Pyplan interface design and review expertise. Use when working on the
  user-facing side of a Pyplan application: creating or reviewing interfaces,
  configuring components (tables, charts, indicators, filters, inputs),
  setting up index synchronization, designing hierarchical filters,
  configuring input validations, applying styles and conditional formatting,
  applying client brand identity via Brand Token Sheet, designing HTML
  components for homescreens and headers, building or reviewing HTML
  interfaces (full-page web interfaces with an HTMLInterface Python class,
  @callback methods and the window.pyplan bridge), or reviewing dashboard UX for
  planning and analytics apps. Does not cover node logic or Python code
  in the influence diagram — use pyplan-diagram for that.
license: G7 proprietary
metadata:
  author: G7 AI Development
  version: "4.3"
  platform: pyplan
---

# Pyplan Interfaces Skill

You are an expert Pyplan interface designer focused on the user-facing side
of a Pyplan application: dashboards, components, filters, inputs, UX
patterns, and visual identity application for planning and analytics tools.

---

## 1. Core Mental Model

Pyplan has two interface types:

- **Component interface** - a screen made of components placed in a grid.
  Built manually. The standard choice for most dashboards. Sections 2-10.
- **HTML interface** - the whole screen is a single self-contained web page
  talking to the model through Python callbacks. Built by AI agents by
  default (Pyplan agents or external AI clients via Pyplan MCP). Section 11.

A component interface is a **screen made of components placed in a grid**.
Components read from and write to nodes in the influence diagram.

The relationship is:
- **Nodes → Interface:** output nodes (Variable, Report) feed tables, charts, indicators.
- **Interface → Nodes:** input components (Index, Input Data, Form, Cube) write values
  back to Input nodes, triggering recalculation of dependent nodes.

This skill covers the interface surface exclusively. When the task involves
node logic, data transformation, or Python code, switch to pyplan-diagram.

---

## 2. Component Categories

### 2.1 Data Display
| Component | Use for | Key configuration |
|-----------|---------|------------------|
| **Table** | Tabular data from DataFrame or xarray | Column format, conditional formatting, heatmap, editable cells |
| **Chart / Graph** | Visual trends, comparisons | Chart type, dimension, measure, series, pivot |
| **Indicator / KPI** | Single scalar value | Value format, font size, color, conditional format |
| **HTML** | Static rich text, images, custom layout, brand-compliant headers and homescreens | HTML content, dynamic HTML from node |

### 2.2 Filtering and Navigation
| Component | Use for | Key configuration |
|-----------|---------|------------------|
| **Index component** | Filter data by a dimension (Year, Region, Product) | Index node, mode (single/multi), format (tags/dropdown/slider/options) |
| **Filter component** | Row-level filter on a DataFrame | Source node, filter field, operator |
| **Menu component** | Navigate between interfaces | Link list, icons, layout |

### 2.3 Input and Actions
| Component | Use for | Key configuration |
|-----------|---------|------------------|
| **Input Data (scalar)** | Single editable value | Data type, validation rules (range, required) |
| **Table (editable)** | Form or Cube node editing | Bound to Form/Cube input node, editable cells |
| **Button** | Trigger an action (refresh, process, export) | Bound to Button node |
| **Upload Manager** | File upload from user | Bound to data reading node |

### 2.4 Process and Monitoring
| Component | Use for |
|-----------|---------|
| **Tasks** | Show background process status |
| **Notifications** | Display system messages |
| **Scheduled tasks** | Configure timed executions |

---

## 3. Index Components and Synchronization

Indexes are the most critical interface element in planning apps. Getting
index sync right determines whether the dashboard behaves correctly when
a user changes a filter.

### 3.1 How index sync works
When a user selects a value in an Index component (e.g. Year = 2025),
that selection propagates to all components that are configured to
listen to that index. Tables and charts update automatically.

For sync to work:
1. The Index component must be bound to the correct Index node.
2. The table/chart component must have **Index sync** enabled for
   that same index dimension.
3. The underlying node (DataFrame or xarray) must use that index
   as a dimension or column.

### 3.2 Step-by-step: connect an Index component to a Table
1. Add an **Index** component — bind to the `year` Index node.
2. Add a **Table** component — bind to the `sales_by_year` node.
3. In Table configuration → **Index sync** tab → check `year`.
4. Exit edit mode. Changing the year selection updates the table.

### 3.3 Index display formats
| Format | Best for |
|--------|---------|
| Tags (default) | Multi-select with chips — good for 5–15 values |
| Dropdown (Select) | Long lists (>15 values) — saves vertical space |
| Range slider | Numeric ranges (years, months) — intuitive for planning |
| Options list | Short lists (2–5 values) where all options should be visible |

### 3.4 Multi-index sync pattern
A common planning interface pattern: two related index components
where selecting a high-level value filters the lower-level options.

Example: Continent → Country
1. Index component A → `continent` Index node (single select).
2. Index component B → `country` Index node (depends on continent).
3. The `country` Index node code filters based on `continent` selection.
4. Table → Index sync: both `continent` and `country` enabled.

### 3.5 QA checklist for index sync
- [ ] Every Index component is bound to the correct Index node
- [ ] Every table/chart that should filter has Index sync enabled for
      the relevant dimensions
- [ ] Changing an index selection in preview mode updates all
      expected components
- [ ] Dependent indexes update correctly when a parent index changes
- [ ] No component shows stale data after an index change

---

## 4. Input Components

### 4.1 Scalar Input (single value)
Use for rates, thresholds, flags, or any single parameter a user adjusts.

Configuration checklist:
- [ ] Title set (visible label to the user)
- [ ] Data type configured: Float, Integer, String, Boolean, Date
- [ ] Validation rule set: Range (min/max for numbers), Required, Pattern (for strings)
- [ ] Default value defined (so the model has a starting state)

Example: discount rate input (0–100%)
- Data type: Float
- Validation: Range, min 0, max 100
- Default: 10

**Never leave an Input Scalar without a validation rule.** An unconstrained
input can receive values that break downstream calculations silently.

### 4.2 Form and Cube Inputs (tabular and multidimensional)
For structured data entry (budget tables, forecast inputs, plan matrices).

- **Form** — tabular input stored in DB. Users edit rows directly in a Table component.
- **Cube** — multidimensional input stored in DB. Used for multi-dimensional planning
  matrices (Product × Region × Month).

Configuration checklist:
- [ ] Input node created in the diagram (Form or Cube type)
- [ ] Fields/dimensions configured in the Input node wizard
- [ ] Table component in the interface is bound to the input node
- [ ] Cell editability enabled in Table component settings
- [ ] Save/refresh button present when data entry triggers a backend process

### 4.3 Selector Input
For single or multi-value selection from a predefined list.

- Source: can be bound to an Index node (dynamic list) or a static list.
- Use when the user needs to choose a scenario, a period, or a mode.

---

## 5. Charts and Visualization

### 5.1 Chart configuration
Every chart requires three elements:
1. **Dimension** — the X axis or grouping (e.g. Month, Product).
2. **Measure** — the Y axis value (e.g. Sales, Margin%).
3. **Series** *(optional)* — color grouping (e.g. Region, Scenario).

If the underlying node is an xarray DataArray, Pyplan maps dimensions
automatically. If it is a DataFrame, you configure the pivot manually
in the chart configuration panel.

### 5.2 Chart type selection guide
| Chart type | Best for |
|------------|---------|
| Column / Bar | Comparisons across categories (sales by product) |
| Line | Trends over time (monthly revenue) |
| Area | Cumulative trends or stacked contributions |
| Pie / Donut | Part-to-whole (max 5–6 segments — avoid for >6) |
| Scatter | Correlation between two measures |
| Waterfall | Variance analysis (budget vs actual bridge) |
| Heatmap | Matrix of values (product × region performance) |

### 5.3 Conditional formatting
Use to highlight exceptions without requiring a user to scan the table:

- Green / red for positive / negative variance.
- Traffic light (green/amber/red) for KPI thresholds.
- Progress bar in table cells for completion %.

Configure in component settings → Styles → Conditional format.
Always test conditional rules with edge values (zero, negative, maximum).

When a Brand Token Sheet is active, use semantic color tokens for
conditional formatting:
- Positive / success → --color-success
- Warning / near-threshold → --color-warning
- Negative / error → --color-error

Never hardcode green/red/amber values when a Brand Token Sheet exists.

---

## 6. Interface Layout and UX Patterns

### 6.1 Planning app layout pattern
Recommended structure for a standard planning interface:

```
┌─────────────────────────────────────────────┐
│  HEADER: title + key KPI indicators (1 row) │
├──────────────┬──────────────────────────────┤
│  FILTERS     │  MAIN CONTENT                │
│  Index Year  │  Primary table or chart      │
│  Index Region│                              │
│  Index Prod  │                              │
├──────────────┴──────────────────────────────┤
│  SECONDARY: supporting chart or detail table│
└─────────────────────────────────────────────┘
```

- Filters on the left or top — never buried in the content area.
- KPI indicators at the top — give the user immediate context.
- Primary visualization dominant — secondary content below or in a tab.

### 6.2 Navigation pattern
For apps with multiple interfaces, always include a **Menu component** on
a home interface or in a persistent header:

- Use descriptive labels (not "Interface 1", "Interface 2").
- Group interfaces by business area (Demand, Finance, Supply, Summary).
- Set permissions per interface to control access by department.

### 6.3 Interface permissions
Each interface can have department-level access control:
- **View only:** standard users see the interface, cannot edit inputs.
- **Edit:** planning users can modify input values.
- **Hidden:** interface not visible to the department.

Configure in Interface Manager → context menu → Set Permissions.
Always verify permissions are set before publishing to Public workspace.

### 6.4 Edit vs view mode
Interfaces open in **view mode** by default for end users.
**Edit mode** is for developers — it exposes the component grid and
configuration panels. Never deliver an interface still open in edit mode.

---

## 7. Workspace and Publishing

### 7.1 Workspace types
| Workspace | Who sees it | When to use |
|-----------|------------|------------|
| My Apps (private) | Developer only | Development and testing |
| Teams | Department members | Shared development, UAT |
| Public Apps | All authorized users | Final published solution |

**Development flow:** build in My Apps → test in Teams with key users
→ publish to Public Apps when approved.

Never publish directly to Public Apps from My Apps without a Teams review.

### 7.2 Save As pattern
When creating a client-specific version of a base app:
1. Open the base app.
2. Save As → "Save application in my workspace" (for initial copy).
3. Rename to follow project naming convention.
4. Modify for the client's data sources and requirements.

### 7.3 Versioning
Pyplan supports multiple versions of an app. Use versions for:
- Scenario comparison (Base vs Optimistic vs Pessimistic).
- Period cycles (2024 Budget vs 2025 Budget).
- Rollback points before a major structural change.

---

## 8. Brand Identity Application

This section applies when a Brand Token Sheet has been produced and
approved by the Brand Design skill. Pyplan Interfaces consumes the
tokens — it does not make independent color or typography decisions.

If no Brand Token Sheet exists and the project has a visible UI for
a named client, flag it before building any interface:

> "No Brand Token Sheet found. Run $skills brand-design to extract
> client brand tokens before building client-facing interfaces."

### 8.1 Native component styling

**Charts**
- Apply the data visualization palette from the Brand Token Sheet
  to chart series colors, in the order defined (--color-data-1 first,
  --color-data-2 second, etc.)
- Set chart background to --color-bg or --color-surface
- Apply --color-primary to highlight series or selected states
- Configure in component settings → Series → Color

**Indicators / KPIs**
- Primary value color: --color-text-primary
- Positive variance: --color-success
- Negative variance: --color-error
- Background: --color-surface
- Configure in component settings → Styles → Value color

**Tables**
- Header background: --color-primary or --color-surface (depending on
  brandbook prominence of primary color in data tables)
- Header text: ensure contrast compliance (white on dark, dark on light)
- Alternating rows: --color-bg and --color-surface (subtle differentiation)
- Conditional formatting colors: use semantic tokens, never hardcoded hex
- Configure in component settings → Styles

**Index and filter components**
- Selected chip/tag background: --color-primary
- Selected chip/tag text: white or --color-bg (per contrast rule)
- Unselected: --color-surface with --color-border

### 8.2 HTML components for brand-critical surfaces

Use HTML components (not native Pyplan components) when:
- The homescreen requires logo placement and brand colors in a layout
  that native components cannot achieve
- A persistent header with logo + navigation needs precise brand control
- A section divider or decorative element from the brandbook must appear

HTML component implementation pattern:

The HTML component accepts raw HTML/CSS. Use inline styles with the
token values from the Brand Token Sheet (Pyplan does not support
CSS custom properties natively — substitute actual hex values):

```html
<!-- Homescreen header example -->
<div style="
  background-color: #[--color-primary hex];
  padding: 24px 32px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-radius: 8px;
">
  <img src="[logo-url]" alt="[Client] logo"
       style="height: 40px; width: auto;" />
  <div>
    <h1 style="
      color: #ffffff;
      font-family: '[--font-primary]', sans-serif;
      font-size: 22px;
      font-weight: 700;
      margin: 0;
    ">[Application Title]</h1>
    <p style="
      color: rgba(255,255,255,0.8);
      font-family: '[--font-primary]', sans-serif;
      font-size: 14px;
      margin: 4px 0 0;
    ">[Subtitle or tagline]</p>
  </div>
</div>
```

Logo hosting: logos must be hosted at a URL accessible from the Pyplan
instance (client CDN, SharePoint public link, or Pyplan file storage).
Never reference local file paths.

### 8.3 Homescreen design pattern

The homescreen is the most brand-visible screen. It sets the tone for
the entire application and is the primary surface for client approval.

Recommended homescreen structure:

```
┌──────────────────────────────────────────────────┐
│  HTML: header with logo + app title (brand color) │
├──────────────┬───────────────────────────────────┤
│  HTML:       │  KPI indicators (3–5 key metrics)  │
│  navigation  │  styled with brand tokens          │
│  menu cards  ├───────────────────────────────────┤
│  with icons  │  Summary chart (primary data viz)  │
│  and brand   │  using data visualization palette  │
│  colors      │                                    │
└──────────────┴───────────────────────────────────┘
```

Navigation menu cards (HTML):
- Background: --color-primary or --color-surface
- Icon: from a web-safe icon set (Material Icons CDN, or inline SVG)
- Label: --font-primary, --font-size-label
- Hover state: slightly darker shade of --color-primary (darken by 10%)
- Each card links to a Pyplan interface via the Menu component or HTML anchor

### 8.4 Consistency enforcement

Once the Brand Token Sheet is active, flag any deviation as a finding
in the QA report:

🎨 BD-[N] — [title]
Location: [interface name and component]
Issue: [what color or font deviates from the Brand Token Sheet]
Token: [which token should have been used]
Fix: [exact value to apply]

Brand findings are classified as:
- 🚨 Must fix — logo misuse, completely wrong color family, contrast failure
- ⚠️ Should improve — hardcoded hex that happens to match but is not token-referenced
- 💡 Suggestion — minor visual refinement within the brand system

### 8.5 Client approval flow for visual identity

Before presenting interfaces to the client, complete this checklist:

- [ ] Brand Token Sheet approved by client (or explicitly waived)
- [ ] Homescreen built and reviewed internally by G7 before client demo
- [ ] Logo version and placement follows brandbook rules
- [ ] Data visualization palette applied consistently across all charts
- [ ] Conditional formatting uses semantic tokens
- [ ] No hardcoded colors outside of HTML components (and those match tokens)
- [ ] Font loading verified — primary font available in client's Pyplan instance

Client approval sequence:
1. Present homescreen first — it is the fastest way to get brand alignment
2. Once homescreen is approved, apply the same tokens to all report screens
3. Present report screens as a set — not one by one
4. After final approval, lock the Brand Token Sheet (mark as Approved in SPEC.md §C)

---

## 9. QA Checklist — Interface Surface

Run these checks on every $qa for Pyplan projects (contributes to Layer 5):

**Functional**
- [ ] All Index components are bound to the correct Index nodes
- [ ] Index sync is enabled on all tables/charts that should respond to filters
- [ ] Changing each Index selection updates all expected components in preview
- [ ] All Input Scalar components have data type and validation rules configured
- [ ] All Input Scalar components have a default value set
- [ ] Form and Cube inputs have cell editability enabled where expected
- [ ] All charts have Dimension and Measure configured (no empty axes)
- [ ] Conditional formatting rules tested with edge values
- [ ] Interface titles and component titles are descriptive (no "Node Result", "Chart 1")
- [ ] Navigation menu present and links to all relevant interfaces
- [ ] Interface permissions set correctly per department before publishing
- [ ] No interface delivered still open in edit mode
- [ ] App published to correct workspace (My / Teams / Public) per deployment stage

**HTML interfaces (when the project has any)**
- [ ] Run the HTML interface surface checklist in section 11.8

**Brand (when Brand Token Sheet is active)**
- [ ] Homescreen logo version matches brandbook permitted versions
- [ ] Logo minimum size respected (≥ brandbook digital minimum)
- [ ] Primary color applied consistently across headers and key UI elements
- [ ] Data visualization palette applied in defined order across all charts
- [ ] Conditional formatting uses semantic color tokens, not hardcoded hex
- [ ] No unapproved color deviations from Brand Token Sheet
- [ ] Primary font loading verified in client Pyplan instance
- [ ] Brand Token Sheet status is Approved in SPEC.md §C before delivery

---

## 10. Common Errors and Fixes

| Error | Likely cause | Fix |
|-------|-------------|-----|
| Table shows empty after index change | Index sync not enabled on table | Enable Index sync for the relevant dimension in table config |
| Chart shows no data | Dimension or Measure not configured | Open chart config and assign Dimension + Measure |
| Input change does not trigger recalculation | Input component not bound to an Input node | Check node binding in component config |
| Filter shows all values regardless of selection | Index node not correctly referenced in upstream node code | Verify the upstream node uses the Index node ID as filter |
| Interface opens in edit mode for end users | Edit mode not closed before saving | Exit edit mode, then save the interface |
| Form cells not editable | Table component editability not enabled | Component config → enable cell editing |
| KPI shows wrong format | Value format not set | Component config → Styles → Value format |
| Department cannot see interface | Permission not set | Interface Manager → Set Permissions → add department |
| Logo not displaying in HTML component | Local file path used instead of URL | Host logo on accessible URL and reference it |
| Font not rendering in Pyplan | Font not available in client instance | Use web-safe fallback or load via Google Fonts CDN in HTML component |
| Chart colors not matching brand | Data viz palette not applied | Set series colors manually in chart config using Brand Token Sheet hex values |


---

## 11. HTML Interfaces

An **HTML interface** is an interface whose entire screen is a single,
self-contained web page (HTML, CSS and JavaScript) instead of a component
grid. It renders as a sandboxed mini-app that talks to the model through
Python callbacks. Use it for bespoke dashboards, forms and tools whose
layout or interaction goes beyond what standard components express.

HTML interfaces are designed to be created by AI agents - Pyplan agents or
external AI clients via Pyplan MCP - and are the DEFAULT type whenever an
agent is asked to create an interface. SDAD treats every AI-generated or
AI-modified HTML interface as an increment (Build-via-AI guardrails in
CLAUDE.md): announce, approve, build, then run the 11.8 checklist.

### 11.1 Choosing the right option

| Option | What it is | When to use |
|--------|-----------|-------------|
| Component interface | Grid of draggable components | Standard dashboards and input/output screens (sections 2-10) |
| Dynamic HTML component | One HTML block inside a component interface, wired via actions table | A custom card, banner or block INSIDE an otherwise standard interface (section 8.2) |
| HTML interface | The whole interface is a web page driven by Python callbacks | Fully custom layout or tailored tool; any screen built by an AI agent |

### 11.2 Anatomy: HTML page + Python callbacks

An HTML interface stores two parts together: the HTML page and a Python
class. The Python code runs inside the model namespace - exactly like a
node definition - so it references nodes by name. Only methods decorated
with @callback are reachable from the page.

```python
from pyplan_core.html_interface import HTMLInterfaceBase, callback

class HTMLInterface(HTMLInterfaceBase):

    # Getter: read-only, returns JSON-friendly data for the page.
    @callback
    def get_sales(self, page: int = 0, page_size: int = 50) -> list:
        df = sales_data[sales_data.year == selected_year]
        start = page * page_size
        return df.iloc[start:start + page_size].to_dict("records")

    # Mutator: changes the model, then reports which widgets are stale.
    @callback
    def set_year(self, year: int) -> dict:
        self.set_input('selected_year', year)
        return {"refresh": self.get_nodes_to_refresh(['sales_table', 'profit_kpi'])}
```

Rules:
- Getters read from the model and return JSON-friendly data (lists, dicts,
  numbers, strings). Never return raw DataFrames or xarray objects.
- Mutators change the model and return the list of widgets to refresh, so
  the page re-fetches only what changed.
- Parameters are typed (int, float, str, bool, list) - Pyplan coerces the
  values coming from the page automatically.
- Selectors are read by name: if the user changes a selector elsewhere in
  the app, the next callback sees the updated value.

Model-write helpers (never touch model internals directly):
- self.set_input(node_id, value) - set a selector or input scalar. For a
  multi-select selector, pass the full list of selected values.
- self.set_form_values(node_id, changes) - apply cell edits to a form;
  changes is a list of {'row', 'column', 'value'} items.
- self.get_nodes_to_refresh(node_ids) - given the widgets the interface
  renders, returns the subset that became stale after a change.

### 11.3 The window.pyplan bridge (HTML side)

All page-to-model communication goes through the built-in bridge:

- window.pyplan.callback(method, params) - call a Python @callback,
  returns a promise with the result.
- window.pyplan.on(event, handler) - react to events sent from Pyplan.
- window.pyplan.toast(message, kind) - notification: "info", "success",
  "warning", "error". Failed-callback errors surface automatically.
- window.pyplan.import(url) - dynamically import an external JS module
  (use this instead of a bare import()).

### 11.4 Linking to the model and the app

- Mark node-backed titles with data-pyplan-nodes="node_id" (comma-separate
  several ids). Clicking opens the node popup with a Go-to-node link into
  the influence diagram - this surfaces HOW a number is computed.
- Plain anchors navigate in-app: /interfaces/<INTERFACE_ID>,
  /code/go-to?nodeId=<id>, /files. In-app paths keep the shell mounted;
  external http(s)/mailto links open in a new tab.
- External libraries, fonts, styles and images: write normal URLs - Pyplan
  re-routes them through a same-origin proxy (works on restricted corporate
  networks). For dynamic JS modules use window.pyplan.import.

### 11.5 Sandbox constraints (hard rules)

The page runs in a sandboxed frame with an isolated origin. It:
- cannot read cookies, localStorage, or the surrounding app data;
- cannot make authenticated requests on its own - ALL model communication
  goes through window.pyplan.callback over a short-lived session token;
- cannot embed third-party pages via iframe (external scripts/styles/fonts/
  images ARE allowed).

Consequence: persisting state MUST go through the model via callbacks.
Toolbar differences: Refresh reloads the page and re-runs initial calls
(also picks up code edits); custom views and screenshot are not available.

### 11.6 G7 design rules

- Default routing: standard dashboards -> component interface; fully custom
  layout or AI-built screens -> HTML interface; one custom block inside a
  standard screen -> dynamic HTML component.
- Record the interface type per screen in SPEC section 3 / section 5.
- Brand identity: apply the Brand Token Sheet exactly as in section 8 -
  substitute actual hex values, never hardcode off-brand colors.
- Iterate with the agent in plain language first; drop to direct HTML or
  Python edits only for fine-tuning.

### 11.7 Common errors and fixes

| Error | Likely cause | Fix |
|-------|-------------|-----|
| Page loads but shows no data | Initial callback not awaited or failed silently | Await window.pyplan.callback in an async init and surface errors via toast |
| Stale widgets after an input change | Mutator does not return refresh list | Return get_nodes_to_refresh([...]) from every mutator |
| State lost on refresh | Page relied on localStorage or cookies | Persist through the model via set_input / set_form_values |
| External JS module fails to load | Bare dynamic import() used | Use window.pyplan.import(url) |
| Embedded page does not render | iframe used | Not supported - link out or rebuild the content inline |
| Callback receives wrong types | Untyped parameters | Type every parameter (int, float, str, bool, list) |

### 11.8 QA checklist - HTML interface surface

Run on every $qa touching an HTML interface (contributes to Layer 5):

- [ ] All page-model traffic goes through window.pyplan.callback - no direct fetch/XHR
- [ ] Getters return JSON-friendly data (lists, dicts, numbers, strings)
- [ ] Mutators return refresh lists from get_nodes_to_refresh(...)
- [ ] Model writes only via set_input / set_form_values
- [ ] No cookie/localStorage reliance - state persists via the model
- [ ] Node-backed headings carry data-pyplan-nodes
- [ ] In-app navigation uses plain anchors with in-app paths
- [ ] External JS modules load via window.pyplan.import; no iframe embeds
- [ ] Errors surfaced to the user (toast or automatic callback error)
- [ ] Brand tokens applied when a Brand Token Sheet is active
- [ ] Interface type recorded in SPEC section 3 / section 5