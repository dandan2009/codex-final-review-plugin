# Codex Final Review Plugin

[English](README.md) | [简体中文](README.zh-CN.md)

`final-review` is a local Codex plugin for the final code-review loop before shipping. It lets you type short prompts such as:

```text
$final-review uncommitted
$final-review staged
$final-review mr 123
$final-review pr 123
```

The plugin resolves the requested diff, collects review context, runs two review perspectives, validates findings, fixes true issues, reruns relevant checks, performs impact review, and reports remaining risk.

## What It Includes

- A Codex plugin manifest: `.codex-plugin/plugin.json`
- A `final-review` skill: `skills/final-review/SKILL.md`
- A local stdio MCP server: `scripts/final_review_mcp.py`
- A one-command installer: `install.py`

## Requirements

- Codex desktop app with local plugin support
- Python 3.10 or newer
- `git`
- Optional for PR/MR review:
  - GitHub CLI: `gh`
  - GitLab CLI: `glab`

The installer creates a plugin-local `.venv` and installs Python dependencies from `requirements.txt`. To install dependencies manually instead:

```bash
python3 -m pip install mcp
```

For GitHub PR review, authenticate `gh`:

```bash
gh auth login
```

For GitLab MR review, authenticate `glab`:

```bash
glab auth login
```

## Install

Clone the repository:

```bash
git clone https://github.com/dandan2009/codex-final-review-plugin.git
cd codex-final-review-plugin
```

Run the installer:

```bash
python3 install.py
```

The installer:

- Creates `~/plugins/final-review` as a symlink to this checkout
- Creates `~/plugins/final-review/.venv` and installs Python dependencies
- Creates or updates `~/.agents/plugins/marketplace.json`
- Adds the plugin entry required by Codex
- Leaves your repository checkout as the source of truth for updates

Restart Codex after installation so the plugin and MCP server are discovered.

## Usage

Review all local uncommitted changes:

```text
$final-review uncommitted
```

Review only staged changes:

```text
$final-review staged
```

Review a merge request:

```text
$final-review mr 123
$final-review mr https://gitlab.example.com/group/project/-/merge_requests/123
```

Review a pull request:

```text
$final-review pr 123
$final-review pr https://github.com/owner/repo/pull/123
```

For Chinese commands, see [简体中文](README.zh-CN.md).


If Codex needs explicit permission to open independent reviewer sub-sessions, it will ask:

```text
May I open two independent read-only sub-sessions for this final-review?
```

Answer yes to use two independent read-only reviewers. If you decline, or if subagents are unavailable, the workflow falls back to local two-pass review and reports that downgrade.

## How It Works

The plugin has three layers:

- Plugin: makes the capability installable and discoverable in Codex.
- Skill: defines the final-review workflow, validation rules, ledger states, and stopping conditions.
- MCP: collects review context deterministically and read-only.

The MCP tool is local, not remote. Codex starts:

```bash
python3 ./scripts/run_mcp.py
```

through stdio. The wrapper uses the plugin-local `.venv` when present. It does not send your code to a third-party server. It only runs local git/CLI commands and returns structured context to Codex.

## MCP Tool

The plugin exposes one MCP tool:

```text
final_review_collect(scope, identifier?, cwd?)
```

Supported scopes:

- `uncommitted`: collects `git status`, `git diff`, `git diff --cached`, and small safe untracked regular files
- `staged`: collects `git diff --cached` and reports unstaged/untracked contamination
- `pr`: collects `gh pr view` and `gh pr diff`
- `mr`: collects `glab mr view` and `glab mr diff`

The tool is read-only. It does not edit files, stage files, run tests, or create commits.

## Update

If installed with the default symlink mode:

```bash
cd ~/plugins/final-review
git pull
```

If you cloned somewhere else, update that checkout:

```bash
cd /path/to/codex-final-review-plugin
git pull
```

Then restart Codex.

## Uninstall

Remove the symlink or copied plugin:

```bash
rm -rf ~/plugins/final-review
```

Then remove the `final-review` entry from:

```text
~/.agents/plugins/marketplace.json
```

Restart Codex.

## More Docs

- [Installation Guide](docs/INSTALL.md)
- [Usage Guide](docs/USAGE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security Notes](docs/SECURITY.md)
