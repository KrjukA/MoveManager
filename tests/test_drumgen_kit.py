import unittest

import drumgen


def cell(note, sample):
    dev = {"kind": "drumCell", "deviceData": {"sampleUri": f"ableton:/user-library/Samples/{sample}"}} if sample else {"kind": "drumCell"}
    return {"devices": [dev], "drumZoneSettings": {"receivingNote": note}}


def song_with(samples):
    drum = {"kind": "drumRack", "chains": [cell(36 + i, s) for i, s in enumerate(samples)]}
    rack = {"kind": "instrumentRack", "chains": [{"devices": [drum, {"kind": "saturator"}]}]}
    return {"tracks": [{"devices": [rack]}, {"devices": [{"kind": "drift"}]}]}


SLOW = ["bd_cleanest.wav", "bd_clickdevil.wav", "bd_clkclean.wav", "bd_clkfm.wav", "bd_notreally.wav",
        "bd_particle_drop.wav", "tm_bass_thing.wav", "tm_classix4.wav", "sd_aecclk.wav",
        "Set 93 Bounce 4 - 100 bpm.wav", "Set 93 Bounce 3 - 100 bpm.wav", "sd_efem.wav", "sd_hollows_rmod.wav",
        "Set 93 Bounce 1 - 100 bpm.wav", "Set 93 Bounce 2 - 100 bpm.wav", "sd_snap_pn1.wav"]


class Kit(unittest.TestCase):
    def test_slow_dreamy_kit(self):
        pads = drumgen.kit_pads(song_with(SLOW), 0)
        role = {p["note"]: p["role"] for p in pads}
        self.assertEqual([role[n] for n in range(36, 42)], ["kick"] * 6)
        self.assertTrue(role[42].startswith("tom") and role[43].startswith("tom"))
        self.assertEqual([role[n] for n in (44, 47, 48, 51)], ["snare"] * 4)
        self.assertEqual(role[45], "tom_mid")        # имя ничего не говорит — раскладка Live
        self.assertEqual(role[46], "ohh")
        self.assertEqual(pads[0]["sample"], "bd_cleanest.wav")

    def test_role_from_name(self):
        f = drumgen.role_from_name
        self.assertEqual(f("bd_x.wav"), "kick")
        self.assertEqual(f("Kick 01.wav"), "kick")
        self.assertEqual(f("HH closed.wav"), "chh")
        self.assertEqual(f("OH long.wav"), "ohh")
        self.assertEqual(f("Open Hat.wav"), "ohh")
        self.assertEqual(f("clap tight.wav"), "clap")
        self.assertEqual(f("rim 2.wav"), "rim")
        self.assertEqual(f("Set 93 Bounce 4.wav"), None)

    def test_not_drum_track(self):
        self.assertIsNone(drumgen.kit_pads(song_with(SLOW), 1))

    def test_empty_pad_uses_live_layout(self):
        pads = drumgen.kit_pads(song_with([None] * 16), 0)
        self.assertEqual({p["note"]: p["role"] for p in pads}[42], "chh")

    def test_role_substitution(self):
        pads = drumgen.kit_pads(song_with(SLOW), 0)
        self.assertEqual(drumgen.pads_for_role(pads, "clap"), [44, 47, 48, 51])
        self.assertEqual(drumgen.pads_for_role(pads, "kick"), [36, 37, 38, 39, 40, 41])

    def test_overrides(self):
        pads = drumgen.kit_pads(song_with(SLOW), 0, {"45": "clap"})
        self.assertEqual({p["note"]: p["role"] for p in pads}[45], "clap")


if __name__ == "__main__":
    unittest.main()
