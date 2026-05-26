# Architecture

`final-review` is a Codex plugin with a skill and a local MCP server.

```text
Plugin
  .codex-plugin/plugin.json
  .mcp.json
  scripts/run_mcp.py
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

For the second review perspective, the skill prefers real gstack-review when the current Codex environment exposes the gstack `review` / `gstack-review` skill. If it is unavailable or blocked, the workflow uses a built-in gstack-style structural checklist and reports the downgrade.

## MCP Layer

`scripts/run_mcp.py` is the entrypoint configured in `.mcp.json`. It starts the server with the plugin-local `.venv` when available.

`scripts/final_review_mcp.py` is the local stdio MCP server. It exposes:

```text
final_review_collect(scope, identifier?, cwd?)
```

It returns structured context for the chosen scope. It is read-only.

## Why Both Skill And MCP?

The MCP tool is deterministic and good at collecting context:

- Which git commands to run
- How to treat staged-only review
- How to detect contamination
- How to avoid reading untracked symlinks or paths outside the repository
- How to call `gh` and `glab`

The skill is procedural and good at controlling the review:

- What counts as a real finding
- When to fix
- When to reject
- How to avoid infinite loops
- What final report to produce

Codex uses both: MCP for evidence collection, skill for workflow and reasoning.
