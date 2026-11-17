"""Сборка 55: Windows и кириллица в имени пользователя — ssh получает «короткий» латинский путь."""
import unittest
from pathlib import PureWindowsPath

import app


class WinPaths(unittest.TestCase):
    def test_ascii_path_unchanged(self):
        p = r"C:\Users\the author\AppData\Roaming\KRJUK Move Manager\move_ssh_key"
        self.assertEqual(app.ssh_safe_path(p, platform="win32", short=lambda s: "X"), p)

    def test_cyrillic_uses_short_parent(self):
        p = r"C:\Users\Иван\AppData\Roaming\KRJUK Move Manager\move_ssh_key"
        calls = []
        def short(s):
            calls.append(s)
            return r"C:\Users\D0B0~1\AppData\Roaming\KRJUKM~1"
        got = app.ssh_safe_path(p, platform="win32", short=short)
        self.assertEqual(PureWindowsPath(got), PureWindowsPath(r"C:\Users\D0B0~1\AppData\Roaming\KRJUKM~1\move_ssh_key"))
        self.assertEqual(calls, [r"C:\Users\Иван\AppData\Roaming\KRJUK Move Manager"])

    def test_no_short_names_keeps_original(self):
        p = r"C:\Users\Иван\AppData\Roaming\KRJUK Move Manager\known_hosts"
        self.assertEqual(app.ssh_safe_path(p, platform="win32", short=lambda s: s), p)     # 8.3 выключены
        self.assertEqual(app.ssh_safe_path(p, platform="win32", short=lambda s: ""), p)

    def test_mac_unchanged(self):
        p = "/Users/Иван/Library/Application Support/KRJUK Move Manager/move_ssh_key"
        self.assertEqual(app.ssh_safe_path(p, platform="darwin", short=lambda s: "X"), p)
