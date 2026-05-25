#!/usr/bin/env python3
"""Install the final-review plugin into a personal Codex marketplace."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


PLUGIN_NAME = "final-review"
MARKETPLACE_ENTRY = {
    "name": PLUGIN_NAME,
    "source": {
        "source": "local",
        "path": f"./plugins/{PLUGIN_NAME}",
    },
    "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    },
    "category": "Productivity",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the final-review Codex plugin.")
    parser.add_argument(
        "--marketplace",
        default=str(Path.home() / ".agents" / "plugins" / "marketplace.json"),
        help="Path to the personal marketplace.json file.",
    )
    parser.add_argument(
        "--target",
        default=str(Path.home() / "plugins" / PLUGIN_NAME),
        help="Plugin install path. Defaults to ~/plugins/final-review.",
    )
    parser.add_argument("--copy", action="store_true", help="Copy files instead of creating a symlink.")
    parser.add_argument("--force", action="store_true", help="Replace an existing install target.")
    return parser.parse_args()


def ensure_plugin_root(root: Path) -> None:
    required = [
        root / ".codex-plugin" / "plugin.json",
        root / ".mcp.json",
        root / "scripts" / "final_review_mcp.py",
        root / "skills" / "final-review" / "SKILL.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("This directory is not a complete final-review plugin checkout:\n" + "\n".join(missing))


def install_target(root: Path, target: Path, copy: bool, force: bool) -> None:
    target_parent = target.parent
    target_parent.mkdir(parents=True, exist_ok=True)

    if target.exists() or target.is_symlink():
        try:
            same_target = target.resolve() == root.resolve()
        except OSError:
            same_target = False
        if same_target:
            print(f"Plugin target already points to this checkout: {target}")
            return
        if not force:
            raise SystemExit(
                f"Install target already exists: {target}\n"
                "Re-run with --force to replace it, or pass --target for a different path."
            )
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()

    if copy:
        ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store")
        shutil.copytree(root, target, ignore=ignore)
        print(f"Copied plugin to {target}")
    else:
        os.symlink(root, target, target_is_directory=True)
        print(f"Linked plugin: {target} -> {root}")


def load_marketplace(path: Path) -> dict:
    if not path.exists():
        return {
            "name": "personal",
            "interface": {
                "displayName": "Personal",
            },
            "plugins": [],
        }

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    data.setdefault("name", "personal")
    data.setdefault("interface", {}).setdefault("displayName", "Personal")
    data.setdefault("plugins", [])
    return data


def upsert_marketplace(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_marketplace(path)

    plugins = data["plugins"]
    for index, plugin in enumerate(plugins):
        if plugin.get("name") == PLUGIN_NAME:
            plugins[index] = MARKETPLACE_ENTRY
            break
    else:
        plugins.append(MARKETPLACE_ENTRY)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Updated marketplace: {path}")


def check_mcp_dependency() -> None:
    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401
    except Exception:
        print(
            "Warning: Python cannot import mcp.server.fastmcp.\n"
            "Install it with: python3 -m pip install mcp",
            file=sys.stderr,
        )


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    target = Path(args.target).expanduser().resolve()
    marketplace = Path(args.marketplace).expanduser().resolve()

    ensure_plugin_root(root)
    install_target(root, target, copy=args.copy, force=args.force)
    upsert_marketplace(marketplace)
    check_mcp_dependency()

    print("\nDone. Restart Codex, then try:")
    print("$final-review 未提交的代码")


if __name__ == "__main__":
    main()
