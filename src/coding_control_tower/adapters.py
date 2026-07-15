"""External adapter loader — the public adapter interface.

An adapter is a single .py file in one of ``config.adapter_dirs`` exposing::

    def collect(config) -> dict

The returned dict may contain ONLY these channels (anything else is dropped):

- ``usage_models``: list of {provider:str, model:str, tin:int, tout:int, approx:bool}
- ``wrapups``: dict of project_id -> {focus,next,blockers,at,path} (str values)

Adapters run inside the scan; failures are captured per-adapter and surfaced in
state.adapterErrors — an adapter can degrade the dashboard to absence, never to a
crash and never silently (the staleness-must-announce-itself rule).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable

ALLOWED_KEYS = frozenset({"usage_models", "wrapups"})
_WRAPUP_KEYS = frozenset({"focus", "next", "blockers", "at", "path"})


def load_external(config) -> tuple[list[tuple[str, Callable[..., Any]]], list[dict[str, str]]]:
    collectors: list[tuple[str, Callable[..., Any]]] = []
    errors: list[dict[str, str]] = []
    for raw_dir in getattr(config, "adapter_dirs", []) or []:
        base = Path(raw_dir).expanduser()
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.py")):
            name = path.name
            try:
                spec = importlib.util.spec_from_file_location(f"cct_adapter_{path.stem}", path)
                if spec is None or spec.loader is None:
                    raise ImportError("unloadable module spec")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                collect = getattr(module, "collect", None)
                if not callable(collect):
                    raise AttributeError("adapter has no callable collect(config)")
                collectors.append((name, collect))
            except Exception as exc:  # noqa: BLE001 — one bad adapter must not sink the rest
                errors.append({"adapter": name, "error": str(exc)[:200]})
    return collectors, errors


def _coerce_usage_rows(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return rows
    for item in value:
        if not isinstance(item, dict):
            continue
        provider = str(item.get("provider") or "").strip()
        model = str(item.get("model") or "").strip()
        if not provider or not model:
            continue
        tin = item.get("tin")
        tout = item.get("tout")
        rows.append({
            "provider": provider[:40], "model": model[:80],
            "tin": max(0, int(tin)) if isinstance(tin, (int, float)) else 0,
            "tout": max(0, int(tout)) if isinstance(tout, (int, float)) else 0,
            "approx": bool(item.get("approx", False)),
        })
    return rows


def _coerce_wrapups(value: Any) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not isinstance(value, dict):
        return out
    for key, item in value.items():
        if not isinstance(item, dict):
            continue
        clean = {k: str(v)[:500] for k, v in item.items() if k in _WRAPUP_KEYS and v}
        if clean:
            out[str(key)[:120]] = clean
    return out


def run_collectors(collectors, config) -> tuple[dict[str, Any], list[dict[str, str]]]:
    merged: dict[str, Any] = {"usage_models": [], "wrapups": {}}
    errors: list[dict[str, str]] = []
    for name, collect in collectors:
        try:
            result = collect(config)
            if not isinstance(result, dict):
                raise TypeError("collect() must return a dict")
            merged["usage_models"].extend(_coerce_usage_rows(result.get("usage_models")))
            merged["wrapups"].update(_coerce_wrapups(result.get("wrapups")))
        except Exception as exc:  # noqa: BLE001
            errors.append({"adapter": name, "error": str(exc)[:200]})
    return merged, errors
