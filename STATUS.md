# coding-control-tower — STATUS

> **Resume prompt** — paste this whole file into Claude Code or Codex to pick up where I stopped. It is self-contained: repo path, state, commands, and the next action are all below.

**Repo:** `~/code workshop/claude projects/Orange Health/coding-control-tower` (`cd` here first)
**What it is:** Local, read-only, project-first dashboard — "what am I working on, where did it stop, what's next, which PRs belong to which project." Python ≥3.10, src-layout, zero runtime deps. Public OSS.
**Updated:** 2026-07-15
**Branch:** specs/002-mission-control-build
**HEAD:** a6e331d — docs: STATUS.md — pack merged, next: manufacture assemble 002
**Tree:** clean

**Commands:** `PYTHONPATH=src python3 -m pytest tests/ -q` (16 tests) · `PYTHONPATH=src python3 -m coding_control_tower scan` (rebuild snapshot) · `… serve` (dashboard on :7777) · `… doctor` (adapter check).

## Current goal

Build **Mission Control v1** (specs/002) — pivot from PR-ledger to agent-fleet
dashboard: blocked-on-you queue, live-sessions board, wrap-up ingestion,
multi-provider usage, LIVE/DORMANT/ARCHIVE buckets, STATUS.md resume panel. The
design pack is authored + merged; the BUILD has not started.

## Latest verified evidence

- **Design pack merged** (PR #1 → `d6dff2b`): 14 Haiku-proof components,
  `manuf-pack-validate` VALID, `lint-pack-coherence` ALL THREADS HOLD.
- Design source VENDORED at `specs/002-mission-control/design/` — `tower-data.js` is
  the state.json field-name contract; `VariantGrid` JSX is the 1:1 frontend target.
- All data shapes probe-verified live: Claude transcripts at
  `~/.claude/projects/<munged>/<uuid>.jsonl` (mtime-live), blocked marker =
  unmatched AskUserQuestion tool_use (id-matching proven 3/3), brain-router audit
  `~/.local/state/brain-router-delegations.jsonl` has `tokens_out`.
- v0.1.x shipped earlier: 406→38 card collapse, grid/UTC/timezone/full-width-card
  fixes, pip + brew installs V-gated, 16/16 tests.

## Blocker

_none — next step is a single command_

## Next action

- [ ] Run `/manufacture assemble 002-mission-control` in a fresh session (Opus
  orchestrates; pack is the contract). Then the SC1-SC8 ship gates in
  `specs/002-mission-control/verification.md`, then deploy personal (serve restart +
  `adapter_dirs` config) and public (v0.2.0 release + Formula sha).

---
_Refresh with `bin/gen-status.rb coding-control-tower` before /save, /park, /wrap-up. Machine header (Updated/Branch/HEAD/Tree) is auto-filled; the prose is yours._
