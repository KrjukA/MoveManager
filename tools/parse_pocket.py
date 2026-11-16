"""Разовый разбор буклета Pocket Operations (P. Wenzel, 2019) в patterns/pocket_operations.json.
Запуск: python3 tools/parse_pocket.py docs/sources/pocket-operations-2019.pdf (нужен pypdf)."""
import json
import logging
import re
import sys

import pypdf

CODES = {"BD": "kick", "SN": "snare", "CH": "chh", "OH": "ohh", "CL": "clap", "RS": "rim", "CY": "ride",
         "CB": "cowbell", "SH": "shaker", "LT": "tom_low", "MT": "tom_mid", "HT": "tom_high"}
SECTION_GENRE = {"breaks": "Breaks", "drum rolls": "Fills", "ghost snares": "Ghost Snares"}
NAME_GENRE = [("DRUM AND BASS", "Drum and Bass"), ("DUBSTEP", "Dubstep"), ("TRAP", "Trap"),
              ("FOOTWORK", "Footwork"), ("JUNGLE", "Jungle"), ("GARAGE", "UK Garage"),
              ("TECHNO", "Techno"), ("HOUSE", "House"), ("ELECTRO", "Electro"), ("HIP HOP", "Hip Hop")]


def split_steps(text):
    out = []
    for tok in text.split():
        i = 0
        while i < len(tok):
            prev = out[-1] if out else 0
            two = int(tok[i:i + 2]) if i + 1 < len(tok) else None
            if two is not None and 10 <= two <= 16 and two > prev:
                out.append(two)
                i += 2
            else:
                out.append(int(tok[i]))
                i += 1
    return [s for s in out if 1 <= s <= 16]


def genre_for(section, name):
    for key, g in NAME_GENRE:
        if key in name:
            return g
    low = section.lower()
    for key, g in SECTION_GENRE.items():
        if key in low:
            return g
    return section.strip().title() if section else "Other"


def parse(path):
    logging.disable(logging.CRITICAL)
    text = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(path).pages[6:])
    pats, section, cur = [], "", None
    for raw in text.splitlines():
        line = raw.strip().replace(" ", "").replace(" ", "")
        if not line or re.fullmatch(r"b\d+", line) or line.startswith("AC"):
            continue
        m = re.fullmatch(r"([A-Z]{2})\s*([\d\s]*)", line)
        if m and m.group(1) in CODES and cur is not None:
            cur["rows"][CODES[m.group(1)]] = split_steps(m.group(2))
            continue
        name = re.sub(r"^↳\s*(OR\s+)?(FOLLOW WITH\s+)?", "", line).strip()
        if name.upper() == name and re.search(r"[A-Z]", name):
            cur = {"name": name, "section": section, "rows": {}}
            pats.append(cur)
        else:
            section = line
    return [p for p in pats if p["rows"]]


def build(pats):
    out, i = [], 0
    while i < len(pats):
        p = pats[i]
        m = re.fullmatch(r"(.*?)\s*-\s*A", p["name"])
        nxt = pats[i + 1] if i + 1 < len(pats) else None
        if m and nxt and re.fullmatch(re.escape(m.group(1)) + r"\s*-\s*B", nxt["name"]):
            name, bars, i = m.group(1), [p, nxt], i + 2
        else:
            name, bars, i = p["name"], [p], i + 1
        n = 16 * len(bars)
        hits = {}
        for b, bar in enumerate(bars):
            for role, st in bar["rows"].items():
                row = hits.setdefault(role, [0.0] * n)
                for s in st:
                    row[b * 16 + s - 1] = 0.8
        for row in hits.values():           # дорожки первого такта без второго — длина уже n
            pass
        out.append({"name": name, "genre": genre_for(p["section"], name), "steps": n, "hits": hits})
    return out


if __name__ == "__main__":
    res = build(parse(sys.argv[1]))
    with open("patterns/pocket_operations.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=0)
    print(len(res), "patterns")
