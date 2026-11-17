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

    def test_buttons_and_tabs_stay_english(self):
        # the author (17.11): короткие кнопки, вкладки и заголовки — по-английски; переводятся описания и сообщения
        # the author (17.11): шапка остаётся английской; кнопки .mid и Generate — тоже
        labels = ["Projects", "Samples", "Presets", "Refresh", "Report", "Enable pad control", "Save report",
                  "Report a problem", "Default input", "Save .mid", "Load .mid", "Generate…"]
        self.assertEqual(translate(labels), labels)

    def test_panel_and_generator_controls_are_russian(self):
        got = translate(["Description", "Notes", "To computer →", "← To Move", "Open", "Copy to computer →", "Tracks", "Clips",
                         "History", "Restore", "Genre", "Mutation", "Put in cell", "on computer"])
        self.assertEqual([g for g in got if not CYR.search(g)], [])

    def test_descriptions_are_russian_with_english_terms(self):
        r = translate(["Looking for Move on the network…", "Deleting a clip on Move needs pad control enabled",
                       "Drop loops on a cell of an audio track"])
        self.assertEqual(r, ["Ищу Move в сети…", "Для удаления Clip на Move включите Pad control",
                             "Перетащите Loops на ячейку audio Track"])

    def test_patterns_and_fragments(self):
        cases = {
            "Clip deleted: track 2, scene 3. Leave the project on Move and open it again to see the changes":
                "Clip удалён: Track 2, Scene 3. Выйдите из проекта на Move и откройте его снова, чтобы увидеть изменения",
            "Clip moved: track 1, scene 1 → track 2, scene 4": "Clip перенесён: Track 1, Scene 1 → Track 2, Scene 4",
            "A clip from a Drum Rack track can only go to a Drum Rack track": "Clip с Drum Rack Track можно положить только на Drum Rack Track",
            "Loops added: 3 to track 3, scenes 4–6": "Добавлено лупов: 3 на дорожку 3, scenes 4–6",
        }
        got = translate(list(cases))
        for (src, want), r in zip(cases.items(), got):
            if src.startswith("Loops added"):
                self.assertEqual(r, "Добавлено Loops: 3 на Track 3, Scene 4–6")
            else:
                self.assertEqual(r, want)

    def test_variable_led_messages(self):
        cases = {"Samples/Kick.wav — done, 2 projects updated": "Samples/Kick.wav — готово, обновлено проектов: 2",
                 "Clip moved: track 1, scene 1 → track 2, scene 3. Leave the project on Move and open it again to see the changes":
                     "Clip перенесён: Track 1, Scene 1 → Track 2, Scene 3. Выйдите из проекта на Move и откройте его снова, чтобы увидеть изменения",
                 "Cut: track 2, scene 3. Pick a cell and press ⌘V": "Вырезано: Track 2, Scene 3. Выберите ячейку и нажмите ⌘V",
                 'Ordered by Camelot, starting from "Nord Jam"': "Упорядочено по Camelot, начиная с «Nord Jam»",
                 '"Song" deleted from Move. A copy is in the "_Deleted" folder on the computer: Song (deleted from Move 20261117-101010)':
                     "«Song» удалён с Move. Копия — в папке «_Deleted» на компьютере: Song (deleted from Move 20261117-101010)",
                 "Copied to Samples/Kicks on Move: 3 files · skipped 1 that aren't audio": "Скопировано в Samples/Kicks на Move: 3 · пропущено 1 (не звук)",
                 "Replace 1 clip in track 2, scene 4?": "Заменить Clip на Track 2, Scene 4?",
                 "before: Clip moved T2 S3 → T2 S4": "до: Clip перенесён: Track 2, Scene 3 → Track 2, Scene 4",
                 "Restored to 17 Nov 07:33:40. Leave the project on Move and open it again to see the changes":
                     "Проект возвращён к версии 17 ноя 07:33:40. Выйдите из проекта на Move и откройте его снова, чтобы увидеть изменения"}
        self.assertEqual(translate(list(cases)), list(cases.values()))

    def test_names_in_quotes_untouched(self):
        r = translate(['Clip from "Delete" loaded: track 1, scene 2', '"Restore" uploaded to Move'])
        self.assertIn("«Delete»", r[0])
        self.assertIn("«Restore»", r[1])

    def test_whitespace_kept_and_unknown_left(self):
        r = translate(["  Notes saved  ", "Heavy Mellow Kit", "12", ""])
        self.assertEqual(r, ["  Заметки сохранены  ", "Heavy Mellow Kit", "12", ""])

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


KEEP = re.compile(r"Xname|Move|Manager|KRJUK|Schwung|Drum Rack|Finder|SSH|MIDI|WAV|AIFF|FLAC|MP3|M4A|WebM|OGG|Samples/UPLOAD|"
                  r"_Deleted|_edit|bpm|Wi-Fi|Camelot|the author|USB|ablbundle|Song\.abl|python3|Terminal|Ctrl|Recordings|Settings|"
                  r"Pocket Operations|Paul Wenzel|Basic Drum Patterns|config\.json|meta\.json|Esc|Shift|Cmd|Wavetable|Drift|UPLOAD|"
                  r"Samples|Core Library|User Library|Track Presets|IP|"
                  # музыкальные термины остаются английскими и внутри русских фраз (the author, 17.11)
                  r"Pad control|Clips?|Tracks?|Scenes?|Loops?|Pads?|Presets?|Patterns?|Kit|Half time|Swing|Ghosts|Euclid|Mutation|Sample|Pad control|audio|Audio")


@unittest.skipUnless(shutil.which("node"), "нужен Node.js")
class Coverage(unittest.TestCase):
    """Каждое сообщение status/confirm/prompt и подсказка title из index.html переводится целиком."""
    def test_ui_messages_are_russian(self):
        from tests.i18n_samples import ui_samples
        samples = ui_samples()
        got = translate(samples)
        def label(s):                       # короткая подпись или подсказка-название кнопки — остаётся английской
            return len(s.split()) <= 3 and not re.search(r"[.?!:…]$|\d", s)
        left = [f"{a!r} → {b!r}" for a, b in zip(samples, got)
                if not label(a) and not re.search(r"[a-z]3\b", a) and re.search(r"[A-Za-z]{4,}", KEEP.sub("", b))]
        self.assertEqual(left, [], "\n" + "\n".join(left))
