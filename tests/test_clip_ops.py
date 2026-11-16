"""Сборка 51: копия, перенос и обмен клипов внутри проекта."""
import copy
import unittest

import app
from app import AppError, CellBusy, clip_op, parse_song, track_clip_kind
from tests.test_clips import NOTES, song as base_song


def song():
    """Дорожки: 0 — мелодия (Drift, клип в сцене 0), 1 — аудио, 2 — ударные (клип в сцене 1), 3 — мелодия без устройств."""
    s = base_song()
    s["tracks"][0]["devices"] = [{"kind": "drift"}]
    s["tracks"][0]["clipSlots"][0]["clip"].update({"name": "Lead", "color": 7,
                                                    "envelopes": [{"parameterId": 1, "points": [0, 1]}]})
    drum_clip = copy.deepcopy(s["tracks"][0]["clipSlots"][0]["clip"])
    drum_clip.update({"name": "Beat", "notes": copy.deepcopy(NOTES[:1]), "envelopes": []})
    s["tracks"].append({"kind": "midi", "devices": [{"kind": "drumRack"}], "mixer": {"pan": 0.0},
                        "clipSlots": [{"hasStop": True, "clip": None}, {"hasStop": True, "clip": drum_clip}]})
    s["tracks"].append({"kind": "midi", "devices": [], "mixer": {"pan": 0.0},
                        "clipSlots": [{"hasStop": True, "clip": None}, {"hasStop": True, "clip": None}]})
    return s


def cell(s, t, sc):
    return s["tracks"][t]["clipSlots"][sc]["clip"]


