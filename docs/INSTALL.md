# Installation Guide

This guide installs `final-review` as a personal Codex plugin.

## 1. Clone

```bash
git clone https://github.com/dandan2009/codex-final-review-plugin.git
cd codex-final-review-plugin
```

## 2. Install

Run:

```bash
python3 install.py
```

The installer creates `~/plugins/final-review`, creates a plugin-local `.venv`, installs `requirements.txt`, and updates `~/.agents/plugins/marketplace.json`.

## 3. Restart Codex

Restart Codex so it reloads local plugins and MCP servers.

## Manual Dependency Install

If you run the installer with `--no-deps`, install the MCP dependency yourself:

```bash
python3 -m pip install mcp
```

## Install Options

Use a physical copy instead of a symlink:

```bash
python3 install.py --copy
```

Replace an existing `~/plugins/final-review`:

```bash
python3 install.py --force
```

Skip dependency installation:

```bash
python3 install.py --no-deps
```

Use a specific Python interpreter for the plugin `.venv`:

```bash
python3 install.py --python /path/to/python3
```

The installer requires Python 3.10 or newer for the MCP dependency. If your system `python3` is older, it will try `python3.13`, `python3.12`, `python3.11`, and `python3.10` before failing with a clear message.

Install to a custom marketplace path:

```bash
python3 install.py --marketplace ~/.agents/plugins/marketplace.json
```

## Verify

In a Codex session, try:

```text
$final-review uncommitted
```

If the plugin is loaded correctly, Codex should use the final-review workflow. If independent subagents need permission, Codex will ask one short permission question before review.

## Troubleshooting

If Codex cannot start the MCP server, check Python can import `mcp`:

```bash
~/plugins/final-review/.venv/bin/python - <<'PY'
from mcp.server.fastmcp import FastMCP
print("mcp ok")
PY
```

If PR review fails, check GitHub CLI auth:

```bash
gh auth status
```

If MR review fails, check GitLab CLI auth:

```bash
glab auth status
```
