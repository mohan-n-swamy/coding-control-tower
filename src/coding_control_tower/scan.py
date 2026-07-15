"""Portable evidence collectors and project-first state assembly."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

from .config import Config, state_dir
from .paths import pr_cache_path, snapshot_path

SCHEMA_VERSION = 1
ACTIVE_HOURS = 6
HISTORY_DAYS = 30
PR_CACHE_SECONDS = 900
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", "Library"}
ACRONYMS = {"ai": "AI", "api": "API", "cli": "CLI", "cpo": "CPO", "mcp": "MCP", "oh": "OH", "ui": "UI", "voc": "VOC"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"]?\S{12,}"),
]
PR_RE = re.compile(r"(?i)\bPR\s*#?\s*(\d+)\b")


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_mtime(path: Path) -> str | None:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except OSError:
        return None


def parse_time(value: Any) -> dt.datetime | None:
    if isinstance(value, (int, float)):
        value = value / 1000 if value > 10_000_000_000 else value
        try:
            return dt.datetime.fromtimestamp(value, dt.timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def timestamp(value: Any) -> float:
    parsed = parse_time(value)
    return parsed.timestamp() if parsed else 0.0


def recent(value: Any, hours: int = ACTIVE_HOURS) -> bool:
    parsed = parse_time(value)
    return bool(parsed and (dt.datetime.now(dt.timezone.utc) - parsed).total_seconds() <= hours * 3600)


def in_history(value: Any) -> bool:
    parsed = parse_time(value)
    return bool(parsed and (dt.datetime.now(dt.timezone.utc) - parsed).days <= HISTORY_DAYS)


def key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def human_name(value: Any) -> str:
    words = re.split(r"[-_\s]+", str(value or "").strip())
    return " ".join(ACRONYMS.get(word.lower(), word.capitalize()) for word in words if word) or "Unassigned"


def redact(value: Any) -> Any:
    if isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            value = pattern.sub("[REDACTED]", value)
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {name: redact(item) for name, item in value.items()}
    return value


def discover_repositories(config: Config) -> list[dict[str, Any]]:
    """Discover git roots below arbitrary configured folders, with bounded depth."""
    repos: dict[str, dict[str, Any]] = {}
    for base in config.roots():
        base_depth = len(base.parts)
        for current, dirs, _files in os.walk(base, followlinks=False):
            path = Path(current)
            depth = len(path.parts) - base_depth
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (d.startswith(".") and d != ".git")]
            if (path / ".git").exists():
                repo_key = key(path.name)
                repos[os.path.normcase(str(path.resolve()))] = {
                    "id": repo_key,
                    "name": config.project_names.get(repo_key, human_name(path.name)),
                    "path": str(path.resolve()),
                    "repoName": path.name,
                    "branch": git_branch(path),
                }
                dirs[:] = []
            elif depth >= max(1, config.scan_depth):
                dirs[:] = []
    return list(repos.values())


def git_branch(repo: Path) -> str:
    try:
        head = (repo / ".git" / "HEAD").read_text(encoding="utf-8", errors="replace").strip()
        return head.removeprefix("ref: refs/heads/") if head.startswith("ref:") else head[:12]
    except OSError:
        return ""


def index_claude_sessions(claude_dir: Path | None) -> dict[str, Path]:
    found: dict[str, Path] = {}
    projects = claude_dir / "projects" if claude_dir else None
    if not projects or not projects.is_dir():
        return found
    for current, dirs, files in os.walk(projects, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            if filename.endswith(".jsonl"):
                found.setdefault(filename[:-6], Path(current) / filename)
    return found


def read_jsonl_metadata(path: Path | None) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    if not path:
        return meta
    try:
        # Working directory can change during a long session. Read a bounded
        # tail so project correlation uses the latest observed cwd/branch.
        with path.open("rb") as handle:
            size = handle.seek(0, os.SEEK_END)
            handle.seek(max(0, size - 512_000))
            if size > 512_000:
                handle.readline()  # discard a partial JSONL record
            lines = handle.read().decode("utf-8", errors="replace").splitlines()
            for line in lines:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                payload = row.get("payload") if isinstance(row.get("payload"), dict) else row
                if payload.get("cwd"):
                    meta["cwd"] = payload["cwd"]
                if payload.get("gitBranch"):
                    meta["branch"] = payload["gitBranch"]
                if row.get("timestamp"):
                    meta["updatedAt"] = row["timestamp"]
    except OSError:
        return meta
    meta["updatedAt"] = iso_mtime(path) or meta.get("updatedAt")
    return meta


def collect_claude(config: Config) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claude = config.resolved_claude_dir()
    if not claude:
        return [], []
    session_index = index_claude_sessions(claude)
    work: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    tasks_dir = claude / "tasks"
    if tasks_dir.is_dir():
        for session_dir in tasks_dir.iterdir():
            if not session_dir.is_dir():
                continue
            meta = read_jsonl_metadata(session_index.get(session_dir.name))
            for task_file in session_dir.glob("*.json"):
                try:
                    task = json.loads(task_file.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                status = str(task.get("status") or "pending")
                updated = iso_mtime(task_file)
                if status == "completed" and not in_history(updated):
                    continue
                work.append({
                    "type": "task", "source": "Claude", "session": session_dir.name,
                    "cwd": meta.get("cwd"), "branch": meta.get("branch", ""),
                    "title": str(task.get("subject") or "Claude task")[:240],
                    "status": status if status != "in_progress" or recent(updated) else "stopped",
                    "activityAt": updated, "prNumber": parse_pr(task.get("subject")),
                })
    projects_dir = claude / "projects"
    if projects_dir.is_dir():
        for workflow_file in projects_dir.rglob("workflows/wf_*.json"):
            try:
                raw = json.loads(workflow_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            updated = iso_mtime(workflow_file)
            if not in_history(updated):
                continue
            session = workflow_file.parent.parent.name
            meta = read_jsonl_metadata(session_index.get(session))
            status = str(raw.get("status") or "running")
            if status == "running" and not recent(updated):
                status = "stopped"
            item = {
                "type": "workflow", "source": "Claude", "session": session,
                "cwd": meta.get("cwd"), "branch": meta.get("branch", ""),
                "title": str(raw.get("workflowName") or raw.get("summary") or workflow_file.stem)[:240],
                "status": status, "stage": str(raw.get("currentPhase") or ""),
                "activityAt": updated, "prNumber": parse_pr(" ".join((str(raw.get("workflowName") or ""), str(raw.get("summary") or "")))),
            }
            if status == "failed":
                error = error_report(raw.get("error"))
                item["error"] = error
                failures.append({"title": item["title"], "activityAt": updated, "kind": "workflow_failure", "error": error})
            work.append(item)
    return work, failures


def collect_codex(config: Config) -> list[dict[str, Any]]:
    codex = config.resolved_codex_dir()
    sessions = codex / "sessions" if codex else None
    if not sessions or not sessions.is_dir():
        return []
    work: list[dict[str, Any]] = []
    cutoff = time.time() - HISTORY_DAYS * 86400
    for path in sessions.rglob("*.jsonl"):
        try:
            if path.stat().st_mtime < cutoff:
                continue
            first = path.open("r", encoding="utf-8", errors="replace").readline()
            row = json.loads(first)
            payload = row.get("payload") or {}
            if row.get("type") != "session_meta" or payload.get("thread_source") == "subagent":
                continue
        except (OSError, ValueError):
            continue
        updated = iso_mtime(path)
        work.append({
            "type": "session", "source": "Codex", "session": payload.get("id") or path.stem,
            "cwd": payload.get("cwd"), "branch": "", "title": "Codex session",
            "status": "in_progress" if recent(updated) else "stopped", "activityAt": updated,
            "prNumber": None,
        })
    return work


LIVE_WINDOW_MIN = 10  # a session whose transcript moved within this window is "live now"


def _claude_session_probe(path: Path) -> dict[str, Any]:
    """Cheap tail/head probe of one Claude transcript: model + startedAt + cwd.
    Reads at most 64 lines from each end; malformed lines skipped per-line."""
    model = None
    started = None
    cwd = None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            head = [handle.readline() for _ in range(64)]
        tail = path.read_text(encoding="utf-8", errors="replace").splitlines()[-64:]
    except OSError:
        return {"model": None, "startedAt": None, "cwd": None}
    for line in head:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        started = started or row.get("timestamp")
        cwd = cwd or row.get("cwd")
        if started and cwd:
            break
    for line in reversed(tail):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        cwd = row.get("cwd") or cwd
        message = row.get("message") if isinstance(row.get("message"), dict) else {}
        candidate = str(message.get("model") or "")
        if candidate and not candidate.startswith("<"):
            model = candidate
            break
    return {"model": model, "startedAt": started, "cwd": cwd}


def collect_live_sessions(config: Config, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every session whose transcript was written within LIVE_WINDOW_MIN minutes."""
    cutoff = time.time() - LIVE_WINDOW_MIN * 60
    out: list[dict[str, Any]] = []
    claude = config.resolved_claude_dir()
    projects_dir = claude / "projects" if claude else None
    if projects_dir and projects_dir.is_dir():
        for path in projects_dir.glob("*/*.jsonl"):
            try:
                if path.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            probe = _claude_session_probe(path)
            repo = project_for_cwd(probe["cwd"], repos)
            out.append({
                "source": "Claude", "session": path.stem,
                "projectId": repo["id"] if repo else None,
                "project": repo["name"] if repo else None,
                "cwd": probe["cwd"], "model": probe["model"],
                "activityAt": iso_mtime(path), "startedAt": probe["startedAt"],
            })
    codex = config.resolved_codex_dir()
    sessions = codex / "sessions" if codex else None
    if sessions and sessions.is_dir():
        for path in sessions.rglob("*.jsonl"):
            try:
                if path.stat().st_mtime < cutoff:
                    continue
                first = path.open("r", encoding="utf-8", errors="replace").readline()
                row = json.loads(first)
                payload = row.get("payload") or {}
                if row.get("type") != "session_meta" or payload.get("thread_source") == "subagent":
                    continue
            except (OSError, ValueError):
                continue
            repo = project_for_cwd(payload.get("cwd"), repos)
            out.append({
                "source": "Codex", "session": str(payload.get("id") or path.stem),
                "projectId": repo["id"] if repo else None,
                "project": repo["name"] if repo else None,
                "cwd": payload.get("cwd"), "model": None,
                "activityAt": iso_mtime(path), "startedAt": row.get("timestamp"),
            })
    out.sort(key=lambda item: timestamp(item.get("activityAt")), reverse=True)
    return out[:8]


