"""Portable configuration with no third-party dependencies."""

from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

APP_SLUG = "coding-control-tower"


def _home() -> Path:
    return Path.home()


def config_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA", _home() / "AppData" / "Roaming")) / APP_SLUG
    if system == "Darwin":
        return _home() / "Library" / "Application Support" / APP_SLUG
    return Path(os.environ.get("XDG_CONFIG_HOME", _home() / ".config")) / APP_SLUG


def state_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", _home() / "AppData" / "Local")) / APP_SLUG
    if system == "Darwin":
        return _home() / "Library" / "Application Support" / APP_SLUG / "state"
    return Path(os.environ.get("XDG_STATE_HOME", _home() / ".local" / "state")) / APP_SLUG


def _existing_default_roots() -> list[str]:
    candidates = [_home() / "Projects", _home() / "projects", _home() / "code", _home() / "dev"]
    return [str(p.resolve()) for p in candidates if p.is_dir()]


@dataclass
class Config:
    owner_name: str = "You"
    project_roots: list[str] = field(default_factory=_existing_default_roots)
    claude_dir: str | None = None
    codex_dir: str | None = None
    github_enabled: bool = True
    port: int = 7777
    scan_depth: int = 5
    project_names: dict[str, str] = field(default_factory=dict)

    def resolved_claude_dir(self) -> Path | None:
        value = self.claude_dir or os.environ.get("CLAUDE_CONFIG_DIR")
        candidate = Path(value).expanduser() if value else _home() / ".claude"
        return candidate.resolve() if candidate.exists() else None

    def resolved_codex_dir(self) -> Path | None:
        value = self.codex_dir or os.environ.get("CODEX_HOME")
        candidate = Path(value).expanduser() if value else _home() / ".codex"
        return candidate.resolve() if candidate.exists() else None

    def roots(self) -> list[Path]:
        seen: set[str] = set()
        roots: list[Path] = []
        for raw in self.project_roots:
            path = Path(raw).expanduser().resolve()
            key = os.path.normcase(str(path))
            if path.is_dir() and key not in seen:
                roots.append(path)
                seen.add(key)
        return roots

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Config":
        config = cls()
        if isinstance(raw.get("owner_name"), str):
            config.owner_name = raw["owner_name"].strip() or "You"
        if isinstance(raw.get("project_roots"), list):
            config.project_roots = [item for item in raw["project_roots"] if isinstance(item, str)]
        if raw.get("claude_dir") is None or isinstance(raw.get("claude_dir"), str):
            config.claude_dir = raw.get("claude_dir")
        if raw.get("codex_dir") is None or isinstance(raw.get("codex_dir"), str):
            config.codex_dir = raw.get("codex_dir")
        if isinstance(raw.get("github_enabled"), bool):
            config.github_enabled = raw["github_enabled"]
        if isinstance(raw.get("port"), int) and 1 <= raw["port"] <= 65535:
            config.port = raw["port"]
        if isinstance(raw.get("scan_depth"), int) and 1 <= raw["scan_depth"] <= 20:
            config.scan_depth = raw["scan_depth"]
        if isinstance(raw.get("project_names"), dict):
            config.project_names = {str(k): str(v) for k, v in raw["project_names"].items()}
        return config


def config_path() -> Path:
    override = os.environ.get("CODING_CONTROL_TOWER_CONFIG")
    return Path(override).expanduser() if override else config_dir() / "config.json"


def load_config() -> Config:
    path = config_path()
    if not path.exists():
        return Config()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return Config.from_dict(raw if isinstance(raw, dict) else {})
    except (OSError, ValueError, TypeError):
        return Config()


def save_config(config: Config) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(config), indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)
    return path
