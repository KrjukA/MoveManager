import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

import app

OID = "11111111-2222-3333-4444-555555555555"
B4 = "Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav"


def song(uri):
    return json.dumps({"tracks": [{"devices": [{"kind": "drumRack", "chains": [{"devices": [
        {"kind": "drumCell", "deviceData": {"sampleUri": uri}}, {"kind": "drumCell", "deviceData": {"sampleUri": uri}}]}]}]}]}, indent=2)


class Device(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.lib, self.sw = self.root / "UserLibrary", self.root / "schwung"
        self._saved = (app.USERLIB_DIR, app.SCHWUNG_DIR, app.DATA_DIR, os.environ.get("MOVE_SSH_CMD"))
        app.USERLIB_DIR, app.SCHWUNG_DIR, app.DATA_DIR = str(self.lib), str(self.sw), self.root / "app"
        (self.root / "app").mkdir()
        os.environ["MOVE_SSH_CMD"] = "sh -c"
        app.USERLIB_CACHE.clear()
        uri = "ableton:/user-library/Samples/Bounces/Set%2093%20Bounce%204%20-%20100%20bpm.wav"
        for rel, data in [(B4, b"RIFFb4"), ("Samples/Bounces/sub/deep.wav", b"RIFFdeep"), ("Samples/Other/unused.wav", b"RIFFu"),
                          ("Samples/Other/taken.wav", b"RIFFt")]:
            p = self.lib / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        s = self.lib / "Sets" / OID / "Slow Dreamy IDM"; s.mkdir(parents=True); (s / "Song.abl").write_text(song(uri))
        pr = self.lib / "Track Presets" / "Drums"; pr.mkdir(parents=True)
        (pr / "Kit.ablpreset").write_text(json.dumps({"kind": "drumCell", "deviceData": {"sampleUri": uri}}))
        w = self.sw / "set_state" / OID; w.mkdir(parents=True)
        (w / "slot_0.json").write_text(json.dumps({"synth": {"file": "/data/UserData/UserLibrary/" + B4}}))

    def tearDown(self):
        app.USERLIB_DIR, app.SCHWUNG_DIR, app.DATA_DIR = self._saved[:3]
        if self._saved[3] is None:
            os.environ.pop("MOVE_SSH_CMD", None)
        else:
            os.environ["MOVE_SSH_CMD"] = self._saved[3]
        for p in self.root.rglob("*"):
            try: os.chmod(p, 0o755 if p.is_dir() else 0o644)
            except OSError: pass

    def stage(self, *a, **k):
        pass

    def test_tree(self):
        t = app.lib_tree("samples")
        self.assertIn("Samples/Bounces/sub", t["folders"])
        self.assertEqual({f["rel"]: f["size"] for f in t["files"]}[B4], 6)

    def test_index_sees_project_preset_and_schwung(self):
        idx = app.userlib_index()
        users = idx["refs"][B4]
        self.assertEqual(len(users), 3)
        self.assertEqual(idx["projects"][f"{app.USERLIB_DIR}/Sets/{OID}/Slow Dreamy IDM/Song.abl"], "Slow Dreamy IDM")

    def test_move_folder_rewrites_everything(self):
        plan = app.userlib_plan("samples", [("Samples/Bounces", "Samples/Resamples/Bounces")])
        self.assertEqual(plan["conflicts"], [])
        res = app.apply_userlib_plan(plan, self.stage)
        self.assertEqual(res["moved"], 2)
        self.assertTrue((self.lib / "Samples/Resamples/Bounces/Set 93 Bounce 4 - 100 bpm.wav").exists())
        self.assertTrue((self.lib / "Samples/Resamples/Bounces/sub/deep.wav").exists())
        self.assertFalse((self.lib / B4).exists())
        s = (self.lib / "Sets" / OID / "Slow Dreamy IDM" / "Song.abl").read_text()
        self.assertEqual(s.count("Samples/Resamples/Bounces/Set%2093%20Bounce%204"), 2)
        self.assertIn("Resamples/Bounces", (self.lib / "Track Presets/Drums/Kit.ablpreset").read_text())
        self.assertIn("/data/UserData/UserLibrary/Samples/Resamples/Bounces/Set 93", (self.sw / "set_state" / OID / "slot_0.json").read_text())
        backups = list((self.root / "app" / "backups").glob("samples-*/manifest.json"))
        self.assertEqual(len(backups), 1)

    def test_failure_rolls_back(self):
        plan = app.userlib_plan("samples", [(B4, "Samples/Other/new name.wav")])
        preset = self.lib / "Track Presets/Drums/Kit.ablpreset"
        before = {p: p.read_text() for p in (preset, self.lib / "Sets" / OID / "Slow Dreamy IDM" / "Song.abl")}
        real = app.ssh_run
        def failing(script, data=None, timeout=40):            # запись пресета не удастся
            if "Kit.ablpreset" in script and ".mmtmp" in script:
                raise app.SshError("SSH: disk full")
            return real(script, data=data, timeout=timeout)
        app.ssh_run = failing
        try:
            with self.assertRaises(app.AppError):
                app.apply_userlib_plan(plan, self.stage)
        finally:
            app.ssh_run = real
        self.assertTrue((self.lib / B4).exists())
        self.assertFalse((self.lib / "Samples/Other/new name.wav").exists())
        for p, text in before.items():
            self.assertEqual(p.read_text(), text)

    def test_conflict_and_bad_paths(self):
        self.assertEqual(app.userlib_plan("samples", [(B4, "Samples/Other/taken.wav")])["conflicts"], ["Samples/Other/taken.wav"])
        with self.assertRaises(app.AppError):
            app.userlib_plan("samples", [(B4, "Track Presets/x.wav")])           # вне своего режима
        with self.assertRaises(app.AppError):
            app.userlib_plan("samples", [("Samples/../x", "Samples/y")])

    def test_delete_only_unused(self):
        with self.assertRaises(app.AppError):
            app.userlib_delete("samples", [B4])
        app.userlib_delete("samples", ["Samples/Other/unused.wav"])
        self.assertFalse((self.lib / "Samples/Other/unused.wav").exists())

    def test_upload_and_folder(self):
        app.userlib_mkdir("samples", "Samples/New Folder")
        self.assertTrue((self.lib / "Samples/New Folder").is_dir())
        a = app.userlib_upload("samples", "Samples/Other", "taken.wav", b"RIFFnew")
        self.assertEqual(a, "Samples/Other/taken 2.wav")
        self.assertEqual((self.lib / a).read_bytes(), b"RIFFnew")
        with self.assertRaises(app.AppError):
            app.userlib_upload("samples", "Samples/Other", "../evil.wav", b"x")

    def test_read_file(self):
        self.assertEqual(app.userlib_read("samples", B4), b"RIFFb4")


if __name__ == "__main__":
    unittest.main()


from tests.test_routes_midi import RouteBase  # noqa: E402


class Routes(RouteBase):
    def setUp(self):
        super().setUp()
        self.dev = Device("test_tree")
        self.dev.setUp()

    def tearDown(self):
        self.dev.tearDown()
        super().tearDown()

    def js(self, method, path, obj=None):
        st, _, b = self.req(method, path, json.dumps(obj).encode() if obj is not None else None)
        return st, (json.loads(b) if b and b[:1] in (b"{", b"[") else b)

    def test_tree_with_uses(self):
        st, d = self.js("GET", "/api/userlib?mode=samples")
        self.assertEqual(st, 200)
        f = {x["rel"]: x for x in d["files"]}
        self.assertEqual(sorted(u["kind"] for u in f[B4]["used"]), ["preset", "project", "schwung"])
        self.assertEqual(f["Samples/Other/unused.wav"]["used"], [])
        self.assertIn({"kind": "project", "name": "Slow Dreamy IDM"}, f[B4]["used"])

    def test_plan_apply_and_file(self):
        st, plan = self.js("POST", "/api/userlib/plan", {"mode": "samples", "moves": [[B4, "Samples/Other/Slow Dreamy IDM - Bounce 4.wav"]]})
        self.assertEqual(st, 200)
        self.assertEqual(plan["projects"], ["Slow Dreamy IDM"])
        st, job = self.js("POST", "/api/userlib/apply", {"mode": "samples", "moves": [[B4, "Samples/Other/Slow Dreamy IDM - Bounce 4.wav"]]})
        job = self.wait_job(json.dumps(job).encode())
        self.assertEqual(job["status"], "done", job)
        st, data = self.js("GET", "/api/userlib/file?mode=samples&rel=" + urllib.parse.quote("Samples/Other/Slow Dreamy IDM - Bounce 4.wav"))
        self.assertEqual((st, data), (200, b"RIFFb4"))

    def test_bad_requests(self):
        st, _ = self.js("GET", "/api/userlib?mode=etc")
        self.assertEqual(st, 400)
        st, _ = self.js("POST", "/api/userlib/plan", {"mode": "samples", "moves": [["Samples/../../x", "Samples/y"]]})
        self.assertEqual(st, 400)
        app.ssh_enabled = lambda: False
        st, d = self.js("GET", "/api/userlib?mode=samples")
        self.assertIn("pad control", d["message"])


import urllib.parse  # noqa: E402