BLOCKING_TOOLS = frozenset({"AskUserQuestion", "ExitPlanMode"})
DECISION_MAX_AGE_H = 24  # a pending question older than this is a dead session, not a decision


def _pending_blockers(path: Path) -> list[dict[str, Any]]:
    """Single forward pass over one Claude transcript: blocking tool_use entries
    with no matching tool_result. Returns [{id, name, question, askedAt, cwd}]."""
    pending: dict[str, dict[str, Any]] = {}
    cwd = None
    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return []
    with handle:
        for line in handle:
            if '"tool_use"' not in line and '"tool_result"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            cwd = row.get("cwd") or cwd
            message = row.get("message") if isinstance(row.get("message"), dict) else {}
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and block.get("name") in BLOCKING_TOOLS:
                    question = ""
                    if block.get("name") == "AskUserQuestion":
                        questions = (block.get("input") or {}).get("questions") or []
                        if questions and isinstance(questions[0], dict):
                            question = str(questions[0].get("question") or "")
                    else:
                        question = "Approve the proposed plan?"
                    pending[str(block.get("id"))] = {
                        "id": str(block.get("id")), "name": str(block.get("name")),
                        "question": question[:200], "askedAt": row.get("timestamp"), "cwd": cwd,
                    }
                elif block.get("type") == "tool_result":
                    pending.pop(str(block.get("tool_use_id")), None)
    return list(pending.values())


