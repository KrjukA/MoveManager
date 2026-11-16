"""История версий проекта: Song.abl до каждой правки + что за правка шла следом.

Версия — пара файлов в папке истории: <id>.abl (байты Song.abl) и <id>.json ({"action", "savedAt"}).
id = ГГГГММДД-ЧЧММСС-mmm, при совпадении — с суффиксом -2, -3… (без «:», чтобы работало на Windows).
"""
import json
import re
import time
from pathlib import Path

KEEP = 20
ID_RE = re.compile(r"(\d{8})-(\d{6})-(\d{3})(?:-(\d+))?")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _key(vid):
    """Порядок версий: время, затем номер совпадения."""
    m = ID_RE.fullmatch(vid)
    return (m.group(1), m.group(2), m.group(3), int(m.group(4) or 1))


def _ids(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted((p.stem for p in folder.glob("*.abl") if ID_RE.fullmatch(p.stem)), key=_key)


def save_version(folder, song_bytes, action, now=None):
    """Сохраняет версию и возвращает её id; лишние сверх KEEP удаляются после записи."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    now = time.time() if now is None else now
    base = time.strftime("%Y%m%d-%H%M%S", time.localtime(now)) + f"-{int(now * 1000) % 1000:03d}"
    vid, n = base, 2
    while (folder / f"{vid}.abl").exists():
        vid, n = f"{base}-{n}", n + 1
    tmp = folder / f".{vid}.tmp"
    tmp.write_bytes(song_bytes)
    tmp.replace(folder / f"{vid}.abl")
    meta = {"action": str(action or ""), "savedAt": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))}
    (folder / f"{vid}.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    prune(folder)
    return vid


def list_versions(folder):
    """Версии от новых к старым: {"id", "savedAt", "action", "legacy": False}."""
    out = []
    for vid in reversed(_ids(folder)):
        try:
            meta = json.loads((Path(folder) / f"{vid}.json").read_text("utf-8"))
        except (OSError, ValueError):
            meta = {}
        m = ID_RE.fullmatch(vid)
        d, t = m.group(1), m.group(2)
        saved = meta.get("savedAt") or f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:{t[4:]}"
        out.append({"id": vid, "savedAt": saved, "action": meta.get("action") or "", "legacy": False})
    return out


def read_version(folder, vid):
    if not isinstance(vid, str) or not ID_RE.fullmatch(vid):
        raise ValueError("Unknown version")
    p = Path(folder) / f"{vid}.abl"
    if not p.is_file():
        raise ValueError("Unknown version")
    return p.read_bytes()


def prune(folder, keep=KEEP):
    for vid in _ids(folder)[:-keep] if keep else _ids(folder):
        for ext in (".abl", ".json"):
            (Path(folder) / f"{vid}{ext}").unlink(missing_ok=True)


def move_history(src, dst):
    """Переносит историю проекта в другую папку (новый ID сета); в существующую — дописывает файлы."""
    src, dst = Path(src), Path(dst)
    if not src.is_dir():
        return
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return
    for p in src.iterdir():
        target = dst / p.name
        if not target.exists():
            p.replace(target)
        else:
            p.unlink()
    src.rmdir()
    prune(dst)


def fmt_when(iso):
    """2026-11-16T22:56:19 → 16 Nov 22:56:19."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2}:\d{2})", iso or "")
    if not m:
        return iso
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(4)}"
