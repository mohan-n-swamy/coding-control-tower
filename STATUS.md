# coding-control-tower — STATUS

> **Resume prompt** — paste this whole file into Claude Code or Codex to pick up where I stopped. It is self-contained: repo path, state, commands, and the next action are all below.

**Repo:** `~/code workshop/claude projects/Orange Health/coding-control-tower` (`cd` here first)
**What it is:** Local, read-only, project-first dashboard — "what am I working on, where did it stop, what's next, which PRs belong to which project." Python ≥3.10, src-layout, zero runtime deps. Public OSS.
**Updated:** 2026-07-15
**Branch:** main
**HEAD:** 8782938 — chore(brew): pin real v0.1.0 tarball sha256 in Formula
**Tree:** clean

**Commands:** `PYTHONPATH=src python3 -m pytest tests/ -q` (16 tests) · `PYTHONPATH=src python3 -m coding_control_tower scan` (rebuild snapshot) · `… serve` (dashboard on :7777) · `… doctor` (adapter check).

## Current goal

Published v0.1.0 as public OSS (pip + brew installable) with the unassigned-session flood fixed. Now in maintenance — next work is optional coverage/UX polish.

## Latest verified evidence

- Scan collapse: **406 → 38 cards** on the real rig (30 repos + 7 PR-derived + 1 demoted `unassigned` bucket), `scan` output confirmed.
- Tests: **16/16 pass** (bare `pytest`, `pythonpath=["src"]`).
- Adversarial verify: 3-refuter Workflow (`wf_df6a12a5`) caught a now-slot regression the unit tests missed → fixed with a structural bucket-pin + regression test.
- Distribution V-gated in a clean env: `pip install git+https://…` (CLI + static assets bundle) AND `brew install mohan-n-swamy/tap/coding-control-tower` (`brew test` green).
- Public: `github.com/mohan-n-swamy/coding-control-tower` @ `main` `8782938`; tap `github.com/mohan-n-swamy/homebrew-tap`.

## Blocker

_none_

## Next action

- [ ] _Optional:_ raise `unassigned`-bucket coverage or add a project-`STATUS.md` adapter to the dashboard (surface each scanned repo's STATUS.md in the UI). Not started — pick up only if the tool gets active again.

---
_Refresh with `bin/gen-status.rb coding-control-tower` before /save, /park, /wrap-up. Machine header (Updated/Branch/HEAD/Tree) is auto-filled; the prose is yours._
