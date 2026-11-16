import copy
import json
import zipfile

import app
from tests.test_clips import song
from tests.test_routes_midi import OID, RouteBase


class RemoveClip(RouteBase):
    def test_remove_clip_function(self):
        s = song()
        app.remove_clip(s, 0, 0)
        self.assertIsNone(s["tracks"][0]["clipSlots"][0]["clip"])
        self.assertTrue(s["tracks"][0]["clipSlots"][0]["hasStop"])
        with self.assertRaises(app.AppError):
            app.remove_clip(s, 0, 1)                    # уже пусто

    def test_delete_library(self):
        st, _, _ = self.req("DELETE", "/api/library/Demo/clip?track=0&scene=0")
        self.assertEqual(st, 200)
        with zipfile.ZipFile(self.tmp / "lib" / "Demo" / "Demo.ablbundle") as z:
            s = json.loads(z.read("Song.abl"))
            self.assertIn("Samples/kick.wav", z.namelist())
        self.assertIsNone(s["tracks"][0]["clipSlots"][0]["clip"])

    def test_delete_move_with_backup(self):
        st, _, b = self.req("DELETE", f"/api/move/sets/{OID}/clip?track=0&scene=0")
        self.assertEqual(st, 200)
        job = self.wait_job(b)
        self.assertEqual(job["status"], "done", job)
        self.assertIsNone(self.writes[-1]["tracks"][0]["clipSlots"][0]["clip"])
        self.assertEqual(len(list((self.tmp / "history" / "move" / OID).glob("*.abl"))), 1)   # сборка 52: история вместо backups/

    def test_delete_move_needs_ssh(self):
        app.ssh_enabled = lambda: False
        st, _, b = self.req("DELETE", f"/api/move/sets/{OID}/clip?track=0&scene=0")
        self.assertEqual(st, 400)
