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
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": OID}))   # тот же проект
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
        # сборка 55: история переезжает, только если проект на компьютере пришёл с этого сета (sourceId)
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": OID}))
        history.save_version(app.history_dir("move", OID), b"{}", "old")
        app.ssh_enabled = lambda: False
        app.job_push("Demo", replace_id=OID)(lambda *a, **k: None)
        self.assertEqual([v["action"] for v in self.mv(NEW)], ["old"])
        self.assertEqual(self.mv(OID), [])

    def test_push_onto_other_project_keeps_its_history(self):
        history.save_version(app.history_dir("move", OID), b"{}", "old")
        app.ssh_enabled = lambda: False
        app.job_push("Demo", replace_id=OID)(lambda *a, **k: None)      # другой проект на занятый пэд
        self.assertEqual(self.mv(NEW), [])

    def deleted(self):
        trash = self.tmp / "lib" / "_Deleted"
        return sorted(p.name for p in trash.rglob("*.ablbundle")) if trash.exists() else []

    def test_push_replace_backs_up_deleted_project(self):
        app.ssh_enabled = lambda: False
        app.job_push("Demo", replace_id=OID)(lambda *a, **k: None)
        self.assertEqual(self.deleted(), ["Live Set.ablbundle"])
        self.assertNotIn(OID, [o["objectId"] for o in app.MOVE.list_sets()])

    def test_backup_failure_blocks_delete(self):
        def boom(oid, dest, progress=None):
            raise app.MoveOffline("Wi-Fi gone")
        app.MOVE.download = boom
        app.ssh_enabled = lambda: False
        with self.assertRaises(app.AppError):
            app.job_push("Demo", replace_id=OID)(lambda *a, **k: None)
        self.assertIn(OID, [o["objectId"] for o in app.MOVE.list_sets()])
        st, _, b = self.req("DELETE", f"/api/move/sets/{OID}")
        self.assertEqual(self.wait_job(b)["status"], "error")
        self.assertIn(OID, [o["objectId"] for o in app.MOVE.list_sets()])

    def test_delete_route_backs_up(self):
        st, _, b = self.req("DELETE", f"/api/move/sets/{OID}")
        self.assertEqual(st, 200, b)
        self.assertEqual(self.wait_job(b)["status"], "done")
        self.assertEqual(self.deleted(), ["Live Set.ablbundle"])
        self.assertNotIn(OID, [o["objectId"] for o in app.MOVE.list_sets()])

    def test_no_ssh_edit_replace_backs_up_original(self):
        app.ssh_enabled = lambda: False
        app.job_edit_move(OID, None, {"0": 0.3}, True)(lambda *a, **k: None)
        self.assertEqual(self.deleted(), ["Live Set.ablbundle"])

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

    def test_no_ssh_edit_unidentified_leaves_no_false_version(self):
        app.ssh_enabled = lambda: False
        app.MOVE.identify = False
        with self.assertRaises(app.AppError):
            app.job_edit_move(OID, None, {"0": 0.3}, True)(lambda *a, **k: None)
        self.assertEqual(self.mv(OID), [])                 # правки не было — и строки «before: …» нет

    def test_no_ssh_edit_rename_failure_keeps_history(self):
        history.save_version(app.history_dir("move", OID), b"{}", "old")
        app.ssh_enabled = lambda: False
        def boom(oid, name):
            raise app.AppError("rename failed")
        app.MOVE.rename = boom
        with self.assertRaises(app.AppError):
            app.job_edit_move(OID, None, {"0": 0.3}, True)(lambda *a, **k: None)
        self.assertEqual([v["action"] for v in self.mv(NEW)], ["Pan changed", "old"])

    def test_legacy_ignores_sets_with_unusable_names(self):
        app.MOVE.sets.append({"objectId": "dd98954a-8822-4a82-92d4-10529d5ca3a9", "name": "", "lastModifiedDateTime": "1"})
        app.MOVE.sets.append({"objectId": "ee98954a-8822-4a82-92d4-10529d5ca3a9", "name": "...", "lastModifiedDateTime": "1"})
        st, _, b = self.req("GET", f"/api/move/sets/{OID}/history")
        self.assertEqual(st, 200, b)

    def test_history_dir_validates(self):
        with self.assertRaises(app.AppError):
            app.history_dir("move", "../../etc")


