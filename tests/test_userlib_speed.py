"""Скорость библиотеки: тексты источников переживают перезапуск, SSH держит одно соединение."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app
from tests.test_samples_device import Device as Base, B4


class Speed(Base):
    def setUp(self):
        super().setUp()
        self._cache = app.CACHE_DIR
        app.CACHE_DIR = self.root / "cache"; app.CACHE_DIR.mkdir()

    def tearDown(self):
        app.CACHE_DIR = self._cache
        super().tearDown()

    def test_source_texts_survive_restart(self):
        self.assertTrue(app.userlib_index()["refs"][B4])
        app.USERLIB_CACHE.clear()                       # как после перезапуска программы
        with mock.patch.object(app, "_read_many", side_effect=AssertionError("re-read")):
            self.assertTrue(app.userlib_index()["refs"][B4])

    def test_changed_source_is_read_again(self):
        app.userlib_index()
        app.USERLIB_CACHE.clear()
        song = next(self.lib.glob("Sets/*/*/Song.abl"))
        song.write_text(json.dumps({"x": "ableton:/user-library/Samples/Other/unused.wav", "pad": "longer text"}))
        os.utime(song, (1, 1))
        self.assertTrue(app.userlib_index()["refs"].get("Samples/Other/unused.wav"))


class SshNoMux(unittest.TestCase):
    def test_ssh_does_not_use_shared_connection(self):
        # macOS: общее соединение (ControlMaster) падает с «mm_send_fd: Message too long», когда данные идут через stdin
        saved = os.environ.pop("MOVE_SSH_CMD", None)
        try:
            with mock.patch.object(app.subprocess, "run") as run, \
                    mock.patch.dict(os.environ, {"MOVE_MANAGER_TESTING": ""}):   # запуск подменён — сети нет
                run.return_value = mock.Mock(returncode=0, stdout=b"", stderr=b"")
                app.ssh_run("true", data=b"x")
            self.assertNotIn("ControlMaster", " ".join(run.call_args[0][0]))
        finally:
            if saved is not None:
                os.environ["MOVE_SSH_CMD"] = saved


if __name__ == "__main__":
    unittest.main()
