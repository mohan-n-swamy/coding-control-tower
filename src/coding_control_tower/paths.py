"""Package resource and runtime paths."""

from importlib.resources import files
from pathlib import Path

from .config import state_dir


def static_dir():
    return files("coding_control_tower").joinpath("static")


def snapshot_path() -> Path:
    return state_dir() / "state.json"


def pr_cache_path() -> Path:
    return state_dir() / "github-prs.json"

