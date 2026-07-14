"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .config import Config, config_path, load_config, save_config
from .scan import scan
from .server import serve


def _bool_prompt(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    value = input(f"{prompt} {suffix}: ").strip().lower()
    return default if not value else value in ("y", "yes")


def init_config(args: argparse.Namespace) -> int:
    current = load_config()
    if args.non_interactive:
        roots = args.project_root or current.project_roots or [str(Path.cwd())]
        owner = args.name or current.owner_name
        github = not args.no_github
    else:
        owner = input(f"Your name [{current.owner_name}]: ").strip() or current.owner_name
        defaults = ", ".join(current.project_roots) or str(Path.cwd())
        raw_roots = input(f"Project folders, comma-separated [{defaults}]: ").strip()
        roots = [part.strip() for part in raw_roots.split(",") if part.strip()] if raw_roots else (current.project_roots or [str(Path.cwd())])
        github = _bool_prompt("Use GitHub PR history?", current.github_enabled)
    config = Config(
        owner_name=owner or "You", project_roots=[str(Path(root).expanduser().resolve()) for root in roots],
        claude_dir=args.claude_dir or current.claude_dir, codex_dir=args.codex_dir or current.codex_dir,
        github_enabled=github, port=args.port or current.port, scan_depth=current.scan_depth,
        project_names=current.project_names,
    )
    path = save_config(config)
    print(f"Config saved: {path}")
    print(f"Owner: {config.owner_name} · roots: {len(config.roots())}")
    return 0


def doctor(config: Config) -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python >=3.10", sys.version_info >= (3, 10), sys.version.split()[0]))
    checks.append(("Config", config_path().exists(), str(config_path())))
    checks.append(("Project roots", bool(config.roots()), ", ".join(str(root) for root in config.roots()) or "none"))
    checks.append(("Claude adapter", config.resolved_claude_dir() is not None, str(config.resolved_claude_dir() or "not found")))
    checks.append(("Codex adapter", config.resolved_codex_dir() is not None, str(config.resolved_codex_dir() or "not found")))
    gh_ok = False
    if shutil.which("gh"):
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=10)
        gh_ok = result.returncode == 0
    checks.append(("GitHub adapter", not config.github_enabled or gh_ok, "authenticated" if gh_ok else "disabled or unavailable"))
    for label, ok, detail in checks:
        print(f"{'PASS' if ok else 'WARN'}  {label}: {detail}")
    required = checks[0][1] and checks[2][1]
    return 0 if required else 1


def show_config(config: Config) -> int:
    print(json.dumps(config.__dict__, indent=2))
    return 0


def set_config(config: Config, key: str, value: str) -> int:
    if key == "name":
        config.owner_name = value.strip() or "You"
    elif key == "port":
        config.port = int(value)
    else:
        print(f"Unknown config key: {key}. Supported: name, port", file=sys.stderr)
        return 2
    save_config(config)
    print(f"Updated {key}: {value}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="coding-control-tower", description="Project-first coding work ledger")
    root.add_argument("--version", action="version", version=__version__)
    sub = root.add_subparsers(dest="command")
    init = sub.add_parser("init", help="Configure owner and project folders")
    init.add_argument("--name")
    init.add_argument("--project-root", action="append")
    init.add_argument("--claude-dir")
    init.add_argument("--codex-dir")
    init.add_argument("--port", type=int)
    init.add_argument("--no-github", action="store_true")
    init.add_argument("--non-interactive", action="store_true")
    scan_parser = sub.add_parser("scan", help="Write one state snapshot")
    scan_parser.add_argument("--refresh-github", action="store_true")
    serve_parser = sub.add_parser("serve", help="Run local dashboard server")
    serve_parser.add_argument("--no-open", action="store_true")
    sub.add_parser("doctor", help="Check environment and adapters")
    config_parser = sub.add_parser("config", help="Show or change configuration")
    config_sub = config_parser.add_subparsers(dest="config_command")
    set_parser = config_sub.add_parser("set")
    set_parser.add_argument("key", choices=("name", "port"))
    set_parser.add_argument("value")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    config = load_config()
    if args.command == "init":
        return init_config(args)
    if args.command == "scan":
        path = scan(config, args.refresh_github)
        print(f"Snapshot: {path}")
        return 0
    if args.command == "doctor":
        return doctor(config)
    if args.command == "config":
        return set_config(config, args.key, args.value) if args.config_command == "set" else show_config(config)
    if args.command == "serve":
        serve(config, open_browser=not args.no_open)
        return 0
    if not config_path().exists() and sys.stdin.isatty():
        init_config(argparse.Namespace(non_interactive=False, name=None, project_root=None, claude_dir=None, codex_dir=None, port=None, no_github=False))
        config = load_config()
    serve(config, open_browser=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

