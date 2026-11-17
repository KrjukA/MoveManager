"""Сборка 56: русский интерфейс. Переводчик static/i18n.js гоняется через Node (есть на Mac и на GitHub)."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import app
from tests.test_routes_midi import RouteBase

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "static" / "i18n.js"
HARNESS = """
const g = globalThis;
g.localStorage = {getItem: k => k === "mm-lang" ? process.argv[2] : null, setItem(){}};
g.navigator = {language: "en-US"};
g.document = {documentElement: {}, body: null, addEventListener(){}, title: ""};
g.window = {confirm(){}, prompt(){}, alert(){}};
g.NodeFilter = {SHOW_TEXT: 4, SHOW_ELEMENT: 1};
const src = require("fs").readFileSync(process.argv[1], "utf8");
eval(src + "; g.tr = tr; g.t = t; g.LANG = LANG;");
const items = JSON.parse(require("fs").readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(items.map(s => g.tr(s))));
"""


def translate(strings, lang="ru"):
    r = subprocess.run(["node", "-e", HARNESS, str(I18N), lang], input=json.dumps(strings).encode(),
                       capture_output=True, timeout=30)
    if r.returncode:
        raise AssertionError(r.stderr.decode())
    return json.loads(r.stdout)


def server_messages():
    """Неизменные тексты ошибок сервера (не f-строки)."""
    src = (ROOT / "app.py").read_text("utf-8")
    out = set()
    for m in re.finditer(r'(?:AppError|CellBusy|SshError|MoveOffline)\("((?:[^"\\]|\\.)*)"\)', src):
        out.add(m.group(1).replace('\\"', '"'))
    out.discard("Tests must not reach a real Move over HTTP")
    out.discard("Tests must not reach a real Move over SSH")
    return sorted(s for s in out if not s.endswith(": ") and re.search("[A-Za-z]", s))


CYR = re.compile("[А-Яа-яЁё]")


@unittest.skipUnless(shutil.which("node"), "нужен Node.js")
class Translate(unittest.TestCase):
    def test_every_server_message_is_russian(self):
        msgs = server_messages()
        got = translate(msgs)
        missing = [m for m, r in zip(msgs, got) if not CYR.search(r)]
        self.assertEqual(missing, [], "нет перевода для сообщений сервера")

    def test_main_labels(self):
        labels = ["Projects", "Samples", "Presets", "Refresh", "Report", "Tracks", "Clips", "History", "Restore",
                  "Delete clip", "Add loops…", "To computer →", "← To Move", "Enable pad control", "Cancel",
                  "Save report", "Report a problem", "Looking for Move on the network…", "Default input"]
        got = translate(labels)
        self.assertEqual([l for l, r in zip(labels, got) if not CYR.search(r)], [])

    def test_patterns_and_fragments(self):
        cases = {
            "Clip deleted: track 2, scene 3. Leave the project on Move and open it again to see the changes":
                "Клип удалён: дорожка 2, сцена 3. Выйдите из проекта на Move и откройте его снова, чтобы увидеть изменения",
            "Clip moved: track 1, scene 1 → track 2, scene 4": "Клип перенесён: дорожка 1, сцена 1 → дорожка 2, сцена 4",
            "A clip from a Drum Rack track can only go to a Drum Rack track": "Клип с дорожки Drum Rack кладётся только на дорожку Drum Rack",
            "Loops added: 3 to track 3, scenes 4–6": "Добавлено лупов: 3 на дорожку 3, scenes 4–6",
        }
        got = translate(list(cases))
        for (src, want), r in zip(cases.items(), got):
            if src.startswith("Loops added"):
                self.assertTrue(r.startswith("Добавлено лупов: 3 на дорожку 3"), r)
            else:
                self.assertEqual(r, want)

    def test_names_in_quotes_untouched(self):
        r = translate(['Clip from "Delete" loaded: track 1, scene 2', '"Restore" uploaded to Move'])
        self.assertIn("«Delete»", r[0])
        self.assertIn("«Restore»", r[1])

    def test_whitespace_kept_and_unknown_left(self):
        r = translate(["  Refresh  ", "Heavy Mellow Kit", "12", ""])
        self.assertEqual(r, ["  Обновить  ", "Heavy Mellow Kit", "12", ""])

    def test_english_mode_untouched(self):
        self.assertEqual(translate(["Refresh", "Cell is empty"], lang="en"), ["Refresh", "Cell is empty"])


class Serve(RouteBase):
    def test_static_script_served(self):
        st, headers, body = self.req("GET", "/static/i18n.js")
        self.assertEqual(st, 200)
        self.assertIn("javascript", headers["Content-Type"])
        self.assertIn(b"I18N", body)
        st, _, _ = self.req("GET", "/static/../app.py")
        self.assertNotEqual(st, 200)

    def test_page_loads_translator_first(self):
        html = (ROOT / "static" / "index.html").read_text("utf-8")
        self.assertLess(html.index('src="/static/i18n.js"'), html.index("const $ = s =>"))
