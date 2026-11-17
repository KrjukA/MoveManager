"""Сборка 53: лупы на сервере — сетка, правило дорожек, образец клипа, загрузка в UPLOAD, маршрут."""
import copy
import hashlib
import json
import uuid

import app
import history
import samplelib
from tests.test_clip_ops import song as clip_song
from tests.test_history_hooks import FakeMove
from tests.test_loops import wav_bytes
from tests.test_routes_midi import OID, RouteBase


def song():
    """Дорожки: 0 — мелодия (клип S1), 1 — аудио (пусто), 2 — ударные (клип S2), 3 — мелодия. 2 сцены → расширяем до 4."""
    s = clip_song()
    for tr in s["tracks"]:
        tr["clipSlots"] += [{"hasStop": True, "clip": None}, {"hasStop": True, "clip": None}]
    s["tracks"][1]["color"] = 11
    return s


def audio(rel="Samples/UPLOAD/Old 100bpm.wav", tempo=100.0, beats=16.0):
    return {"isPlaying": False, "name": "", "color": 4, "isEnabled": True, "timeSignature": {"upper": 4, "lower": 4},
            "region": {"start": 0.0, "end": beats, "loop": {"start": 0.0, "end": beats, "isEnabled": True}},
            "stepEditorScrollPosition": 0.0, "sampleUri": samplelib.rel_to_uri(rel),
            "warping": {"markers": [], "tempoAfterLastMarker": tempo}, "gain": 0.0, "transpose": -3, "detune": 0.0,
            "envelopes": []}


def multipart(files):
    b = uuid.uuid4().hex
    out = b""
    for name, data in files:
        out += (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
                f"Content-Type: audio/wav\r\n\r\n").encode() + data + b"\r\n"
    return out + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"


class Grid(RouteBase):
    def test_grid_audio_fields(self):
        s = song()
        s["tracks"][1]["clipSlots"][0]["clip"] = audio()
        g = app.clips_grid(s)
        self.assertEqual(g[1][0], {"audio": True, "sample": "Old 100bpm.wav", "tempo": 100.0, "transpose": -3,
                                   "notes": 0, "length": 16.0})
        self.assertEqual(g[0][0], {"notes": 3, "length": 4.0})

    def test_stale_without_audio_flag(self):
        s = song()
        s["tracks"][1]["clipSlots"][0]["clip"] = audio()
        info = app.parse_song(s)
        self.assertFalse(app.stale_info(info))
        del info["clips"][1][0]["audio"]
        self.assertTrue(app.stale_info(info))

    def test_put_clip_template_midi_only(self):
        s = song()
        s["tracks"][0]["clipSlots"][0]["clip"] = None
        s["tracks"][1]["clipSlots"][0]["clip"] = audio()
        s["tracks"][2]["clipSlots"][1]["clip"] = None
        app.put_clip(s, 3, 0, [{"noteNumber": 60, "startTime": 0.0, "duration": 1.0, "velocity": 90.0}], 4)
        c = s["tracks"][3]["clipSlots"][0]["clip"]
        for k in ("sampleUri", "warping", "gain", "transpose", "detune"):
            self.assertNotIn(k, c)

    def test_clip_op_audio_allowed_and_rule(self):
        s = song()
        s["tracks"][1]["clipSlots"][0]["clip"] = audio()
        app.clip_op(s, "copy", (1, 0), (1, 2))
        self.assertEqual(s["tracks"][1]["clipSlots"][2]["clip"]["sampleUri"], audio()["sampleUri"])
        with self.assertRaises(app.AppError) as e:
            app.clip_op(copy.deepcopy(s), "copy", (1, 0), (0, 3))
        self.assertIn("audio track", str(e.exception))
        with self.assertRaises(app.AppError):
            app.clip_op(copy.deepcopy(s), "copy", (0, 0), (1, 3))


