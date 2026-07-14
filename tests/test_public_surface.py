import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicSurfaceTests(unittest.TestCase):
    def test_static_ui_is_local_and_configurable(self):
        html = (ROOT / "src" / "coding_control_tower" / "static" / "index.html").read_text()
        self.assertIn("ownerName", html)
        self.assertNotIn("NEEDS MOHAN", html)
        self.assertNotIn("unpkg.com", html)
        self.assertNotIn("innerHTML", html)
        self.assertIn("Content-Security-Policy", html)

    def test_public_text_has_no_private_machine_path(self):
        text = "\n".join(path.read_text(errors="replace") for path in ROOT.rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".html", ".cfg"})
        private_prefix = "/Users/" + "mohann" + "arayanswamy"
        self.assertNotIn(private_prefix, text)


if __name__ == "__main__":
    unittest.main()
