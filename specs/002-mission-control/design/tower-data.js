window.TOWER_DATA = {
  now: {
    project: "freshchat-bot", projectId: "fcb", task: "Harden webhook retry queue", pr: 81,
    started: "09:12", elapsed: "1h 40m",
    stop: "Backoff test written; jitter-bounds assertion is flaky (fails ~1 in 5 runs)",
    next: "Pin RNG seed in test_backoff_jitter, re-run pytest -k retry",
    lastRun: "pytest 47/48 · 10:41", mascot: "working"
  },
  usage: {
    period: "today", totalIn: "2.15M", totalOut: "322k",
    models: [
      { provider: "Anthropic", model: "claude-sonnet-4-5", tin: "1.20M", tout: "184k", share: 62 },
      { provider: "Anthropic", model: "claude-opus-4-1", tin: "310k", tout: "42k", share: 21 },
      { provider: "OpenAI", model: "gpt-4.1-mini", tin: "640k", tout: "96k", share: 17 }
    ]
  },
  needsMohan: [
    { project: "coding-control-tower", ask: "Choose ledger storage: repo-local .tower/ vs global ~/.tower", blocks: "PR #13 (draft) — session ledger sync", age: "2d" },
    { project: "golden-flow", ask: "Product call: allow guest checkout in the v2 address step?", blocks: "PR #33 — checkout flow v2", age: "19h" }
  ],
  projects: [
    {
      id: "fcb", name: "Freshchat Bot", path: "~/dev/freshchat-bot", branch: "fix/webhook-retry-81",
      activity: "24m ago", state: "active", counts: "1 active · 4 merged · 1 failed",
      prs: [
        { num: 81, title: "Webhook retry queue with exponential backoff", status: "active", statusLabel: "Active", date: "opened Jul 12", updated: "updated 24m ago",
          progress: "In progress — retries land in queue and drain; jitter test still flaky.",
          verification: [{ tone: "wait", label: "CI · 2/3 checks, 1 pending" }],
          tasks: { done: 4, total: 6, items: [
            { t: "Queue table migration", done: true }, { t: "Backoff calculator (base 2s, cap 5m)", done: true },
            { t: "Retry worker + dead-letter handoff", done: true }, { t: "Wire retries into webhook handler", done: true },
            { t: "Jitter-bounds test (flaky — current)", done: false }, { t: "Runbook note in docs/ops.md", done: false } ] },
          runs: [{ label: "pytest 47/48", time: "10:41", ok: false }, { label: "pytest 44/48", time: "09:58", ok: false }, { label: "ruff + mypy clean", time: "09:31", ok: true }] },
        { num: 79, title: "Dedupe inbound message events", status: "merged", statusLabel: "Merged", date: "merged Jul 9",
          outcome: "Duplicate bot replies eliminated — inbound events are idempotent via an event-id cache (24h TTL).",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Verified in staging · Jul 9" }, { tone: "link", label: "Screenshot", href: "#" }],
          tasks: { done: 6, total: 6 }, runs: [{ label: "pytest 52/52", time: "Jul 9 16:02", ok: true }] },
        { num: 74, title: "Rate-limit Freshchat API client", status: "merged", statusLabel: "Merged", date: "merged Jul 2",
          outcome: "API 429s dropped to zero under burst load; client honors Retry-After headers.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Load test 500 rpm · pass" }],
          tasks: { done: 5, total: 5 }, runs: [{ label: "pytest 49/49", time: "Jul 2 11:20", ok: true }] },
        { num: 71, title: "Structured logging for webhook handlers", status: "merged", statusLabel: "Merged", date: "merged Jun 26",
          outcome: "Every webhook request traceable by request-id; JSON logs ship to Loki.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Log queries verified in Grafana · Jun 26" }],
          tasks: { done: 3, total: 3 }, runs: [{ label: "pytest 46/46", time: "Jun 26 10:05", ok: true }] },
        { num: 68, title: "Migrate bot config to pydantic-settings", status: "merged", statusLabel: "Merged", date: "merged Jun 19",
          outcome: "Config typos fail fast at boot instead of at runtime; .env schema documented.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Boot check on staging · Jun 19" }],
          tasks: { done: 4, total: 4 }, runs: [{ label: "pytest 45/45", time: "Jun 19 15:40", ok: true }] },
        { num: 65, title: "Conversation-context window pruning", status: "failed", statusLabel: "Failed — not built", date: "closed Jun 12",
          error: { cause: "Pruning dropped system messages, breaking bot persona in 3/10 test convos", impact: "No artifact shipped — feature was never built", next: "Redo with role-aware pruning; superseded by planned PR" },
          verification: [{ tone: "fail", label: "QA failed — never shipped" }],
          tasks: { done: 3, total: 4 }, runs: [{ label: "convo eval 7/10", time: "Jun 12 13:02", ok: false }] }
      ],
      local: [{ t: "Rotated staging API keys", date: "Jul 8", note: ".env.staging updated — secrets stay local, no PR" }]
    },
    {
      id: "gf", name: "Golden Flow", path: "~/dev/golden-flow", branch: "feat/checkout-v2",
      activity: "Jul 13", state: "planning", counts: "1 draft · 3 merged",
      prs: [
        { num: 33, title: "Checkout v2 — address step", status: "draft", statusLabel: "Draft", date: "opened Jul 11", updated: "updated Jul 13",
          progress: "Blocked on guest-checkout decision (see NEEDS MOHAN). Address form + validation done; save path pending.",
          verification: [{ tone: "ok", label: "CI green on draft" }],
          tasks: { done: 3, total: 7 }, runs: [{ label: "vitest 31/31", time: "Jul 13 17:45", ok: true }] },
        { num: 29, title: "Golden-path smoke suite", status: "merged", statusLabel: "Merged", date: "merged Jun 28",
          outcome: "Checkout golden path covered end-to-end; suite runs in CI on every PR (2m 40s).",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "12/12 scenarios vs staging · Jun 28" }],
          tasks: { done: 8, total: 8 }, runs: [{ label: "playwright 12/12", time: "Jun 28 14:10", ok: true }] },
        { num: 27, title: "Cart state — server reconciliation", status: "merged", statusLabel: "Merged", date: "merged Jun 20",
          outcome: "Cart survives refresh and multi-tab; server is source of truth with optimistic UI.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Multi-tab manual pass · Jun 20" }],
          tasks: { done: 6, total: 6 }, runs: [{ label: "vitest 29/29", time: "Jun 20 12:30", ok: true }] },
        { num: 24, title: "Design tokens → CSS variables", status: "merged", statusLabel: "Merged", date: "merged Jun 11",
          outcome: "All colors/spacing flow from tokens.css; dark mode now a one-file switch.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "link", label: "Before/after screenshots", href: "#" }],
          tasks: { done: 5, total: 5 }, runs: [{ label: "vitest 27/27", time: "Jun 11 09:55", ok: true }] }
      ],
      local: [{ t: "Upgraded Playwright 1.44 → 1.46", date: "Jul 5", note: "Lockfile bump only; suite green, no PR needed" }]
    },
    {
      id: "cct", name: "Coding Control Tower", path: "~/dev/coding-control-tower", branch: "main",
      activity: "Jul 11", state: "attention", counts: "3 merged · 1 failed",
      prs: [
        { num: 12, title: "Session ledger persistence (SQLite)", status: "merged", statusLabel: "Merged", date: "merged Jul 10",
          outcome: "Sessions survive restarts — ledger in SQLite with WAL; zero data loss across 50 kill tests.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Kill-test 50/50" }],
          tasks: { done: 4, total: 4 }, runs: [{ label: "vitest 38/38", time: "Jul 10 09:12", ok: true }] },
        { num: 11, title: "Mascot state machine", status: "failed", statusLabel: "Failed — not built", date: "closed Jul 6",
          error: { cause: "Circular import mascot ↔ store breaks the Vite build", impact: "No artifact produced — feature was never built or shipped", next: "Extract shared types into mascot-types.ts, reopen as a new PR" },
          verification: [{ tone: "fail", label: "Build failed — never shipped" }],
          tasks: { done: 2, total: 5 }, runs: [{ label: "vite build · exit 1", time: "Jul 6 15:33", ok: false }] },
        { num: 9, title: "Project folder scanner + git status probe", status: "merged", statusLabel: "Merged", date: "merged Jun 30",
          outcome: "Tower auto-discovers every repo under ~/dev and reads branch, ahead/behind, dirty state.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Scanned 14 real repos · Jun 30" }],
          tasks: { done: 5, total: 5 }, runs: [{ label: "vitest 24/24", time: "Jun 30 16:20", ok: true }] },
        { num: 7, title: "Zero-dependency index.html shell", status: "merged", statusLabel: "Merged", date: "merged Jun 22",
          outcome: "Single-file dashboard loads offline in <100ms; no build step, no npm.",
          verification: [{ tone: "ok", label: "Opened from file:// · pass" }, { tone: "ok", label: "Lighthouse 100 perf" }],
          tasks: { done: 3, total: 3 }, runs: [{ label: "manual smoke · pass", time: "Jun 22 11:00", ok: true }] }
      ],
      local: [{ t: "Spike: watchman-based folder scanner", date: "Jul 11", note: "Prototype in scratch/watch.js — promising, needs a PR" }]
    },
    {
      id: "inv", name: "Invoice Parser", path: "~/dev/invoice-parser", branch: "main",
      activity: "May 30", state: "idle", counts: "2 merged",
      prs: [
        { num: 18, title: "PDF table extraction v2", status: "merged", statusLabel: "Merged", date: "merged May 30",
          outcome: "Line-item accuracy 91% → 98% on the 40-doc eval set.",
          verification: [{ tone: "ok", label: "CI green" }, { tone: "ok", label: "Eval 40/40 docs" }],
          tasks: { done: 4, total: 4 }, runs: [{ label: "eval 40/40", time: "May 30 13:15", ok: true }] },
        { num: 15, title: "OCR fallback for scanned invoices", status: "merged", statusLabel: "Merged", date: "merged May 18",
          outcome: "Scanned invoices no longer rejected — OCR fallback covers the full test corpus.",
          verification: [{ tone: "ok", label: "CI green" }],
          tasks: { done: 3, total: 3 }, runs: [{ label: "pytest 33/33", time: "May 18 10:22", ok: true }] }
      ],
      local: []
    }
  ]
};
