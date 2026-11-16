import json
import unittest

import samplelib as sl

SONG = json.dumps({"tracks": [{"devices": [{"kind": "drumRack", "presetUri": "ableton:/user-library/Track%20Presets/Drums/Kit%201.ablpreset",
    "chains": [{"devices": [{"kind": "drumCell", "deviceData": {"sampleUri": "ableton:/user-library/Samples/Bounces/Set%2093%20Bounce%204%20-%20100%20bpm.wav"}}]},
               {"devices": [{"kind": "drumCell", "deviceData": {"sampleUri": "ableton:/user-library/Samples/Bounces/Set%2093%20Bounce%204%20-%20100%20bpm.wav"}}]},
               {"devices": [{"kind": "drumCell", "deviceData": {"sampleUri": "ableton:/user-library/Samples/CHD-DeepSaw%20%D0%A1.wav"}}]},
               {"devices": [{"kind": "drumCell", "deviceData": {"sampleUri": "ableton:/core-library/Samples/x.wav"}}]}]}]}]}, indent=2)
SCHWUNG = json.dumps({"synth": {"module": "sampler", "params": {"file": "/data/UserData/UserLibrary/Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav"}}})


class Uri(unittest.TestCase):
    def test_roundtrip(self):
        for rel in ["Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav", "Samples/CHD-DeepSaw С.wav",
                    "Samples/Drums & Perc (old)/kick.wav", "Track Presets/Drums/Kit 1.ablpreset"]:
            self.assertEqual(sl.uri_to_rel(sl.rel_to_uri(rel)), rel)
        self.assertEqual(sl.rel_to_uri("Samples/a b.wav"), "ableton:/user-library/Samples/a%20b.wav")
        self.assertEqual(sl.uri_to_rel("ableton:/user-library/Samples/CHD-DeepSaw%20%D0%A1.wav"), "Samples/CHD-DeepSaw С.wav")
        self.assertIsNone(sl.uri_to_rel("ableton:/core-library/Samples/x.wav"))

    def test_find_refs(self):
        self.assertEqual(sorted(set(sl.find_refs(SONG))), ["Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav",
                                                           "Samples/CHD-DeepSaw С.wav", "Track Presets/Drums/Kit 1.ablpreset"])
        self.assertEqual(sl.find_refs(SCHWUNG), ["Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav"])

    def test_index(self):
        idx = sl.build_index({"Sets/a/Slow/Song.abl": SONG, "schwung/x/slot_0.json": SCHWUNG})
        self.assertEqual(sorted(idx["Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav"]), ["Sets/a/Slow/Song.abl", "schwung/x/slot_0.json"])


class Plan(unittest.TestCase):
    FILES = ["Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav", "Samples/Bounces/sub/deep.wav", "Samples/Other/taken.wav",
             "Samples/CHD-DeepSaw С.wav"]

    def test_expand_folder(self):
        got = sl.expand_moves([("Samples/Bounces", "Samples/Resamples/Bounces")], self.FILES)
        self.assertEqual(sorted(got), [("Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav", "Samples/Resamples/Bounces/Set 93 Bounce 4 - 100 bpm.wav"),
                                       ("Samples/Bounces/sub/deep.wav", "Samples/Resamples/Bounces/sub/deep.wav")])

    def test_plan_counts_and_conflicts(self):
        src = {"Sets/a/Slow/Song.abl": SONG, "schwung/x/slot_0.json": SCHWUNG}
        p = sl.make_plan([("Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav", "Samples/Other/new.wav")], self.FILES, src)
        self.assertEqual(p["touch"], {"Sets/a/Slow/Song.abl": 2, "schwung/x/slot_0.json": 1})
        self.assertEqual(p["conflicts"], [])
        p = sl.make_plan([("Samples/CHD-DeepSaw С.wav", "Samples/Other/taken.wav")], self.FILES, src)
        self.assertEqual(p["conflicts"], ["Samples/Other/taken.wav"])
        p = sl.make_plan([("Samples/a.wav", "Samples/../x.wav")], self.FILES, src)
        self.assertTrue(p["conflicts"])

    def test_rewrite_all_forms(self):
        mapping = {"Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav": "Samples/Res/Slow Dreamy IDM - Bounce 4.wav"}
        text, n = sl.rewrite(SONG, mapping)
        self.assertEqual(n, 2)
        self.assertIn('"ableton:/user-library/Samples/Res/Slow%20Dreamy%20IDM%20-%20Bounce%204.wav"', text)
        self.assertIn("CHD-DeepSaw%20%D0%A1.wav", text)                      # остальное не тронуто
        self.assertEqual(json.loads(text)["tracks"][0]["devices"][0]["presetUri"], "ableton:/user-library/Track%20Presets/Drums/Kit%201.ablpreset")
        text, n = sl.rewrite(SCHWUNG, mapping)
        self.assertEqual(n, 1)
        self.assertEqual(json.loads(text)["synth"]["params"]["file"], "/data/UserData/UserLibrary/Samples/Res/Slow Dreamy IDM - Bounce 4.wav")


class Names(unittest.TestCase):
    def test_suggest(self):
        rel = "Samples/Bounces/Set 93 Bounce 4 - 100 bpm.wav"
        self.assertEqual(sl.suggest_names(rel, ["Slow Dreamy IDM"]), ["Slow Dreamy IDM - Bounce 4 - 100 bpm.wav"])
        self.assertEqual(sl.suggest_names(rel, []), [])
        self.assertEqual(sl.suggest_names(rel, ["Acid Set", "Set 93"]), ["Set 93 - Bounce 4 - 100 bpm.wav", "Acid Set - Bounce 4 - 100 bpm.wav"])
        self.assertEqual(sl.suggest_names("Samples/kick.wav", ["X"]), ["X - kick.wav"])


if __name__ == "__main__":
    unittest.main()
