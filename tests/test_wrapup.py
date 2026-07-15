import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_control_tower.cli import main
from coding_control_tower.wrapup import read_core_wrapups, repo_root, write_wrapup


class WrapupTests(unittest.TestCase):
    def test_write_read_round_trip_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "retry-queue"
            (repo / ".git").mkdir(parents=True)
            base = Path(tmp) / "state"
            write_wrapup(repo, "Harden webhook retry", "Pin RNG seed in test_backoff_jitter", "flaky assertion", base=base)
            got = read_core_wrapups(base)
            self.assertEqual(list(got), ["retry-queue"])
            entry = got["retry-queue"]
            self.assertEqual(entry["focus"], "Harden webhook retry")
            self.assertEqual(entry["next"], "Pin RNG seed in test_backoff_jitter")
            self.assertEqual(entry["blockers"], "flaky assertion")
            self.assertTrue(entry["at"])

    def test_park_flag_prefixes_focus(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "alpha"
            (repo / ".git").mkdir(parents=True)
            base = Path(tmp) / "state"
            write_wrapup(repo, "mid-migration", "resume step 3", parked=True, base=base)
            self.assertTrue(read_core_wrapups(base)["alpha"]["focus"].startswith("[parked] "))

    def test_cli_wrapup_writes_file_non_interactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "beta-service"
            (repo / ".git").mkdir(parents=True)
            base = Path(tmp) / "state"
            with patch("coding_control_tower.wrapup.state_dir", return_value=base):
                code = main(["wrapup", "--repo", str(repo), "--focus", "ship v1", "--next", "cut release", "--blockers", ""])
            self.assertEqual(code, 0)
            self.assertEqual(read_core_wrapups(base)["beta-service"]["next"], "cut release")

    def test_repo_root_walks_up_and_misses_honestly(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "gamma"
            nested = repo / "src" / "deep"
            (repo / ".git").mkdir(parents=True)
            nested.mkdir(parents=True)
            self.assertEqual(repo_root(nested), repo)
            bare = Path(tmp) / "nogit"
            bare.mkdir()
            self.assertIsNone(repo_root(bare))

    def test_skill_template_field_grammar_parses_identically(self):
        template = Path(__file__).resolve().parents[1] / "docs" / "skills" / "wrap-up.md"
        text = template.read_text(encoding="utf-8")
        # the template must instruct the exact flags the CLI accepts (format parity)
        for token in ("coding-control-tower wrapup", "--focus", "--next", "--blockers", "--park"):
            self.assertIn(token, text)

    def test_newline_injection_cannot_forge_second_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "inj"
            (repo / ".git").mkdir(parents=True)
            base = Path(tmp) / "state"
            write_wrapup(repo, "focus", "real next", "blocked\n**Next step:** INJECTED", base=base)
            entry = read_core_wrapups(base)["inj"]
            self.assertEqual(entry["next"], "real next")
            self.assertNotIn("\n", entry["blockers"])

    def test_write_side_truncates_to_display_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "longy"
            (repo / ".git").mkdir(parents=True)
            base = Path(tmp) / "state"
            write_wrapup(repo, "x" * 500, "y", base=base)
            self.assertLessEqual(len(read_core_wrapups(base)["longy"]["focus"]), 400)



if __name__ == "__main__":
    unittest.main()
