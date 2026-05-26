# Security Notes

## Local MCP

The MCP server is local. Codex starts it as:

```bash
python3 ./scripts/run_mcp.py
```

It communicates over stdio, not a remote HTTP server.

## Read-Only Context Collection

`final_review_collect` is designed to be read-only. It does not:

- Modify files
- Stage files
- Commit files
- Push code
- Run tests
- Open network connections by itself

For PR/MR scopes, it may call:

- `gh pr view`
- `gh pr diff`
- `glab mr view`
- `glab mr diff`

Those commands use your existing CLI authentication.

## Untracked Files

For uncommitted review, the MCP tool includes only small safe untracked text files. It skips likely secrets and private keys, including paths containing:

- `.env`
- `secret`
- `credential`
- `private`
- `id_rsa`

and files ending in:

- `.pem`
- `.key`
- `.p12`
- `.pfx`

It also skips untracked symlinks and files that resolve outside the repository root.

## Code Changes

The MCP tool never changes code. Code changes are made by Codex only after the skill validates a finding and marks it `accepted`.