def collect_decisions(config: Config, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """needsOwner kind:'decision' entries — sessions waiting on the user right now."""
    claude = config.resolved_claude_dir()
    projects_dir = claude / "projects" if claude else None
    if not projects_dir or not projects_dir.is_dir():
        return []
    cutoff = time.time() - DECISION_MAX_AGE_H * 3600
    out: list[dict[str, Any]] = []
    for path in projects_dir.glob("*/*.jsonl"):
        try:
            if path.stat().st_mtime < cutoff:
                continue
        except OSError:
            continue
        blockers = _pending_blockers(path)
        if not blockers:
            continue
        newest = max(blockers, key=lambda item: timestamp(item.get("askedAt")))
        repo = project_for_cwd(newest.get("cwd"), repos)
        session = path.stem
        out.append({
            "kind": "decision",
            "projectId": repo["id"] if repo else None,
            "project": repo["name"] if repo else (newest.get("cwd") or "unknown"),
            "ask": newest["question"] or f"{newest['name']} pending",
            "blocks": f"session {session[:8]} — waiting since ask",
            "askedAt": newest.get("askedAt"),
            "activityAt": newest.get("askedAt"),
            "session": session, "source": "Claude",
            "resumeCmd": f"claude --resume {session}" + (f"  # cwd: {newest.get('cwd')}" if newest.get("cwd") else ""),
        })
    out.sort(key=lambda item: timestamp(item.get("askedAt")), reverse=True)
    return out


def _provider_for_model(model: str) -> str:
    lowered = model.lower()
    if lowered.startswith("claude"):
        return "Anthropic"
    if lowered.startswith(("gpt", "o1", "o3", "o4", "codex")):
        return "OpenAI"
    return "Other"


def collect_usage(config: Config) -> dict[str, Any]:
    """Aggregate today's per-model token usage from Claude session logs."""
    claude = config.resolved_claude_dir()
    projects = claude / "projects" if claude else None
    models: dict[str, dict[str, int]] = {}
    if projects and projects.is_dir():
        midnight = dt.datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
        midnight_ts = midnight.timestamp()
        for path in projects.rglob("*.jsonl"):
            try:
                if path.stat().st_mtime < midnight_ts:
                    continue
                with path.open("r", encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        if '"usage"' not in line:
                            continue
                        try:
                            row = json.loads(line)
                        except ValueError:
                            continue
                        message = row.get("message") if isinstance(row.get("message"), dict) else {}
                        usage = message.get("usage") if isinstance(message.get("usage"), dict) else None
                        if not usage:
                            continue
                        recorded = parse_time(row.get("timestamp"))
                        if not recorded or recorded < midnight.astimezone(dt.timezone.utc):
                            continue
                        model = str(message.get("model") or "")
                        if not model or model.startswith("<"):
                            continue
                        bucket = models.setdefault(model, {"in": 0, "out": 0})
                        for field in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
                            value = usage.get(field)
                            bucket["in"] += int(value) if isinstance(value, (int, float)) else 0
                        out_value = usage.get("output_tokens")
                        bucket["out"] += int(out_value) if isinstance(out_value, (int, float)) else 0
            except OSError:
                continue
    grand_total = sum(bucket["in"] + bucket["out"] for bucket in models.values())
    rows = [
        {
            "provider": _provider_for_model(model), "model": model,
            "tin": bucket["in"], "tout": bucket["out"],
            "share": round(100 * (bucket["in"] + bucket["out"]) / grand_total) if grand_total else 0,
        }
        for model, bucket in models.items()
    ]
    rows.sort(key=lambda row: row["tin"] + row["tout"], reverse=True)
    return {
        "period": "today",
        "totalIn": sum(bucket["in"] for bucket in models.values()),
        "totalOut": sum(bucket["out"] for bucket in models.values()),
        "models": rows[:6],
    }


def parse_pr(value: Any) -> int | None:
    match = PR_RE.search(str(value or ""))
    return int(match.group(1)) if match else None


def body_section(body: str, labels: Iterable[str]) -> str | None:
    names = "|".join(re.escape(label) for label in labels)
    match = re.search(rf"(?ims)^##+\s*(?:{names})\s*$\n(.*?)(?=^##+\s|\Z)", body or "")
    if not match:
        return None
    clean = " ".join(re.sub(r"^[\s>*-]+", "", line).strip() for line in match.group(1).splitlines()).strip()
    return clean[:500] or None


CHECKBOX_RE = re.compile(r"(?im)^\s*[-*]\s*\[( |x|X)\]\s+(.+?)\s*$")


def parse_body_tasks(body: str) -> dict[str, Any] | None:
    """PR-body markdown checklist -> design tasks shape, or None if no checklist."""
    items = [{"t": match.group(2)[:160], "done": match.group(1).lower() == "x"}
             for match in CHECKBOX_RE.finditer(body or "")]
    if not items:
        return None
    return {"done": sum(1 for item in items if item["done"]), "total": len(items), "items": items[:20]}


def _pr_verification(pr: dict[str, Any]) -> list[dict[str, Any]]:
    """Data-driven badges from scanned facts ONLY — never invented."""
    badges: list[dict[str, Any]] = []
    if pr.get("outcome"):
        badges.append({"tone": "ok", "label": "Outcome claimed · PR body"})
    elif pr.get("status") == "merged":
        badges.append({"tone": "wait", "label": "Merged — no delivery proof in body"})
    if pr.get("status") == "closed":
        badges.append({"tone": "fail", "label": "Closed — not built"})
    if pr.get("url"):
        badges.append({"tone": "link", "label": "OPEN ON GITHUB", "href": pr["url"]})
    return badges


def normalize_pr(raw: dict[str, Any]) -> dict[str, Any]:
    repo = raw.get("repository") or {}
    status = "draft" if raw.get("isDraft") else str(raw.get("state") or "closed").lower()
    body = str(raw.get("body") or "")
    summary = body_section(body, ("Summary", "What", "Fix", "Problem")) or str(raw.get("title") or "")
    outcome = body_section(body, ("Outcome", "Delivered", "Deploy state", "Done proof"))
    number = int(raw.get("number") or 0)
    progress = body_section(CHECKBOX_RE.sub("", body), ("Where it stands", "Status", "Progress")) or summary
    status_label = {"open": "Active", "draft": "Draft", "merged": "Merged", "closed": "Failed — not built"}.get(status, status.title())
    pr = {
        "number": number, "num": number, "title": str(raw.get("title") or "Untitled PR")[:240],
        "status": status, "statusLabel": status_label,
        "createdAt": raw.get("createdAt"), "updatedAt": raw.get("updatedAt") or raw.get("closedAt"),
        "url": raw.get("url"), "repoName": str(repo.get("name") or ""), "repoFullName": str(repo.get("nameWithOwner") or ""),
        "summary": summary[:280], "progress": progress[:280],
        "claimedOutcome": outcome, "outcome": outcome, "claimSource": "PR body" if outcome else None,
        "tasks": parse_body_tasks(body), "runs": None, "error": None,
        "workItems": [],
    }
    pr["verification"] = _pr_verification(pr)
    return pr


def collect_github(config: Config, refresh: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not config.github_enabled:
        return [], {"enabled": False, "available": bool(shutil.which("gh")), "generatedAt": None, "count": 0, "error": None}
    cache = pr_cache_path()
    payload: dict[str, Any] = {}
    try:
        payload = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    except (OSError, ValueError):
        pass
    generated = parse_time(payload.get("generatedAt"))
    expired = not generated or (dt.datetime.now(dt.timezone.utc) - generated).total_seconds() > PR_CACHE_SECONDS
    error = None
    if shutil.which("gh") and (refresh or expired):
        command = ["gh", "search", "prs", "--involves", "@me", "--limit", "1000", "--sort", "updated", "--order", "desc", "--json", "number,title,state,isDraft,createdAt,updatedAt,closedAt,url,repository,body"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                prs = [normalize_pr(item) for item in json.loads(result.stdout)]
                payload = {"generatedAt": iso_now(), "pullRequests": prs}
                atomic_json(cache, payload)
            else:
                error = (result.stderr or "GitHub query failed").strip()[:300]
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            error = str(exc)[:300]
    prs = payload.get("pullRequests") if isinstance(payload.get("pullRequests"), list) else []
    return prs, {"enabled": config.github_enabled, "available": bool(shutil.which("gh")), "generatedAt": payload.get("generatedAt"), "count": len(prs), "error": error}


def project_for_cwd(cwd: Any, repos: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not cwd:
        return None
    try:
        path = Path(str(cwd)).expanduser().resolve()
    except (OSError, ValueError):
        return None
    matches = []
    for repo in repos:
        try:
            path.relative_to(Path(repo["path"]))
            matches.append(repo)
        except ValueError:
            pass
    return max(matches, key=lambda item: len(Path(item["path"]).parts), default=None)


def error_report(value: Any) -> dict[str, str]:
    cause = re.sub(r"^Error:\s*", "", str(value or "Workflow failed").splitlines()[0])[:220]
    return {"cause": cause, "impact": "Workflow did not complete; no delivery claim made.", "next": "Inspect source run, then fix or retry."}


def assemble(config: Config, repos: list[dict[str, Any]], work: list[dict[str, Any]], failures: list[dict[str, Any]], prs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = {}

    def ensure(project_id: str, name: str, path: str = "", branch: str = "", repo_name: str = "") -> dict[str, Any]:
        if project_id not in projects:
            projects[project_id] = {"id": project_id, "name": name, "path": path, "branch": branch, "repoName": repo_name, "repoFullName": "", "state": "history", "activityAt": None, "hasActiveTask": False, "hasRunningWorkflow": False, "needsAction": [], "prs": [], "localWork": [], "artifacts": [], "provenance": []}
        return projects[project_id]

    def touch(project: dict[str, Any], at: Any) -> None:
        if timestamp(at) > timestamp(project.get("activityAt")):
            project["activityAt"] = at

    for repo in repos:
        ensure(repo["id"], repo["name"], repo["path"], repo["branch"], repo["repoName"])
    by_repo_name = {key(repo["repoName"]): projects[repo["id"]] for repo in repos}
    for pr in prs:
        project = by_repo_name.get(key(pr.get("repoName")))
        if not project:
            project_id = key(pr.get("repoName")) or "unassigned-github"
            project = ensure(project_id, config.project_names.get(project_id, human_name(pr.get("repoName"))), repo_name=str(pr.get("repoName") or ""))
            by_repo_name[project_id] = project
        project["repoFullName"] = pr.get("repoFullName", "")
        project["prs"].append(dict(pr))
        touch(project, pr.get("updatedAt"))
    for item in work:
        repo = project_for_cwd(item.get("cwd"), repos)
        if repo:
            project = projects[repo["id"]]
        else:
            # floor: all cwd-unmapped work collapses into ONE bucket, not one card per
            # session — otherwise hundreds of non-repo sessions drown the real repos.
            project = ensure("unassigned", "Unassigned sessions")
        project["provenance"].append({"source": item.get("source"), "session": item.get("session"), "method": "observed cwd" if repo else "unassigned"})
        project["localWork"].append(item)
        touch(project, item.get("activityAt"))
        if item.get("status") == "in_progress" or (item.get("type") == "workflow" and item.get("status") == "running"):
            project["hasActiveTask"] = True
            project["state"] = "active"
        elif item.get("status") in ("pending", "stopped") and project["state"] == "history":
            project["state"] = "planning"
        if item.get("error"):
            project["needsAction"].append({"kind": "workflow_failure", "title": item["title"], "activityAt": item.get("activityAt"), "error": item["error"]})
            if project["state"] != "active":
                project["state"] = "attention"
    bucket = projects.get("unassigned")
    if bucket is not None and not bucket["path"]:
        # The unassigned bucket is noise, not a project: it must never claim active
        # status, win the "now" slot, or sort above a real repo. Pin it to history and
        # null its activity so real repos always outrank it on the recency sort too.
        bucket["hasActiveTask"] = False
        bucket["state"] = "history"
        bucket["needsAction"] = []
        bucket["activityAt"] = None
    for project in projects.values():
        by_number = {int(pr["number"]): pr for pr in project["prs"] if pr.get("number")}
        local = []
        for item in project["localWork"]:
            number = item.get("prNumber")
            if number and number in by_number:
                by_number[number]["workItems"].append(item)
            else:
                local.append(item)
        for pr in project["prs"]:
            if pr.get("workItems") and not pr.get("tasks"):
                # session task files are the fresher truth when the body has no checklist
                items = [{"t": str(w.get("title") or "Untitled")[:160],
                          "done": str(w.get("status") or "") == "completed"}
                         for w in pr["workItems"]]
                pr["tasks"] = {"done": sum(1 for i in items if i["done"]),
                               "total": len(items), "items": items[:20]}
        project["localWork"] = sorted(local, key=lambda item: timestamp(item.get("activityAt")), reverse=True)
        project["prs"].sort(key=lambda pr: timestamp(pr.get("updatedAt")), reverse=True)
        open_prs = sum(pr.get("status") in ("open", "draft") for pr in project["prs"])
        merged = sum(pr.get("status") == "merged" for pr in project["prs"])
        failed = len(project["needsAction"])
        project["counts"] = {"openPRs": open_prs, "mergedPRs": merged, "needsAction": failed, "failedRuns": failed, "localWork": len(project["localWork"])}
        if project["state"] == "history" and open_prs:
            project["state"] = "planning"
        project["provenance"] = list({(p["source"], p["session"], p["method"]): p for p in project["provenance"]}.values())
    return sorted(projects.values(), key=lambda project: (0 if project["hasActiveTask"] else 1, -timestamp(project.get("activityAt"))))


def derive_now(projects: list[dict[str, Any]]) -> dict[str, Any] | None:
    for project in projects:
        candidates = list(project["localWork"])
        for pr in project["prs"]:
            candidates.extend(pr.get("workItems", []))
        active = [item for item in candidates if item.get("status") in ("in_progress", "running")]
        if active:
            item = max(active, key=lambda entry: timestamp(entry.get("activityAt")))
            return {"projectId": project["id"], "project": project["name"], "title": item["title"], "stage": item.get("stage") or f"{item.get('source')} session", "stoppedAt": "No source-backed stopping point recorded.", "next": f"Continue: {item['title']}", "activityAt": item.get("activityAt"), "session": item.get("session"), "correlation": "observed" if project["path"] else "unassigned"}
    return None


def build_state(config: Config, refresh_github: bool = False) -> dict[str, Any]:
    repos = discover_repositories(config)
    claude_work, failures = collect_claude(config)
    codex_work = collect_codex(config)
    prs, github = collect_github(config, refresh_github)
    projects = assemble(config, repos, claude_work + codex_work, failures, prs)
    needs = [{"projectId": project["id"], "project": project["name"], **item} for project in projects for item in project["needsAction"]]
    needs.sort(key=lambda item: timestamp(item.get("activityAt")), reverse=True)
    running = sum(project["hasActiveTask"] for project in projects)
    state = {
        "schema_version": SCHEMA_VERSION, "scanner_version": "0.1.0", "generated_at": iso_now(),
        "config": {"stale_threshold_ms": 900_000, "poll_interval_ms": 3_000, "timezone": config.timezone or ""},
        "ownerName": config.owner_name or "You", "mood": "concerned" if needs else "watching" if running else "sleeping",
        "summary": {"running": running, "needs_review": 0, "failed": len(needs), "idle": running == 0},
        "skipped_files": 0, "now": derive_now(projects), "needsOwner": needs,
        "usage": collect_usage(config),
        "github": github, "projects": projects,
        "tasks": [item for item in claude_work if item["type"] == "task"],
        "workflows": [item for item in claude_work if item["type"] == "workflow"],
        "codexSessions": codex_work,
        "sources": {"projectRoots": [str(root) for root in config.roots()], "claude": str(config.resolved_claude_dir() or ""), "codex": str(config.resolved_codex_dir() or "")},
    }
    return redact(state)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


def scan(config: Config, refresh_github: bool = False) -> Path:
    path = snapshot_path()
    atomic_json(path, build_state(config, refresh_github))
    return path
