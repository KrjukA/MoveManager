"""Загрузка проекта на Move: сэмплы ищутся в библиотеке Move по содержимому (сборка 58).

Move при загрузке бандла смотрит в BundleInfo.json → originalSampleUris: если файл по этому пути есть — ссылается
на него, если нет — оставляет копию из бандла внутри сета. Программа перед загрузкой поправляет эти пути:
перенесённый сэмпл находится по содержимому, сэмпл с тем же именем, но другим звуком не подставляется."""
import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

import app

OID = "11111111-2222-3333-4444-555555555555"
NEW = "66666666-7777-8888-9999-000000000000"
md5 = lambda b: hashlib.md5(b).hexdigest()
URI = "ableton:/user-library/"


class PlanLinks(unittest.TestCase):
    def test_same_place_same_sound_kept(self):
        info, n = app.plan_sample_links({"Samples/a.wav": "h1"}, {"Samples/a.wav": URI + "Samples/Kit/a.wav"},
                                        {"Samples/Kit/a.wav": "h1"})
        self.assertEqual(info, {"Samples/a.wav": URI + "Samples/Kit/a.wav"})
        self.assertEqual(n, {"linked": 0, "kept": 0, "found": 1})

    def test_moved_sample_found_by_content(self):
        info, n = app.plan_sample_links({"Samples/a.wav": "h1"}, {"Samples/a.wav": URI + "Samples/Kit/a.wav"},
                                        {"Samples/New%20Place/a renamed.wav": "x", "Samples/Other/b.wav": "h1"})
        self.assertEqual(info, {"Samples/a.wav": URI + "Samples/Other/b.wav"})
        self.assertEqual(n["linked"], 1)

    def test_same_name_other_sound_not_linked(self):
        # по старому пути лежит другой файл с тем же именем — ссылку убираем, Move оставит копию из проекта
        info, n = app.plan_sample_links({"Samples/a.wav": "h1"}, {"Samples/a.wav": URI + "Samples/Kit/a.wav"},
                                        {"Samples/Kit/a.wav": "other"})
        self.assertEqual(info, {})
        self.assertEqual(n, {"linked": 0, "kept": 1, "found": 0})

    def test_new_sample_found_in_library(self):
        info, n = app.plan_sample_links({"Samples/a%20b.wav": "h1"}, {}, {"Samples/Loops/a b.wav": "h1"})
        self.assertEqual(info, {"Samples/a%20b.wav": URI + "Samples/Loops/a%20b.wav"})
        self.assertEqual(n["linked"], 1)

    def test_prefers_same_file_name(self):
        info, _ = app.plan_sample_links({"Samples/kick.wav": "h1"}, {},
                                        {"Samples/A/copy.wav": "h1", "Samples/B/kick.wav": "h1"})
        self.assertEqual(info["Samples/kick.wav"], URI + "Samples/B/kick.wav")


class PushRelinks(unittest.TestCase):
    """job_push с подменённым SSH (sh -c) и библиотекой Move во временной папке."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.userlib, self.libdir = self.root / "userlib", self.root / "lib"
        (self.userlib / "Samples" / "Moved").mkdir(parents=True)
        (self.userlib / "Samples" / "Kit").mkdir(parents=True)
        (self.userlib / "Sets" / OID).mkdir(parents=True)
        self.kick, self.snare = b"RIFF-kick-sound" * 50, b"RIFF-snare-sound" * 50
        (self.userlib / "Samples" / "Moved" / "kick.wav").write_bytes(self.kick)              # перенесён на Move
        (self.userlib / "Samples" / "Kit" / "snare.wav").write_bytes(b"another snare" * 61)   # то же имя, другой звук
        (self.userlib / "Sets" / OID / "kick.wav").write_bytes(self.kick)                    # копии внутри сетов не в счёт
        d = self.libdir / "Beat"
        d.mkdir(parents=True)
        song = {"tracks": [{"devices": [{"kind": "drumRack", "chains": [
            {"devices": [{"kind": "drumCell", "sampleUri": "Samples/kick.wav"}]},
            {"devices": [{"kind": "drumCell", "sampleUri": "Samples/snare.wav"}]}]}]}], "scenes": []}
        with zipfile.ZipFile(d / "Beat.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(song))
            z.writestr("Samples/kick.wav", self.kick)
            z.writestr("Samples/snare.wav", self.snare)
            z.writestr("BundleInfo.json", json.dumps({"originalSampleUris": {
                "Samples/kick.wav": URI + "Samples/Kit/kick.wav", "Samples/snare.wav": URI + "Samples/Kit/snare.wav"}}))
        self.saved = {k: getattr(app, k) for k in ("USERLIB_DIR", "DATA_DIR", "CACHE_DIR", "ssh_enabled", "update_meta")}
        self.saved_env = os.environ.get("MOVE_SSH_CMD")
        self.saved_lib = app.CFG.get("library")
        mv = app.MOVE
        self.saved_mv = (mv.upload, mv.list_sets)
        app.USERLIB_DIR, app.DATA_DIR, app.CACHE_DIR = str(self.userlib), self.root / "app", self.root / "app" / "cache"
        app.CACHE_DIR.mkdir(parents=True)
        app.CFG["library"] = str(self.libdir)
        app.ssh_enabled = lambda: True
        app.update_meta = lambda *a, **k: None
        os.environ["MOVE_SSH_CMD"] = "sh -c"
        self.sets, self.uploaded = [], []

        def upload(path, name):
            with zipfile.ZipFile(path) as z:
                self.uploaded.append({n: z.read(n) for n in z.namelist()})
            self.sets.append({"objectId": NEW, "name": "Beat"})
        mv.upload, mv.list_sets = upload, lambda: list(self.sets)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(app, k, v)
        app.MOVE.upload, app.MOVE.list_sets = self.saved_mv
        app.CFG["library"] = self.saved_lib
        if self.saved_env is None:
            os.environ.pop("MOVE_SSH_CMD", None)
        else:
            os.environ["MOVE_SSH_CMD"] = self.saved_env

    def push(self):
        return app.job_push("Beat")(lambda *a, **k: None)

    def test_push_points_to_moved_sample_and_drops_wrong_one(self):
        res = self.push()
        info = json.loads(self.uploaded[0]["BundleInfo.json"])["originalSampleUris"]
        self.assertEqual(info, {"Samples/kick.wav": URI + "Samples/Moved/kick.wav"})
        self.assertEqual(res["samples"], {"linked": 1, "kept": 1, "found": 0})
        self.assertEqual(self.uploaded[0]["Samples/kick.wav"], self.kick)        # сэмплы едут в бандле как были

    def test_bundle_on_computer_unchanged(self):
        before = (self.libdir / "Beat" / "Beat.ablbundle").read_bytes()
        self.push()
        self.assertEqual((self.libdir / "Beat" / "Beat.ablbundle").read_bytes(), before)

    def test_checksums_cached(self):
        self.push()
        cache = json.loads((app.CACHE_DIR / "sample-md5.json").read_text())
        self.assertEqual(cache["Samples/Moved/kick.wav"][2], md5(self.kick))

    def test_without_ssh_bundle_goes_as_is(self):
        app.ssh_enabled = lambda: False
        res = self.push()
        self.assertEqual(json.loads(self.uploaded[0]["BundleInfo.json"])["originalSampleUris"]["Samples/kick.wav"],
                         URI + "Samples/Kit/kick.wav")
        self.assertIsNone(res["samples"])


if __name__ == "__main__":
    unittest.main()
