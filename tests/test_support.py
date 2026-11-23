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
