# coding-control-tower — STATUS

> **Resume prompt** — paste this whole file into Claude Code or Codex to pick up where I stopped. It is self-contained: repo path, state, commands, and the next action are all below.

**Repo:** `~/code workshop/claude projects/Orange Health/coding-control-tower` (`cd` here first)
**What it is:** Local, read-only, project-first dashboard — "what am I working on, where did it stop, what's next, which PRs belong to which project." Python ≥3.10, src-layout, zero runtime deps. Public OSS.
**Updated:** 2026-07-15
**Branch:** main
**HEAD:** (main) — v0.3.0 released
**Tree:** clean

**Commands:** `PYTHONPATH=src python3 -m pytest tests/ -q` (34 tests) · `PYTHONPATH=src python3 -m coding_control_tower scan` (rebuild snapshot) · `… serve` (dashboard on :7777) · `… doctor` (adapter check).

## Current goal

**Mission Control v1 + Closure Loop SHIPPED (v0.2.0 → v0.2.1 → v0.3.0, one night).** 002 pack fully assembled: 14/14 components,
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

- [ ] v2 candidates: crashed-session detection (went-quiet-without-wrapup -> NEEDS YOU),
      path-keyed project identity (dirname-collision limitation, specs/003), G4 card
      detail (runs), tmux deep-link, cross-machine merge. brew formula at 0.3.0 both repos.

---
_Refresh with `bin/gen-status.rb coding-control-tower` before /save, /park, /wrap-up. Machine header (Updated/Branch/HEAD/Tree) is auto-filled; the prose is yours._
