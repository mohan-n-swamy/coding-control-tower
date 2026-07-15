import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_control_tower.config import Config
from coding_control_tower.scan import (
    assemble,
    body_section,
    build_state,
    collect_usage,
    discover_repositories,
    human_name,
    iso_now,
    read_jsonl_metadata,
    redact,
)


class ScanTests(unittest.TestCase):
    def test_discovers_nested_repositories_under_any_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "company" / "group" / "strange_repo"
            (repo / ".git").mkdir(parents=True)
            (repo / ".git" / "HEAD").write_text("ref: refs/heads/feature/test\n")
            found = discover_repositories(Config(project_roots=[tmp], scan_depth=5))
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["name"], "Strange Repo")
            self.assertEqual(found[0]["branch"], "feature/test")

    def test_unmapped_sessions_collapse_into_one_bucket(self):
        # Many cwd-unmapped sessions must not each spawn a top-level card — they
        # collapse into ONE "unassigned" bucket, else real repos get drowned.
        work = [
            {"type": "task", "source": "Claude", "session": "aaaaaaaa-1", "cwd": None, "title": "One", "status": "pending", "activityAt": "2026-07-14T10:00:00Z", "prNumber": None},
            {"type": "task", "source": "Claude", "session": "bbbbbbbb-2", "cwd": None, "title": "Two", "status": "pending", "activityAt": "2026-07-14T11:00:00Z", "prNumber": None},
        ]
        projects = assemble(Config(), [], work, [], [])
        self.assertEqual({project["id"] for project in projects}, {"unassigned"})
        bucket = next(p for p in projects if p["id"] == "unassigned")
        self.assertEqual(len(bucket["localWork"]), 2)

    def test_unassigned_bucket_never_wins_now_over_real_repo(self):
        # An in-progress item in the noise bucket must NOT flip it active and steal
        # the "now" slot from a real repo (adversarial regression, 2026-07-14).
        repo = {"id": "alpha", "name": "Alpha", "path": "/work/alpha", "repoName": "alpha", "branch": "main"}
        work = [
            {"type": "task", "source": "Claude", "session": "orphan-1", "cwd": None, "title": "Orphan running", "status": "in_progress", "activityAt": "2099-01-01T00:00:00Z", "prNumber": None},
            {"type": "task", "source": "Claude", "session": "s", "cwd": "/work/alpha/src", "title": "Real pending", "status": "pending", "activityAt": "2026-01-01T00:00:00Z", "prNumber": None},
        ]
        projects = assemble(Config(), [repo], work, [], [])
        bucket = next(p for p in projects if p["id"] == "unassigned")
        self.assertFalse(bucket["hasActiveTask"])
        self.assertEqual(bucket["state"], "history")
        # bucket must sort AFTER the real repo despite its newer in-progress item
        self.assertEqual(projects[0]["id"], "alpha")

    def test_active_first_and_exact_pr_link(self):
        repo = {"id": "alpha", "name": "Alpha", "path": "/work/alpha", "repoName": "alpha", "branch": "main"}
        work = [{"type": "task", "source": "Claude", "session": "s", "cwd": "/work/alpha/src", "title": "Finish PR #7", "status": "in_progress", "activityAt": "2099-01-01T00:00:00Z", "prNumber": 7}]
        prs = [{"number": 7, "title": "Feature", "status": "open", "updatedAt": "2026-01-01T00:00:00Z", "repoName": "alpha", "repoFullName": "acme/alpha", "summary": "Feature", "claimedOutcome": None, "workItems": []}]
        projects = assemble(Config(), [repo], work, [], prs)
        self.assertTrue(projects[0]["hasActiveTask"])
        self.assertEqual(projects[0]["prs"][0]["workItems"][0]["title"], "Finish PR #7")

    def test_delivery_claim_requires_explicit_section(self):
        self.assertEqual(body_section("## Outcome\nShipped to staging.\n", ("Outcome",)), "Shipped to staging.")
        self.assertIsNone(body_section("## Summary\nMerged change.\n", ("Outcome",)))

    def test_redacts_common_tokens(self):
        secret = "gh" + "p_" + "a" * 24
        self.assertNotIn(secret, redact({"value": secret})["value"])

    def test_build_state_uses_configured_owner_without_optional_adapters(self):
        config = Config(owner_name="Priya", project_roots=[], github_enabled=False)
        empty_usage = {"period": "today", "totalIn": 0, "totalOut": 0, "models": []}
        with patch("coding_control_tower.scan.discover_repositories", return_value=[]), patch("coding_control_tower.scan.collect_claude", return_value=([], [])), patch("coding_control_tower.scan.collect_codex", return_value=[]), patch("coding_control_tower.scan.collect_github", return_value=([], {"enabled": False, "count": 0})), patch("coding_control_tower.scan.collect_usage", return_value=empty_usage):
            state = build_state(config)
        self.assertEqual(state["ownerName"], "Priya")
        self.assertEqual(state["projects"], [])
        self.assertEqual(state["usage"], empty_usage)
        self.assertNotIn("needsMohan", state)

    def test_collect_usage_aggregates_todays_model_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "projects" / "demo" / "session.jsonl"
            session.parent.mkdir(parents=True)
            now = iso_now()
            rows = [
                {"timestamp": now, "message": {"model": "claude-sonnet-4-5", "usage": {"input_tokens": 100, "cache_read_input_tokens": 900, "output_tokens": 50}}},
                {"timestamp": now, "message": {"model": "claude-sonnet-4-5", "usage": {"input_tokens": 1000, "output_tokens": 150}}},
                {"timestamp": "2001-01-01T00:00:00Z", "message": {"model": "claude-sonnet-4-5", "usage": {"input_tokens": 999999, "output_tokens": 999999}}},
                {"timestamp": now, "message": {"model": "<synthetic>", "usage": {"input_tokens": 5, "output_tokens": 5}}},
                {"timestamp": now, "no_usage": True},
            ]
            session.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
            usage = collect_usage(Config(claude_dir=tmp))
        self.assertEqual(usage["totalIn"], 2000)
        self.assertEqual(usage["totalOut"], 200)
        self.assertEqual(len(usage["models"]), 1)
        self.assertEqual(usage["models"][0]["model"], "claude-sonnet-4-5")
        self.assertEqual(usage["models"][0]["provider"], "Anthropic")
        self.assertEqual(usage["models"][0]["share"], 100)

    def test_human_name_preserves_common_acronyms(self):
        self.assertEqual(human_name("mcp-api-ui"), "MCP API UI")

    def test_session_metadata_uses_latest_observed_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            first = {"cwd": "/work/old", "gitBranch": "old", "timestamp": "2026-01-01T00:00:00Z", "padding": "x" * 600_000}
            latest = {"cwd": "/work/new", "gitBranch": "feature/new", "timestamp": "2026-07-14T12:00:00Z"}
            session.write_text(json.dumps(first) + "\n" + json.dumps(latest) + "\n")
            metadata = read_jsonl_metadata(session)
        self.assertEqual(metadata["cwd"], "/work/new")
        self.assertEqual(metadata["branch"], "feature/new")

    def test_collect_live_sessions_detects_fresh_transcripts_by_mtime(self):
        from coding_control_tower.scan import collect_live_sessions
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "projects" / "-work-alpha"
            proj.mkdir(parents=True)
            fresh = proj / "abc.jsonl"
            fresh.write_text(json.dumps({"timestamp": iso_now(), "cwd": "/work/alpha",
                "message": {"model": "claude-opus-4-8"}}) + "\n")
            stale = proj / "old.jsonl"
            stale.write_text("{}\n")
            os.utime(stale, (0, 0))
            repos = [{"id": "alpha", "name": "Alpha", "path": "/work/alpha", "repoName": "alpha", "branch": "main"}]
            live = collect_live_sessions(Config(claude_dir=tmp, codex_dir=tmp), repos)
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0]["session"], "abc")
        self.assertEqual(live[0]["projectId"], "alpha")
        self.assertEqual(live[0]["model"], "claude-opus-4-8")

    def _write_transcript(self, tmp, name, events):
        proj = Path(tmp) / "projects" / "-work-alpha"
        proj.mkdir(parents=True, exist_ok=True)
        f = proj / (name + ".jsonl")
        f.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        return f

    def test_pending_askuserquestion_is_a_decision(self):
        from coding_control_tower.scan import collect_decisions
        ask = {"timestamp": iso_now(), "cwd": "/work/alpha", "message": {"content": [
            {"type": "tool_use", "name": "AskUserQuestion", "id": "tu1",
             "input": {"questions": [{"question": "Ship v1 now?"}]}}]}}
        with tempfile.TemporaryDirectory() as tmp:
            self._write_transcript(tmp, "pending", [ask])
            repos = [{"id": "alpha", "name": "Alpha", "path": "/work/alpha", "repoName": "alpha", "branch": "main"}]
            out = collect_decisions(Config(claude_dir=tmp), repos)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "decision")
        self.assertEqual(out[0]["ask"], "Ship v1 now?")
        self.assertEqual(out[0]["projectId"], "alpha")
        self.assertIn("claude --resume pending", out[0]["resumeCmd"])

    def test_answered_question_and_foreign_tools_do_not_flag(self):
        from coding_control_tower.scan import collect_decisions
        ask = {"timestamp": iso_now(), "cwd": "/w", "message": {"content": [
            {"type": "tool_use", "name": "AskUserQuestion", "id": "tu1",
             "input": {"questions": [{"question": "Q?"}]}}]}}
        answer = {"timestamp": iso_now(), "message": {"content": [
            {"type": "tool_result", "tool_use_id": "tu1"}]}}
        busy = {"timestamp": iso_now(), "message": {"content": [
            {"type": "tool_use", "name": "Bash", "id": "tu2", "input": {}}]}}
        with tempfile.TemporaryDirectory() as tmp:
            self._write_transcript(tmp, "answered", [ask, answer, busy])
            out = collect_decisions(Config(claude_dir=tmp), [])
        self.assertEqual(out, [])

    def test_body_checklist_becomes_tasks_and_contract_names(self):
        from coding_control_tower.scan import normalize_pr
        raw = {"number": 81, "title": "Retry queue", "state": "open",
               "url": "https://x", "repository": {"name": "alpha", "nameWithOwner": "o/alpha"},
               "body": "## Where it stands\nDraining fine.\n- [x] migration\n- [ ] jitter test\n"}
        pr = normalize_pr(raw)
        self.assertEqual(pr["num"], 81)
        self.assertEqual(pr["statusLabel"], "Active")
        self.assertEqual(pr["progress"], "Draining fine.")
        self.assertEqual(pr["tasks"], {"done": 1, "total": 2, "items": [
            {"t": "migration", "done": True}, {"t": "jitter test", "done": False}]})
        self.assertEqual(pr["verification"][-1]["tone"], "link")

    def test_merged_without_outcome_gets_wait_badge_never_ok(self):
        from coding_control_tower.scan import normalize_pr
        pr = normalize_pr({"number": 9, "title": "x", "state": "merged", "repository": {}, "body": ""})
        tones = [b["tone"] for b in pr["verification"]]
        self.assertIn("wait", tones)
        self.assertNotIn("ok", tones)


