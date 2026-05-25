# Installation Guide

This guide installs `final-review` as a personal Codex plugin.

## 1. Clone

```bash
git clone https://github.com/dandan2009/codex-final-review-plugin.git
cd codex-final-review-plugin
```

## 2. Install Python Dependency

The local MCP server uses the Python `mcp` package:

```bash
python3 -m pip install mcp
```

If your Codex environment already provides `mcp`, this command may be unnecessary.

## 3. Run Installer

```bash
python3 install.py
```

By default, the installer creates:

```text
~/plugins/final-review -> /path/to/codex-final-review-plugin
```

and updates:

```text
~/.agents/plugins/marketplace.json
```

## 4. Restart Codex

Restart Codex so it reloads local plugins and MCP servers.

## Install Options

Use a physical copy instead of a symlink:

```bash
python3 install.py --copy
```

Replace an existing `~/plugins/final-review`:

```bash
python3 install.py --force
```

Install to a custom marketplace path:

```bash
python3 install.py --marketplace ~/.agents/plugins/marketplace.json
```

## Verify

In a Codex session, try:

```text
$final-review 未提交的代码
```

If the plugin is loaded correctly, Codex should use the final-review workflow. If independent subagents need permission, Codex will ask one short permission question before review.

## Troubleshooting

If Codex cannot start the MCP server, check Python can import `mcp`:

```bash
python3 - <<'PY'
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

