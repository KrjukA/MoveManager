"""Сборка 55: проекты с кириллицей в имени правятся на Move (BusyBox ls печатает «?» вместо не-ASCII)."""
import json
import os
import shlex
import tempfile
import unittest
from pathlib import Path

import app

OID = "12345678-2222-3333-4444-555555555555"


class CyrillicSets(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.sets = self.root / "Sets"
        (self.sets / OID / "Песня").mkdir(parents=True)
        (self.sets / OID / "Песня" / "Song.abl").write_text(json.dumps({"tempo": 100}))
        bindir = self.root / "bin"
        bindir.mkdir()
        fake = bindir / "ls"                                   # как BusyBox без UTF-8-локали
        fake.write_text("#!/bin/sh\n/bin/ls \"$@\" | LC_ALL=C sed 's/[\\x80-\\xff]/?/g'\n")
        fake.chmod(0o755)
        self._env = os.environ.get("MOVE_SSH_CMD")
        os.environ["MOVE_SSH_CMD"] = f"env PATH={shlex.quote(str(bindir) + ':' + os.environ['PATH'])} sh -c"
        self._sets = app.SETS_DIR
        app.SETS_DIR = str(self.sets)
        app.ssh_session_reset()

    def tearDown(self):
        app.SETS_DIR = self._sets
        if self._env is None:
            os.environ.pop("MOVE_SSH_CMD", None)
        else:
            os.environ["MOVE_SSH_CMD"] = self._env
        app.ssh_session_reset()

    def test_write_song_in_cyrillic_folder(self):
        app.ssh_write_song(OID, json.dumps({"tempo": 128}).encode())
        self.assertEqual(json.loads((self.sets / OID / "Песня" / "Song.abl").read_text())["tempo"], 128)
        self.assertEqual(sorted(p.name for p in (self.sets / OID).iterdir()), ["Песня"])
        self.assertEqual(app.ssh_read_song(OID)["tempo"], 128)

    def test_missing_set_fails_without_writing(self):
        with self.assertRaises(app.SshError):
            app.ssh_write_song("99999999-2222-3333-4444-555555555555", b"{}")
