"""Исправления после финальной проверки библиотеки сэмплов."""
import json
import os
import stat
import tempfile
import time
import unittest
from pathlib import Path

import app
from tests.test_samples_device import Device as Base, OID, B4


class Fixes(Base):
    def test_busybox_ls_mangling_does_not_hide_users(self):
        # BusyBox ls без UTF-8-локали печатает «?» вместо не-ASCII; имена должны браться не из ls
        bindir = self.root / "bin"; bindir.mkdir()
        fake = bindir / "ls"
        fake.write_text("#!/bin/sh\n/bin/ls \"$@\" | LC_ALL=C sed 's/[\\x80-\\xff]/?/g'\n")
        fake.chmod(0o755)
        os.environ["MOVE_SSH_CMD"] = f"env PATH={bindir}:/usr/bin:/bin sh -c"
        (self.lib / "Samples/Кик.wav").write_bytes(b"RIFFk")
        s = self.lib / "Sets" / "22222222-2222-3333-4444-555555555555" / "Медленный"; s.mkdir(parents=True)
        (s / "Song.abl").write_text(json.dumps({"a": "ableton:/user-library/Samples/Other/unused.wav",
                                                "b": "ableton:/user-library/Samples/%D0%9A%D0%B8%D0%BA.wav"}))
        tree = {f["rel"] for f in app.lib_tree("samples")["files"]}
        self.assertIn("Samples/Кик.wav", tree)
        refs = app.userlib_index()["refs"]
        self.assertTrue(refs.get("Samples/Other/unused.wav"))
        self.assertTrue(refs.get("Samples/Кик.wav"))
        with self.assertRaises(app.AppError):
            app.userlib_delete("samples", ["Samples/Other/unused.wav"])
        self.assertTrue((self.lib / "Samples/Other/unused.wav").exists())

    def test_listing_without_stat_refuses(self):
        bindir = self.root / "bin"; bindir.mkdir()
        os.environ["MOVE_SSH_CMD"] = f"env PATH={bindir} /bin/sh -c"
        with self.assertRaises(app.AppError):
            app.userlib_index()

    def test_moved_preset_referencing_itself_is_moved_not_copied(self):
        d = self.lib / "Track Presets/Bass"; d.mkdir(parents=True)
        (d / "P.ablpreset").write_text(json.dumps({"presetUri": "ableton:/user-library/Track%20Presets/Bass/P.ablpreset"}))
        app.apply_userlib_plan(app.userlib_plan("presets", [("Track Presets/Bass", "Track Presets/Lead")]), self.stage)
        self.assertFalse((d / "P.ablpreset").exists())
        moved = (self.lib / "Track Presets/Lead/P.ablpreset").read_text()
        self.assertIn("Track%20Presets/Lead/P.ablpreset", moved)
        self.assertNotIn("/Bass/", moved)

    def test_backup_folders_are_unique(self):
        r1 = app.apply_userlib_plan(app.userlib_plan("samples", [(B4, "Samples/Bounces/A.wav")]), self.stage)
        r2 = app.apply_userlib_plan(app.userlib_plan("samples", [("Samples/Bounces/A.wav", "Samples/Bounces/B.wav")]), self.stage)
        self.assertNotEqual(r1["backup"], r2["backup"])
        m1 = json.loads((self.root / "app/backups" / r1["backup"] / "manifest.json").read_text())
        self.assertEqual(m1["moves"][0][0], B4)

    def test_upload_failure_is_reported(self):
        (self.lib / "Samples/blocker").write_bytes(b"x")
        with self.assertRaises((app.AppError, app.SshError)):
            app.userlib_upload("samples", "Samples/blocker", "a.wav", b"RIFF")

    def test_folder_move_leaves_no_empty_folders(self):
        app.apply_userlib_plan(app.userlib_plan("samples", [("Samples/Bounces", "Samples/Resamples")]), self.stage)
        self.assertFalse((self.lib / "Samples/Bounces").exists())
        self.assertTrue((self.lib / "Samples/Resamples/sub/deep.wav").exists())

    def test_empty_folder_can_be_renamed(self):
        (self.lib / "Samples/Empty/inner").mkdir(parents=True)
        app.apply_userlib_plan(app.userlib_plan("samples", [("Samples/Empty", "Samples/Full")]), self.stage)
        self.assertTrue((self.lib / "Samples/Full/inner").is_dir())
        self.assertFalse((self.lib / "Samples/Empty").exists())

    def test_folder_onto_existing_folder_is_a_conflict(self):
        plan = app.userlib_plan("samples", [("Samples/Bounces", "Samples/Other")])
        self.assertTrue(plan["conflicts"])


if __name__ == "__main__":
    unittest.main()
