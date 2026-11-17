import unittest

import drumgen
from tests.test_drumgen_kit import SLOW, song_with

PATS = drumgen.load_patterns()
HOUSE = next(p for p in PATS if p["source"] == "pocket" and p["name"] == "HOUSE")
LIVE = drumgen.kit_pads(song_with([None] * 16), 0)          # раскладка Live
SLOWK = drumgen.kit_pads(song_with(SLOW), 0)


def gen(**kw):
    args = dict(patterns=PATS, genre="House", pattern_id=HOUSE["id"], pads=LIVE, mutation=0, seed=1,
                bars=1, swing=50, deja_vu=50, ghosts=0, euclid=0)
    args.update(kw)
    return drumgen.generate(**args)


def sig(res):
    return sorted((n["noteNumber"], round(n["startTime"], 4)) for n in res["notes"])


class Generate(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(sig(gen(mutation=60, seed=5)), sig(gen(mutation=60, seed=5)))
        self.assertNotEqual(sig(gen(mutation=60, seed=5)), sig(gen(mutation=60, seed=6)))

    def test_mutation_zero_is_reference(self):
        res = gen(mutation=0)
        want = sorted([(36, s * 0.25) for s in (0, 4, 8, 12)] + [(38, 1.0), (38, 3.0)] +
                      [(46, s * 0.25) for s in (2, 6, 10, 14)] + [(51, 0.0)])
        self.assertEqual(sig(res), want)
        self.assertEqual(res["length"], 4.0)

    def test_full_mutation_density_bounded(self):
        house = [p for p in PATS if p["genre"] == "House"]
        for seed in range(10):
            res = gen(mutation=100, seed=seed, bars=1, ghosts=False, euclid=False)
            for role, row in res["grid"].items():
                hits = sum(1 for v in row if v > 0)
                most = max(sum(1 for v in p["hits"].get(role, [])[:16] if v > 0) for p in house)
                self.assertLessEqual(hits, most + 4, (seed, role))

    def test_any_pattern_picked_by_seed(self):
        a, b = gen(pattern_id=None, mutation=0, seed=1), gen(pattern_id=None, mutation=0, seed=1)
        self.assertEqual(a["pattern"], b["pattern"])
        self.assertTrue(any(gen(pattern_id=None, mutation=0, seed=s)["pattern"] != a["pattern"] for s in range(2, 12)))

    def test_deja_vu_repeats_first_bar(self):
        res = gen(mutation=80, seed=3, bars=4, deja_vu=100, pattern_id=None)
        bars = [sorted((n["noteNumber"], round(n["startTime"] - 4 * b, 4)) for n in res["notes"]
                       if 4 * b <= n["startTime"] < 4 * (b + 1)) for b in range(4)]
        self.assertEqual(bars[1], bars[0]); self.assertEqual(bars[3], bars[0])

    def test_deja_vu_is_gradual_for_one_seed(self):
        def diff(d, mut=35, seed=4):
            res = gen(mutation=mut, seed=seed, bars=2, deja_vu=d, pattern_id=None)
            bars = [{(n["noteNumber"], round(n["startTime"] - 4 * b, 3)) for n in res["notes"] if 4 * b <= n["startTime"] < 4 * b + 4}
                    for b in range(2)]
            return len(bars[0] ^ bars[1])
        for seed in range(6):
            ds = [diff(d, seed=seed) for d in (0, 25, 50, 75, 100)]
            self.assertEqual(ds, sorted(ds, reverse=True), (seed, ds))
            self.assertGreater(ds[0], ds[-1])
            self.assertEqual(ds[-1], 0)
        self.assertGreater(diff(0, mut=0), 0)          # даже без мутации второй такт — вариация

    def test_always_kick_snare_hat(self):
        odd_kits = {
            "all perc": [{"note": n, "sample": f"Guitar Jazz {n}.wav", "role": "perc"} for n in range(36, 52)],
            "all kick": [{"note": n, "sample": "", "role": "kick"} for n in range(36, 52)],
            "live": LIVE, "slow": SLOWK,
        }
        genres = drumgen.genres(PATS)
        for name, pads in odd_kits.items():
            for genre in genres:
                for mut in (0, 50, 100):
                    res = gen(genre=genre, pattern_id=None, pads=pads, mutation=mut, seed=mut + 7, bars=2)
                    role_of = {}
                    for core in ("kick", "snare", "chh"):
                        for b in range(2):
                            row = res["grid"].get(core, [0] * 32)[16 * b:16 * b + 16]
                            if core == "chh":               # хэт — закрытый или открытый
                                row = row + res["grid"].get("ohh", [0] * 32)[16 * b:16 * b + 16]
                            self.assertTrue(any(row), (name, genre, mut, core, b))
                    used = {n["noteNumber"] for n in res["notes"]}
                    self.assertGreaterEqual(len(used), 3, (name, genre, mut))

    def test_notes_carry_their_role_and_land_on_matching_pads(self):
        for pads in (LIVE, SLOWK):
            for seed in range(5):
                res = gen(pattern_id=None, genre="Breaks", mutation=60, seed=seed, bars=2, pads=pads)
                for n in res["notes"]:
                    self.assertIn(n["role"], drumgen.ROLES)
                    self.assertIn(n["noteNumber"], drumgen.role_choices(pads, n["role"]), n)
        res = gen(mutation=0, pads=LIVE)
        self.assertEqual({n["role"] for n in res["notes"] if n["noteNumber"] == 36}, {"kick"})

    def test_single_pattern_genre_still_mutates(self):
        one = [g for g in drumgen.genres(PATS) if sum(p["genre"] == g for p in PATS) == 1]
        for genre in one[:5]:
            variants = {tuple(sorted((n["role"], n["startTime"]) for n in gen(genre=genre, pattern_id=None, mutation=60,
                                                                                seed=sd, bars=1, ghosts=False, euclid=False)["notes"])) for sd in range(6)}
            self.assertGreater(len(variants), 1, genre)

    def test_ghost_amount_is_a_slider(self):
        def ghosts(amount, seed):
            res = gen(genre="House", pattern_id=None, mutation=30, seed=seed, bars=2, ghosts=amount, euclid=False)
            return sum(1 for n in res["notes"] if n["role"] == "snare" and n["velocity"] <= 60)
        for seed in range(5):
            counts = [ghosts(a, seed) for a in (0, 30, 60, 100)]
            self.assertEqual(counts[0], 0, counts)
            self.assertEqual(counts, sorted(counts), counts)
        self.assertGreater(sum(ghosts(100, sd) for sd in range(5)), sum(ghosts(30, sd) for sd in range(5)))

    def test_euclid_amount_is_a_slider(self):
        def layer_hits(amount, seed):
            base = gen(genre="House", pattern_id=None, mutation=30, seed=seed, bars=1, euclid=0)
            res = gen(genre="House", pattern_id=None, mutation=30, seed=seed, bars=1, euclid=amount)
            return len(res["notes"]) - len(base["notes"])
        self.assertEqual(sum(layer_hits(0, sd) for sd in range(8)), 0)
        self.assertGreater(sum(layer_hits(100, sd) for sd in range(8)), sum(layer_hits(30, sd) for sd in range(8)))
        self.assertGreater(sum(layer_hits(30, sd) for sd in range(8)), 0)

    def test_ghosts_work_when_backbeat_is_a_clap(self):
        # Footwork: бэкбит — клэп, малого нет; на Mutation 100 ручка Ghosts всё равно должна добавлять тихие удары
        def quiet(amount, seed):
            res = gen(genre="Footwork", pattern_id=None, mutation=100, seed=seed, bars=2, ghosts=amount, euclid=0)
            return sum(1 for n in res["notes"] if n["velocity"] <= 60)
        self.assertEqual(sum(quiet(0, sd) for sd in range(10)), 0)
        self.assertGreaterEqual(sum(quiet(100, sd) for sd in range(10)), 40)     # в среднем ≥ 2 на такт

    def test_euclid_audible_even_when_rim_is_dense(self):
        # в Footwork римшот звучит на каждом шаге — слой Euclid не должен прятаться в нём
        for seed in range(8):
            base = gen(genre="Footwork", pattern_id=None, mutation=30, seed=seed, bars=1, euclid=0)
            res = gen(genre="Footwork", pattern_id=None, mutation=30, seed=seed, bars=1, euclid=100)
            self.assertGreaterEqual(len(res["notes"]) - len(base["notes"]), 4, seed)

    def test_half_time_stretches_the_pattern(self):
        normal = gen(genre="House", pattern_id=None, mutation=40, seed=9, bars=1, ghosts=0, euclid=0)
        half = gen(genre="House", pattern_id=None, mutation=40, seed=9, bars=2, ghosts=0, euclid=0, half=True)
        self.assertEqual(half["length"], 8.0)
        self.assertEqual(sorted((n["noteNumber"], round(n["startTime"], 4)) for n in half["notes"]),
                         sorted((n["noteNumber"], round(n["startTime"] * 2, 4)) for n in normal["notes"]))
        self.assertTrue(all(abs(n["duration"] - 0.5) < 1e-9 for n in half["notes"]))

    def test_half_time_for_kick_or_kick_and_snare_only(self):
        args = dict(genre="House", pattern_id=None, mutation=40, seed=9, bars=2, ghosts=0, euclid=0)
        normal, whole = gen(**args), gen(**args, half="all")
        for mode, roles in (("kick", {"kick"}), ("kick+snare", {"kick", "snare"})):
            res = gen(**args, half=mode)
            self.assertEqual(res["length"], normal["length"])
            pick = lambda r, keep: sorted((n["role"], n["noteNumber"], round(n["startTime"], 4)) for n in r["notes"] if (n["role"] in roles) == keep)
            self.assertEqual(pick(res, True), pick(whole, True), mode)      # эти роли — вдвое медленнее
            self.assertEqual(pick(res, False), pick(normal, False), mode)   # остальное — как было

    def test_half_modes_never_overlap_same_note(self):
        for mode in ("all", "kick", "kick+snare"):
            for seed in range(25):
                res = gen(genre="Breaks", pattern_id=None, mutation=80, seed=seed, bars=2, pads=SLOWK, half=mode, ghosts=60, euclid=60)
                end = {}
                for n in sorted(res["notes"], key=lambda n: (n["noteNumber"], n["startTime"])):
                    self.assertTrue(n["noteNumber"] not in end or n["startTime"] >= end[n["noteNumber"]] - 1e-9, (mode, seed, n))
                    end[n["noteNumber"]] = n["startTime"] + n["duration"]

    def test_avoid_previous_reference(self):
        for seed in range(10):
            res = gen(genre="Trap", pattern_id=None, mutation=1, seed=seed, avoid="pocket:73")
            self.assertNotEqual(res["pattern"], "pocket:73")

    def test_swing_moves_only_offbeat_sixteenths(self):
        straight, swung = gen(swing=50, mutation=0), gen(swing=66, mutation=0)
        for a, b in zip(sorted(straight["notes"], key=lambda n: (n["startTime"], n["noteNumber"])),
                        sorted(swung["notes"], key=lambda n: (n["startTime"], n["noteNumber"]))):
            step = round(a["startTime"] / 0.25)
            if step % 2 == 0:
                self.assertAlmostEqual(a["startTime"], b["startTime"])
            else:
                self.assertGreater(b["startTime"], a["startTime"])

    def test_notes_valid(self):
        for seed in range(20):
            res = gen(mutation=90, seed=seed, bars=2, pads=SLOWK, pattern_id=None)
            seen = {}
            for n in sorted(res["notes"], key=lambda n: (n["noteNumber"], n["startTime"])):
                self.assertTrue(36 <= n["noteNumber"] <= 51)
                self.assertTrue(1 <= n["velocity"] <= 127)
                self.assertIsInstance(n["velocity"], float)
                end = seen.get(n["noteNumber"])
                self.assertTrue(end is None or n["startTime"] >= end - 1e-9)
                seen[n["noteNumber"]] = n["startTime"] + n["duration"]

    def test_timbre_swap_uses_several_kicks(self):
        kicks = set()
        for seed in range(10):
            res = gen(mutation=70, seed=seed, pads=SLOWK, bars=2)
            kicks |= {n["noteNumber"] for n in res["notes"] if 36 <= n["noteNumber"] <= 41}
        self.assertGreaterEqual(len(kicks), 2)

    def test_missing_role_substituted(self):
        res = gen(mutation=0, pads=SLOWK)            # ohh → chh? в ките нет ни ohh, ни chh (кроме Live-раскладки 46)
        notes = {n["noteNumber"] for n in res["notes"]}
        self.assertTrue(notes <= set(range(36, 52)))


if __name__ == "__main__":
    unittest.main()
