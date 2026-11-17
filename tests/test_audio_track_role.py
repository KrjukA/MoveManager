"""Сборка 54: аудиодорожка — роль Audio, а не роль первого эффекта на ней."""
import unittest

import app


def song(tr):
    return {"tempo": 120.0, "rootNote": 0, "scale": "Major", "timeSignature": {"upper": 4, "lower": 4}, "scenes": [{}],
            "tracks": [tr]}


DELAY = {"kind": "delay", "name": "4th Band-pass",
         "presetUri": "ableton:/abl-core-library/Track%20Presets/Audio%20Effects/Delay/4th%20Band-pass.ablpreset"}


class AudioRole(unittest.TestCase):
    def test_audio_track_with_effect_is_audio(self):
        t = app.parse_song(song({"kind": "audio", "devices": [DELAY], "clipSlots": [{"clip": None}]}))["tracks"][0]
        self.assertEqual(t["role"], "Audio")
        self.assertEqual(t["name"], "Audio")
        self.assertEqual(t["clipKind"], "audio")

    def test_audio_track_keeps_own_name(self):
        t = app.parse_song(song({"kind": "audio", "name": "Vox loops", "devices": [DELAY], "clipSlots": []}))["tracks"][0]
        self.assertEqual((t["role"], t["name"]), ("Audio", "Vox loops"))

    def test_midi_fx_preset_still_fx(self):
        tr = {"kind": "midi", "devices": [{"kind": "wavetable", "name": "Riser",
              "presetUri": "ableton:/abl-core-library/Track%20Presets/FX/Riser.ablpreset"}], "clipSlots": []}
        self.assertEqual(app.parse_song(song(tr))["tracks"][0]["role"], "FX")


class StaleRole(unittest.TestCase):
    def test_cached_fx_role_on_audio_track_is_stale(self):
        info = app.parse_song(song({"kind": "audio", "devices": [DELAY], "clipSlots": [{"clip": None}]}))
        self.assertFalse(app.stale_info(info))
        info["tracks"][0]["role"] = "FX"                     # разбор сборки ≤ 53
        self.assertTrue(app.stale_info(info))
