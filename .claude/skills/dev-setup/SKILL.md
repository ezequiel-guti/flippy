---
name: dev-setup
description: >
  Activate this skill when the developer asks about onboarding, dev setup, or
  which native Claude Code features complement SDAD. Use when the user says
  "how do I set this up", "what tools should I install", "what features help
  with SDAD", "dev setup", "onboarding checklist", or asks about plan mode,
  hooks, skills, MCP, sub-agents, scheduled tasks, or the status line in the
  context of getting a project running. Triggered by the $sdad "Dev Setup"
  pointer. This skill points to live external docs — it never transcribes
  feature names, commands, or release dates (zero rot per roadmap C-014).
---

# Dev Setup — Claude Code features that complement SDAD

**Design rule (C-014, decided 2026-06-05):** this skill links to official, living docs
and gives a one-line stable-concept mapping to SDAD. It does NOT copy feature names,
commands, keybindings, or dates — those rot. When in doubt, follow the link.

**Canonical docs root:** https://code.claude.com/docs/en/overview
(verified live 2026-06-07; migrated from docs.claude.com — that host now 301-redirects here)

## Stable concept → SDAD mapping

| Claude Code concept | Official doc (stable) | How it maps to SDAD |
|---|---|---|
| CLAUDE.md / memory | https://code.claude.com/docs/en/memory | The project CLAUDE.md SDAD maintains — see $build step 5.5 protocol |
| Skills | https://code.claude.com/docs/en/skills | SDAD specialist skills in `.claude/skills/` (AI Architect, QA, Pyplan, etc.) |
| Hooks | https://code.claude.com/docs/en/hooks | SDAD Track B automation (SessionStart, PostToolUse, PreCompact) |
| MCP | https://code.claude.com/docs/en/mcp | $specout §7 MCP-vs-CLI rule (consumer) and §D @mcp_tool (Pyplan producer) |
| Sub-agents | https://code.claude.com/docs/en/sub-agents | SDAD $agent delegation (review / test / audit) |
| Routines / scheduled | https://code.claude.com/docs/en/routines | Recurring audits (e.g. periodic $verify audit) |
| CLI reference | https://code.claude.com/docs/en/cli-reference | `/model` + `/effort` switching for the §2.1b routing table |
| Settings | https://code.claude.com/docs/en/settings | Status line, permissions, env config |

## Notes
- Plan mode, recap, and other interactive features: see the docs index at
  https://code.claude.com/docs/en/overview rather than relying on a transcribed name
  or keybinding here (these change between releases).
- cc-status-line is documented in the SDAD CLAUDE.md "Required Environment Tool" section;
  it is the primary context-budget indicator (50% / 65% thresholds).
- §2.1 single-source validation for C-014: 🧠 [verificar — pendiente workflow G7].
