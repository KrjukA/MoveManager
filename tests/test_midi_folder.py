import struct
import tempfile
import unittest
from pathlib import Path

import app
import drumgen
from tests.test_drumgen_data import Data  # noqa: F401 — данные эталонов грузятся
from tests.test_midi import smf, track


def drum_file(path, notes):
    events = sorted([(t, 1, p) for t, p in notes] + [(t + 60, 0, p) for t, p in notes])
    ev, last = [], 0
    for tick, on, pitch in events:
        ev.append((tick - last, bytes([0x99 if on else 0x89, pitch, 100 if on else 0])))
        last = tick
    path.write_bytes(smf([track(ev)]))


class MidiFolder(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "Jungle").mkdir()
        drum_file(self.root / "Jungle" / "amen.mid", [(0, 36), (480, 38), (960, 36), (1440, 38)] + [(i * 240, 42) for i in range(8)])
        drum_file(self.root / "loose.MID", [(0, 36), (960, 40)])
        (self.root / "notes.txt").write_text("x")
        (self.root / "broken.mid").write_bytes(b"MThd garbage")

    def test_patterns_from_folder(self):
        pats = app.midi_folder_patterns(str(self.root))
        by = {p["name"]: p for p in pats}
        self.assertEqual(set(by), {"amen", "loose"})
        amen = by["amen"]
        self.assertEqual(amen["genre"], "Jungle")
        self.assertEqual(amen["source"], "midi")
        self.assertEqual([i for i, v in enumerate(amen["hits"]["kick"]) if v], [0, 8])
        self.assertEqual([i for i, v in enumerate(amen["hits"]["snare"]) if v], [4, 12])
        self.assertEqual(sum(1 for v in amen["hits"]["chh"] if v), 8)
        self.assertEqual(by["loose"]["genre"], "MIDI folder")

    def test_my_genres_not_merged_with_builtin(self):
        mine = [{"id": "mine:x", "name": "x", "genre": "House", "source": "mine", "steps": 16, "hits": {"kick": [0.8] + [0.0] * 15}}]
        pats = drumgen.unify_genres(drumgen.load_patterns() + mine)
        g = drumgen.genre_list(pats)
        house = [x for x in g if x["name"].startswith("House")]
        self.assertEqual(sorted(x["group"] for x in house), ["builtin", "mine"])
        self.assertTrue(all(x["name"] != y["name"] for x in house for y in house if x is not y))


if __name__ == "__main__":
    unittest.main()
