"""Двухпанельный перенос: папки компьютера, копирование компьютер ↔ Move."""
import os
import unittest
from pathlib import Path

import app
from tests.test_samples_device import Device as Base, B4


class Xfer(Base):
    def setUp(self):
        super().setUp()
        self.pc = self.root / "pc"
        (self.pc / "Kits/Sub").mkdir(parents=True)
        (self.pc / "Kits/snare.wav").write_bytes(b"RIFFsn")
        (self.pc / "Kits/Sub/hat.aif").write_bytes(b"FORMhat")
        (self.pc / "Kits/notes.txt").write_text("x")
        (self.pc / "Kits/.DS_Store").write_bytes(b"x")
        (self.pc / "lead.ablpreset").write_text("{}")
        self._roots = app.FS_ROOTS
        app.FS_ROOTS = [str(self.pc)]

    def tearDown(self):
        app.FS_ROOTS = self._roots
        super().tearDown()

    def test_list_shows_folders_and_section_files(self):
        d = app.fs_list(str(self.pc / "Kits"), "samples")
        self.assertEqual(d["folders"], ["Sub"])
        self.assertEqual([f["name"] for f in d["files"]], ["snare.wav"])
        self.assertEqual(d["parent"], str(self.pc))
        self.assertEqual([f["name"] for f in app.fs_list(str(self.pc), "presets")["files"]], ["lead.ablpreset"])

    def test_list_refuses_outside_allowed_roots(self):
        with self.assertRaises(app.AppError):
            app.fs_list(str(self.root), "samples")
        with self.assertRaises(app.AppError):
            app.fs_list(str(self.pc / ".." / "app"), "samples")
        self.assertIsNone(app.fs_list(str(self.pc), "samples")["parent"])

    def test_copy_file_and_folder_to_move(self):
        res = app.copy_to_move("samples", [str(self.pc / "Kits/snare.wav"), str(self.pc / "Kits")], "Samples/Other", self.stage)
        self.assertEqual((self.lib / "Samples/Other/snare.wav").read_bytes(), b"RIFFsn")
        self.assertEqual((self.lib / "Samples/Other/Kits/Sub/hat.aif").read_bytes(), b"FORMhat")
        self.assertFalse((self.lib / "Samples/Other/Kits/notes.txt").exists())
        self.assertFalse((self.lib / "Samples/Other/Kits/.DS_Store").exists())
        self.assertEqual(res["copied"], 3)
        self.assertTrue((self.pc / "Kits/snare.wav").exists())          # копирование, не перенос

    def test_copy_to_move_never_overwrites(self):
        (self.lib / "Samples/Other/snare.wav").write_bytes(b"OLD")
        app.copy_to_move("samples", [str(self.pc / "Kits/snare.wav")], "Samples/Other", self.stage)
        self.assertEqual((self.lib / "Samples/Other/snare.wav").read_bytes(), b"OLD")
        self.assertEqual((self.lib / "Samples/Other/snare 2.wav").read_bytes(), b"RIFFsn")
        app.copy_to_move("samples", [str(self.pc / "Kits")], "Samples", self.stage)
        app.copy_to_move("samples", [str(self.pc / "Kits")], "Samples", self.stage)
        self.assertTrue((self.lib / "Samples/Kits 2/snare.wav").exists())

    def test_copy_file_and_folder_to_computer(self):
        dest = self.pc / "From Move"; dest.mkdir()
        res = app.copy_to_pc("samples", [B4, "Samples/Bounces"], str(dest), self.stage)
        self.assertEqual((dest / "Set 93 Bounce 4 - 100 bpm.wav").read_bytes(), b"RIFFb4")
        self.assertEqual((dest / "Bounces/sub/deep.wav").read_bytes(), b"RIFFdeep")
        self.assertTrue((self.lib / B4).exists())
        self.assertEqual(res["copied"], 3)
        app.copy_to_pc("samples", [B4], str(dest), self.stage)
        self.assertTrue((dest / "Set 93 Bounce 4 - 100 bpm 2.wav").exists())

    def test_copy_to_computer_refuses_outside_roots(self):
        with self.assertRaises(app.AppError):
            app.copy_to_pc("samples", [B4], str(self.root), self.stage)

    def test_move_inside_computer(self):
        app.fs_move(str(self.pc / "Kits/snare.wav"), str(self.pc / "Kits/Sub"))
        self.assertTrue((self.pc / "Kits/Sub/snare.wav").exists())
        (self.pc / "Kits/Sub/hat2.aif").write_bytes(b"x")
        with self.assertRaises(app.AppError):            # в саму себя нельзя
            app.fs_move(str(self.pc / "Kits"), str(self.pc / "Kits/Sub"))
        (self.pc / "x.wav").write_bytes(b"1"); (self.pc / "Kits/x.wav").write_bytes(b"2")
        with self.assertRaises(app.AppError):            # не затирает
            app.fs_move(str(self.pc / "x.wav"), str(self.pc / "Kits"))


