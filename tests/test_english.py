import ast
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CYR = re.compile(r"[А-Яа-яЁё]")


def cyrillic_literals(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docs.add(id(body[0].value))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            if CYR.search(node.value):
                bad.append((node.lineno, node.value[:60]))
    return bad


class EnglishStrings(unittest.TestCase):
    def test_app_strings_are_english(self):
        self.assertEqual(cyrillic_literals(os.path.join(ROOT, "app.py")), [])

    def test_midi_strings_are_english(self):
        self.assertEqual(cyrillic_literals(os.path.join(ROOT, "midi.py")), [])

    def test_ui_has_no_cyrillic_text(self):
        html = open(os.path.join(ROOT, "static", "index.html"), encoding="utf-8").read()
        # comments in CSS/JS are allowed; visible strings are not
        html = re.sub(r"/\*.*?\*/", "", html, flags=re.S)
        html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
        lines = [l for l in html.splitlines() if CYR.search(re.sub(r"(^|\s)//.*$", "", l))]
        self.assertEqual(lines[:5], [])

    def test_page_language_is_english(self):
        html = open(os.path.join(ROOT, "static", "index.html"), encoding="utf-8").read()
        self.assertIn('<html lang="en"', html)


if __name__ == "__main__":
    unittest.main()
