import json
import time

import app
from tests.test_routes_drumgen import drum_song
from tests.test_routes_midi import RouteBase


class MineScan(RouteBase):
    def setUp(self):
        super().setUp()
        import zipfile
        d = self.tmp / "lib" / "Kit"
        d.mkdir()
        with zipfile.ZipFile(d / "Kit.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(drum_song()))
        self._rs = app.read_song
        self.reads = []

    def tearDown(self):
        for _ in range(100):                     # фоновый разбор не должен перейти в следующий тест
            if not app.MINE_STATE["running"]:
                break
            time.sleep(0.05)
        app.read_song = self._rs
        super().tearDown()

    def slow_read(self, path):
        self.reads.append(str(path)); time.sleep(1.5); return self._rs(path)

    def wait_ready(self):
        for _ in range(100):
            st, _, b = self.req("GET", "/api/drumgen/patterns")
            d = json.loads(b)
            if d["mine"]["ready"]:
                return d
            time.sleep(0.1)
        self.fail("scan never finished")

    def test_patterns_answer_at_once_while_projects_are_read(self):
        app.read_song = self.slow_read
        t = time.time()
        st, _, b = self.req("GET", "/api/drumgen/patterns")
        d = json.loads(b)
        self.assertLess(time.time() - t, 1.0)
        self.assertFalse(d["mine"]["ready"])
        self.assertTrue(any(p["source"] == "pocket" for p in d["patterns"]))
        d = self.wait_ready()
        self.assertTrue(any(p["source"] == "mine" for p in d["patterns"]))

    def test_unchanged_projects_are_not_read_again(self):
        self.wait_ready()
        self.assertTrue((app.CACHE_DIR / "mine_patterns.json").exists())
        self._idle_scan()
        app.MINE_CACHE.clear()                                  # как после перезапуска программы
        app.MINE_STATE.update({"running": False, "ready": False})
        app.read_song = self.slow_read
        d = self.wait_ready()
        self.assertEqual(self.reads, [])
        self.assertTrue(any(p["source"] == "mine" for p in d["patterns"]))

    def test_group_change_without_rereading(self):
        self.wait_ready()
        self._idle_scan()
        (self.tmp / "lib" / "Kit" / "meta.json").write_text(json.dumps({"group": "Live"}))
        app.MINE_STATE.update({"ready": False})
        app.read_song = self.slow_read
        d = self.wait_ready()
        self.assertEqual(self.reads, [])
        self.assertTrue(any(p["source"] == "mine" and p["genre"].startswith("Live") for p in d["patterns"]))
