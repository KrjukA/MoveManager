"""Исправления по итогам финальной проверки ветки MIDI-клипов."""
import copy
import json
import socket
import tempfile
import threading
import time
import unittest
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path

import app
from midi import midi_to_notes
from tests.test_clips import song
from tests.test_midi import PPQ, smf, track
from tests.test_routes_midi import OID


class StaleCacheTests(unittest.TestCase):
    """I1: информация, прочитанная прошлой сборкой (без clips), должна перечитываться."""

    def test_library_meta_without_clips_is_reparsed(self):
        d = Path(tempfile.mkdtemp()) / "Demo"
        d.mkdir()
        with zipfile.ZipFile(d / "Demo.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(song()))
        b = d / "Demo.ablbundle"
        stamp = f"{b.stat().st_mtime_ns}:{b.stat().st_size}"
        old = app.parse_song(song())
        del old["clips"]
        (d / "meta.json").write_text(json.dumps({"bundleStamp": stamp, "info": old}))
        self.assertEqual(app.lib_item(d)["info"]["clips"][0][0], {"notes": 3, "length": 4.0, "roll": [[0.0, 0.25, 36], [1.0, 0.25, 36], [2.0, 0.25, 36]]})

    def test_device_cache_without_clips_is_stale(self):
        old = app.parse_song(song())
        del old["clips"]
        app.INFO_CACHE["x-old"] = {"stamp": "s1", "info": old}
        self.assertIsNone(app.cached_info("x-old", "s1"))


class VelocityAndUnclosedTests(unittest.TestCase):
    """M5: velocity как в проектах Move (float); незакрытая нота — до последнего события файла."""

    def test_velocity_is_float(self):
        notes, _ = midi_to_notes(smf([track([(0, b"\x90\x3c\x64"), (PPQ, b"\x80\x3c\x00")])]))
        self.assertIsInstance(notes[0]["velocity"], float)
        self.assertEqual(notes[0]["velocity"], 100.0)

    def test_unclosed_note_ends_at_file_end(self):
        short = track([(0, b"\x90\x3c\x64")])                         # нота без конца в короткой дорожке
        long_ = track([(0, b"\x91\x24\x64"), (4 * PPQ, b"\x81\x24\x00")])
        notes, length = midi_to_notes(smf([short, long_], fmt=1))
        by = {n["noteNumber"]: n for n in notes}
        self.assertEqual(by[60]["duration"], 4.0)
        self.assertEqual(length, 4.0)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self._saved = {k: getattr(app, k) for k in ("ssh_enabled", "ssh_read_song", "ssh_write_song",
                                                    "set_by_id", "DATA_DIR")}
        app.DATA_DIR = Path(tempfile.mkdtemp())

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(app, k, v)

    def test_error_before_body_does_not_break_next_request(self):
        """M1: ответ-ошибка до чтения тела не должен ломать следующий запрос на том же соединении."""
        app.ssh_enabled = lambda: False
        body = b"MThd" + b"\x00" * 60
        s = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        s.sendall((f"POST /api/move/sets/{OID}/clip?track=0&scene=0 HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                   f"Content-Length: {len(body)}\r\n\r\n").encode() + body
                  + b"GET /api/config HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        data = b""
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                chunk = s.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        self.assertNotIn(b" 501 ", data)
        self.assertNotIn(b"Unsupported method", data)

    def test_concurrent_imports_keep_both_clips(self):
        """M2: два импорта в один проект подряд — оба клипа на месте."""
        state = {"song": song()}

        def slow_read(oid):
            s = copy.deepcopy(state["song"])
            time.sleep(0.3)
            return s

        app.ssh_enabled = lambda: True
        app.ssh_read_song = slow_read
        app.ssh_write_song = lambda oid, payload: state.__setitem__("song", json.loads(payload))
        app.set_by_id = lambda oid: {"objectId": oid, "name": "Live Set"}
        notes = [{"noteNumber": 60, "startTime": 0.0, "duration": 1.0, "velocity": 90.0, "offVelocity": 0.0}]
        state["song"]["tracks"][0]["clipSlots"].append({"hasStop": True, "clip": None})   # третья ячейка
        a = app.start_job("clip", app.job_clip_move(OID, 0, 1, notes, 4.0))
        b = app.start_job("clip", app.job_clip_move(OID, 0, 2, notes, 4.0))
        for _ in range(100):
            if a["status"] != "running" and b["status"] != "running":
                break
            time.sleep(0.05)
        self.assertEqual((a["status"], b["status"]), ("done", "done"), (a.get("error"), b.get("error")))
        grid = app.parse_song(state["song"])["clips"][0]
        self.assertIsNotNone(grid[1])
        self.assertIsNotNone(grid[2])


if __name__ == "__main__":
    unittest.main()