class Loops(RouteBase):
    def setUp(self):
        super().setUp()
        self.move_song = song()
        self._saved_up = (app.MOVE, app.set_by_id, app.upload_dir_md5, app.put_sample)
        app.MOVE = FakeMove(song())
        app.set_by_id = lambda oid: next(o for o in app.MOVE.list_sets() if o["objectId"] == oid)
        self.remote = {}                         # имя в UPLOAD → байты
        self.fail_on = None
        app.upload_dir_md5 = lambda: {n: hashlib.md5(d).hexdigest() for n, d in self.remote.items()}

        def put(rel, data):
            name = rel.rsplit("/", 1)[1]
            if name == self.fail_on:
                raise app.SshError("connection lost")
            self.remote[name] = data
        app.put_sample = put

    def tearDown(self):
        app.MOVE, app.set_by_id, app.upload_dir_md5, app.put_sample = self._saved_up
        super().tearDown()

    def send(self, files, track=1, scene=0, replace=0):
        body, ctype = multipart(files)
        import urllib.request, urllib.error
        r = urllib.request.Request(f"{self.base}/api/move/sets/{OID}/loops?track={track}&scene={scene}&replace={replace}",
                                   data=body, method="POST", headers={"Content-Type": ctype})
        try:
            with urllib.request.urlopen(r, timeout=20) as x:
                return x.status, json.loads(x.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def run_job(self, st, d):
        self.assertEqual(st, 200, d)
        return self.wait_job(json.dumps(d).encode())

    def test_upload_reuses_identical_and_renames_different(self):
        same, other = wav_bytes(0.5), wav_bytes(0.25)
        self.remote = {"Loop 120bpm.wav": same, "Hit.wav": other}
        self.assertEqual(app.upload_loops([("Loop 120bpm.wav", same)]), ["Samples/UPLOAD/Loop 120bpm.wav"])
        self.assertEqual(app.upload_loops([("Hit.wav", same)]), ["Samples/UPLOAD/Hit 2.wav"])
        self.assertEqual(app.upload_loops([("Hit.wav", same)]), ["Samples/UPLOAD/Hit 2.wav"])   # уже есть такой же
        self.assertEqual(self.remote["Hit.wav"], other)
        self.assertEqual(app.upload_loops([("../../evil.wav", wav_bytes(0.1))]), ["Samples/UPLOAD/evil.wav"])   # только имя файла
        with self.assertRaises(app.AppError):
            app.upload_loops([(".hidden.wav", same)])

    def test_add_loops_places_in_order_one_write_one_version(self):
        files = [("10 c 120bpm.wav", wav_bytes(2.0)), ("2 b.wav", wav_bytes(4.0)), ("1 a 120bpm.wav", wav_bytes(8.0))]
        job = self.run_job(*self.send(files))
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(len(self.writes), 1)
        row = self.writes[0]["tracks"][1]["clipSlots"]
        self.assertEqual([samplelib.uri_to_rel(row[i]["clip"]["sampleUri"]) for i in range(3)],
                         ["Samples/UPLOAD/1 a 120bpm.wav", "Samples/UPLOAD/2 b.wav", "Samples/UPLOAD/10 c 120bpm.wav"])
        self.assertEqual(row[0]["clip"]["region"]["end"], 16.0)                    # 8 с при 120 = 16 долей
        self.assertEqual(row[1]["clip"]["warping"]["tempoAfterLastMarker"], 120.0)  # без темпа: 4 с → 2 такта при 120
        self.assertEqual(row[1]["clip"]["region"]["end"], 8.0)
        self.assertEqual(row[2]["clip"]["color"], 11)
        vs = history.list_versions(app.history_dir("move", OID))
        self.assertEqual([v["action"] for v in vs], ["Loops added T2 S1–S3"])
        self.assertEqual([p["scene"] for p in job["result"]["placed"]], [0, 1, 2])

    def test_add_loops_single_action_name(self):
        self.run_job(*self.send([("a 120bpm.wav", wav_bytes(2.0))], scene=2))
        self.assertEqual(history.list_versions(app.history_dir("move", OID))[0]["action"], "Loop added T2 S3")

    def test_add_loops_uses_audio_template(self):
        self.move_song["tracks"][1]["clipSlots"][3]["clip"] = audio()
        self.run_job(*self.send([("a 120bpm.wav", wav_bytes(2.0))]))
        c = self.writes[0]["tracks"][1]["clipSlots"][0]["clip"]
        self.assertEqual((c["color"], c["transpose"]), (4, 0))

    def test_add_loops_busy_409_before_upload(self):
        self.move_song["tracks"][1]["clipSlots"][1]["clip"] = audio()
        st, d = self.send([("a.wav", wav_bytes(1.0)), ("b.wav", wav_bytes(1.0))])
        self.assertEqual((st, d["error"], d["cells"]), (409, "busy", [1]))
        self.assertEqual(self.remote, {})
        self.assertEqual(self.writes, [])

    def test_add_loops_replace(self):
        self.move_song["tracks"][1]["clipSlots"][1]["clip"] = audio()
        self.run_job(*self.send([("a.wav", wav_bytes(1.0)), ("b.wav", wav_bytes(1.0))], replace=1))
        self.assertEqual(samplelib.uri_to_rel(self.writes[0]["tracks"][1]["clipSlots"][1]["clip"]["sampleUri"]),
                         "Samples/UPLOAD/b.wav")

    def test_add_loops_more_files_than_cells(self):
        files = [(f"{i} x.wav", wav_bytes(0.5)) for i in range(1, 4)]
        job = self.run_job(*self.send(files, scene=2))
        self.assertEqual(job["result"]["skipped"], ["3 x.wav"])
        self.assertNotIn("3 x.wav", self.remote)

    def test_add_loops_rejects_midi_track(self):
        st, d = self.send([("a.wav", wav_bytes(1.0))], track=0)
        self.assertEqual(st, 400)
        self.assertIn("audio track", d["message"])

    def test_add_loops_bad_file_400(self):
        for name, data in [("notes.txt", b"hello"), ("fake.wav", b"not audio at all")]:
            st, d = self.send([(name, data)])
            self.assertEqual(st, 400, d)
            self.assertIn(name, d["message"])
        self.assertEqual(self.remote, {})

    def test_add_loops_needs_ssh(self):
        app.ssh_enabled = lambda: False
        st, d = self.send([("a.wav", wav_bytes(1.0))])
        self.assertEqual(st, 400)

    def test_add_loops_upload_failure_keeps_project(self):
        self.fail_on = "2 b.wav"
        job = self.run_job(*self.send([("1 a.wav", wav_bytes(1.0)), ("2 b.wav", wav_bytes(1.0)), ("3 c.wav", wav_bytes(1.0))]))
        self.assertEqual(job["status"], "error")
        self.assertIn("2 b.wav", job["error"])
        self.assertIn("1 a.wav", job["error"])               # уже загруженные названы
        self.assertEqual(self.writes, [])
        self.assertEqual(history.list_versions(app.history_dir("move", OID)), [])
