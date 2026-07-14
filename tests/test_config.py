import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_control_tower.config import Config, config_dir, load_config, save_config, state_dir


class ConfigTests(unittest.TestCase):
    def test_round_trip_arbitrary_root_and_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "nested" / "config.json"
            project = Path(tmp) / "unusual" / "workspace" / "source"
            project.mkdir(parents=True)
            with patch.dict(os.environ, {"CODING_CONTROL_TOWER_CONFIG": str(config_file)}):
                save_config(Config(owner_name="Alex", project_roots=[str(project)], github_enabled=False))
                loaded = load_config()
            self.assertEqual(loaded.owner_name, "Alex")
            self.assertEqual(loaded.roots(), [project.resolve()])
            self.assertFalse(loaded.github_enabled)
            self.assertEqual(json.loads(config_file.read_text())["owner_name"], "Alex")

    def test_invalid_config_types_fall_back_safely(self):
        config = Config.from_dict({"owner_name": 42, "project_roots": "not-a-list", "port": 99999})
        self.assertEqual(config.owner_name, "You")
        self.assertEqual(config.port, 7777)
        self.assertIsInstance(config.project_roots, list)

    def test_linux_uses_xdg_paths(self):
        with patch("coding_control_tower.config.platform.system", return_value="Linux"), patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/xdg-config", "XDG_STATE_HOME": "/tmp/xdg-state"}):
            self.assertEqual(config_dir(), Path("/tmp/xdg-config/coding-control-tower"))
            self.assertEqual(state_dir(), Path("/tmp/xdg-state/coding-control-tower"))

    def test_windows_uses_appdata_paths(self):
        with patch("coding_control_tower.config.platform.system", return_value="Windows"), patch.dict(os.environ, {"APPDATA": "C:/Users/Alex/AppData/Roaming", "LOCALAPPDATA": "C:/Users/Alex/AppData/Local"}):
            self.assertEqual(config_dir(), Path("C:/Users/Alex/AppData/Roaming/coding-control-tower"))
            self.assertEqual(state_dir(), Path("C:/Users/Alex/AppData/Local/coding-control-tower"))


if __name__ == "__main__":
    unittest.main()
