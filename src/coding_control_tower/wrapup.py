"""Session closure loop: write and read structured wrap-up files.

One file per project under <state>/wrapups/<project-id>.md. The id is key(repo
dir name) — the same key the scanner assigns discovered repos, so a wrap-up
correlates with its project card without any config. Format is line-parseable
markdown (identical field grammar to the docs/skills templates):

    # Wrap-up — <Project Name>
    repo: /abs/path
    at: 2026-07-15T02:30:00Z

    **Focus:** what this session worked on
    **Next step:** the one concrete next action
    **Blockers:** anything stuck (or 'none')
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from .config import state_dir
from .scan import human_name, key

FIELD = {
    "focus": re.compile(r"(?im)^\*\*Focus:?\*\*[:\s—-]*(.+)$"),
    "next": re.compile(r"(?im)^\*\*Next step:?\*\*[:\s—-]*(.+)$"),
    "blockers": re.compile(r"(?im)^\*\*Blockers?:?\*\*[:\s—-]*(.+)$"),
}
AT = re.compile(r"(?im)^at:\s*(\S+)\s*$")
REPO = re.compile(r"(?im)^repo:\s*(.+)$")


def wrapups_dir(base: Path | None = None) -> Path:
    return (base or state_dir()) / "wrapups"


def repo_root(start: Path) -> Path | None:
    """Nearest ancestor (or start) containing .git — the project the wrap-up belongs to."""
    for path in [start, *start.parents]:
        if (path / ".git").exists():
            return path
    return None


def _clean(value: str) -> str:
    """Single-line field: collapse whitespace/newlines (a newline would forge a
    second **field:** line — adversary finding, run wf_ae392986-368) and cap at
    the same 400 chars the reader keeps, so written == displayed."""
    return re.sub(r"\s+", " ", str(value or "")).strip()[:400]


def write_wrapup(repo: Path, focus: str, next_step: str, blockers: str = "",
                 parked: bool = False, base: Path | None = None) -> Path:
    project_id = key(repo.name)
    focus, next_step, blockers = _clean(focus), _clean(next_step), _clean(blockers)
    focus = ("[parked] " if parked else "") + focus
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = (
        f"# Wrap-up — {human_name(repo.name)}\n"
        f"repo: {repo}\n"
        f"at: {now}\n\n"
        f"**Focus:** {focus}\n"
        f"**Next step:** {next_step}\n"
        f"**Blockers:** {blockers or 'none'}\n"
    )
    target = wrapups_dir(base)
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{project_id}.md"
    path.write_text(body, encoding="utf-8")
    return path


def read_core_wrapups(base: Path | None = None) -> dict[str, dict[str, Any]]:
    """{project-id: {focus,next,blockers,at,path}} from the tower's own wrapups dir."""
    out: dict[str, dict[str, Any]] = {}
    target = wrapups_dir(base)
    if not target.is_dir():
        return out
    for path in target.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        entry: dict[str, Any] = {}
        for name, rx in FIELD.items():
            match = rx.search(text)
            if match and match.group(1).strip():
                entry[name] = match.group(1).strip()[:400]
        if not entry:
            continue
        at = AT.search(text)
        entry["at"] = at.group(1) if at else None
        entry["path"] = str(path)
        out[path.stem] = entry
    return out
