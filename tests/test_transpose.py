"""Сборка 66: при смене тональности ноты мелодических клипов и транспонирование лупов сдвигаются; Drum Rack — никогда."""
import copy
import unittest

import app


def song(melodic=(45, 52, 125), audio_tr=0):
    def clip(notes):
        return {"clip": {"notes": [{"noteNumber": n, "startTime": 0.0, "duration": 1.0, "velocity": 100.0} for n in notes],
                         "region": {"start": 0.0, "end": 4.0}}}
    return {"rootNote": 9, "scale": "Minor", "tempo": 120, "tracks": [
        {"kind": "midi", "devices": [{"kind": "wavetable"}], "clipSlots": [clip(melodic), {"clip": None}]},
        {"kind": "midi", "devices": [{"kind": "drumRack"}], "clipSlots": [clip([36])]},
        {"kind": "audio", "devices": [], "clipSlots": [{"clip": {"sampleUri": "ableton:/user-library/Samples/a.wav",
                                                                  "transpose": audio_tr, "region": {"start": 0, "end": 4}}}]},
    ]}


def notes(s, t=0):
    return [n["noteNumber"] for n in s["tracks"][t]["clipSlots"][0]["clip"]["notes"]]


class Transpose(unittest.TestCase):
    def test_shift_moves_melodic_and_audio(self):
        s = app.edit_song(song(), key={"rootNote": 4, "scale": "Minor", "shift": -5})
        self.assertEqual(notes(s), [40, 47, 120])
        self.assertEqual(notes(s, 1), [36])
        self.assertEqual(s["tracks"][2]["clipSlots"][0]["clip"]["transpose"], -5)
        self.assertEqual(s["rootNote"], 4)

    def test_fold_into_range(self):
        self.assertEqual(notes(app.edit_song(song((125,)), key={"rootNote": 4, "scale": "Minor", "shift": 7})), [120])
        self.assertEqual(notes(app.edit_song(song((2,)), key={"rootNote": 4, "scale": "Minor", "shift": -5})), [9])

    def test_audio_transpose_fold(self):
        s = app.edit_song(song(audio_tr=45), key={"rootNote": 4, "scale": "Minor", "shift": 7})
        self.assertEqual(s["tracks"][2]["clipSlots"][0]["clip"]["transpose"], 40)

    def test_clip_without_notes(self):
        s = song()
        del s["tracks"][0]["clipSlots"][0]["clip"]["notes"]
        app.edit_song(s, key={"rootNote": 4, "scale": "Minor", "shift": -5})

    def test_bad_shift(self):
        for key in ({"rootNote": 4, "scale": "Minor", "shift": 12}, {"tempo": 120, "shift": 3},
                    {"rootNote": 4, "scale": "Minor", "shift": "x"}):
            with self.assertRaises(app.AppError):
                app.edit_song(song(), key=key)

    def test_no_shift_keeps_notes(self):
        s = app.edit_song(song(), key={"rootNote": 4, "scale": "Minor"})
        self.assertEqual(notes(s), [45, 52, 125])

    def test_count(self):
        self.assertEqual(app.transpose_song(song(), -5), 4)       # три ноты + один аудиоклип

    def test_action_name(self):
        self.assertEqual(app.edit_action(None, {}, {"rootNote": 4, "scale": "Minor", "shift": -5}),
                         "Key changed to E Minor, notes -5")
