import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

import app

OLD = "11111111-2222-3333-4444-555555555555"
NEW = "66666666-7777-8888-9999-000000000000"


def tar_names(data):
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
        return sorted(m.name.lstrip("./") for m in t.getmembers() if m.isfile())


class Schwung(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self._saved = (app.SCHWUNG_DIR, os.environ.get("MOVE_SSH_CMD"))
        app.SCHWUNG_DIR = str(self.root)
        os.environ["MOVE_SSH_CMD"] = "sh -c"
        d = self.root / OLD
        (d / "snapshot").mkdir(parents=True)
        (d / "slot_0.json").write_text('{"module": "obxd", "module_path": "/data/x/obxd"}')
        (d / "lanes_0.json").write_text("{}")
        (d / "copy_source.txt").write_text("x")
        (d / "snapshot" / "slot_0.json").write_text("{}")

    def tearDown(self):
        app.SCHWUNG_DIR = self._saved[0]
        if self._saved[1] is None:
            os.environ.pop("MOVE_SSH_CMD", None)
        else:
            os.environ["MOVE_SSH_CMD"] = self._saved[1]

    def test_fetch_filters_service_files(self):
        data = app.schwung_fetch(OLD)
        self.assertEqual(tar_names(data), ["lanes_0.json", "slot_0.json"])

    def test_fetch_none_when_absent_or_empty(self):
        self.assertIsNone(app.schwung_fetch(NEW))
        (self.root / NEW).mkdir()
        self.assertIsNone(app.schwung_fetch(NEW))

    def test_restore_into_new_set(self):
        self.assertEqual(app.schwung_restore(NEW, app.schwung_fetch(OLD)), "copied")
        self.assertEqual(json.loads((self.root / NEW / "slot_0.json").read_text()), {"module": "obxd", "module_path": "/data/x/obxd"})

    def test_restore_never_overwrites(self):
        (self.root / NEW).mkdir()
        (self.root / NEW / "slot_0.json").write_text('{"synth": {"module": "mine"}}')
        self.assertEqual(app.schwung_restore(NEW, app.schwung_fetch(OLD)), "exists")
        self.assertEqual(json.loads((self.root / NEW / "slot_0.json").read_text()), {"synth": {"module": "mine"}})

    def test_restore_over_seeded_empty_state(self):
        d = self.root / NEW
        d.mkdir()
        for i in range(4):
            (d / f"slot_{i}.json").write_text("{}\n")
        (d / "shadow_chain_config.json").write_text('{"slots": []}')
        self.assertEqual(app.schwung_restore(NEW, app.schwung_fetch(OLD)), "copied")
        self.assertEqual(json.loads((d / "slot_0.json").read_text()), {"module": "obxd", "module_path": "/data/x/obxd"})

    def test_sets_using_schwung_modules(self):
        # так выглядит настоящий Move: в каждом сете заготовки «{}» по 3 байта, master_fx_0 на 543 байта
        # и имена «Untitled» в цепочке — это НЕ использование Schwung; использование — слот больше 10 байт
        def seeded(u):
            d = self.root / u
            d.mkdir(exist_ok=True)
            for i in range(4):
                (d / f"slot_{i}.json").write_text("{}\n")
            for i in range(8):
                (d / f"master_fx_{i}.json").write_text("{}\n")
            (d / "master_fx_0.json").write_text("x" * 543)
            (d / "shadow_chain_config.json").write_text('{"slots": [' + ",".join(['{"name": "Untitled", "channel": 1}'] * 4) + ']}')
            return d
        seeded(NEW)
        seeded(OLD)
        (self.root / OLD / "slot_0.json").write_text("y" * 1297)
        self.assertEqual(app.schwung_sets(), {OLD})

    def test_unsafe_archive_rejected(self):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as t:
            info = tarfile.TarInfo("../escape.txt"); info.size = 1
            t.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(app.AppError):
            app.schwung_restore(NEW, buf.getvalue())
        self.assertFalse((self.root / "escape.txt").exists())

    def test_bad_id_rejected(self):
        with self.assertRaises(app.AppError):
            app.schwung_fetch("../../etc")

    def test_song_uses_schwung(self):
        song = {"tracks": [{"devices": [{"kind": "instrumentRack", "name": "ME Slot 4",
                                         "presetUri": "ableton:/user-library/Track%20Presets/Schwung/ME%20Slot%204.json"}]}]}
        self.assertTrue(app.parse_song(song)["schwung"])
        self.assertFalse(app.parse_song({"tracks": [{"devices": []}]})["schwung"])


if __name__ == "__main__":
    unittest.main()


class SchwungJobs(Schwung):
    def setUp(self):
        super().setUp()
        import zipfile
        self.lib = Path(tempfile.mkdtemp())
        self._s2 = {k: getattr(app, k) for k in ("ssh_enabled", "set_by_id", "save_config", "cache_info")}
        self._lib = app.CFG.get("library")
        app.CFG["library"] = str(self.lib)
        app.save_config = lambda: None
        app.cache_info = lambda *a, **k: None
        app.ssh_enabled = lambda: True
        app.set_by_id = lambda oid: {"objectId": oid, "name": "Acid Set", "lastModifiedDateTime": "x"}
        self.sets = [{"objectId": OLD, "name": "Acid Set"}]
        mv = app.MOVE
        self._mv = (mv.download, mv.upload, mv.list_sets)
        def download(oid, dest, progress=None):
            with zipfile.ZipFile(dest, "w") as z:
                z.writestr("Song.abl", json.dumps({"tracks": [], "scenes": []}))
            return dest
        def upload(path, name):
            self.sets.append({"objectId": NEW, "name": "Acid Set"})
        mv.download, mv.upload, mv.list_sets = download, upload, lambda: list(self.sets)

    def tearDown(self):
        for k, v in self._s2.items():
            setattr(app, k, v)
        app.MOVE.download, app.MOVE.upload, app.MOVE.list_sets = self._mv
        app.CFG["library"] = self._lib
        super().tearDown()

    def stage(self, *a, **k):
        pass

    def test_pull_copies_schwung_state(self):
        res = app.job_pull(OLD, False)(self.stage)
        self.assertTrue(res["schwung"])
        f = self.lib / "Acid Set" / app.SCHWUNG_FILE
        self.assertEqual(tar_names(f.read_bytes()), ["lanes_0.json", "slot_0.json"])
        self.assertTrue(json.loads((self.lib / "Acid Set" / "meta.json").read_text())["schwung"])

    def test_push_restores_schwung_state(self):
        app.job_pull(OLD, False)(self.stage)
        res = app.job_push("Acid Set")(self.stage)
        self.assertEqual(res["schwung"], "copied")
        self.assertTrue((self.root / NEW / "slot_0.json").exists())

    def test_push_without_ssh_reports(self):
        app.job_pull(OLD, False)(self.stage)
        app.ssh_enabled = lambda: False
        res = app.job_push("Acid Set")(self.stage)
        self.assertEqual(res["schwung"], "needs pad control")
        self.assertFalse((self.root / NEW).exists())


class SchwungUsedOnComputer(unittest.TestCase):
    """Сборка 62: значок S у проекта на компьютере — только если в слотах Schwung есть модуль (как на Move),
    а не просто потому, что сохранены пустые заготовки «{}», которые Schwung создаёт в любом сете."""
    def tar(self, files):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as t:
            for name, body in files.items():
                info = tarfile.TarInfo("./" + name); info.size = len(body)
                t.addfile(info, io.BytesIO(body))
        return buf.getvalue()

    def test_seeded_state_is_not_use(self):
        data = self.tar({"slot_0.json": b"{}\n", "slot_1.json": b"{}\n", "master_fx_0.json": b"x" * 543})
        self.assertFalse(app.schwung_tar_used(data))

    def test_module_in_slot_is_use(self):
        data = self.tar({"slot_0.json": b'{"module": "obxd", "module_path": "/data/x"}', "slot_1.json": b"{}\n"})
        self.assertTrue(app.schwung_tar_used(data))

    def test_broken_data(self):
        self.assertFalse(app.schwung_tar_used(b"not a tar"))

    def test_library_flag_follows_state_content(self):
        d = Path(tempfile.mkdtemp()) / "P"
        d.mkdir()
        (d / app.SCHWUNG_FILE).write_bytes(self.tar({"slot_0.json": b"{}\n"}))
        self.assertFalse(app.lib_schwung(d, {"schwung": True}))            # старая пометка от прежней сборки — не в счёт
        (d / app.SCHWUNG_FILE).write_bytes(self.tar({"slot_2.json": b'{"module": "dexed"}' + b" " * 20}))
        self.assertTrue(app.lib_schwung(d, {}))
        (d / app.SCHWUNG_FILE).unlink()
        self.assertFalse(app.lib_schwung(d, {}))
