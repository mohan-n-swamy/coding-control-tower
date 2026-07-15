---
name: wrap-up
description: Close the current coding session — record focus, next step, and blockers so the Coding Control Tower dashboard shows where this project stands. Use when the user says "/wrap-up", "close the session", "park this", or ends a work session.
---

# Wrap-up — close the session for the dashboard

When the session is ending (or the user asks to park), record where things stand
so the Coding Control Tower shows a source-backed resume packet for this project.

1. Summarize THIS session in three short fields (be concrete, not generic):
   - **focus** — what was actually worked on
   - **next** — the ONE next physical action (a command, a file, a decision)
   - **blockers** — anything stuck, or leave empty for none
2. Run (from anywhere inside the repo):

```bash
coding-control-tower wrapup \
  --focus "<what this session worked on>" \
  --next "<the one concrete next action>" \
  --blockers "<what is stuck, or empty>"
```

3. Parking instead of finishing? Add `--park` — the dashboard marks the project
   `[parked]` and surfaces the pending step.

The dashboard picks it up on the next scan (the server rescans every 30 seconds).
Codex or any other agent can run the same command — it is plain CLI, no Claude
dependency.