class AdapterLoaderTests(unittest.TestCase):
    def test_valid_adapter_contributes_and_bad_keys_dropped(self):
        from coding_control_tower.adapters import load_external, run_collectors
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "good.py").write_text(
                "def collect(config):\n"
                "    return {'usage_models': [{'provider':'Z.ai','model':'glm-5.2','tin':10,'tout':5,'approx':True}],\n"
                "            'wrapups': {'proj': {'focus':'f','next':'n','evil':'x'}},\n"
                "            'evil_channel': 1}\n")
            collectors, errs = load_external(Config(adapter_dirs=[tmp]))
            self.assertEqual(errs, [])
            merged, run_errs = run_collectors(collectors, Config())
            self.assertEqual(run_errs, [])
            self.assertEqual(merged["usage_models"][0]["provider"], "Z.ai")
            self.assertTrue(merged["usage_models"][0]["approx"])
            self.assertEqual(merged["wrapups"]["proj"], {"focus": "f", "next": "n"})

    def test_broken_adapter_isolated_as_error(self):
        from coding_control_tower.adapters import load_external, run_collectors
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "boom.py").write_text("def collect(config):\n    raise RuntimeError('x')\n")
            Path(tmp, "noattr.py").write_text("VALUE = 1\n")
            collectors, errs = load_external(Config(adapter_dirs=[tmp]))
            self.assertEqual(len(errs), 1)  # noattr rejected at load
            merged, run_errs = run_collectors(collectors, Config())
            self.assertEqual(len(run_errs), 1)  # boom rejected at run
            self.assertEqual(merged["usage_models"], [])


if __name__ == "__main__":
    unittest.main()
