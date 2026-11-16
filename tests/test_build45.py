"""Сборка 45: удаление папок и пресетов, журнал ошибок, Schwung без пустых и служебных файлов."""
import json
import time
from pathlib import Path

import app
from tests.test_samples_device import Device as Base, B4, OID


class Build45(Base):
    def setUp(self):
        super().setUp()
        self._cache = app.CACHE_DIR
        app.CACHE_DIR = self.root / "cache"; app.CACHE_DIR.mkdir()

    def tearDown(self):
        app.CACHE_DIR = self._cache
        super().tearDown()

    def test_schwung_listing_only_used_slots(self):
        w = self.sw / "set_state" / OID
        (w / "slot_1.json").write_text("{}")
        (w / "master_fx_0.json").write_text(json.dumps({"x": "y" * 600}))
        keys = set(app._source_listing())
        self.assertIn(str(w / "slot_0.json"), keys)
        self.assertNotIn(str(w / "slot_1.json"), keys)
        self.assertNotIn(str(w / "master_fx_0.json"), keys)
        self.assertEqual(len(app.userlib_index()["refs"][B4]), 3)

    def test_delete_folder_with_only_unused_files(self):
        (self.lib / "Samples/Other/deeper").mkdir()
        (self.lib / "Samples/Other/deeper/x.wav").write_bytes(b"x")
        app.userlib_delete("samples", ["Samples/Other"])
        self.assertFalse((self.lib / "Samples/Other").exists())

    def test_folder_with_used_file_is_not_deleted(self):
        with self.assertRaises(app.AppError):
            app.userlib_delete("samples", ["Samples/Bounces"])
        self.assertTrue((self.lib / B4).exists())

    def test_section_root_is_never_deleted(self):
        with self.assertRaises(app.AppError):
            app.userlib_delete("samples", ["Samples"])
        self.assertTrue((self.lib / "Samples").is_dir())

    def test_delete_preset(self):
        app.userlib_delete("presets", ["Track Presets/Drums/Kit.ablpreset"])
        self.assertFalse((self.lib / "Track Presets/Drums/Kit.ablpreset").exists())

    def test_job_errors_are_logged(self):
        def boom(stage):
            raise app.AppError("SSH: head: invalid option -- c")
        job = app.start_job("move", boom)
        for _ in range(50):
            if job["status"] != "running":
                break
            time.sleep(0.02)
        log = (app.CACHE_DIR / "errors.log").read_text()
        self.assertIn("head: invalid option", log)
        self.assertIn("move", log)
