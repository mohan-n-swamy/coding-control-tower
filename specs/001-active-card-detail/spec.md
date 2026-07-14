# 001 — Active-card detail (WHERE IT STANDS / VERIFICATION / TASKS / RUNS)

**Status:** spec — not built. Authored 2026-07-15.

## Problem / Why

The dashboard's expanded ACTIVE project card is far thinner than the design intends.
The design (`docs/mission-grid.png` region + the demo state `docs/demo-state.json`)
shows a rich per-PR panel:

- **WHERE IT STANDS** — a prose status line ("In progress — retries land in queue and drain; jitter test still flaky")
- **VERIFICATION** — CI check summary ("CI · 2/3 checks, 1 pending")
- **TASKS** — a ✓/○ checklist (Queue migration, Backoff calculator, Retry worker…)
- **RUNS** — timestamped run history ("pytest 47/48 · 10:41")

What the adapters actually emit (verified 2026-07-14 against a live scan of the rig):
a PR carries `summary`/`title`/`status`/`url` but **`workItems: []`** and no
`runs`/`checks` fields at all; a live session's `localWork` is just
`{title:"Codex session", status:"in_progress"}` — no task breakdown, no run history,
no CI. The UI template can render these sections but the data is never produced, so
they show empty. The design was mocked with hand-authored demo data; the real
Claude/Codex/GitHub adapters don't extract the structure.

This is a **feature gap in the scan adapters**, not a UI bug.

## End-State (the gold)

When a project is expanded on the live dashboard, each of its active/recent PRs shows
the four design sections populated from REAL scanned data:

1. **WHERE IT STANDS** — the PR's `summary` (already produced) rendered as prose.
2. **VERIFICATION** — a CI line derived from GitHub check-runs for the PR's head SHA:
   `CI · <passed>/<total> checks, <pending> pending` with a per-state color.
3. **TASKS** — a checklist extracted from the session/PR TODO state: each item with a
   done/not-done marker. Source: Claude Code session TaskList state and/or a PR-body
   task list (`- [ ]` / `- [x]`), whichever is present.
4. **RUNS** — the last N (≤5) observed command/test runs for the project with a
   timestamp and pass/fail, parsed from session logs (test invocations + their
   result lines).

A project with none of this data still renders cleanly (graceful empty, no broken
sections) — the current behavior is the zero-data floor, not a regression.

## Success Criteria (measurable, derived backward from the gold)

- **SC1 — VERIFICATION populated:** for a repo with ≥1 open PR that has GitHub
  check-runs, the scanned PR object carries a `checks` field `{passed:int, total:int,
  pending:int}` and the UI renders the `CI · N/M` line. Verify: scan a repo with a
  live PR, assert `checks.total ≥ 1` in state.json; load dashboard, VERIFICATION line
  present. Target: ≥1 real PR renders it.
- **SC2 — TASKS populated:** for a session or PR body containing a task list, the
  scanned PR/localWork carries `workItems` with `≥1` entry each having `{title,
  status∈(completed|pending|in_progress)}`. Verify: state.json has a PR with
  `len(workItems) ≥ 1`; dashboard shows the ✓/○ checklist. Target: the active project
  this session shows its real task list.
- **SC3 — RUNS populated:** for a project with test runs in its session logs, the
  scanned project carries a `runs` array (≤5) of `{label, ok:bool, at:iso}`. Verify:
  state.json project has `len(runs) ≥ 1`; dashboard RUNS section lists them
  newest-first with pass/fail color. Target: ≥1 project shows real runs.
- **SC4 — no-data graceful:** a project with zero PRs/tasks/runs renders every section
  empty-but-clean (no "undefined", no broken layout). Verify: scan the tool's own repo
  (few of these), load, inspect — no JS console error, no empty-bracket artifacts.
- **SC5 — no regression:** full `pytest` suite stays green and card-collapse +
  now-slot behavior (the shipped `8d69f99` fix) is unaffected. Verify: `pytest` green,
  unassigned bucket still demoted, 406→~38 card count holds.
- **SC6 — read-only + no new deps:** all extraction stays read-only (no writes to
  session logs or GitHub), zero new runtime dependencies (stdlib + `gh` only, per the
  project's zero-dep constraint). Verify: `pip show` deps unchanged; grep the diff for
  any write/POST to a scanned source.

## Non-goals

- Live-streaming run output (this is a periodic scan, not a tail).
- Editing tasks from the dashboard (read-only ledger — a hard project invariant).
- Backfilling historical runs beyond what session logs already hold.

## Open design questions (resolve in plan.md before tasks)

- Task source of truth when BOTH a session TaskList AND a PR-body checklist exist —
  merge, or prefer one? (Likely: session state is fresher; PR body is the durable
  record. Precedence needs a decision.)
- RUNS parsing is log-format-dependent — which session-log lines count as a "run"?
  (test invocations only, or any command with an exit code?)
- GitHub check-runs cost: an extra API call per PR — respect the existing ≤15-min PR
  cache; do not add a per-refresh check-runs fetch.
