import unittest

import app


def rack(name, chains):
    return {"kind": "instrumentRack", "name": name, "chains": [{"devices": c} for c in chains]}


SAMPLER = {"kind": "melodicSampler", "name": ""}
DELAY = {"kind": "delay", "name": "Delay"}
REVERB = {"kind": "reverb", "name": ""}


class Unwrap(unittest.TestCase):
    def test_nested_rack_is_unwrapped(self):
        song = {"tracks": [{"devices": [rack("ME Slot 4", [[rack("ME Slot 4", [[SAMPLER, DELAY, REVERB]])]])]}]}
        out, changed = app.unwrap_nested_racks(song)
        self.assertTrue(changed)
        self.assertEqual(out["tracks"][0]["devices"][0]["chains"][0]["devices"], [SAMPLER, DELAY, REVERB])
        self.assertEqual(out["tracks"][0]["devices"][0]["name"], "ME Slot 4")

    def test_normal_rack_untouched(self):
        drums = {"kind": "drumRack", "chains": [{"devices": [{"kind": "drumCell"}]}]}
        song = {"tracks": [{"devices": [rack("", [[drums, {"kind": "saturator"}]])]}]}
        out, changed = app.unwrap_nested_racks(song)
        self.assertFalse(changed)
        self.assertEqual(out["tracks"][0]["devices"][0]["chains"][0]["devices"][0], drums)

    def test_inner_rack_with_several_chains_untouched(self):
        inner = rack("x", [[SAMPLER], [DELAY]])
        song = {"tracks": [{"devices": [rack("x", [[inner]])]}]}
        _, changed = app.unwrap_nested_racks(song)
        self.assertFalse(changed)


if __name__ == "__main__":
    unittest.main()
