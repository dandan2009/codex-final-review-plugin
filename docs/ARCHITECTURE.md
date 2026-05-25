# Architecture

`final-review` is a Codex plugin with a skill and a local MCP server.

```text
Plugin
  .codex-plugin/plugin.json
  .mcp.json
  scripts/final_review_mcp.py
  skills/final-review/SKILL.md
```

## Plugin Layer

`.codex-plugin/plugin.json` makes the plugin installable and discoverable by Codex. It points Codex to:

- `skills/`
- `.mcp.json`

It also defines display metadata and default prompts.

## Skill Layer

`skills/final-review/SKILL.md` defines the workflow:

- Scope routing
- Diff collection rules
- Baseline checks
- Review pass protocol
- Subagent permission handling
- Finding schema
- Ledger state transitions
- Fix and verification rules
- Impact review
- Final report format

The skill is intentionally explicit because the workflow is high stakes: it can change code after validating findings.

## MCP Layer

`scripts/final_review_mcp.py` is a local stdio MCP server. It exposes:

```text
final_review_collect(scope, identifier?, cwd?)
```

It returns structured context for the chosen scope. It is read-only.

## Why Both Skill And MCP?

The MCP tool is deterministic and good at collecting context:

- Which git commands to run
- How to treat staged-only review
- How to detect contamination
- How to call `gh` and `glab`

The skill is procedural and good at controlling the review:

- What counts as a real finding
- When to fix
- When to reject
- How to avoid infinite loops
- What final report to produce

Codex uses both: MCP for evidence collection, skill for workflow and reasoning.