class PullNames(Hooks):
    """Сборка 55: «To computer →» не затирает другой проект с тем же именем."""
    def run_pull(self, name):
        app.MOVE.sets[0]["name"] = name
        app.ssh_enabled = lambda: False
        app.job_pull(OID, False)(lambda *a, **k: None)

    def test_same_source_updates_folder(self):
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": OID}))
        self.run_pull("Demo")
        self.assertFalse((self.tmp / "lib" / "Demo 2").exists())
        self.assertEqual(self.lib()[0]["action"], "Replaced by copy from Move")

    def test_other_project_same_name_gets_new_folder(self):
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": "ffffffff-2222-3333-4444-555555555555"}))
        before = (self.tmp / "lib" / "Demo" / "Demo.ablbundle").read_bytes()
        self.run_pull("Demo")
        self.assertEqual((self.tmp / "lib" / "Demo" / "Demo.ablbundle").read_bytes(), before)
        self.assertTrue(list((self.tmp / "lib" / "Demo 2").glob("*.ablbundle")))
        self.assertEqual(json.loads((self.tmp / "lib" / "Demo 2" / "meta.json").read_text())["sourceId"], OID)

    def test_local_project_without_source_is_not_overwritten(self):
        before = (self.tmp / "lib" / "Demo" / "Demo.ablbundle").read_bytes()
        self.run_pull("Demo")
        self.assertEqual((self.tmp / "lib" / "Demo" / "Demo.ablbundle").read_bytes(), before)
        self.assertTrue((self.tmp / "lib" / "Demo 2").exists())


class PullChoice(Hooks):
    """Сборка 62: проект уже есть на компьютере — человек выбирает «Дублировать» или «Заменить»."""
    def run_pull(self, name, mode):
        app.MOVE.sets[0]["name"] = name
        app.ssh_enabled = lambda: False
        return app.job_pull(OID, False, mode=mode)(lambda *a, **k: None)

    def test_duplicate_same_project_makes_new_folder(self):
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": OID}))
        before = (self.tmp / "lib" / "Demo" / "Demo.ablbundle").read_bytes()
        self.run_pull("Demo", "duplicate")
        self.assertEqual((self.tmp / "lib" / "Demo" / "Demo.ablbundle").read_bytes(), before)
        self.assertTrue(list((self.tmp / "lib" / "Demo 2").glob("*.ablbundle")))
        self.assertEqual(self.lib(), [])                          # старый проект не тронут — версии в историю нет

    def test_replace_same_project(self):
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": OID, "notes": "keep"}))
        self.run_pull("Demo", "replace")
        self.assertFalse((self.tmp / "lib" / "Demo 2").exists())
        self.assertEqual(self.lib()[0]["action"], "Replaced by copy from Move")
        self.assertEqual(json.loads((self.tmp / "lib" / "Demo" / "meta.json").read_text())["notes"], "keep")

    def test_replace_other_project_with_same_name(self):
        other = "ffffffff-2222-3333-4444-555555555555"
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": other, "notes": "other"}))
        self.run_pull("Demo", "replace")
        self.assertFalse((self.tmp / "lib" / "Demo 2").exists())
        meta = json.loads((self.tmp / "lib" / "Demo" / "meta.json").read_text())
        self.assertEqual(meta["sourceId"], OID)
        self.assertEqual(meta.get("notes", ""), "")                # заметки чужого проекта не переносятся
        self.assertEqual(self.lib()[0]["action"], "Replaced by copy from Move")   # старая версия — в истории

    def test_replace_finds_renamed_copy_by_source(self):
        d = self.tmp / "lib" / "My Demo"
        d.mkdir()
        (d / "My Demo.ablbundle").write_bytes((self.tmp / "lib" / "Demo" / "Demo.ablbundle").read_bytes())
        (d / "meta.json").write_text(json.dumps({"sourceId": OID}))
        self.run_pull("Demo", "replace")
        self.assertTrue(list(d.glob("*.ablbundle")))
        self.assertEqual(json.loads((d / "meta.json").read_text())["sourceId"], OID)

    def test_route_passes_mode(self):
        seen = []
        saved = app.job_pull
        app.job_pull = lambda oid, audio, group=None, mode=None: seen.append(mode) or (lambda stage: {})
        try:
            self.req("POST", f"/api/move/sets/{OID}/pull", json.dumps({"audio": False, "mode": "duplicate"}).encode())
        finally:
            app.job_pull = saved
        self.assertEqual(seen, ["duplicate"])


