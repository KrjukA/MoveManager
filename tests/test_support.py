"""Сборка 61: кнопка Support в шапке открывает страницу Ko-fi разработчика; адрес почты в коде не светится."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Support(unittest.TestCase):
    def test_button_and_link(self):
        html = (ROOT / "static" / "index.html").read_text("utf-8")
        self.assertRegex(html, r'<button id="supportBtn" class="hb" title="[^"]+">Support</button>')
        self.assertIn('SUPPORT_URL = "https://ko-fi.com/krjuk"', html)
        self.assertIn('window.open(SUPPORT_URL, "_blank", "noopener")', html)

    def test_no_email_addresses_in_published_files(self):
        for f in ["README.md", "static/index.html", "static/i18n.js", "app.py", ".github/FUNDING.yml"]:
            text = (ROOT / f).read_text("utf-8")
            found = [m for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text) if not m.endswith("users.noreply.github.com")]
            self.assertEqual(found, [], f)

    def test_github_sponsor_button(self):
        self.assertIn("ko_fi: krjuk", (ROOT / ".github" / "FUNDING.yml").read_text("utf-8"))


class ConfigLine(unittest.TestCase):
    """Сборка 62: строка в loadConfig, ушедшая в комментарий (сборка 60), — номер сборки и формат звука снова ставятся."""
    def test_build_label_and_audio_format_not_commented_out(self):
        html = (ROOT / "static" / "index.html").read_text("utf-8")
        line = next(l for l in html.splitlines() if 'S.audioFormat = c.audioFormat' in l)   # сборка 64: подпись — версия или сборка
        self.assertTrue(line.strip().startswith("S.audioFormat = c.audioFormat"))
        self.assertNotIn("//", line.split('$("#build")')[0])
        label = next(l for l in html.splitlines() if 'b.textContent = c.frozen' in l)
        self.assertFalse(label.strip().startswith("//"))