class Kinds(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual([t["clipKind"] for t in parse_song(song())["tracks"]],
                         ["melodic", "audio", "drums", "melodic"])

    def test_drum_rack_inside_rack(self):
        tr = {"kind": "midi", "devices": [{"kind": "instrumentRack", "chains": [{"devices": [{"kind": "drumRack"}]}]}]}
        self.assertEqual(track_clip_kind(tr), "drums")


class ClipOp(unittest.TestCase):
    def test_copy_full_clip(self):
        s = song()
        src = copy.deepcopy(cell(s, 0, 0))
        clip_op(s, "copy", (0, 0), (0, 1))
        new = cell(s, 0, 1)
        for k in ("notes", "color", "name", "grooveId", "envelopes", "region"):
            self.assertEqual(new[k], src[k], k)
        self.assertIs(new["isPlaying"], False)
        self.assertEqual(cell(s, 0, 0), src)                     # исходник не тронут
        self.assertIsNot(new, cell(s, 0, 0))
        self.assertIsNot(new["notes"], cell(s, 0, 0)["notes"])

    def test_copy_to_other_melodic_track(self):
        s = song()
        clip_op(s, "copy", (0, 0), (3, 1))
        self.assertEqual(cell(s, 3, 1)["name"], "Lead")

    def test_move(self):
        s = song()
        clip_op(s, "move", (0, 0), (3, 0))
        self.assertIsNone(cell(s, 0, 0))
        self.assertTrue(s["tracks"][0]["clipSlots"][0]["hasStop"])
        self.assertEqual(cell(s, 3, 0)["name"], "Lead")
        self.assertIs(cell(s, 3, 0)["isPlaying"], False)

    def test_swap_both_full(self):
        s = song()
        clip_op(s, "copy", (0, 0), (3, 1))
        cell(s, 3, 1)["name"] = "Other"
        clip_op(s, "swap", (0, 0), (3, 1))
        self.assertEqual(cell(s, 0, 0)["name"], "Other")
        self.assertEqual(cell(s, 3, 1)["name"], "Lead")

    def test_swap_with_empty_is_move(self):
        s = song()
        clip_op(s, "swap", (0, 0), (0, 1))
        self.assertIsNone(cell(s, 0, 0))
        self.assertEqual(cell(s, 0, 1)["name"], "Lead")
        s = song()
        clip_op(s, "swap", (0, 1), (0, 0))                       # пустой источник, полная цель
        self.assertIsNone(cell(s, 0, 0))
        self.assertEqual(cell(s, 0, 1)["name"], "Lead")

    def test_busy(self):
        s = song()
        clip_op(s, "copy", (0, 0), (3, 1))
        for op in ("copy", "move"):
            with self.assertRaises(CellBusy):
                clip_op(s, op, (0, 0), (3, 1))
        cell(s, 0, 0)["name"] = "New"
        clip_op(s, "copy", (0, 0), (3, 1), replace=True)
        self.assertEqual(cell(s, 3, 1)["name"], "New")
        self.assertTrue(issubclass(CellBusy, AppError))

    def test_rules(self):
        for op, a, b in [("copy", (0, 0), (2, 0)),      # мелодия → ударные
                         ("move", (2, 1), (0, 1)),      # ударные → мелодия
                         ("copy", (0, 0), (1, 1)),      # → аудио
                         ("swap", (0, 0), (2, 0)),      # обмен с пустой ячейкой ударных
                         ("swap", (2, 1), (3, 0))]:     # ударные → мелодия обменом
            s = song()
            before = copy.deepcopy(s)
            with self.assertRaises(AppError, msg=(op, a, b)):
                clip_op(s, op, a, b)
            self.assertEqual(s, before, (op, a, b))

    def test_audio_source_refused(self):
        s = song()
        s["tracks"][1]["clipSlots"][0]["clip"] = {"name": "loop"}
        with self.assertRaises(AppError):
            clip_op(s, "copy", (1, 0), (1, 1))

    def test_errors(self):
        s = song()
        for op, a, b in [("copy", (0, 1), (3, 0)),      # пустой источник
                         ("move", (0, 0), (0, 0)),      # та же ячейка
                         ("swap", (0, 1), (3, 0)),      # обе пустые
                         ("copy", (9, 0), (0, 1)),
                         ("copy", (0, 0), (0, 9)),
                         ("paste", (0, 0), (0, 1))]:
            with self.assertRaises(AppError, msg=(op, a, b)):
                clip_op(s, op, a, b)



import json  # noqa: E402
import zipfile  # noqa: E402

from tests.test_routes_midi import OID, RouteBase  # noqa: E402


class Routes(RouteBase):
    def setUp(self):
        super().setUp()
        with zipfile.ZipFile(self.tmp / "lib" / "Demo" / "Demo.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(song()))
            z.writestr("Samples/kick.wav", b"RIFF")
        self.move_song = song()

    def op(self, where, op, a, b, replace=False):
        body = json.dumps({"op": op, "from": list(a), "to": list(b), "replace": replace}).encode()
        return self.req("POST", f"{where}/clip-op", body)

    def test_library_swap(self):
        s = self.lib_song()[0]
        clip_op(s, "copy", (0, 0), (3, 1))
        with zipfile.ZipFile(self.tmp / "lib" / "Demo" / "Demo.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(s))
            z.writestr("Samples/kick.wav", b"RIFF")
        s2 = self.lib_song()[0]
        s2["tracks"][3]["clipSlots"][1]["clip"]["name"] = "Other"
        with zipfile.ZipFile(self.tmp / "lib" / "Demo" / "Demo.ablbundle", "w") as z:
            z.writestr("Song.abl", json.dumps(s2))
            z.writestr("Samples/kick.wav", b"RIFF")
        st, _, b = self.op("/api/library/Demo", "swap", (0, 0), (3, 1))
        self.assertEqual(st, 200, b)
        s, names = self.lib_song()
        self.assertEqual(cell(s, 0, 0)["name"], "Other")
        self.assertEqual(cell(s, 3, 1)["name"], "Lead")
        self.assertIn("Samples/kick.wav", names)

    def test_library_busy_409(self):
        st, _, _ = self.op("/api/library/Demo", "copy", (0, 0), (3, 0))
        self.assertEqual(st, 200)
        before = self.lib_song()[0]
        st, _, b = self.op("/api/library/Demo", "copy", (0, 0), (3, 0))
        self.assertEqual(st, 409)
        self.assertEqual(json.loads(b)["error"], "busy")
        self.assertEqual(self.lib_song()[0], before)
        st, _, _ = self.op("/api/library/Demo", "move", (0, 0), (3, 0), replace=True)
        self.assertEqual(st, 200)
        self.assertIsNone(cell(self.lib_song()[0], 0, 0))

    def test_library_rule_400(self):
        st, _, b = self.op("/api/library/Demo", "copy", (0, 0), (2, 0))
        self.assertEqual(st, 400)
        self.assertIn("melodic", json.loads(b)["message"])

    def test_move_single_write_and_backup(self):
        st, _, b = self.op(f"/api/move/sets/{OID}", "move", (0, 0), (3, 1))
        self.assertEqual(st, 200, b)
        job = self.wait_job(b)
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(len(self.writes), 1)
        self.assertIsNone(cell(self.writes[0], 0, 0))
        self.assertEqual(cell(self.writes[0], 3, 1)["name"], "Lead")
        self.assertEqual(len(list((self.tmp / "history" / "move" / OID).glob("*.abl"))), 1)   # сборка 52: история вместо backups/

    def test_move_busy_and_rule_refused_before_job(self):
        self.move_song["tracks"][3]["clipSlots"][1]["clip"] = copy.deepcopy(cell(self.move_song, 0, 0))
        st, _, _ = self.op(f"/api/move/sets/{OID}", "copy", (0, 0), (3, 1))
        self.assertEqual(st, 409)
        st, _, _ = self.op(f"/api/move/sets/{OID}", "copy", (0, 0), (2, 0))
        self.assertEqual(st, 400)
        self.assertEqual(self.writes, [])

    def test_move_needs_ssh(self):
        app.ssh_enabled = lambda: False
        st, _, _ = self.op(f"/api/move/sets/{OID}", "swap", (0, 0), (3, 1))
        self.assertEqual(st, 400)
        self.assertEqual(self.writes, [])

    def test_bad_body(self):
        st, _, _ = self.req("POST", "/api/library/Demo/clip-op", b'{"op":"copy","from":[0],"to":"x"}')
        self.assertEqual(st, 400)


class StaleCache(unittest.TestCase):
    def test_info_without_clip_kind_is_stale(self):
        info = parse_song(song())
        self.assertFalse(app.stale_info(info))
        del info["tracks"][0]["clipKind"]
        self.assertTrue(app.stale_info(info))
        app.INFO_CACHE["x-51"] = {"stamp": "s1", "info": info}
        try:
            self.assertIsNone(app.cached_info("x-51", "s1"))
        finally:
            app.INFO_CACHE.pop("x-51", None)


if __name__ == "__main__":
    unittest.main()
