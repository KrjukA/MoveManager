"""Сборка 52: версия в истории перед каждой записью проекта."""
import copy
import json
import zipfile

import app
import history
from tests.test_clip_ops import song
from tests.test_routes_midi import OID, RouteBase

NEW = "bb98954a-8822-4a82-92d4-10529d5ca3a9"


def bundle_bytes(s):
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Song.abl", json.dumps(s))
        z.writestr("Samples/kick.wav", b"RIFF")
    return buf.getvalue()


class FakeMove:
    """Поддельный HTTP API Move: список сетов, скачивание, загрузка (новый ID), удаление, переименование."""
    def __init__(self, s):
        self.sets = [{"objectId": OID, "name": "Live Set", "lastModifiedDateTime": "1"}]
        self.song = s
        self.uploaded = []
        self.identify = True

    def list_sets(self):
        return list(self.sets)

    def download(self, oid, dest, progress=None):
        dest.write_bytes(bundle_bytes(self.song))

    def upload(self, path, filename):
        self.uploaded.append(filename)
        if self.identify:
            self.sets.append({"objectId": NEW, "name": filename[:-10], "lastModifiedDateTime": "2"})

    def delete(self, oid):
        self.sets = [o for o in self.sets if o["objectId"] != oid]

    def rename(self, oid, name):
        for o in self.sets:
            if o["objectId"] == oid:
                o["name"] = name


