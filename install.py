#!/usr/bin/env python3
"""Install the final-review plugin into a personal Codex marketplace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PLUGIN_NAME = "final-review"
MIN_PYTHON = (3, 10)
GSTACK_REPO = "https://github.com/garrytan/gstack.git"
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
        "--codex-config",
        default=str(Path.home() / ".codex" / "config.toml"),
        help="Path to Codex config.toml. Defaults to ~/.codex/config.toml.",
    )
    parser.add_argument(
        "--target",
        default=str(Path.home() / "plugins" / PLUGIN_NAME),
        help="Plugin install path. Defaults to ~/plugins/final-review.",
    )
    parser.add_argument("--copy", action="store_true", help="Copy files instead of creating a symlink.")
    parser.add_argument("--force", action="store_true", help="Replace an existing install target.")
    parser.add_argument("--no-deps", action="store_true", help="Skip creating .venv and installing Python deps.")
    parser.add_argument(
        "--no-gstack",
        action="store_true",
        help="Skip automatic gstack-review installation when the gstack review skill is missing.",
    )
    parser.add_argument(
        "--gstack-dir",
        default=str(Path.home() / "gstack"),
        help="Directory used when auto-installing gstack for Codex. Defaults to ~/gstack.",
    )
    parser.add_argument(
        "--python",
        default=None,
        help="Python 3.10+ interpreter to use when creating the plugin .venv.",
    )
    return parser.parse_args()


def ensure_plugin_root(root: Path) -> None:
    required = [
        root / ".codex-plugin" / "plugin.json",
        root / ".mcp.json",
        root / "scripts" / "run_mcp.py",
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
        ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store", ".venv")
        shutil.copytree(root, target, ignore=ignore)
        print(f"Copied plugin to {target}")
    else:
        try:
            os.symlink(root, target, target_is_directory=True)
            print(f"Linked plugin: {target} -> {root}")
        except OSError as exc:
            print(f"Could not create symlink ({exc}); copying plugin instead.")
            ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store", ".venv")
            shutil.copytree(root, target, ignore=ignore)
            print(f"Copied plugin to {target}")


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


def toml_basic_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def replace_toml_table(text: str, table: str, block: str) -> str:
    pattern = re.compile(rf"(?ms)^\[{re.escape(table)}\]\n.*?(?=^\[|\Z)")
    if pattern.search(text):
        return pattern.sub(block.rstrip() + "\n\n", text)

    separator = "" if not text or text.endswith("\n") else "\n"
    return text + separator + "\n" + block.rstrip() + "\n"


def upsert_codex_config(path: Path, marketplace_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    marketplace_block = "\n".join(
        [
            "[marketplaces.personal]",
            f"last_updated = {toml_basic_string(timestamp)}",
            'source_type = "local"',
            f"source = {toml_basic_string(str(marketplace_root))}",
        ]
    )
    plugin_block = "\n".join(
        [
            f'[plugins."{PLUGIN_NAME}@personal"]',
            "enabled = true",
        ]
    )

    text = replace_toml_table(text, "marketplaces.personal", marketplace_block)
    text = replace_toml_table(text, f'plugins."{PLUGIN_NAME}@personal"', plugin_block)
    path.write_text(text, encoding="utf-8")
    print(f"Updated Codex config: {path}")


def check_mcp_dependency() -> None:
    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401
    except Exception:
        print(
            "Warning: Python cannot import mcp.server.fastmcp.\n"
            "Install it with: python3 -m pip install mcp",
            file=sys.stderr,
        )


def venv_python(plugin_path: Path) -> Path:
    if os.name == "nt":
        return plugin_path / ".venv" / "Scripts" / "python.exe"
    return plugin_path / ".venv" / "bin" / "python"


def python_version(python: str) -> tuple[int, int] | None:
    result = subprocess.run(
        [
            python,
            "-c",
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        major, minor = result.stdout.strip().split(".", 1)
        return int(major), int(minor)
    except ValueError:
        return None


def select_python(requested: str | None) -> str:
    candidates = [requested] if requested else [
        sys.executable,
        "python3.13",
        "python3.12",
        "python3.11",
        "python3.10",
        "python3",
    ]

    checked: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        path = shutil.which(candidate) if os.sep not in candidate else candidate
        if not path:
            continue
        version = python_version(path)
        checked.append(f"{path} ({'.'.join(map(str, version)) if version else 'unknown'})")
        if version and version >= MIN_PYTHON:
            return path

    checked_text = "\n".join(f"- {item}" for item in checked) or "- no Python candidates found"
    raise SystemExit(
        "Python 3.10 or newer is required to install the MCP dependency.\n"
        "Install Python 3.10+ and rerun, or pass --python /path/to/python3.10+.\n"
        f"Checked:\n{checked_text}"
    )


def install_dependencies(plugin_path: Path, requested_python: str | None) -> None:
    requirements = plugin_path / "requirements.txt"
    if not requirements.exists():
        print("No requirements.txt found; skipping Python dependency install.")
        return

    python = select_python(requested_python)
    py = venv_python(plugin_path)
    if py.exists():
        existing_version = python_version(str(py))
        if not existing_version or existing_version < MIN_PYTHON:
            print(f"Existing .venv uses Python {existing_version}; rebuilding with {python}.")
            shutil.rmtree(plugin_path / ".venv")

    if not py.exists():
        subprocess.run([python, "-m", "venv", str(plugin_path / ".venv")], check=True)

    subprocess.run([str(py), "-m", "pip", "install", "-U", "pip"], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "-r", str(requirements)], check=True)
    print(f"Installed Python dependencies into {plugin_path / '.venv'}")


def gstack_review_skill_paths(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    return [
        home / ".codex" / "skills" / "gstack-review" / "SKILL.md",
        home / ".codex" / "skills" / "review" / "SKILL.md",
    ]


def has_gstack_review(home: Path | None = None) -> bool:
    return any(path.exists() for path in gstack_review_skill_paths(home))


def install_gstack_for_codex(gstack_dir: Path) -> bool:
    if not shutil.which("bun"):
        print(
            "Warning: gstack-review is missing, but automatic gstack install requires Bun.\n"
            "Install Bun from https://bun.sh/ and rerun this installer, or use the built-in gstack-style fallback.",
            file=sys.stderr,
        )
        return False

    if gstack_dir.exists():
        setup = gstack_dir / "setup"
        if not setup.exists():
            print(
                f"Warning: gstack install directory exists but does not look like gstack: {gstack_dir}\n"
                "Remove it or pass --gstack-dir to another path if you want automatic gstack installation.",
                file=sys.stderr,
            )
            return False
        print(f"Using existing gstack checkout: {gstack_dir}")
    else:
        if not shutil.which("git"):
            print(
                "Warning: gstack-review is missing, but automatic gstack install requires git.",
                file=sys.stderr,
            )
            return False
        gstack_dir.parent.mkdir(parents=True, exist_ok=True)
        print(f"gstack-review not found; cloning gstack into {gstack_dir}")
        subprocess.run(
            ["git", "clone", "--single-branch", "--depth", "1", GSTACK_REPO, str(gstack_dir)],
            check=True,
        )

    if not shutil.which("bash"):
        print(
            "Warning: gstack-review is missing, but automatic gstack setup requires bash.",
            file=sys.stderr,
        )
        return False

    subprocess.run(["bash", "./setup", "--host", "codex"], cwd=str(gstack_dir), check=True)
    return has_gstack_review()


def ensure_gstack_review(no_gstack: bool, gstack_dir: Path) -> None:
    if has_gstack_review():
        print("gstack-review is already available to Codex.")
        return

    if no_gstack:
        print(
            "gstack-review is not installed. Skipping because --no-gstack was passed; "
            "final-review will use the built-in gstack-style fallback."
        )
        return

    try:
        if install_gstack_for_codex(gstack_dir):
            print("Installed gstack-review for Codex.")
        else:
            print("gstack-review was not installed; final-review will use the built-in gstack-style fallback.")
    except subprocess.CalledProcessError as exc:
        print(
            f"Warning: automatic gstack install failed with exit code {exc.returncode}.\n"
            "final-review is installed and will use the built-in gstack-style fallback until gstack-review is available.",
            file=sys.stderr,
        )


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    target = Path(args.target).expanduser().resolve()
    marketplace = Path(args.marketplace).expanduser().resolve()
    codex_config = Path(args.codex_config).expanduser().resolve()
    gstack_dir = Path(args.gstack_dir).expanduser().resolve()

    ensure_plugin_root(root)
    install_target(root, target, copy=args.copy, force=args.force)
    if not args.no_deps:
        install_dependencies(target, args.python)
    upsert_marketplace(marketplace)
    upsert_codex_config(codex_config, marketplace.parents[2])
    ensure_gstack_review(args.no_gstack, gstack_dir)
    if args.no_deps:
        check_mcp_dependency()

    print("\nDone. Restart Codex, then try:")
    print("$final-review uncommitted")


if __name__ == "__main__":
    main()
