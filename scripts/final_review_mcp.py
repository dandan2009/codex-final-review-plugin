#!/usr/bin/env python3
"""MCP helpers for the final-review plugin.

The tool is intentionally read-only. It collects the review packet that Codex
will pass to reviewer passes, but it does not edit files, stage changes, or run
tests.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from shutil import which
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    "final-review",
    instructions=(
        "Collect read-only review context for final-review workflows. "
        "Use before running reviewer passes."
    ),
)


Scope = Literal["uncommitted", "staged", "mr", "pr"]

MAX_DIFF_CHARS = 180_000
MAX_UNTRACKED_BYTES = 80_000

SECRET_NAME_PARTS = (
    ".env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "private",
    "id_rsa",
)
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".crt", ".cer")


def _run(args: list[str], cwd: Path, timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"ok": False, "cmd": args, "returncode": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "cmd": args,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": f"timed out after {timeout}s",
        }

    return {
        "ok": result.returncode == 0,
        "cmd": args,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _repo_root(cwd: str | None) -> tuple[Path | None, dict[str, Any] | None]:
    start = Path(cwd or os.getcwd()).expanduser().resolve()
    result = _run(["git", "rev-parse", "--show-toplevel"], start)
    if not result["ok"]:
        return None, result
    return Path(result["stdout"].strip()).resolve(), None


def _clip(text: str, limit: int = MAX_DIFF_CHARS) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit] + "\n\n[truncated]\n", True


def _safe_untracked_path(path: str) -> bool:
    lowered = path.lower()
    if any(part in lowered for part in SECRET_NAME_PARTS):
        return False
    if lowered.endswith(SECRET_SUFFIXES):
        return False
    return True


def _read_small_text(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {"included": False, "reason": str(exc)}
    if len(data) > MAX_UNTRACKED_BYTES:
        return {"included": False, "reason": f"larger than {MAX_UNTRACKED_BYTES} bytes"}
    if b"\x00" in data:
        return {"included": False, "reason": "binary file"}
    try:
        return {"included": True, "content": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"included": False, "reason": "not utf-8 text"}


def _command_text(result: dict[str, Any], limit: int = MAX_DIFF_CHARS) -> dict[str, Any]:
    stdout, truncated_stdout = _clip(result["stdout"], limit)
    stderr, truncated_stderr = _clip(result["stderr"], 20_000)
    return {
        "cmd": result["cmd"],
        "ok": result["ok"],
        "returncode": result["returncode"],
        "stdout": stdout,
        "stderr": stderr,
        "truncated": truncated_stdout or truncated_stderr,
    }


def _collect_untracked(root: Path) -> list[dict[str, Any]]:
    result = _run(["git", "ls-files", "--others", "--exclude-standard"], root)
    if not result["ok"]:
        return [{"error": result["stderr"]}]

    files: list[dict[str, Any]] = []
    for rel in [line for line in result["stdout"].splitlines() if line.strip()]:
        entry: dict[str, Any] = {"path": rel}
        if not _safe_untracked_path(rel):
            entry.update({"included": False, "reason": "possible secret or private key"})
        else:
            entry.update(_read_small_text(root / rel))
        files.append(entry)
    return files


def _collect_uncommitted(root: Path) -> dict[str, Any]:
    status = _run(["git", "status", "--short"], root)
    diff_stat = _run(["git", "diff", "--stat"], root)
    diff = _run(["git", "diff"], root)
    cached_stat = _run(["git", "diff", "--cached", "--stat"], root)
    cached = _run(["git", "diff", "--cached"], root)

    return {
        "scope": "uncommitted",
        "repo_root": str(root),
        "status": _command_text(status, 30_000),
        "diff_stat": _command_text(diff_stat, 30_000),
        "diff": _command_text(diff),
        "cached_diff_stat": _command_text(cached_stat, 30_000),
        "cached_diff": _command_text(cached),
        "untracked_files": _collect_untracked(root),
    }


def _collect_staged(root: Path) -> dict[str, Any]:
    status = _run(["git", "status", "--short"], root)
    cached_stat = _run(["git", "diff", "--cached", "--stat"], root)
    cached = _run(["git", "diff", "--cached"], root)
    unstaged = _run(["git", "diff", "--name-only"], root)
    untracked = _run(["git", "ls-files", "--others", "--exclude-standard"], root)

    unstaged_files = [line for line in unstaged["stdout"].splitlines() if line.strip()]
    untracked_files = [line for line in untracked["stdout"].splitlines() if line.strip()]
    contamination = bool(unstaged_files or untracked_files)

    return {
        "scope": "staged",
        "repo_root": str(root),
        "status": _command_text(status, 30_000),
        "cached_diff_stat": _command_text(cached_stat, 30_000),
        "cached_diff": _command_text(cached),
        "contamination": {
            "present": contamination,
            "unstaged_files": unstaged_files,
            "untracked_files": untracked_files,
            "guidance": (
                "Do not treat checks run in this dirty worktree as proof that staged-only code passes."
                if contamination
                else "No unstaged or untracked contamination detected."
            ),
        },
    }


def _collect_pr(root: Path, identifier: str | None) -> dict[str, Any]:
    if which("gh") is None:
        return {"scope": "pr", "repo_root": str(root), "error": "gh CLI not found"}
    target = identifier or ""
    view_args = [
        "gh",
        "pr",
        "view",
        *([target] if target else []),
        "--json",
        "number,title,baseRefName,headRefName,headRepository,headRepositoryOwner,url,state,isDraft",
    ]
    diff_args = ["gh", "pr", "diff", *([target] if target else [])]
    return {
        "scope": "pr",
        "repo_root": str(root),
        "identifier": identifier,
        "view": _command_text(_run(view_args, root), 60_000),
        "diff": _command_text(_run(diff_args, root)),
    }


def _collect_mr(root: Path, identifier: str | None) -> dict[str, Any]:
    if which("glab") is None:
        return {"scope": "mr", "repo_root": str(root), "error": "glab CLI not found"}
    target = identifier or ""
    view_args = ["glab", "mr", "view", *([target] if target else [])]
    diff_args = ["glab", "mr", "diff", *([target] if target else [])]
    return {
        "scope": "mr",
        "repo_root": str(root),
        "identifier": identifier,
        "view": _command_text(_run(view_args, root), 60_000),
        "diff": _command_text(_run(diff_args, root)),
    }


@mcp.tool()
def final_review_collect(scope: Scope, identifier: str | None = None, cwd: str | None = None) -> dict[str, Any]:
    """Collect read-only review context for a final-review run.

    Args:
        scope: One of "uncommitted", "staged", "mr", or "pr".
        identifier: Optional MR/PR URL, number, branch, or tool-specific identifier.
        cwd: Optional working directory. Defaults to the current process directory.
    """

    root, error = _repo_root(cwd)
    if root is None:
        return {"ok": False, "scope": scope, "error": "not a git repository", "detail": error}

    if scope == "uncommitted":
        packet = _collect_uncommitted(root)
    elif scope == "staged":
        packet = _collect_staged(root)
    elif scope == "pr":
        packet = _collect_pr(root, identifier)
    elif scope == "mr":
        packet = _collect_mr(root, identifier)
    else:
        return {"ok": False, "error": f"unsupported scope: {scope}"}

    packet["ok"] = "error" not in packet
    packet["read_only"] = True
    packet["notes"] = [
        "This tool only collects context. Codex still validates findings and applies accepted fixes.",
        "Independent subagents are governed by the active Codex tool rules and user authorization.",
    ]
    return packet


if __name__ == "__main__":
    mcp.run()