class Hooks(RouteBase):
    def setUp(self):
        super().setUp()
        with zipfile.ZipFile(self.tmp / "lib" / "Demo" / "Demo.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(song()))
            z.writestr("Samples/kick.wav", b"RIFF")
        self.move_song = song()
        self._move = app.MOVE
        app.MOVE = FakeMove(song())
        self._ss = app.set_by_id
        app.set_by_id = lambda oid: next(o for o in app.MOVE.list_sets() if o["objectId"] == oid)

    def tearDown(self):
        app.MOVE = self._move
        super().tearDown()

    def mv(self, oid=OID):
        return history.list_versions(app.history_dir("move", oid))

    def lib(self):
        return history.list_versions(app.history_dir("lib", "Demo"))

    def run_job(self, st_body):
        st, _, b = st_body
        self.assertEqual(st, 200, b)
        job = self.wait_job(b)
        self.assertEqual(job["status"], "done", job)

    def post(self, path, body):
        return self.req("POST", path, json.dumps(body).encode())

    # ── Move по SSH ──
    def test_move_edit(self):
        before = copy.deepcopy(self.move_song)
        self.run_job(self.post(f"/api/move/sets/{OID}/edit", {"pans": {"0": 0.5}, "replace": True}))
        vs = self.mv()
        self.assertEqual(len(vs), 1)
        self.assertEqual(vs[0]["action"], "Pan changed")
        self.assertEqual(json.loads(history.read_version(app.history_dir("move", OID), vs[0]["id"])), before)

    def test_move_edit_action_names(self):
        self.assertEqual(app.edit_action([1, 0, 2, 3], {"0": 0.1}, {"rootNote": 9, "scale": "Minor"}),
                         "Tracks reordered, Pan changed, Key changed to A Minor")
        self.assertEqual(app.edit_action(None, {}, {"tempo": 120}), "Tempo changed to 120 bpm")
        self.assertEqual(app.edit_action([0, 1], {}, None), "")

    def test_move_load_mid(self):
        self.run_job(self.req("POST", f"/api/move/sets/{OID}/clip?track=3&scene=0&replace=1", self.midi_file()))
        self.assertEqual(self.mv()[0]["action"], "Clip loaded from file T4 S1")

    def test_move_delete_clip(self):
        self.run_job(self.req("DELETE", f"/api/move/sets/{OID}/clip?track=0&scene=0"))
        self.assertEqual(self.mv()[0]["action"], "Clip deleted T1 S1")

    def test_move_generator(self):
        notes = [{"noteNumber": 36, "startTime": 0.0, "duration": 0.25, "velocity": 100.0}]
        self.run_job(self.post(f"/api/move/sets/{OID}/clip-notes?track=2&scene=0&replace=1", {"notes": notes, "length": 4}))
        self.assertEqual(self.mv()[0]["action"], "Pattern generated T3 S1")

    def test_move_clip_op(self):
        self.run_job(self.post(f"/api/move/sets/{OID}/clip-op", {"op": "swap", "from": [0, 0], "to": [3, 1]}))
        self.assertEqual(self.mv()[0]["action"], "Clips swapped T1 S1 ↔ T4 S2")

    def test_no_more_backups_dir(self):
        self.run_job(self.req("DELETE", f"/api/move/sets/{OID}/clip?track=0&scene=0"))
        self.assertFalse(list((self.tmp / "backups").glob("*.abl")) if (self.tmp / "backups").exists() else [])

    def test_version_failure_blocks_write(self):
        def boom(*a, **k):
            raise OSError("disk full")
        saved = history.save_version
        history.save_version = boom
        try:
            st, _, b = self.req("DELETE", f"/api/move/sets/{OID}/clip?track=0&scene=0")
            job = self.wait_job(b)
            self.assertEqual(job["status"], "error", job)
            self.assertIn("History", json.dumps(job))
            self.assertEqual(self.writes, [])
            st, _, _ = self.post("/api/library/Demo/clip-op", {"op": "move", "from": [0, 0], "to": [3, 1]})
            self.assertEqual(st, 400)
            s, _ = self.lib_song()
            self.assertIsNotNone(s["tracks"][0]["clipSlots"][0]["clip"])
        finally:
            history.save_version = saved

    # ── компьютер ──
    def test_library_edit(self):
        before = self.lib_song()[0]
        st, _, _ = self.post("/api/library/Demo/edit", {"pans": {"0": -0.5}})
        self.assertEqual(st, 200)
        vs = self.lib()
        self.assertEqual(vs[0]["action"], "Pan changed")
        self.assertEqual(json.loads(history.read_version(app.history_dir("lib", "Demo"), vs[0]["id"])), before)
        self.assertTrue((self.tmp / "lib" / "Demo" / ".history").is_dir())
        self.assertFalse(any(".history" in n for n in self.lib_song()[1]))

    def test_library_load_mid_generator_delete_clip_op(self):
        self.assertEqual(self.req("POST", "/api/library/Demo/clip?track=3&scene=0&replace=1", self.midi_file())[0], 200)
        notes = [{"noteNumber": 36, "startTime": 0.0, "duration": 0.25, "velocity": 100.0}]
        self.assertEqual(self.post("/api/library/Demo/clip-notes?track=2&scene=0&replace=1", {"notes": notes, "length": 4})[0], 200)
        self.assertEqual(self.req("DELETE", "/api/library/Demo/clip?track=0&scene=0")[0], 200)
        self.assertEqual(self.post("/api/library/Demo/clip-op", {"op": "copy", "from": [3, 0], "to": [3, 1]})[0], 200)
        self.assertEqual([v["action"] for v in self.lib()],
                         ["Clip copied T4 S1 → T4 S2", "Clip deleted T1 S1", "Pattern generated T3 S1",
                          "Clip loaded from file T4 S1"])

    # ── перенос и смена ID ──
    def test_pull_into_existing_folder_saves_version(self):
        app.MOVE.sets[0]["name"] = "Demo"
        before = self.lib_song()[0]
        app.ssh_enabled = lambda: False
        app.job_pull(OID, False)(lambda *a, **k: None)
        vs = self.lib()
        self.assertEqual(vs[0]["action"], "Replaced by copy from Move")
        self.assertEqual(json.loads(history.read_version(app.history_dir("lib", "Demo"), vs[0]["id"])), before)

    def test_pull_into_new_folder_no_version(self):
        app.MOVE.sets[0]["name"] = "Fresh"
        app.ssh_enabled = lambda: False
        app.job_pull(OID, False)(lambda *a, **k: None)
        self.assertEqual(history.list_versions(app.history_dir("lib", "Fresh")), [])

    def test_push_replace_moves_history(self):
        history.save_version(app.history_dir("move", OID), b"{}", "old")
        app.ssh_enabled = lambda: False
        app.job_push("Demo", replace_id=OID)(lambda *a, **k: None)
        self.assertEqual([v["action"] for v in self.mv(NEW)], ["old"])
        self.assertEqual(self.mv(OID), [])

    def test_no_ssh_edit_replace_moves_history(self):
        app.ssh_enabled = lambda: False
        before = copy.deepcopy(app.MOVE.song)
        app.job_edit_move(OID, None, {"0": 0.3}, True)(lambda *a, **k: None)
        vs = self.mv(NEW)
        self.assertEqual([v["action"] for v in vs], ["Pan changed"])
        self.assertEqual(json.loads(history.read_version(app.history_dir("move", NEW), vs[0]["id"])), before)
        self.assertEqual(self.mv(OID), [])

    def test_no_ssh_edit_copy_no_version(self):
        app.ssh_enabled = lambda: False
        app.job_edit_move(OID, None, {"0": 0.3}, False)(lambda *a, **k: None)
        self.assertEqual(self.mv(OID), [])
        self.assertEqual(self.mv(NEW), [])

    def test_no_ssh_edit_unidentified_keeps_version_on_old(self):
        app.ssh_enabled = lambda: False
        app.MOVE.identify = False
        with self.assertRaises(app.AppError):
            app.job_edit_move(OID, None, {"0": 0.3}, True)(lambda *a, **k: None)
        self.assertEqual(len(self.mv(OID)), 1)

    def test_history_dir_validates(self):
        with self.assertRaises(app.AppError):
            app.history_dir("move", "../../etc")
