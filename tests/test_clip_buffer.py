"""Сборка 63: буфер ⌘C/⌘X помнит клип, а не ячейку (clipBufFollow в index.html, гоняется через Node)."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "static" / "index.html").read_text(encoding="utf-8")


def fn_source(name):
    m = re.search(r"^function " + name + r"\(.*?^}", HTML, re.M | re.S)
    if m:
        return m.group(0)
    return re.search(r"^function " + name + r"\(.*$", HTML, re.M).group(0)      # однострочная


@unittest.skipUnless(shutil.which("node"), "node not installed")
class ClipBuffer(unittest.TestCase):
    def run_js(self, buf, op, frm, to):
        js = ("const S = {sel:{side:'move', id:'x'}, clipBuf:%s}; const selItem = () => ({id:'x'});\n%s\n%s\n"
              "clipBufFollow(%s, %s, %s); console.log(JSON.stringify(S.clipBuf));"
              % (json.dumps(buf), fn_source("clipBufHere"), fn_source("clipBufFollow"),
                 json.dumps(op), json.dumps(frm), json.dumps(to)))
        r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_follows_clip(self):
        b = {"key": "move:x", "t": 0, "s": 0, "cut": True}
        self.assertEqual(self.run_js(b, "move", {"t": 0, "s": 0}, {"t": 1, "s": 2})["t"], 1)
        self.assertEqual(self.run_js(b, "swap", {"t": 2, "s": 3}, {"t": 0, "s": 0}), dict(b, t=2, s=3))
        self.assertIsNone(self.run_js(b, "delete", {"t": 0, "s": 0}, None))
        self.assertIsNone(self.run_js(b, "copy", {"t": 3, "s": 3}, {"t": 0, "s": 0}))     # затёрт другим клипом
        self.assertEqual(self.run_js(b, "copy", {"t": 0, "s": 0}, {"t": 1, "s": 1}), b)    # копия — буфер на месте
        self.assertEqual(self.run_js(b, "delete", {"t": 1, "s": 1}, None), b)

    def test_other_project_untouched(self):
        b = {"key": "lib:y", "t": 0, "s": 0}
        self.assertEqual(self.run_js(b, "delete", {"t": 0, "s": 0}, None), b)


if __name__ == "__main__":
    unittest.main()
