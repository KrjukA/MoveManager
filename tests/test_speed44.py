"""Сборка 44: перенос внутри Move без лишних подключений и без перечитывания всех проектов; папки и имена на компьютере."""
import os
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
