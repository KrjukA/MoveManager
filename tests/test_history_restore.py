"""Сборка 52: список истории, откат, проверка сэмплов, старые копии из backups/."""
import json
import time
import zipfile

import app
import history
from tests.test_clip_ops import song
from tests.test_history_hooks import FakeMove
from tests.test_routes_midi import OID, RouteBase

OTHER = "cc98954a-8822-4a82-92d4-10529d5ca3a9"


def with_sample(s, uri):
    s["tracks"][2]["devices"][0]["sampleUri"] = uri
    return s


class Restore(RouteBase):
    def setUp(self):
        super().setUp()
        self.write_lib(song())
        self.move_song = song()
        self._move, self._ss, self._miss = app.MOVE, app.set_by_id, app.move_missing_files
        app.MOVE = FakeMove(song())
        app.set_by_id = lambda oid: next(o for o in app.MOVE.list_sets() if o["objectId"] == oid)
        self.missing_on_move = []
        app.move_missing_files = lambda rels: [r for r in rels if r in self.missing_on_move]

    def tearDown(self):
        app.MOVE, app.set_by_id, app.move_missing_files = self._move, self._ss, self._miss
        super().tearDown()

    def write_lib(self, s, extra=("Samples/kick.wav",)):
        with zipfile.ZipFile(self.tmp / "lib" / "Demo" / "Demo.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(s))
            for n in extra:
                z.writestr(n, b"RIFF")

    def post(self, path, body):
        return self.req("POST", path, json.dumps(body).encode())

    def get(self, path):
        st, _, b = self.req("GET", path)
        return st, json.loads(b)

    # ── список ──
    def test_history_list_move_with_legacy(self):
        hd = app.history_dir("move", OID)
        t = time.mktime((2026, 11, 16, 22, 0, 0, 0, 0, -1))
        history.save_version(hd, b"{}", "Pan changed", now=t)
        (self.tmp / "backups").mkdir()
        (self.tmp / "backups" / "Live Set 20261115-101500.abl").write_text("{}")
        (self.tmp / "backups" / "Other Set 20261115-101500.abl").write_text("{}")
        st, d = self.get(f"/api/move/sets/{OID}/history")
        self.assertEqual(st, 200)
        vs = d["versions"]
        self.assertEqual([(v["action"], v["legacy"]) for v in vs], [("Pan changed", False), ("", True)])
        self.assertEqual(vs[1]["savedAt"], "2026-11-15T10:15:00")
        self.assertEqual(vs[1]["id"], "legacy:Live Set 20261115-101500.abl")
        self.assertEqual(d["versions"][0]["when"], "16 Nov 22:00:00")

    def test_legacy_hidden_when_names_duplicate(self):
        app.MOVE.sets.append({"objectId": OTHER, "name": "Live Set", "lastModifiedDateTime": "1"})
        (self.tmp / "backups").mkdir()
        (self.tmp / "backups" / "Live Set 20261115-101500.abl").write_text("{}")
        self.assertEqual(self.get(f"/api/move/sets/{OID}/history")[1]["versions"], [])

    def test_history_list_library_empty_and_filled(self):
        self.assertEqual(self.get("/api/library/Demo/history")[1]["versions"], [])
        self.post("/api/library/Demo/edit", {"pans": {"0": 0.2}})
        self.assertEqual(self.get("/api/library/Demo/history")[1]["versions"][0]["action"], "Pan changed")

    # ── откат на Move ──
    def test_restore_move_writes_version_and_saves_current(self):
        old = song()
        old["tempo"] = 99.0
        vid = history.save_version(app.history_dir("move", OID), app.dump_song(old), "Tempo changed to 120 bpm")
        st, _, b = self.post(f"/api/move/sets/{OID}/history/restore", {"id": vid})
        self.assertEqual(st, 200, b)
        job = self.wait_job(b)
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.writes[0]["tempo"], 99.0)
        vs = history.list_versions(app.history_dir("move", OID))
        self.assertTrue(vs[0]["action"].startswith("Restore of "))
        self.assertEqual(json.loads(history.read_version(app.history_dir("move", OID), vs[0]["id"]))["tempo"], 120.0)

    def test_restore_move_legacy(self):
        (self.tmp / "backups").mkdir()
        old = song()
        old["tempo"] = 77.0
        (self.tmp / "backups" / "Live Set 20261115-101500.abl").write_text(json.dumps(old))
        st, _, b = self.post(f"/api/move/sets/{OID}/history/restore", {"id": "legacy:Live Set 20261115-101500.abl"})
        self.assertEqual(self.wait_job(b)["status"], "done")
        self.assertEqual(self.writes[0]["tempo"], 77.0)

    def test_restore_move_missing_samples_409_then_force(self):
        uri = "ableton:/user-library/Samples/Gone%20Kick.wav"
        vid = history.save_version(app.history_dir("move", OID),
                                   app.dump_song(with_sample(song(), uri)), "x")
        self.missing_on_move = ["Samples/Gone Kick.wav"]
        st, _, b = self.post(f"/api/move/sets/{OID}/history/restore", {"id": vid})
        self.assertEqual(st, 409)
        d = json.loads(b)
        self.assertEqual((d["error"], d["missing"]), ("missing", ["Samples/Gone Kick.wav"]))
        self.assertEqual(self.writes, [])
        st, _, b = self.post(f"/api/move/sets/{OID}/history/restore", {"id": vid, "force": True})
        self.assertEqual(self.wait_job(b)["status"], "done")
        self.assertEqual(len(self.writes), 1)

    def test_restore_packs_not_checked(self):
        vid = history.save_version(app.history_dir("move", OID),
                                   app.dump_song(with_sample(song(), "ableton:/packs/Drift/Samples/a.wav")), "x")
        self.missing_on_move = ["Drift/Samples/a.wav", "packs/Drift/Samples/a.wav"]
        st, _, b = self.post(f"/api/move/sets/{OID}/history/restore", {"id": vid})
        self.assertEqual(st, 200, b)
        self.assertEqual(self.wait_job(b)["status"], "done")      # дождаться: иначе задача переживёт подмены теста

    def test_restore_move_needs_ssh(self):
        vid = history.save_version(app.history_dir("move", OID), app.dump_song(song()), "x")
        app.ssh_enabled = lambda: False
        st, _, _ = self.post(f"/api/move/sets/{OID}/history/restore", {"id": vid})
        self.assertEqual(st, 400)

    def test_restore_bad_id_400(self):
        for bad in ("../../x", "legacy:../../config.json", "legacy:Other Set 20261115-101500.abl", "", None):
            st, _, _ = self.post(f"/api/move/sets/{OID}/history/restore", {"id": bad})
            self.assertEqual(st, 400, bad)
            st, _, _ = self.post("/api/library/Demo/history/restore", {"id": bad})
            self.assertEqual(st, 400, bad)

    # ── откат на компьютере ──
    def test_restore_library_keeps_samples(self):
        self.post("/api/library/Demo/edit", {"pans": {"0": 0.7}})
        vid = self.get("/api/library/Demo/history")[1]["versions"][0]["id"]
        st, _, b = self.post("/api/library/Demo/history/restore", {"id": vid})
        self.assertEqual(st, 200, b)
        s, names = self.lib_song()
        self.assertEqual(s["tracks"][0]["mixer"]["pan"], 0.0)
        self.assertIn("Samples/kick.wav", names)
        self.assertFalse(any(".history" in n for n in names))
        vs = self.get("/api/library/Demo/history")[1]["versions"]
        self.assertEqual(len(vs), 2)
        self.assertTrue(vs[0]["action"].startswith("Restore of "))

    def test_restore_library_missing_samples(self):
        old = with_sample(song(), "Samples/Gone%20Snare.wav")
        vid = history.save_version(app.history_dir("lib", "Demo"), json.dumps(old).encode(), "x")
        st, _, b = self.post("/api/library/Demo/history/restore", {"id": vid})
        self.assertEqual(st, 409)
        self.assertEqual(json.loads(b)["missing"], ["Samples/Gone Snare.wav"])
        st, _, _ = self.post("/api/library/Demo/history/restore", {"id": vid, "force": True})
        self.assertEqual(st, 200)
        self.assertEqual(self.lib_song()[0]["tracks"][2]["devices"][0]["sampleUri"], "Samples/Gone%20Snare.wav")

    def test_restore_library_sample_present(self):
        old = with_sample(song(), "Samples/kick.wav")
        vid = history.save_version(app.history_dir("lib", "Demo"), json.dumps(old).encode(), "x")
        st, _, _ = self.post("/api/library/Demo/history/restore", {"id": vid})
        self.assertEqual(st, 200)