if __name__ == "__main__":
    unittest.main()


import json  # noqa: E402
import urllib.parse  # noqa: E402
from tests.test_routes_midi import RouteBase  # noqa: E402


class XferRoutes(RouteBase):
    def setUp(self):
        super().setUp()
        self.dev = Xfer("test_list_shows_folders_and_section_files")
        self.dev.setUp()
        self.pc = self.dev.pc

    def tearDown(self):
        self.dev.tearDown()
        super().tearDown()

    def js(self, method, path, obj=None):
        st, _, b = self.req(method, path, json.dumps(obj).encode() if obj is not None else None)
        return st, (json.loads(b) if b and b[:1] in (b"{", b"[") else b)

    def test_list_file_and_move(self):
        st, d = self.js("GET", "/api/fs?mode=samples&path=" + urllib.parse.quote(str(self.pc / "Kits")))
        self.assertEqual((st, d["folders"]), (200, ["Sub"]))
        st, data = self.js("GET", "/api/fs/file?path=" + urllib.parse.quote(str(self.pc / "Kits/snare.wav")))
        self.assertEqual((st, data), (200, b"RIFFsn"))
        st, _ = self.js("POST", "/api/fs/move", {"src": str(self.pc / "Kits/snare.wav"), "dst": str(self.pc)})
        self.assertEqual(st, 200)
        self.assertTrue((self.pc / "snare.wav").exists())
        st, _ = self.js("GET", "/api/fs/file?path=" + urllib.parse.quote(str(self.dev.root / "app")))
        self.assertEqual(st, 400)

    def test_default_folder_is_remembered(self):
        app.CFG["samplesFolder"] = str(self.pc / "Kits")
        st, d = self.js("GET", "/api/fs?mode=samples")
        self.assertEqual(d["path"], str((self.pc / "Kits").resolve()))
        st, d = self.js("GET", "/api/fs?mode=samples&path=" + urllib.parse.quote(str(self.pc)))
        self.assertEqual(app.CFG["samplesFolder"], str(self.pc.resolve()))   # последняя открытая папка запоминается

    def test_copy_jobs_both_ways(self):
        st, job = self.js("POST", "/api/xfer/to-move", {"mode": "samples", "paths": [str(self.pc / "Kits")], "dir": "Samples"})
        job = self.wait_job(json.dumps(job).encode())
        self.assertEqual(job["status"], "done", job)
        self.assertTrue((self.dev.lib / "Samples/Kits/snare.wav").exists())
        st, job = self.js("POST", "/api/xfer/to-pc", {"mode": "samples", "rels": ["Samples/Kits"], "dir": str(self.pc)})
        job = self.wait_job(json.dumps(job).encode())
        self.assertEqual(job["status"], "done", job)
        self.assertTrue((self.pc / "Kits 2/snare.wav").exists())
