"""Сборка 56: окно запуска на языке системы."""
import unittest

import launcher


class LauncherLang(unittest.TestCase):
    def test_detect(self):
        self.assertEqual(launcher.system_lang(env={"LANG": "ru_RU.UTF-8"}, platform="linux"), "ru")
        self.assertEqual(launcher.system_lang(env={"LANG": "en_US.UTF-8"}, platform="linux"), "en")
        self.assertEqual(launcher.system_lang(env={}, platform="darwin", mac_langs=lambda: ["ru-RU", "en-US"]), "ru")
        self.assertEqual(launcher.system_lang(env={}, platform="darwin", mac_langs=lambda: ["en-US"]), "en")
        self.assertEqual(launcher.system_lang(env={}, platform="win32", win_lang=lambda: 0x0419), "ru")
        self.assertEqual(launcher.system_lang(env={}, platform="win32", win_lang=lambda: 0x0409), "en")

    def test_texts(self):
        for lang in ("en", "ru"):
            tx = launcher.TEXTS[lang]
            for k in ("running", "keep", "open", "quit"):
                self.assertTrue(tx[k])
        self.assertIn("работает", launcher.TEXTS["ru"]["running"])
