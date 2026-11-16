"""Генератор барабанных клипов: эталоны, роли пэдов, карта жанра, генерация. Только стандартная библиотека."""
import json
import random
import re
from pathlib import Path
from urllib.parse import unquote

PATTERN_DIR = Path(__file__).resolve().parent / "patterns"
ROLES = ["kick", "snare", "clap", "rim", "chh", "ohh", "tom_low", "tom_mid", "tom_high",
         "crash", "ride", "shaker", "cowbell", "perc"]
CREDIT = "Patterns: Pocket Operations — Paul Wenzel, 2019; Basic Drum Patterns chart"


def genre_key(name):
    s = name.lower().replace("&", "and").replace("'n'", "and").replace("’n’", "and")
    s = re.sub(r"\bn\b", "and", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def load_patterns():
    pats = []
    for fname, source in (("pocket_operations.json", "pocket"), ("basic_8_genres.json", "basic8")):
        for i, p in enumerate(json.loads((PATTERN_DIR / fname).read_text(encoding="utf-8"))):
            pats.append({"id": f"{source}:{i}", "name": p["name"], "genre": p["genre"], "source": source,
                         "steps": p["steps"], "hits": p["hits"]})
    return unify_genres(pats)


BUILTIN = {"pocket", "basic8"}
GROUP_SUFFIX = {"mine": " (my projects)", "midi": " (MIDI folder)"}


def unify_genres(pats):
    """Одноимённые встроенные жанры (Drum and Bass / DRUM 'N' BASS) получают одно написание.
    Жанры из своих проектов и папки MIDI не смешиваются со встроенными: при совпадении имени получают пометку."""
    names = {}
    for p in pats:
        if p["source"] in BUILTIN:
            p["genre"] = names.setdefault(genre_key(p["genre"]), p["genre"])
    for p in pats:
        if p["source"] not in BUILTIN and genre_key(p["genre"]) in names:
            p["genre"] = p["genre"] + GROUP_SUFFIX.get(p["source"], " (mine)")
    return pats


def genres(pats):
    return sorted({p["genre"] for p in pats}, key=str.lower)


def genre_list(pats):
    """[{name, group}] — группа: builtin, mine (мои проекты), midi (папка MIDI); сначала встроенные."""
    group = {}
    for p in pats:
        g = "builtin" if p["source"] in BUILTIN else p["source"]
        group.setdefault(p["genre"], g)
    order = {"builtin": 0, "mine": 1, "midi": 2}
    return [{"name": n, "group": group[n]} for n in sorted(group, key=lambda n: (order.get(group[n], 3), n.lower()))]


# ───────── роли пэдов кита ─────────
LIVE_LAYOUT = {36: "kick", 37: "rim", 38: "snare", 39: "clap", 40: "snare", 41: "tom_low", 42: "chh",
               43: "tom_low", 44: "chh", 45: "tom_mid", 46: "ohh", 47: "tom_mid", 48: "tom_high",
               49: "crash", 50: "tom_high", 51: "ride"}
FALLBACK = {"rim": ["snare"], "clap": ["snare"], "ohh": ["chh"], "ride": ["chh"], "shaker": ["chh"],
            "cowbell": ["perc"], "tom_low": ["tom_mid", "tom_high", "perc"], "tom_mid": ["tom_low", "tom_high", "perc"],
            "tom_high": ["tom_mid", "tom_low", "perc"], "crash": ["ride", "ohh"]}
WORDS = [("kick", {"bd", "kick", "kik", "kck", "bassdrum"}), ("snare", {"sd", "snare", "snr", "sn"}),
         ("clap", {"cl", "clap", "clp", "claps"}), ("rim", {"rim", "rs", "rimshot", "stick"}),
         ("crash", {"cy", "crash", "cym", "cymbal"}), ("ride", {"ride", "rd"}),
         ("shaker", {"sh", "shaker", "shk", "shake"}), ("cowbell", {"cb", "cow", "cowbell"}),
         ("perc", {"perc", "conga", "bongo", "tamb", "tambourine", "clave"})]


def role_from_name(name):
    tokens = [t for t in re.split(r"[^a-z]+", (name or "").lower()) if t]
    s = set(tokens)
    if s & {"oh", "ohh", "ophat", "openhat"} or ("open" in s and s & {"hh", "hat", "hihat", "hats"}):
        return "ohh"
    if s & {"hh", "hat", "hats", "chh", "ch", "hihat", "closed"}:
        return "chh"
    if s & {"tm", "tom", "toms"}:
        if s & {"lo", "low", "floor"}:
            return "tom_low"
        if s & {"hi", "high"}:
            return "tom_high"
        return "tom_mid"
    for role, words in WORDS:
        if s & words:
            return role
    return None


def _sample_name(node):
    if isinstance(node, dict):
        uri = node.get("sampleUri")
        if isinstance(uri, str) and uri:
            return unquote(uri).split("/")[-1]
        node = list(node.values())
    if isinstance(node, list):
        for v in node:
            found = _sample_name(v)
            if found:
                return found
    return ""


def _find_drum_rack(devices):
    for dev in devices or []:
        if dev.get("kind") == "drumRack":
            return dev
        if dev.get("kind") in ("instrumentRack", "audioEffectRack", "midiEffectRack"):
            for ch in dev.get("chains") or []:
                found = _find_drum_rack(ch.get("devices"))
                if found:
                    return found
        elif dev.get("kind"):
            return None
    return None


def kit_pads(song, track, overrides=None):
    """Пэды Drum Rack дорожки: [{note, sample, role}] по нотам 36–51; None — дорожка не барабанная."""
    tracks = song.get("tracks") or []
    if not 0 <= track < len(tracks):
        return None
    rack = _find_drum_rack(tracks[track].get("devices"))
    if rack is None:
        return None
    samples = {}
    for ch in rack.get("chains") or []:
        note = (ch.get("drumZoneSettings") or {}).get("receivingNote")
        if isinstance(note, int):
            samples[note] = _sample_name(ch.get("devices"))
    overrides = {int(k): v for k, v in (overrides or {}).items() if v in ROLES}
    pads = []
    for note in range(36, 52):
        sample = samples.get(note, "")
        role = overrides.get(note) or role_from_name(sample) or LIVE_LAYOUT[note]
        pads.append({"note": note, "sample": sample, "role": role})
    return pads


CORE = ("kick", "snare", "chh")
CORE_NOTE = {"kick": 36, "snare": 38, "chh": 42}


def role_choices(pads, role):
    """Пэды для роли. Для kick/snare/hh пэд есть всегда и у каждой из трёх свой:
    если в ките такой роли нет, берётся пэд раскладки Live (36/38/42) или ближайший свободный."""
    if role not in CORE:
        return pads_for_role(pads, role)
    taken = set()
    for core in CORE:
        found = [n for n in pads_for_role(pads, core) if n not in taken] if pads else []
        if not found:
            notes = [p["note"] for p in pads] or list(range(36, 52))
            pref = CORE_NOTE[core]
            free = [n for n in notes if n not in taken]
            found = [pref] if pref in free else free[:1]
        if core == role:
            return found
        taken.update(found[:1] if core != role else [])
    return []


def pads_for_role(pads, role):
    for r in [role] + FALLBACK.get(role, []):
        found = [p["note"] for p in pads if p["role"] == r]
        if found:
            return found
    return []


# ───────── карта жанра и генерация ─────────
STRONG = {"kick": {0, 4, 8, 12}, "snare": {4, 12}, "clap": {4, 12}}
EUCLID_ROLES = ["chh", "perc", "shaker", "rim", "cowbell"]


def genre_map(patterns, steps=16):
    """Доля тактов жанра с ударом роли на каждом шаге такта."""
    counts, bars = {}, 0
    for p in patterns:
        nb = max(1, p["steps"] // steps)
        bars += nb
        for role, row in p["hits"].items():
            acc = counts.setdefault(role, [0] * steps)
            for i, v in enumerate(row[:nb * steps]):
                if v > 0:
                    acc[i % steps] += 1
    return {r: [c / bars for c in acc] for r, acc in counts.items()} if bars else {}


def euclid_rhythm(k, n=16, rotate=0):
    """Евклидов ритм: k ударов на n шагов, равномерно (Bjorklund, через округление)."""
    hits = [(i * k) // n != ((i + 1) * k) // n for i in range(n)] if k else [False] * n
    hits = hits[-1:] + hits[:-1]                    # первый удар — на первый шаг
    return [hits[(i - rotate) % n] for i in range(n)]


def generate(patterns, genre, pattern_id, pads, mutation=35, seed=1, bars=2, swing=50, deja_vu=50,
             ghosts=True, euclid=True, avoid=None, half=False):
    """half=True — половинный темп: рисунок на вдвое меньше тактов растягивается вдвое (темп 140 звучит как 70)."""
    if half in ("kick", "kick+snare"):           # вдвое медленнее только бочка (и малый), остальное — как было
        roles = {"kick"} if half == "kick" else {"kick", "snare"}
        normal = generate(patterns, genre, pattern_id, pads, mutation, seed, bars, swing, deja_vu, ghosts, euclid, avoid)
        slow = generate(patterns, genre, normal["pattern"], pads, mutation, seed, bars, swing, deja_vu, ghosts, euclid,
                        avoid, "all")
        notes = {(n["noteNumber"], round(n["startTime"], 6)): n for n in normal["notes"] if n["role"] not in roles}
        for n in slow["notes"]:
            if n["role"] in roles and n["startTime"] < normal["length"]:
                notes.setdefault((n["noteNumber"], round(n["startTime"], 6)), n)
        grid = {r: (slow["grid"].get(r, [])[:len(row)] if r in roles else row) for r, row in normal["grid"].items()}
        for r in roles:
            if r in slow["grid"] and r not in grid:
                grid[r] = slow["grid"][r][:16 * bars]
        merged = sorted(notes.values(), key=lambda n: (n["noteNumber"], n["startTime"]))
        for a, nxt in zip(merged, merged[1:]):         # одинаковые ноты не должны наезжать друг на друга
            if a["noteNumber"] == nxt["noteNumber"] and a["startTime"] + a["duration"] > nxt["startTime"]:
                a["duration"] = nxt["startTime"] - a["startTime"]
        normal.update(notes=sorted(merged, key=lambda n: (n["startTime"], n["noteNumber"])), grid=grid, half=half)
        return normal
    if half:
        res = generate(patterns, genre, pattern_id, pads, mutation, seed, max(1, bars // 2), swing, deja_vu,
                       ghosts, euclid, avoid, False)
        for n in res["notes"]:
            n["startTime"] *= 2
            n["duration"] *= 2
        res["length"] *= 2
        res["grid"] = {r: [v for x in row for v in (x, 0.0)] for r, row in res["grid"].items()}
        res["half"] = True
        return res

    rng = random.Random(seed)
    m = max(0.0, min(1.0, mutation / 100.0))
    ghost_amt = (0.35 if ghosts is True else 0.0 if ghosts is False else max(0.0, min(1.0, float(ghosts) / 100.0)))
    pool = [p for p in patterns if p["genre"] == genre] or list(patterns)
    choice = [p for p in pool if p["id"] != avoid] or pool          # Another: другой эталон, если он есть
    ref = next((p for p in patterns if p["id"] == pattern_id), None) or rng.choice(choice)
    gmap = genre_map(pool)
    # Четверть общей карты по всем жанрам: у мутации всегда есть из чего выбрать, даже в жанре из одного рисунка.
    wide = genre_map(patterns)
    gmap = {r: [0.75 * a + 0.25 * w for a, w in zip(gmap.get(r, [0.0] * 16), wide.get(r, [0.0] * 16))]
            for r in set(gmap) | set(wide)}
    roles = [r for r in ROLES if r in ref["hits"] or r in gmap]

    def ref_hit(role, idx):
        row = ref["hits"].get(role)
        return 1.0 if row and row[idx % ref["steps"]] > 0 else 0.0

    layer = None                                    # евклидов слой: одна роль на весь клип
    cand = [r for r in EUCLID_ROLES if pads_for_role(pads, r)]
    e_role, e_rot, e_k = (rng.choice(cand) if cand else None), rng.randint(0, 15), rng.randint(3, 7)
    if euclid is True:                              # старый режим: слой с вероятностью Mutation
        if m > 0 and rng.random() < m and e_role:
            layer = (e_role, euclid_rhythm(e_k, 16, e_rot))
    elif euclid and e_role:                         # ползунок 0–100: сколько ударов в слое (2…10)
        amt = max(0.0, min(1.0, float(euclid) / 100.0))
        layer = (e_role, euclid_rhythm(2 + round(amt * 8), 16, e_rot))

    def make_bar(b, m=m):
        bar = {r: [0.0] * 16 for r in roles}
        for role in roles:
            mp = gmap.get(role, [0.0] * 16)
            for s in range(16):
                r = ref_hit(role, b * 16 + s)
                if r and s in STRONG.get(role, ()) and m < 0.7:
                    p = 1.0
                else:
                    p = (1 - m) * r + m * mp[s]
                if p >= 1.0 or (p > 0 and rng.random() < p):
                    base = 112 if s in STRONG.get(role, ()) else (100 if s % 2 == 0 else 84)
                    bar[role][s] = max(1.0, min(127.0, base + rng.uniform(-8, 8) * (m > 0)))
        if "snare" in bar:                          # ghost-ноты: ручка 0–100, от мутации не зависит
            for s in range(16):
                if bar["snare"][s] >= 90:
                    for t in (s - 1, s + 1, s + 3):
                        u, vel = rng.random(), rng.uniform(45, 60)     # жребий тянется всегда — ручка действует плавно
                        if 0 <= t < 16 and not bar["snare"][t] and u < 0.6 * ghost_amt:
                            bar["snare"][t] = vel
        if layer:
            role, hits = layer
            row = bar.setdefault(role, [0.0] * 16)
            for s in range(16):
                if hits[s] and not row[s]:
                    row[s] = rng.uniform(70, 95)
        picked = {}                                 # выбор пэда — часть такта, чтобы дежавю повторяло и тембр
        for role, row in bar.items():
            choices = role_choices(pads, role)
            picked[role] = [None if not v or not choices else
                            (rng.choice(choices[1:]) if len(choices) > 1 and m > 0 and rng.random() < 0.5 * m
                             else choices[0]) for v in row]
        return bar, picked

    ohh_sounds = bool(role_choices(pads, "ohh"))     # открытый хэт считается хэтом, только если ему есть пэд

    def ensure_core(bar, picked):
        """В каждом такте есть бочка, малый и хэт: пустую роль заполняет самый типичный для жанра удар."""
        for role in CORE:
            row = bar.setdefault(role, [0.0] * 16)
            pick = picked.setdefault(role, [None] * 16)
            if any(row) or (role == "chh" and ohh_sounds and any(bar.get("ohh") or [])):
                continue
            mp = gmap.get(role) or [0.0] * 16
            if role == "chh":
                steps = [i for i in range(16) if mp[i] >= 0.3] or list(range(0, 16, 2))
            elif max(mp) > 0:
                steps = [max(range(16), key=lambda i: mp[i])]
            else:
                steps = [0] if role == "kick" else [4, 12]
            note = role_choices(pads, role)[0]
            for i in steps:
                row[i] = 100.0 if role != "chh" else 84.0
                pick[i] = note
        return bar, picked

    first = ensure_core(*make_bar(0))
    # Дежавю (как в Marbles): для каждого шага следующих тактов — повторить первый такт или взять вариацию.
    # Вариация считается всегда с одной и той же силой, а жребий по шагам — отдельным генератором,
    # поэтому ручка действует плавно: чем больше дежавю, тем больше шагов совпадает с первым тактом.
    keep = random.Random(seed * 7919 + 1)
    dv = max(0.0, min(1.0, deja_vu / 100.0))
    out_bars = [first]
    for b in range(1, bars):
        var_bar, var_pick = ensure_core(*make_bar(b, m + (1 - m) * 0.5))
        bar, picked = {}, {}
        for role in set(first[0]) | set(var_bar):
            f_row, f_pick = first[0].get(role, [0.0] * 16), first[1].get(role, [None] * 16)
            v_row, v_pick = var_bar.get(role, [0.0] * 16), var_pick.get(role, [None] * 16)
            take = [keep.random() < dv for _ in range(16)]
            bar[role] = [f_row[i] if take[i] else v_row[i] for i in range(16)]
            picked[role] = [f_pick[i] if take[i] else v_pick[i] for i in range(16)]
        for role in CORE:                           # смесь опустошила роль — берём её из первого такта
            hat = role == "chh" and ohh_sounds and any(bar.get("ohh") or [])
            if not any(bar.get(role) or []) and not hat:
                bar[role], picked[role] = list(first[0][role]), list(first[1][role])
        out_bars.append((bar, picked))

    off = (max(50, min(75, swing)) / 100.0 - 0.5) * 0.5
    notes, grid = {}, {}
    for b, (bar, picked) in enumerate(out_bars):
        for role, row in bar.items():
            g = grid.setdefault(role, [0.0] * (16 * bars))
            for s, vel in enumerate(row):
                note = picked[role][s]
                if not vel or note is None:
                    continue
                g[b * 16 + s] = round(vel / 127.0, 3)
                key = (note, b * 16 + s)
                if float(round(vel)) > notes.get(key, (0.0, ""))[0]:
                    notes[key] = (float(round(vel)), role)
    result = []
    for (note, step), (vel, role) in notes.items():
        shift = off if step % 2 else 0.0
        result.append({"noteNumber": note, "role": role, "startTime": step * 0.25 + shift,
                       "duration": 0.25 - shift, "velocity": max(1.0, min(127.0, vel)), "offVelocity": 0.0})
    result.sort(key=lambda n: (n["startTime"], n["noteNumber"]))
    return {"notes": result, "length": bars * 4.0, "grid": grid, "pattern": ref["id"]}
