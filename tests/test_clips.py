import copy
import unittest

import app
from app import AppError, get_clip, parse_song, put_clip

NOTES = [{"noteNumber": 36, "startTime": t, "duration": 0.25, "velocity": 100.0, "offVelocity": 0.0} for t in (0, 1, 2)]


def song():
    def slot(clip=None):
        return {"hasStop": True, "clip": clip}
    existing = {"isPlaying": True, "name": "", "color": 23, "isEnabled": True,
                "timeSignature": {"upper": 4, "lower": 4},
                "region": {"start": 0.0, "end": 4.0, "loop": {"start": 0.0, "end": 4.0, "isEnabled": True}},
                "grooveId": 1, "stepEditorScrollPosition": 0.0, "notes": copy.deepcopy(NOTES), "envelopes": []}
    return {"tempo": 120.0, "rootNote": 0, "scale": "Major", "timeSignature": {"upper": 4, "lower": 4},
            "scenes": [{}, {}],
            "tracks": [{"kind": "midi", "devices": [], "mixer": {"pan": 0.0}, "clipSlots": [slot(existing), slot()]},
                       {"kind": "audio", "devices": [], "mixer": {"pan": 0.0}, "clipSlots": [slot(), slot()]}]}


class ClipTests(unittest.TestCase):
    def test_clips_grid(self):
        roll = [[0.0, 0.25, 36], [1.0, 0.25, 36], [2.0, 0.25, 36]]
        self.assertEqual(parse_song(song())["clips"], [[{"notes": 3, "length": 4.0, "roll": roll}, None], [None, None]])

    def test_roll_relative_to_region_and_capped(self):
        s = song()
        c = s["tracks"][0]["clipSlots"][0]["clip"]
        c["region"]["start"] = 1.0
        c["notes"] = [{"noteNumber": 60 + i % 12, "startTime": 1.0 + i * 0.01, "duration": 0.123456, "velocity": 100.0}
                      for i in range(400)]
        roll = parse_song(s)["clips"][0][0]["roll"]
        self.assertEqual(len(roll), app.ROLL_MAX)
        self.assertEqual(roll[0], [0.0, 0.123, 60])

    def test_old_cache_without_roll_is_stale(self):
        info = parse_song(song())
        del info["clips"][0][0]["roll"]
        self.assertTrue(app.stale_info(info))

    def test_put_clip_rounds_to_bar(self):
        s = song()
        put_clip(s, 0, 1, copy.deepcopy(NOTES), 5.1)
        c = s["tracks"][0]["clipSlots"][1]["clip"]
        self.assertEqual(c["region"]["end"], 8.0)
        self.assertEqual(c["region"]["loop"], {"start": 0.0, "end": 8.0, "isEnabled": True})
        self.assertIs(c["region"]["loop"]["isEnabled"], True)
        self.assertEqual(len(c["notes"]), 3)
        self.assertEqual(c["envelopes"], [])
        self.assertIs(c["isPlaying"], False)

    def test_put_clip_minimum_one_bar(self):
        s = song()
        put_clip(s, 0, 1, copy.deepcopy(NOTES), 0.0)
        self.assertEqual(s["tracks"][0]["clipSlots"][1]["clip"]["region"]["end"], 4.0)

    def test_put_clip_uses_template_keys(self):
        s = song()
        put_clip(s, 0, 1, copy.deepcopy(NOTES), 4.0)
        c = s["tracks"][0]["clipSlots"][1]["clip"]
        self.assertEqual(c["grooveId"], 1)
        self.assertEqual(c["timeSignature"], {"upper": 4, "lower": 4})

    def test_put_clip_audio_track_refused(self):
        with self.assertRaises(AppError):
            put_clip(song(), 1, 0, copy.deepcopy(NOTES), 4.0)

    def test_put_clip_bad_index(self):
        for t, sc in ((5, 0), (0, 9), (-1, 0)):
            with self.assertRaises(AppError):
                put_clip(song(), t, sc, copy.deepcopy(NOTES), 4.0)

    def test_get_clip(self):
        self.assertEqual(len(get_clip(song(), 0, 0)["notes"]), 3)
        with self.assertRaises(AppError):
            get_clip(song(), 0, 1)


if __name__ == "__main__":
    unittest.main()
