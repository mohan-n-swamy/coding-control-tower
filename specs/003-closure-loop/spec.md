# 003 — Closure Loop for Public Users (v0.3)

**Status:** LOCKED 2026-07-15 by Mohan ("spec and build 0.3", in-session). Open questions resolved by orchestrator call: Q1 state-dir (clean repos) · Q2 `wrapup --park` flag · Q3 docs-only templates.

## Problem

v0.2's resume-packet features (NOW enrichment, RESUME cards) light up only when
something writes wrap-up state. On the author's rig that's /wrap-up, /park, and
personal adapters. A default public install has no writer → the killer features
degrade to placeholders (adversary-adjudicated tradeoff in 002). v0.3 closes the
loop for everyone: the tower ships its own closure writer + agent skill templates.

## Scope (proposed)

- **F1 — `coding-control-tower wrapup` CLI**: guided prompt (focus / next step /
  blockers, project auto-detected from cwd) → writes a structured wrap-up file to a
  documented location the BUILT-IN generic adapter reads. Zero config.
- **F2 — built-in wrapup adapter**: public generic reader for those files (same
  two-channel adapter contract; no rig assumptions).
- **F3 — agent skill templates in docs/**: ready-to-copy `/wrap-up` and `/park`
  skill files for Claude Code (and a Codex prompt snippet) that write the same
  format — so agents close sessions properly without the human typing.
- **Non-goals**: session kill/control from the tower (read-only invariant, locked);
  auto-detecting crashes (separate v1.1 rule, see 002 flagged gap); cloud sync.

## End-State

A fresh public install (pip or brew, zero rig deps) where the user (or their agent
via the shipped skill template) runs one `wrapup` command at session end — and the
dashboard's NOW rows, RESUME cards, and project where-it-stands all render
source-backed facts instead of placeholders.

## Success Criteria

- **SC1**: clean venv, fresh config: `coding-control-tower wrapup` (answers piped) →
  next `scan` → ≥1 project card shows the RESUME packet with the entered next-step
  verbatim; NOW row for a live session in that project shows the entered focus.
- **SC2**: adapter round-trip ≤ 2 new files touched by the user (the wrap-up file
  itself + nothing else); 0 config edits required.
- **SC3**: docs/ skill template pasted into a Claude Code project → agent-written
  wrap-up parses identically (same fields, byte-format test).
- **SC4**: full pytest green; test count grows by ≥4 (CLI, adapter, format,
  round-trip); public scrub gate stays SCRUB-EXIT:1.
- **SC5**: README documents the loop in ≤ 15 lines with one copy-paste example.

## Open questions (for PRD lock)

1. Wrap-up file location: `<repo>/.cct/wrapups/*.md` vs XDG state dir keyed by repo
   path? (repo-local = visible/committable; state-dir = clean repos)
2. Park semantics publicly: separate `park` subcommand or `wrapup --park` flag?
3. Skill template shipped as docs only, or `coding-control-tower init --skills`
   that copies them into `.claude/skills/`?

## Known limitation (adversary-adjudicated, 2026-07-15)
Project identity is keyed by repo DIRECTORY NAME (v0.1 design, whole scanner): two repos with the same dirname under different roots share one wrapup slot. Pre-existing, not introduced by 003; fix = path-keyed identity, a v2 restructure. Adversary run wf_ae392986-368; other real findings (at-compare, newline forge, write-side truncation) fixed + regression-tested this build.
