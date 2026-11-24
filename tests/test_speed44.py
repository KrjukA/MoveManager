"""Сборка 44: перенос внутри Move без лишних подключений и без перечитывания всех проектов; папки и имена на компьютере."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import app
from tests.test_samples_device import Device as Base, B4
from tests.test_xfer import Xfer


class Speed(Base):
    def setUp(self):
        super().setUp()
        self._cache = app.CACHE_DIR
        app.CACHE_DIR = self.root / "cache"; app.CACHE_DIR.mkdir()
        app.ssh_session_reset()

    def tearDown(self):
        app.CACHE_DIR = self._cache
        app.ssh_session_reset()
        super().tearDown()

    def test_apply_sends_texts_in_one_archive(self):
        # тексты — одним сжатым архивом по отдельному подключению (так же, как перенос Schwung, проверено на Move)
        plan = app.userlib_plan("samples", [(B4, "Samples/Other/b4.wav")])
        real = app.subprocess.run
        calls = []
        def spy(cmd, *a, **k):
            calls.append(cmd[-1]); return real(cmd, *a, **k)
        with mock.patch.object(app.subprocess, "run", side_effect=spy):
            app.apply_userlib_plan(plan, lambda *a, **k: None)
        self.assertEqual(len(calls), 1)
        self.assertIn("tar -xzf -", calls[0])
        self.assertNotIn("head -c", calls[0])
        self.assertIn("Samples/Other/b4.wav", (self.lib / "Track Presets/Drums/Kit.ablpreset").read_text())
        song = next(self.lib.glob("Sets/*/*/Song.abl")).read_text()
        self.assertTrue(song.endswith("}"))                     # без лишнего перевода строки в конце

    def test_texts_survive_any_content(self):
        song = next(self.lib.glob("Sets/*/*/Song.abl"))
        tricky = song.read_text().replace('{', '{"t": "EOF\\nMMEOF $HOME `x` \'q\' \\\\ é ✓", ', 1)
        song.write_text(tricky)
        app.apply_userlib_plan(app.userlib_plan("samples", [(B4, "Samples/Other/b4.wav")]), lambda *a, **k: None)
        after = song.read_text()
        self.assertEqual(after, tricky.replace("Samples/Bounces/Set%2093%20Bounce%204%20-%20100%20bpm.wav", "Samples/Other/b4.wav"))

    def test_after_apply_projects_are_not_read_again(self):
        app.userlib_index()
        app.apply_userlib_plan(app.userlib_plan("samples", [(B4, "Samples/Other/b4.wav")]), lambda *a, **k: None)
        with mock.patch.object(app, "_read_many", side_effect=AssertionError("re-read all")):
            refs = app.userlib_index()["refs"]
        self.assertEqual(len(refs["Samples/Other/b4.wav"]), 3)
        self.assertNotIn(B4, refs)

    def test_delete_keeps_the_cache(self):
        app.userlib_index()
        app.userlib_delete("samples", ["Samples/Other/unused.wav"])
        with mock.patch.object(app, "_read_many", side_effect=AssertionError("re-read all")):
            app.userlib_index()


class PcFolders(Xfer):
    def test_make_folder(self):
        p = app.fs_mkdir(str(self.pc / "Kits"), "New one")
        self.assertTrue(Path(p).is_dir())
        with self.assertRaises(app.AppError):
            app.fs_mkdir(str(self.pc / "Kits"), "New one")
        with self.assertRaises(app.AppError):
            app.fs_mkdir(str(self.pc / "Kits"), "../x")

    def test_rename(self):
        p = app.fs_rename(str(self.pc / "Kits/snare.wav"), "Snare 01.wav")
        self.assertTrue((self.pc / "Kits/Snare 01.wav").exists() and Path(p).name == "Snare 01.wav")
        with self.assertRaises(app.AppError):
            app.fs_rename(str(self.pc / "Kits/Snare 01.wav"), "Sub")       # занято
        with self.assertRaises(app.AppError):
            app.fs_rename(str(self.pc / "Kits/Snare 01.wav"), "a/b.wav")


class PcTrash(Xfer):
    """Сборка 62: удаление папок и файлов на компьютере — в Корзину, не насовсем."""
    def setUp(self):
        super().setUp()
        self.trash = self.root / "Trash"; self.trash.mkdir()
        self._lib = app.CFG.get("library")
        app.CFG["library"] = str(self.pc / "Projects")
        (self.pc / "Projects").mkdir()
        self._send = mock.patch.object(app, "_send_to_trash", side_effect=self.fake_trash)
        self._send.start()

    def tearDown(self):
        self._send.stop()
        app.CFG["library"] = self._lib
        super().tearDown()

    def fake_trash(self, p):
        p.rename(self.trash / p.name)

    def test_folder_goes_to_trash(self):
        app.fs_trash(str(self.pc / "Kits/Sub"))
        self.assertFalse((self.pc / "Kits/Sub").exists())
        self.assertTrue((self.trash / "Sub/hat.aif").exists())

    def test_file_goes_to_trash(self):
        app.fs_trash(str(self.pc / "Kits/snare.wav"))
        self.assertTrue((self.trash / "snare.wav").exists())

    def test_refuses_roots_and_library(self):
        for p in (self.pc, self.pc / "Projects", self.pc / "nothing"):
            with self.assertRaises(app.AppError):
                app.fs_trash(str(p))
        app.CFG["library"] = str(self.pc / "Kits/Sub/Deep")
        with self.assertRaises(app.AppError):           # папка, внутри которой лежат проекты
            app.fs_trash(str(self.pc / "Kits"))
        with self.assertRaises(app.AppError):
            app.fs_trash(str(self.root / "app"))          # вне разрешённых корней
        self.assertTrue((self.pc / "Kits").exists())

    def test_linux_trash_keeps_both_on_same_name(self):
        self._send.stop()
        with mock.patch.object(app, "TRASH_DIR", self.trash), mock.patch.object(app.sys, "platform", "linux"):
            (self.trash / "snare.wav").write_bytes(b"old")
            app.fs_trash(str(self.pc / "Kits/snare.wav"))
        self._send.start()
        self.assertEqual((self.trash / "snare.wav").read_bytes(), b"old")
        self.assertEqual(len(list(self.trash.glob("snare*.wav"))), 2)

    @unittest.skipUnless(sys.platform == "darwin" and os.environ.get("MM_REAL_TRASH"), "Mac only; puts an empty folder into the real Trash")
    def test_mac_system_trash(self):
        # настоящая Корзина Mac: тот же вызов, что у Finder; ~/.Trash напрямую закрыт системой
        self._send.stop()
        d = Path.home() / "Music" / f".mm-trash-test-{os.getpid()}"
        try:
            d.mkdir(parents=True)
            app._mac_trash(d)
            self.assertFalse(d.exists())
            with self.assertRaises(app.AppError):
                app._mac_trash(d)                          # уже нет — понятная ошибка, не падение
        finally:
            if d.exists():
                d.rmdir()
            self._send.start()
