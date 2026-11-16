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


if __name__ == "__main__":
    unittest.main()
