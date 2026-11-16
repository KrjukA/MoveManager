import copy
import json
import zipfile

import app
from tests.test_drumgen_kit import SLOW, song_with
from tests.test_routes_midi import OID, RouteBase


def drum_song():
    s = song_with(SLOW)
    for t in s["tracks"]:
        t.update({"kind": "midi", "mixer": {"pan": 0.0}, "clipSlots": [{"hasStop": True, "clip": None} for _ in range(2)]})
    s.update({"tempo": 100.0, "rootNote": 0, "scale": "Minor", "timeSignature": {"upper": 4, "lower": 4}, "scenes": [{}, {}]})
    for i, ch in enumerate(s["tracks"][0]["devices"][0]["chains"][0]["devices"][0]["chains"]):
        dd = ch["devices"][0].get("deviceData")
        if dd:
            dd["sampleUri"] = "Samples/" + SLOW[i]
    clip = {"name": "", "color": 1, "timeSignature": {"upper": 4, "lower": 4},
            "region": {"start": 0.0, "end": 4.0, "loop": {"start": 0.0, "end": 4.0, "isEnabled": True}},
            "notes": [{"noteNumber": 36, "startTime": t, "duration": 0.25, "velocity": 100.0, "offVelocity": 0.0} for t in (0, 1, 2, 3)]
                     + [{"noteNumber": 44, "startTime": t, "duration": 0.25, "velocity": 100.0, "offVelocity": 0.0} for t in (1, 3)],
            "envelopes": []}
    s["tracks"][0]["clipSlots"][0]["clip"] = clip
    return s


class DrumgenRoutes(RouteBase):
    def setUp(self):
        super().setUp()
        d = self.tmp / "lib" / "Kit"
        d.mkdir()
        with zipfile.ZipFile(d / "Kit.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(drum_song()))
            z.writestr("Samples/bd_cleanest.wav", b"RIFFkick")
        self.move_song = drum_song()

    def js(self, method, path, obj=None):
        st, _, b = self.req(method, path, json.dumps(obj).encode() if obj is not None else None)
        return st, json.loads(b) if b else None

    def test_patterns_include_pocket_and_mine(self):
        import time
        for _ in range(100):                      # свои клипы разбираются в фоне
            st, d = self.js("GET", "/api/drumgen/patterns")
            if d["mine"]["ready"]:
                break
            time.sleep(0.05)
        self.assertEqual(st, 200)
        srcs = {p["source"] for p in d["patterns"]}
        self.assertTrue({"pocket", "basic8", "mine"} <= srcs)
        mine = [p for p in d["patterns"] if p["source"] == "mine"]
        self.assertEqual(mine[0]["genre"], "My clips")
        self.assertIn("Pocket Operations", d["credit"])

    def test_kit_and_overrides(self):
        st, d = self.js("GET", "/api/library/Kit/kit?track=1")
        self.assertIsNone(d["pads"])
        st, d = self.js("GET", "/api/library/Kit/kit?track=0")
        self.assertEqual(d["pads"][0]["role"], "kick")
        self.js("POST", "/api/library/Kit/kit?track=0", {"overrides": {"45": "clap"}})
        st, d = self.js("GET", "/api/library/Kit/kit?track=0")
        self.assertEqual({p["note"]: p["role"] for p in d["pads"]}[45], "clap")
        st, g = self.js("POST", "/api/drumgen", {"side": "lib", "id": "Kit", "track": 0, "genre": "House",
                                                  "pattern": None, "mutation": 0, "seed": 1, "bars": 1})
        self.assertEqual(st, 200)
        self.assertTrue(g["notes"])
        if "clap" in g["grid"] and any(g["grid"]["clap"]):
            self.assertIn(45, {n["noteNumber"] for n in g["notes"]})

    def test_generate_with_known_pads_does_not_read_project(self):
        st, d = self.js("GET", "/api/library/Kit/kit?track=0")
        pads = d["pads"]
        saved = app.side_song
        app.side_song = lambda side, ident: (_ for _ in ()).throw(AssertionError("project read"))
        try:
            st, g = self.js("POST", "/api/drumgen", {"side": "move", "id": OID, "track": 0, "genre": "House",
                                                      "mutation": 50, "seed": 3, "bars": 1, "pads": pads})
        finally:
            app.side_song = saved
        self.assertEqual(st, 200)
        self.assertTrue(all(36 <= n["noteNumber"] <= 51 for n in g["notes"]))

    def test_bad_pads_rejected(self):
        st, _ = self.js("POST", "/api/drumgen", {"side": "lib", "id": "Kit", "track": 0, "genre": "House",
                                                  "pads": [{"note": 99, "role": "kick"}]})
        self.assertEqual(st, 400)

    def test_move_kit_overrides_in_config(self):
        self.js("POST", f"/api/move/sets/{OID}/kit?track=0", {"overrides": {"46": "chh"}})
        self.assertEqual(app.CFG["move_meta"][OID]["kitRoles"]["0"], {"46": "chh"})

    def test_clip_notes_library(self):
        notes = [{"noteNumber": 38, "role": "snare", "startTime": 0.5, "duration": 0.25, "velocity": 90.0, "offVelocity": 0.0}]
        st, d = self.js("POST", "/api/library/Kit/clip-notes?track=0&scene=0", {"notes": notes, "length": 4})
        self.assertEqual(st, 409)
        st, d = self.js("POST", "/api/library/Kit/clip-notes?track=0&scene=1", {"notes": notes, "length": 4})
        self.assertEqual(st, 200)
        with zipfile.ZipFile(self.tmp / "lib" / "Kit" / "Kit.ablbundle") as z:
            s = json.loads(z.read("Song.abl"))
        self.assertEqual(s["tracks"][0]["clipSlots"][1]["clip"]["notes"][0]["noteNumber"], 38)
        self.assertNotIn("role", s["tracks"][0]["clipSlots"][1]["clip"]["notes"][0])

    def test_clip_notes_move(self):
        notes = [{"noteNumber": 38, "startTime": 0.0, "duration": 0.25, "velocity": 90.0, "offVelocity": 0.0}]
        st, body = self.js("POST", f"/api/move/sets/{OID}/clip-notes?track=0&scene=1", {"notes": notes, "length": 4})
        self.assertEqual(st, 200)
        job = self.wait_job(json.dumps(body).encode())
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(self.writes[-1]["tracks"][0]["clipSlots"][1]["clip"]["notes"][0]["noteNumber"], 38)
        app.ssh_enabled = lambda: False
        st, d = self.js("POST", f"/api/move/sets/{OID}/clip-notes?track=0&scene=1", {"notes": notes, "length": 4})
        self.assertIn("Import to Move needs pad control enabled", d["message"])

    def test_absurd_length_or_position_rejected(self):
        ok = [{"noteNumber": 38, "startTime": 0.0, "duration": 0.25, "velocity": 90.0}]
        st, _ = self.js("POST", "/api/library/Kit/clip-notes?track=0&scene=1", {"notes": ok, "length": 1e7})
        self.assertEqual(st, 400)
        far = [{"noteNumber": 38, "startTime": 100.0, "duration": 0.25, "velocity": 90.0}]
        st, _ = self.js("POST", "/api/library/Kit/clip-notes?track=0&scene=1", {"notes": far, "length": 8})
        self.assertEqual(st, 400)

    def test_bad_notes_rejected(self):
        notes = [{"noteNumber": 200, "startTime": 0.0, "duration": 0.25, "velocity": 90.0}]
        st, d = self.js("POST", "/api/library/Kit/clip-notes?track=0&scene=1", {"notes": notes, "length": 4})
        self.assertEqual(st, 400)

