# 001 — Adapter-depth: match the dashboard to a real multi-model, multi-session workflow

**Status:** spec — not built. Authored 2026-07-15.

## Scope note

This spec covers FOUR related gaps, all in the scan-adapter layer, all surfaced
2026-07-15 by using the tool against the real rig. They share one root theme: **the
adapters under-extract from a real multi-model (Claude · Codex · Grok · GLM ·
DeepSeek), multi-session (6+ parallel tmux agents) workflow.** They are speced
together because they touch the same files (`scan.py` collectors) and would otherwise
be four colliding patches.

- **G1 — Active-session detection** (§G1): only 1 of 6 live sessions is detected.
- **G2 — Multi-session NOW** (§G2): the NOW card shows one session; the user runs many.
- **G3 — Multi-model usage** (§G3): MODEL USAGE shows only Claude; misses Codex/Grok/GLM/DeepSeek.
- **G4 — Active-card detail** (§G4, original): WHERE IT STANDS / VERIFICATION / TASKS / RUNS empty.
- **G5 — Real "needs you" detection** (§G5): NEEDS MOHAN only counts workflow failures, not agents blocked on a decision.

---

## §G1 — Active-session detection (task-status → log-liveness)

**Problem:** `collect_claude` (scan.py ~185-200) marks a session `in_progress` only if
it has a TaskList task `.json` with `status:"in_progress"` AND `recent()`. Measured
2026-07-15: **0 recent Claude task files**, yet the user had 6 live tmux agent
sessions — so 5-6 of 6 showed idle. Codex fared better (10 live `.jsonl` in 15 min).
Activity is inferred from task-file status, not actual session liveness.

**End-state:** a session whose transcript log (`.jsonl`) was appended within the
active window is detected as active, independent of whether it created a task. Claude
(`~/.claude/projects/**/*.jsonl`), Codex (`~/.codex/**/*.jsonl`), and any other
agent-log source are each probed by log mtime.

**Success criteria:**
- **SC-G1a:** with N live tmux agent sessions (logs written < ACTIVE_HOURS ago), the
  scan reports ≥N active sessions. Verify: count live `.jsonl` by mtime vs
  `sum(hasActiveTask)` in state.json — they match. (Open design Q: find the real
  Claude live-log path; measured 0 in `~/.claude/projects` — confirm where THIS
  session's transcript lands before building.)
- **SC-G1b:** a session with no task file still appears if its log is fresh.

## §G2 — Multi-session NOW card

**Problem:** `derive_now()` (scan.py ~467-476) returns exactly ONE now-item (max by
activityAt across all active). With 6 parallel sessions the other 5 are hidden.

**End-state:** the NOW region shows ALL currently-active sessions (cap ~6, newest
first), each with its project, source (Claude/Codex/…), and last-activity stamp — not
a single card. Design decision needed: list vs small-multiple cards.

**Success criteria:**
- **SC-G2:** with K active sessions, the NOW region renders K entries (capped, with a
  "+M more" if over cap). Verify: state.json `now` becomes a list of K; UI shows K.

## §G3 — Multi-model usage

**Problem:** `collect_usage` (scan.py ~410+) aggregates tokens only from Claude
session logs (`_provider_for_model` maps claude→Anthropic, gpt/codex→OpenAI, else
Other). The user runs Claude, Codex, Grok, GLM, DeepSeek — only Claude shows.

**End-state:** MODEL USAGE · TODAY aggregates token usage across every agent-log
source present (Claude transcripts, Codex logs, and any brain-router/GLM/Grok/DeepSeek
usage record the rig writes), grouped by provider+model.

**Success criteria:**
- **SC-G3a:** for a day with Codex usage, the usage block lists ≥1 non-Anthropic model
  with non-zero tokens. Verify: state.json `usage.models` contains a Codex/OpenAI row.
- **SC-G3b:** models with no usage today are absent (no zero-token noise rows).
- **Open Q:** Grok/GLM/DeepSeek run via brain-router — is there a local usage record to
  parse, or is their token count unavailable? If unavailable, say so in the UI
  ("usage not tracked for <provider>") rather than silently omitting — honesty over a
  misleading Claude-only total.

## §G5 — Real "needs you" detection (decisions, not just failures)

**Problem:** the NEEDS MOHAN panel is built from `needsAction`, which is populated ONLY
by `workflow_failure` items (scan.py ~443). It has no concept of "an agent is blocked
waiting for the user's decision." So it shows `0 — Nothing explicitly waiting on
Mohan` even when several tmux sessions are paused on an `AskUserQuestion` / approval /
`ExitPlanMode` gate. This is the single most useful signal the dashboard could give
(you can't see which of 6 tabs is blocked on you) and it currently shows nothing.

**End-state:** NEEDS YOU lists every session currently blocked on the user: an open
`AskUserQuestion`, a plan-approval gate, a permission prompt, or an explicit
"waiting for input" state — each with the project, the question/ask (truncated), and
how long it's been waiting.

**Success criteria:**
- **SC-G5a:** a session whose latest transcript event is an unanswered
  `AskUserQuestion` / approval prompt appears in NEEDS YOU. Verify: park a real session
  on an AskUserQuestion, scan, assert it's in `needsOwner` with `kind:"decision"`.
- **SC-G5b:** a session actively working (not blocked) does NOT appear. Verify: an
  in-progress non-blocked session is absent from needsOwner.
- **SC-G5c:** the wait-age is shown so the oldest-blocked is obvious.
- **Open Q:** what transcript signal reliably marks "blocked on user"? Claude Code
  transcripts — is there a terminal tool_use with no following tool_result (an open
  AskUserQuestion)? Codex — different marker? This is the load-bearing detection
  question; resolve against real transcript samples before building. If a source has
  no reliable blocked-signal, say so rather than false-negative silently.

## §G4 — Active-card detail (original 001)

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
