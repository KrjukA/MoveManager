import copy
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path

import app
from midi import clip_to_midi, midi_to_notes
from tests.test_clips import song

OID = "aa98954a-8822-4a82-92d4-10529d5ca3a9"


class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._saved = {k: getattr(app, k) for k in ("APP_DIR", "ssh_enabled", "ssh_read_song", "ssh_write_song",
                                                    "set_by_id", "save_config")}
        self._lib = app.CFG.get("library")
        app.CFG["library"] = str(self.tmp / "lib")
        app.APP_DIR = self.tmp
        app.save_config = lambda: None
        d = self.tmp / "lib" / "Demo"
        d.mkdir(parents=True)
        with zipfile.ZipFile(d / "Demo.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(song()))
            z.writestr("Samples/kick.wav", b"RIFF")
        self.move_song = song()
        self.writes = []
        app.ssh_enabled = lambda: True
        app.ssh_read_song = lambda oid: copy.deepcopy(self.move_song)
        app.ssh_write_song = lambda oid, payload: self.writes.append(json.loads(payload))
        app.set_by_id = lambda oid: {"objectId": oid, "name": "Live Set"}

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(app, k, v)
        app.CFG["library"] = self._lib

    def req(self, method, path, data=None):
        r = urllib.request.Request(self.base + path, data=data, method=method)
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                return resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()

    def wait_job(self, body):
        jid = json.loads(body)["id"]
        for _ in range(100):
            _, _, b = self.req("GET", f"/api/jobs/{jid}")
            job = json.loads(b)
            if job["status"] != "running":
                return job
            time.sleep(0.05)
        self.fail("задача не завершилась")

    def lib_song(self):
        with zipfile.ZipFile(self.tmp / "lib" / "Demo" / "Demo.ablbundle") as z:
            return json.loads(z.read("Song.abl")), z.namelist()

    def midi_file(self):
        c = {"timeSignature": {"upper": 4, "lower": 4},
             "region": {"start": 0, "end": 8, "loop": {"start": 0, "end": 8, "isEnabled": True}},
             "notes": [{"noteNumber": 60, "startTime": 0.0, "duration": 1.0, "velocity": 90.0},
                       {"noteNumber": 64, "startTime": 6.0, "duration": 1.5, "velocity": 70.0}]}
        return clip_to_midi(c, 120.0)

    def test_export_from_library(self):
        status, headers, body = self.req("GET", "/api/library/Demo/clip.mid?track=0&scene=0")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "audio/midi")
        self.assertIn("attachment", headers["Content-Disposition"])
        notes, length = midi_to_notes(body)
        self.assertEqual([(n["noteNumber"], n["startTime"]) for n in notes], [(36, 0.0), (36, 1.0), (36, 2.0)])
        self.assertEqual(length, 4.0)

    def test_export_empty_cell(self):
        status, _, body = self.req("GET", "/api/library/Demo/clip.mid?track=0&scene=1")
        self.assertEqual(status, 400)
        self.assertIn("Ячейка пуста", json.loads(body)["message"])

    def test_import_into_library(self):
        status, _, _ = self.req("POST", "/api/library/Demo/clip?track=0&scene=1&replace=0", self.midi_file())
        self.assertEqual(status, 200)
        s, names = self.lib_song()
        self.assertEqual(app.parse_song(s)["clips"][0][1], {"notes": 2, "length": 8.0})
        self.assertIn("Samples/kick.wav", names)

    def test_import_busy_needs_replace(self):
        status, _, body = self.req("POST", "/api/library/Demo/clip?track=0&scene=0&replace=0", self.midi_file())
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["error"], "busy")
        self.assertEqual(app.parse_song(self.lib_song()[0])["clips"][0][0]["notes"], 3)
        status, _, _ = self.req("POST", "/api/library/Demo/clip?track=0&scene=0&replace=1", self.midi_file())
        self.assertEqual(status, 200)
        self.assertEqual(app.parse_song(self.lib_song()[0])["clips"][0][0]["notes"], 2)

    def test_import_broken_file(self):
        status, _, body = self.req("POST", "/api/library/Demo/clip?track=0&scene=1", b"not midi at all")
        self.assertEqual(status, 400)
        self.assertIn("MIDI", json.loads(body)["message"])

    def test_import_into_move(self):
        status, _, body = self.req("POST", f"/api/move/sets/{OID}/clip?track=0&scene=1&replace=0", self.midi_file())
        self.assertEqual(status, 200)
        job = self.wait_job(body)
        self.assertEqual(job["status"], "done", job.get("error"))
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(app.parse_song(self.writes[0])["clips"][0][1], {"notes": 2, "length": 8.0})
        self.assertEqual(len(list((self.tmp / "backups").glob("Live Set *.abl"))), 1)

    def test_import_into_move_busy(self):
        status, _, body = self.req("POST", f"/api/move/sets/{OID}/clip?track=0&scene=0&replace=0", self.midi_file())
        self.assertEqual(status, 409)
        self.assertEqual(self.writes, [])

    def test_import_into_move_without_ssh(self):
        app.ssh_enabled = lambda: False
        status, _, body = self.req("POST", f"/api/move/sets/{OID}/clip?track=0&scene=1", self.midi_file())
        self.assertEqual(status, 400)
        self.assertIn("управлении пэдами", json.loads(body)["message"])

    def test_export_from_move(self):
        status, _, body = self.req("GET", f"/api/move/sets/{OID}/clip.mid?track=0&scene=0")
        self.assertEqual(status, 200)
        self.assertEqual(len(midi_to_notes(body)[0]), 3)


if __name__ == "__main__":
    unittest.main()
