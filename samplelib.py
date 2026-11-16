"""Сэмплы и пресеты Move: ссылки на файлы пользовательской библиотеки, план переноса, переписывание ссылок.
Только стандартная библиотека, без ввода-вывода — устройство обслуживает app.py."""
import json
import posixpath
import re
from urllib.parse import quote, unquote

URI_PREFIX = "ableton:/user-library/"
ABS_PREFIX = "/data/UserData/UserLibrary/"
URI_SAFE = "/()!$&'*+,;=:@~"
JSON_STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')


def uri_to_rel(uri):
    """ableton:/user-library/Samples/a%20b.wav → Samples/a b.wav; чужие URI → None."""
    if not isinstance(uri, str) or not uri.startswith(URI_PREFIX):
        return None
    return unquote(uri[len(URI_PREFIX):])


def rel_to_uri(rel):
    return URI_PREFIX + quote(rel, safe=URI_SAFE)


def _ref_of(value):
    """(rel, вид) для строки-ссылки: 'uri' — ableton:/user-library/…, 'abs' — /data/UserData/UserLibrary/…"""
    if value.startswith(URI_PREFIX):
        return uri_to_rel(value), "uri"
    if value.startswith(ABS_PREFIX):
        return value[len(ABS_PREFIX):], "abs"
    return None, None


def _strings(text):
    for m in JSON_STRING.finditer(text):
        raw = m.group(1)
        if "user-library" not in raw and "UserLibrary" not in raw:
            continue
        try:
            value = json.loads('"' + raw + '"')
        except ValueError:
            continue
        yield m, value


def find_refs(text):
    """Все ссылки текста (JSON) на файлы пользовательской библиотеки — относительные пути."""
    out = []
    for _, value in _strings(text):
        rel, _kind = _ref_of(value)
        if rel:
            out.append(rel)
    return out


def build_index(sources):
    """{rel: [имя файла-источника, …]} по текстам источников (проекты, пресеты, состояние Schwung)."""
    idx = {}
    for name, text in sources.items():
        for rel in set(find_refs(text)):
            idx.setdefault(rel, []).append(name)
    for v in idx.values():
        v.sort()
    return idx


def safe_rel(rel):
    """Путь внутри библиотеки: относительный, без «..», без пустых частей."""
    if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel or "\x00" in rel:
        return False
    parts = rel.split("/")
    return all(p not in ("", ".", "..") for p in parts)


def expand_moves(moves, files):
    """Перенос папки раскрывается в перенос всех файлов внутри (с вложенными папками)."""
    out = []
    fileset = set(files)
    for old, new in moves:
        if old in fileset:
            out.append((old, new))
            continue
        prefix = old.rstrip("/") + "/"
        for f in sorted(files):
            if f.startswith(prefix):
                out.append((f, new.rstrip("/") + "/" + f[len(prefix):]))
    return out


def make_plan(moves, files, sources):
    """План: какие файлы куда, какие источники и сколько ссылок в каждом поменяется, конфликты."""
    flat = expand_moves(moves, files)
    conflicts = []
    leaving = {o for o, _ in flat}
    targets = set()
    for old, new in moves:
        if not (safe_rel(old) and safe_rel(new)):
            conflicts.append(new)
    for old, new in flat:
        if not safe_rel(new) or (new in set(files) and new not in leaving) or new in targets:
            conflicts.append(new)
        targets.add(new)
    mapping = dict(flat)
    touch = {}
    for name, text in sources.items():
        n = sum(1 for rel in find_refs(text) if rel in mapping)
        if n:
            touch[name] = n
    return {"moves": flat, "touch": touch, "conflicts": sorted(set(conflicts))}


def rewrite(text, mapping):
    """Заменяет ссылки rel→новый rel во всех строках текста, сохраняя вид ссылки (URI или абсолютный путь)
    и остальной текст байт в байт. Возвращает (текст, число замен)."""
    pieces, last, n = [], 0, 0
    for m, value in _strings(text):
        rel, kind = _ref_of(value)
        if rel not in mapping:
            continue
        new = rel_to_uri(mapping[rel]) if kind == "uri" else ABS_PREFIX + mapping[rel]
        pieces.append(text[last:m.start()])
        pieces.append(json.dumps(new, ensure_ascii=False))
        last = m.end()
        n += 1
    pieces.append(text[last:])
    return "".join(pieces), n


SET_PREFIX = re.compile(r"^Set\s+(\d+)\s+(.*)$", re.I)


def suggest_names(rel, projects):
    """Имена по проекту для безликого ресемпла: «Set 93 Bounce 4 - 100 bpm.wav» + «Slow» → «Slow - Bounce 4 - 100 bpm.wav».
    Проект с тем же номером «Set NN» — первым. Нет проектов — нет предложений."""
    base = posixpath.basename(rel)
    m = SET_PREFIX.match(base)
    rest, num = (m.group(2), m.group(1)) if m else (base, None)
    order = sorted(projects, key=lambda p: 0 if num and re.fullmatch(rf"Set\s+{num}", p.strip(), re.I) else 1)
    return [f"{p} - {rest}" for p in order]
