import unittest

import drumgen


def steps(p, role):
    return [i + 1 for i, v in enumerate(p["hits"].get(role, [])) if v > 0]


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pats = drumgen.load_patterns()
        cls.by_name = {(p["source"], p["name"]): p for p in cls.pats}

    def test_pocket_has_many_patterns(self):
        self.assertGreaterEqual(sum(1 for p in self.pats if p["source"] == "pocket"), 180)

    def test_house(self):
        p = self.by_name[("pocket", "HOUSE")]
        self.assertEqual(p["genre"], "House")
        self.assertEqual(p["steps"], 16)
        self.assertEqual(steps(p, "kick"), [1, 5, 9, 13])
        self.assertEqual(steps(p, "snare"), [5, 13])
        self.assertEqual(steps(p, "ohh"), [3, 7, 11, 15])

    def test_glued_digits_split(self):
        p = self.by_name[("pocket", "HOUSE 2")]
        self.assertEqual(steps(p, "chh"), list(range(1, 17)))

    def test_ab_pairs_glued(self):
        p = self.by_name[("pocket", "HIP HOP 1")]
        self.assertEqual(p["steps"], 32)
        self.assertEqual(steps(p, "kick"), [1, 7, 8, 12, 15, 17, 24, 28])

    def test_basic8(self):
        b8 = [p for p in self.pats if p["source"] == "basic8"]
        self.assertEqual(len(b8), 8)
        self.assertTrue(all(p["steps"] == 32 for p in b8))
        dnb = self.by_name[("basic8", "Drum and Bass")]
        self.assertEqual(steps(dnb, "snare"), [5, 11, 13, 21, 29])

    def test_genres_merged(self):
        g = drumgen.genres(self.pats)
        self.assertIn("Drum and Bass", g)
        self.assertNotIn("DRUM 'N' BASS", g)
        self.assertEqual(len([x for x in g if "drum" in x.lower() and "bass" in x.lower()]), 1)
        self.assertEqual(self.by_name[("basic8", "Hip Hop")]["genre"], self.by_name[("pocket", "HIP HOP 1")]["genre"])

    def test_roles_valid_and_velocities(self):
        for p in self.pats:
            for role, vals in p["hits"].items():
                self.assertIn(role, drumgen.ROLES)
                self.assertEqual(len(vals), p["steps"])
                self.assertTrue(all(0 <= v <= 1 for v in vals))


if __name__ == "__main__":
    unittest.main()