class SourceFollows(Hooks):
    """Сборка 55 (рецензия): проект с компьютера после «← To Move» помнит новый сет."""
    def meta(self):
        return json.loads((self.tmp / "lib" / "Demo" / "meta.json").read_text())

    def test_push_back_to_own_pad_updates_source(self):
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": OID}))
        app.ssh_enabled = lambda: False
        app.job_push("Demo", replace_id=OID)(lambda *a, **k: None)
        self.assertEqual(self.meta()["sourceId"], NEW)

    def test_local_project_pushed_gets_source(self):
        app.ssh_enabled = lambda: False
        app.job_push("Demo")(lambda *a, **k: None)
        self.assertEqual(self.meta()["sourceId"], NEW)

    def test_copy_of_other_existing_set_keeps_source(self):
        other = "eeeeeeee-2222-3333-4444-555555555555"
        app.MOVE.sets.append({"objectId": other, "name": "X", "lastModifiedDateTime": "1"})
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": other}))
        app.ssh_enabled = lambda: False
        app.job_push("Demo")(lambda *a, **k: None)
        self.assertEqual(self.meta()["sourceId"], other)

    def test_no_ssh_edit_remaps_library_source(self):
        (self.tmp / "lib" / "Demo" / "meta.json").write_text(json.dumps({"sourceId": OID}))
        app.ssh_enabled = lambda: False
        app.job_edit_move(OID, None, {"0": 0.3}, True)(lambda *a, **k: None)
        self.assertEqual(self.meta()["sourceId"], NEW)

    def test_delete_route_is_a_job(self):
        st, _, b = self.req("DELETE", f"/api/move/sets/{OID}")
        self.assertEqual(st, 200, b)
        job = self.wait_job(b)
        self.assertEqual(job["status"], "done", job)
        self.assertNotIn(OID, [o["objectId"] for o in app.MOVE.list_sets()])


class CopyOnMove(Hooks):
    """Сборка 62: копия проекта на Move — перетаскивание с ⌥/Alt. Новый сет «Имя copy» на свободном пэде."""
    def setUp(self):
        super().setUp()
        self.slots = {OID: {"slot": 3}}
        self.placed = []
        self._sv = {k: getattr(app, k) for k in ("ssh_enabled", "ssh_slots", "ssh_set_slots", "schwung_fetch", "schwung_restore")}
        app.ssh_enabled = lambda: True
        app.ssh_slots = lambda: dict(self.slots)
        app.ssh_set_slots = lambda pairs: self.placed.extend(pairs)
        app.schwung_fetch = lambda oid: None
        app.schwung_restore = lambda oid, data: "copied"

    def tearDown(self):
        for k, v in self._sv.items():
            setattr(app, k, v)
        super().tearDown()

    def test_copy_goes_to_requested_free_pad(self):
        res = app.job_copy_move(OID, 7)(lambda *a, **k: None)
        self.assertEqual(app.MOVE.uploaded, ["Live Set copy.ablbundle"])
        self.assertEqual(res["id"], NEW)
        self.assertEqual(self.placed, [(NEW, 7)])
        self.assertEqual(res["slot"], 7)

    def test_busy_pad_takes_first_free(self):
        res = app.job_copy_move(OID, 3)(lambda *a, **k: None)
        self.assertEqual(self.placed, [(NEW, 0)])
        self.assertEqual(res["slot"], 0)

    def test_name_not_taken_twice(self):
        app.MOVE.sets.append({"objectId": "22222222-2222-3333-4444-555555555555", "name": "Live Set copy"})
        app.job_copy_move(OID, None)(lambda *a, **k: None)
        self.assertEqual(app.MOVE.uploaded, ["Live Set copy 2.ablbundle"])

    def test_original_untouched(self):
        app.job_copy_move(OID, None)(lambda *a, **k: None)
        self.assertIn(OID, [o["objectId"] for o in app.MOVE.list_sets()])

    def test_schwung_state_copied(self):
        app.schwung_fetch = lambda oid: b"state" if oid == OID else None
        got = []
        app.schwung_restore = lambda oid, data: got.append((oid, data)) or "copied"
        res = app.job_copy_move(OID, None)(lambda *a, **k: None)
        self.assertEqual(got, [(NEW, b"state")])
        self.assertEqual(res["schwung"], "copied")

    def test_broken_groove_repaired_in_copy(self):
        app.MOVE.song["grooves"] = [{"name": "Swing 16ths"}]
        for t in app.MOVE.song["tracks"]:
            for sl in t.get("clipSlots") or []:
                if (sl or {}).get("clip"):
                    sl["clip"]["grooveId"] = 1
        sent = []
        up = app.MOVE.upload
        def upload(path, filename):
            with zipfile.ZipFile(path) as z:
                sent.append(json.loads(z.read("Song.abl")))
            up(path, filename)
        app.MOVE.upload = upload
        app.job_copy_move(OID, None)(lambda *a, **k: None)
        self.assertEqual(sent[0]["grooves"][0]["id"], 1)

    def test_route(self):
        seen = []
        saved = app.job_copy_move
        app.job_copy_move = lambda oid, slot: seen.append((oid, slot)) or (lambda stage: {})
        try:
            st, _, _ = self.req("POST", f"/api/move/sets/{OID}/copy", json.dumps({"slot": 5}).encode())
        finally:
            app.job_copy_move = saved
        self.assertEqual(seen, [(OID, 5)])
