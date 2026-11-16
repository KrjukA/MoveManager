import tempfile
import time
import unittest
from pathlib import Path

import app


class Backups(unittest.TestCase):
    def test_keeps_last_five_per_project(self):
        d = Path(tempfile.mkdtemp())
        for i in range(8):
            p = d / f"Set 103 20261113-2150{i:02d}.abl"
            p.write_text(str(i))
        (d / "Other 20261113-215000.abl").write_text("x")
        app.prune_backups(d, "Set 103", keep=5)
        left = sorted(p.name for p in d.glob("Set 103 *.abl"))
        self.assertEqual(left, [f"Set 103 20261113-2150{i:02d}.abl" for i in range(3, 8)])
        self.assertTrue((d / "Other 20261113-215000.abl").exists())


if __name__ == "__main__":
    unittest.main()
