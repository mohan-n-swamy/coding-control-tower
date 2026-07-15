# coding-control-tower — STATUS

> **Resume prompt** — paste this whole file into Claude Code or Codex to pick up where I stopped. It is self-contained: repo path, state, commands, and the next action are all below.

**Repo:** `~/code workshop/claude projects/Orange Health/coding-control-tower` (`cd` here first)
**What it is:** Local, read-only, project-first dashboard — "what am I working on, where did it stop, what's next, which PRs belong to which project." Python ≥3.10, src-layout, zero runtime deps. Public OSS.
**Updated:** 2026-07-15
**Branch:** main
**HEAD:** 13f2468 — formula: sha for retagged v0.2.0
**Tree:** clean

**Commands:** `PYTHONPATH=src python3 -m pytest tests/ -q` (27 tests) · `PYTHONPATH=src python3 -m coding_control_tower scan` (rebuild snapshot) · `… serve` (dashboard on :7777) · `… doctor` (adapter check).

## Current goal

**Mission Control v1 SHIPPED (v0.2.0).** 002 pack fully assembled: 14/14 components,
adversary NO BLOCKING ISSUES, SC1-SC8 live-probed green, personal + public deployed.

## Latest verified evidence

- **v0.2.0 released** (tag + GitHub release; PR #1-of-recreated-repo merged `24db77a`).
  Formula sha `a54ad6…` in BOTH repos (tool + homebrew-tap). Clean-venv pip V-gate
  printed `0.2.0`; personal serve `SUCCESS · schema=2 live=6 wrapups=5`.
- SC probes (live, 2026-07-15): SC1 6 live sessions · SC2 park/answer round-trip
  (synthetic transcript, appeared with ask+resumeCmd, removed on answer) · SC4
  5 wrapup projects · SC5 providers Anthropic+Z.ai+xAI, approx labeled.
- Personal config at `~/Library/Application Support/coding-control-tower/config.json`
  (macOS path — NOT ~/.config): `adapter_dirs: ["~/.local/bin/cct_adapters"]`,
  `timezone: Asia/Kolkata`. Adapters: wrapup_notes.py (19 projects), brain_router_usage.py.
- **History purge**: repo deleted+recreated 2026-07-15 to kill PR-ref residuals; old
  pack SHAs (d6dff2b/b7baec5) 404 on GitHub. Private pack lives at
  `../coding-control-tower-private/specs/002-mission-control` (NEVER commit to repo).
- Version gotcha: `--version` reads `__init__.__version__` (C14 missed it once);
  formula test asserts it — bump BOTH pyproject.toml and __init__.py on release.

## Blocker

_none_

## Next action

- [ ] Confirm background `brew upgrade coding-control-tower` V-gate printed 0.2.0
      (was running at last save). Then v2 candidates: G4 card detail (runs), tmux
      deep-link from live-session rows, cross-machine merge.

---
_Refresh with `bin/gen-status.rb coding-control-tower` before /save, /park, /wrap-up. Machine header (Updated/Branch/HEAD/Tree) is auto-filled; the prose is yours._
