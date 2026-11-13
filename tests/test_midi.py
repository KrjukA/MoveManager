import struct
import unittest

from midi import MidiError, clip_to_midi, midi_to_notes

PPQ = 480


def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def track(events):
    """events: список (дельта в тиках, байты события)."""
    body = b"".join(vlq(d) + e for d, e in events) + vlq(0) + b"\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(body)) + body


def smf(tracks, fmt=0, division=PPQ):
    return b"MThd" + struct.pack(">IHHh", 6, fmt, len(tracks), division) + b"".join(tracks)


def clip(notes, start=0.0, end=4.0, loop=True):
    region = {"start": start, "end": end}
    region["loop"] = {"start": start, "end": end, "isEnabled": True} if loop else None
    return {"timeSignature": {"upper": 4, "lower": 4}, "region": region,
            "notes": [{"noteNumber": p, "startTime": t, "duration": d, "velocity": v, "offVelocity": 0.0}
                      for p, t, d, v in notes]}


class MidiTests(unittest.TestCase):
    def test_roundtrip(self):
        data = clip_to_midi(clip([(36, 0.0, 0.25, 100.0), (38, 1.0, 0.5, 64.4), (42, 3.5, 0.5, 127.0)]), 120.0, "T1")
        notes, length = midi_to_notes(data)
        self.assertEqual([(n["noteNumber"], n["startTime"], n["duration"]) for n in notes],
                         [(36, 0.0, 0.25), (38, 1.0, 0.5), (42, 3.5, 0.5)])
        self.assertEqual([n["velocity"] for n in notes], [100, 64, 127])
        self.assertEqual(notes[0]["offVelocity"], 0.0)
        self.assertNotIn("automations", notes[0])
        self.assertEqual(length, 4.0)

    def test_loop_offset(self):
        c = clip([(36, 2.0, 0.5, 100.0), (40, 5.0, 0.5, 100.0)], start=0.0, end=8.0)
        c["region"]["loop"] = {"start": 4.0, "end": 8.0, "isEnabled": True}
        notes, length = midi_to_notes(clip_to_midi(c, 120.0))
        self.assertEqual([(n["noteNumber"], n["startTime"]) for n in notes], [(40, 1.0)])
        self.assertEqual(length, 4.0)

    def test_velocity_zero_is_note_off(self):
        data = smf([track([(0, b"\x90\x3c\x64"), (PPQ, b"\x90\x3c\x00")])])
        notes, _ = midi_to_notes(data)
        self.assertEqual([(n["noteNumber"], n["startTime"], n["duration"]) for n in notes], [(60, 0.0, 1.0)])

    def test_running_status(self):
        # второе и третье событие без статус-байта
        data = smf([track([(0, b"\x90\x3c\x64"), (PPQ, b"\x3c\x00"), (0, b"\x3e\x50"), (PPQ // 2, b"\x80\x3e\x00")])])
        notes, _ = midi_to_notes(data)
        self.assertEqual([(n["noteNumber"], n["startTime"], n["duration"], n["velocity"]) for n in notes],
                         [(60, 0.0, 1.0, 100), (62, 1.0, 0.5, 80)])

    def test_unmatched_off_ignored(self):
        data = smf([track([(0, b"\x80\x40\x00"), (0, b"\x90\x3c\x64"), (PPQ, b"\x80\x3c\x00")])])
        notes, _ = midi_to_notes(data)
        self.assertEqual([n["noteNumber"] for n in notes], [60])

    def test_unclosed_note_ends_at_last_event(self):
        data = smf([track([(0, b"\x90\x3c\x64"), (0, b"\x90\x3e\x64"), (PPQ, b"\x80\x3e\x00"), (PPQ, b"\xb0\x07\x64")])])
        notes, length = midi_to_notes(data)
        by = {n["noteNumber"]: n for n in notes}
        self.assertEqual(by[60]["duration"], 2.0)
        self.assertEqual(length, 2.0)

    def test_type1_merged(self):
        t1 = track([(PPQ, b"\x90\x3c\x64"), (PPQ, b"\x80\x3c\x00")])
        t2 = track([(0, b"\x91\x24\x64"), (PPQ // 2, b"\x81\x24\x00")])
        notes, _ = midi_to_notes(smf([t1, t2], fmt=1))
        self.assertEqual([(n["noteNumber"], n["startTime"]) for n in notes], [(36, 0.0), (60, 1.0)])

    def test_no_notes_raises(self):
        with self.assertRaises(MidiError):
            midi_to_notes(smf([track([(0, b"\xff\x51\x03\x07\xa1\x20")])]))

    def test_smpte_raises(self):
        with self.assertRaises(MidiError):
            midi_to_notes(smf([track([(0, b"\x90\x3c\x64")])], division=-7680))

    def test_garbage_raises(self):
        with self.assertRaises(MidiError):
            midi_to_notes(b"hello")


if __name__ == "__main__":
    unittest.main()
