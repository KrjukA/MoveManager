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


def mixo(notes):
    """Проект в G Mixolydian с одной мелодической дорожкой, Drum Rack и аудиоклипом."""
    s = song(tuple(notes))
    s["rootNote"], s["scale"] = 7, "Mixolydian"
    return s


class Degrees(unittest.TestCase):
    """Сборка 66: «по ступеням» — каждая нота сохраняет роль относительно тоники."""
    def deg(self, s, root, scale):
        return app.edit_song(s, key={"rootNote": root, "scale": scale, "notes": "degrees"})

    def test_mixolydian_to_minor(self):
        s = self.deg(mixo([43, 47, 50, 41, 40]), 9, "Minor")        # G B D F E
        self.assertEqual(notes(s), [45, 48, 52, 43, 41])             # A C E G F
        self.assertEqual(notes(s, 1), [36])                          # Drum Rack на месте
        self.assertEqual(s["tracks"][2]["clipSlots"][0]["clip"]["transpose"], 2)   # тоника G → A: +2

    def test_into_pentatonic_snaps_to_nearest(self):
        s = self.deg(mixo([45, 40]), 9, "Minor Pentatonic")         # A (→B) и E (→F) — их нет в пентатонике
        self.assertEqual(notes(s), [48, 40])                         # B → C, F → E

    def test_chromatic_kept_degrees_snapped(self):
        s = song((63, 65, 59))                                       # A Minor: D♯ (хроматика), F и B (ступени)
        s = self.deg(s, 9, "Minor Pentatonic")
        self.assertEqual(notes(s), [63, 64, 60])                     # D♯ остаётся; F → E; B → C

    def test_same_mode_is_plain_transposition(self):
        s = self.deg(song((45, 52, 58)), 4, "Minor")                 # A Minor → E Minor, A♯ — хроматика
        self.assertEqual(notes(s), [40, 47, 53])

    def test_unknown_scale_refused(self):
        s = song()
        s["scale"] = "Super Locrian"
        with self.assertRaises(app.AppError):
            self.deg(s, 4, "Minor")

    def test_action_name(self):
        self.assertEqual(app.edit_action(None, {}, {"rootNote": 9, "scale": "Minor", "notes": "degrees"}),
                         "Key changed to A Minor, notes by degrees")


class DegreesReview(unittest.TestCase):
    """Замечания рецензента: наложение одинаковых нот (Move не открывает такой проект), пентатоника ↔ пентатоника."""
    def deg(self, s, root, scale):
        return app.edit_song(s, key={"rootNote": root, "scale": scale, "notes": "degrees"})

    def test_chord_into_pentatonic_has_no_same_pitch_overlap(self):
        s = song((57, 60, 64, 59))                                   # аккорд A C E B одновременно, A Minor
        s = self.deg(s, 9, "Minor Pentatonic")                       # B → C — совпадает с C
        ns = s["tracks"][0]["clipSlots"][0]["clip"]["notes"]
        pitches = [n["noteNumber"] for n in ns]
        self.assertEqual(sorted(pitches), [57, 60, 64])

    def test_overlap_is_trimmed(self):
        s = song((59, 60))
        n0, n1 = s["tracks"][0]["clipSlots"][0]["clip"]["notes"]
        n1["startTime"] = 0.5                                        # B (0–1) наезжает на C (0.5–1.5)
        s = self.deg(s, 9, "Minor Pentatonic")
        ns = sorted(s["tracks"][0]["clipSlots"][0]["clip"]["notes"], key=lambda n: n["startTime"])
        self.assertEqual([(n["noteNumber"], n["startTime"], n["duration"]) for n in ns], [(60, 0.0, 0.5), (60, 0.5, 1.0)])

    def test_pentatonic_to_pentatonic_keeps_five_notes(self):
        s = song((60, 62, 64, 67, 69))
        s["rootNote"], s["scale"] = 0, "Major Pentatonic"
        s = self.deg(s, 0, "Minor Pentatonic")
        self.assertEqual(notes(s), [60, 63, 65, 67, 70])

    def test_minor_pent_to_relative_major_pent(self):
        s = song((57, 60, 62, 64, 67))
        s["scale"] = "Minor Pentatonic"                              # A Minor Pentatonic → C Major Pentatonic
        s = self.deg(s, 0, "Major Pentatonic")
        self.assertEqual(notes(s), [60, 62, 64, 67, 69])

    def test_shift_and_degrees_together_refused(self):
        with self.assertRaises(app.AppError):
            app.edit_song(song(), key={"rootNote": 4, "scale": "Minor", "notes": "degrees", "shift": -5})
