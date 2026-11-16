"""Скрипт страницы разбирается без ошибок (иначе вся страница пустая)."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

HTML = Path(__file__).resolve().parent.parent / "static" / "index.html"


@unittest.skipUnless(shutil.which("node"), "node not installed")
class JsSyntax(unittest.TestCase):
    def test_scripts_parse(self):
        for i, body in enumerate(re.findall(r"<script[^>]*>([\s\S]*?)</script>", HTML.read_text("utf-8"))):
            r = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(0,'utf8'))"], input=body,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"script {i}: {r.stderr[-400:]}")


if __name__ == "__main__":
    unittest.main()
