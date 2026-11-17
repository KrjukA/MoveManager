#!/usr/bin/env python3
"""Move Manager — локальный менеджер проектов Ableton Move.

Запуск:  python3 app.py     (откроется http://127.0.0.1:8765)
Нужен только пакет requests:  python3 -m pip install requests
"""
import copy
import hashlib
import io
import json
import math
import mimetypes
import os
import platform
import re
import shlex
import shutil
import subprocess
import tarfile
import traceback
import sys
import threading
import time
import uuid
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests

import drumgen
import history
import loops
import samplelib
from midi import MidiError, _no_overlaps, clip_to_midi, midi_to_notes

APP_DIR = Path(__file__).resolve().parent
FROZEN = bool(getattr(sys, "frozen", False))       # собранное приложение (PyInstaller)
APP_NAME = "KRJUK Move Manager"


def user_data_dir(frozen, platform, env, home):
    """Где лежат личные данные (вход на Move, ключ, кэш, копии). Из исходников — рядом с app.py, как всегда;
    в собранном приложении — в папке пользователя, потому что папка самого приложения временная или только для чтения."""
    if not frozen:
        return APP_DIR
    if platform.startswith("win"):
        return Path(env.get("APPDATA") or (Path(home) / "AppData" / "Roaming")) / APP_NAME
    if platform == "darwin":
        return Path(home) / "Library" / "Application Support" / APP_NAME
    return Path(env.get("XDG_DATA_HOME") or (Path(home) / ".local" / "share")) / "move-manager"


def resource_dir(frozen, meipass):
    """Где лежат файлы программы (страница, рисунки ударных): внутри сборки или рядом с app.py."""
    return Path(meipass) if frozen and meipass else APP_DIR


RES_DIR = resource_dir(FROZEN, getattr(sys, "_MEIPASS", None))
DATA_DIR = user_data_dir(FROZEN, sys.platform, os.environ, Path.home())
CONFIG_PATH = DATA_DIR / "config.json"
CACHE_DIR = DATA_DIR / "cache"
STATIC_DIR = RES_DIR / "static"
KNOWN_HOSTS = DATA_DIR / "known_hosts"


def backups_dir():
    return DATA_DIR / "backups"
PORT = int(os.environ.get("MOVE_MANAGER_PORT", "8765"))
LOCK = threading.RLock()
STARTED = time.time()
BUILD = "55"          # номер сборки: виден в шапке программы и в журнале экспорта
VERSION = "1.1"       # версия для друзей (релиз v1.1); в свойствах Mac-приложения и в отчёте
RENDER_LOCK = threading.Lock()
AUDIO_EXTS = {".wav", ".mp3", ".webm", ".m4a", ".mp4", ".ogg"}


# ───────────────────────── конфигурация ─────────────────────────

def load_config():
    cfg = {
        "move_url": "http://move.local",
        "library": str(Path.home() / "Music" / "Move Library"),
        "cookies": {},
        "move_order": [],
        "move_meta": {},
        "audio_format": "wav",
        "ssh_enabled": False,
    }
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text("utf-8")))
        except Exception:
            pass
    return cfg


CFG = load_config()


def save_config():
    with LOCK:
        tmp = CONFIG_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(CFG, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(CONFIG_PATH)


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except Exception:
        return default


def write_json(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(path)


# ───────────────────────── ошибки ─────────────────────────

def render_log(msg):
    """Журнал экспорта звука: что именно отвечает Move на каждом шаге (cache/render.log)."""
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        path = CACHE_DIR / "render.log"
        if path.exists() and path.stat().st_size > 200_000:
            path.write_text("", "utf-8")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


class AuthRequired(Exception):
    pass


class MoveOffline(Exception):
    pass


class AppError(Exception):
    pass


class SshError(AppError):
    pass


# ───────────────────────── разбор Song.abl ─────────────────────────

RACK_KINDS = {"instrumentRack", "audioEffectRack", "midiEffectRack"}
ROLE_WORDS = [
    ("drum", "Drums"), ("kit", "Drums"), ("perc", "Drums"), ("808", "Drums"),
    ("bass", "Bass"), ("sub", "Bass"),
    ("pad", "Pad"), ("lead", "Lead"), ("arp", "Arp"), ("pluck", "Pluck"),
    ("key", "Keys"), ("piano", "Keys"), ("organ", "Keys"),
    ("string", "Strings"), ("brass", "Brass"), ("mallet", "Mallets"), ("bell", "Mallets"),
    ("guitar", "Guitar"), ("vox", "Vocal"), ("voice", "Vocal"), ("vocal", "Vocal"),
    ("fx", "FX"), ("effect", "FX"), ("ambient", "Pad"), ("texture", "Pad"),
    ("synth", "Synth"), ("sampler", "Sampler"),
]


def parse_preset_uri(uri):
    """ableton:/user-library/Track%20Presets/Bass/Name.ablpreset → источник, папки, имя."""
    if not uri:
        return None
    path = unquote(uri.split(":", 1)[-1]).strip("/")
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    if parts[0] == "packs" and len(parts) > 1:
        source, rest = parts[1], parts[2:]
    else:
        source, rest = parts[0], parts[1:]
    if rest and rest[0] == "Track Presets":
        rest = rest[1:]
    stem = re.sub(r"\.(ablpreset|json|adg|adv)$", "", rest[-1]) if rest else ""
    return {"source": source, "folders": rest[:-1], "name": stem}


def find_instrument(devices):
    """Первое не-rack устройство в цепочке — сам инструмент."""
    for dev in devices or []:
        kind = dev.get("kind")
        if kind == "drumRack":
            return dev
        if kind in RACK_KINDS:
            for chain in dev.get("chains") or []:
                found = find_instrument(chain.get("devices"))
                if found:
                    return found
        elif kind:
            return dev
    return None


def collect_samples(node, out):
    if isinstance(node, dict):
        uri = node.get("sampleUri")
        if isinstance(uri, str) and uri:
            out.append(unquote(uri).split("/")[-1])
        for v in node.values():
            collect_samples(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_samples(v, out)


def guess_role(folders, names, kind, track_kind):
    for text in list(reversed(folders)) + names:
        low = (text or "").lower()
        for word, role in ROLE_WORDS:
            if word in low:
                return role
    if kind == "drumRack":
        return "Drums"
    if kind == "melodicSampler":
        return "Sampler"
    if track_kind == "audio":
        return "Audio"
    return "Synth" if kind else "—"


def parse_song(song):
    tracks = []
    for i, tr in enumerate(song.get("tracks") or []):
        devices = tr.get("devices") or []
        top = devices[0] if devices else {}
        preset = parse_preset_uri(top.get("presetUri"))
        inst = find_instrument(devices) or {}
        kind = inst.get("kind") or ""
        folders = preset["folders"] if preset else []
        audio = tr.get("kind") == "audio"            # на аудиодорожке устройства — эффекты: имя и роль не по ним
        name = tr.get("name") or ("Audio" if audio else top.get("name") or (preset or {}).get("name") or kind or f"Track {i + 1}")
        samples = []
        collect_samples(devices, samples)
        clips = sum(1 for s in tr.get("clipSlots") or [] if s.get("clip"))
        pan = (tr.get("mixer") or {}).get("pan", 0)
        if isinstance(pan, dict):
            pan = pan.get("value", 0)
        tracks.append({
            "index": i,
            "name": name,
            "preset": (preset or {}).get("name") or "",
            "folders": folders,
            "source": (preset or {}).get("source") or "",
            "kind": kind,
            "trackKind": tr.get("kind") or "",
            "clipKind": track_clip_kind(tr),
            "role": "Audio" if audio else guess_role(folders, [name, (preset or {}).get("name") or ""], kind, tr.get("kind")),
            "clips": clips,
            "pan": pan if isinstance(pan, (int, float)) else 0,
            "color": tr.get("color"),
            "samples": samples[:24],
            "sampleCount": len(samples),
        })
    ts = song.get("timeSignature") or {}
    return {
        "rootNote": song.get("rootNote"),
        "scale": song.get("scale"),
        "tempo": song.get("tempo"),
        "timeSignature": f"{ts.get('upper', 4)}/{ts.get('lower', 4)}",
        "scenes": len(song.get("scenes") or []),
        "tracks": tracks,
        "clips": clips_grid(song),
        "schwung": "/Schwung/" in json.dumps([t.get("devices") for t in song.get("tracks") or []]).replace("%20", " ")
                   or any("Schwung" in t["folders"] for t in tracks),
    }


def clips_grid(song):
    """Сетка клипов: по дорожкам, по сценам — {"notes", "length"} или None."""
    grid = []
    for tr in song.get("tracks") or []:
        row = []
        for slot in tr.get("clipSlots") or []:
            c = (slot or {}).get("clip")
            if c:
                region = c.get("region") or {}
                length = float(region.get("end", 0.0)) - float(region.get("start", 0.0))
                if c.get("sampleUri") is not None:       # аудиоклип: ссылка на сэмпл библиотеки
                    row.append({"audio": True, "sample": unquote(str(c.get("sampleUri"))).rsplit("/", 1)[-1],
                                "tempo": (c.get("warping") or {}).get("tempoAfterLastMarker"),
                                "transpose": c.get("transpose", 0), "notes": 0, "length": length})
                else:
                    row.append({"notes": len(c.get("notes") or []), "length": length})
            else:
                row.append(None)
        grid.append(row)
    return grid


def _slot(song, track, scene):
    tracks = song.get("tracks") or []
    if not 0 <= track < len(tracks):
        raise AppError("No such track in the project")
    slots = tracks[track].get("clipSlots") or []
    if not 0 <= scene < len(slots):
        raise AppError("No such scene in the project")
    return tracks[track], slots[scene]


def get_clip(song, track, scene):
    _, slot = _slot(song, track, scene)
    if not slot.get("clip"):
        raise AppError("Cell is empty")
    return slot["clip"]


def remove_clip(song, track, scene):
    """Очищает ячейку: клипа нет — ошибка (чтобы не писать проект впустую)."""
    _, slot = _slot(song, track, scene)
    if not slot.get("clip"):
        raise AppError("Cell is empty")
    slot["clip"] = None
    return song


def put_clip(song, track, scene, notes, length):
    """Ставит клип с нотами в ячейку. Длина — вверх до целого такта, не меньше одного такта."""
    tr, slot = _slot(song, track, scene)
    if tr.get("kind") != "midi":
        raise AppError("A MIDI clip can only go into a MIDI track")
    ts = dict(song.get("timeSignature") or {"upper": 4, "lower": 4})
    bar = int(ts.get("upper", 4)) * 4 / int(ts.get("lower", 4))
    bars = max(1, math.ceil(round(float(length) / bar, 6)))
    total = float(bars * bar)
    template = None
    for t in song.get("tracks") or []:
        for sl in t.get("clipSlots") or []:
            c = (sl or {}).get("clip")
            if c and c.get("sampleUri") is None:      # образец — только MIDI-клип, иначе протекут поля сэмпла
                template = c
                break
        if template:
            break
    if template:
        clip = {k: copy.deepcopy(v) for k, v in template.items() if k not in ("notes", "envelopes")}
    else:
        clip = {"isPlaying": False, "name": "", "color": None, "isEnabled": True,
                "grooveId": None, "stepEditorScrollPosition": 0}
    clip.update({"isPlaying": False, "name": "", "timeSignature": ts,
                 "region": {"start": 0.0, "end": total, "loop": {"start": 0.0, "end": total, "isEnabled": True}},
                 "notes": list(notes), "envelopes": []})
    slot["clip"] = clip
    return song


class CellBusy(AppError):
    """Ячейка-цель занята, а замена не разрешена (маршрут отвечает 409)."""
    def __init__(self, message="Cell is occupied", cells=None):
        super().__init__(message)
        self.cells = cells


def track_clip_kind(track):
    """Вид дорожки для операций с клипами: drums (Drum Rack), melodic (другая MIDI-дорожка), audio."""
    if (track or {}).get("kind") == "audio":
        return "audio"
    inst = find_instrument((track or {}).get("devices")) or {}
    return "drums" if inst.get("kind") == "drumRack" else "melodic"


KIND_WORDS = {"drums": "a Drum Rack track", "melodic": "a melodic track", "audio": "an audio track"}


def clip_op(song, op, src, dst, replace=False):
    """Копия, перенос или обмен клипов внутри проекта — одним изменением song.
    Клип берётся целиком (ноты, длина, имя, цвет, огибающие); ударные — только на ударные, мелодия — на мелодию."""
    if op not in ("copy", "move", "swap"):
        raise AppError("Unknown clip operation")
    (st, ss), (dt, ds) = (int(src[0]), int(src[1])), (int(dst[0]), int(dst[1]))
    s_track, s_slot = _slot(song, st, ss)
    d_track, d_slot = _slot(song, dt, ds)
    if (st, ss) == (dt, ds):
        raise AppError("Pick a different cell")
    a, b = s_slot.get("clip"), d_slot.get("clip")
    if op == "swap" and not a:                       # пустой источник при обмене — переносим клип цели сюда
        (s_track, s_slot, a), (d_track, d_slot, b) = (d_track, d_slot, b), (s_track, s_slot, a)
    if not a:
        raise AppError("Cell is empty")
    sk, dk = track_clip_kind(s_track), track_clip_kind(d_track)
    if sk != dk:
        raise AppError(f"A clip from {KIND_WORDS[sk]} can only go to {KIND_WORDS[sk]}")
    if b and op != "swap" and not replace:
        raise CellBusy("Cell is occupied")
    moved = copy.deepcopy(a)
    moved["isPlaying"] = False
    if op == "swap" and b:
        back = copy.deepcopy(b)
        back["isPlaying"] = False
        s_slot["clip"] = back
    elif op in ("move", "swap"):
        s_slot["clip"] = None
    d_slot["clip"] = moved
    return song


def find_song_entry(zf):
    for name in zf.namelist():
        if name.split("/")[-1] == "Song.abl":
            return name
    raise AppError("Song.abl not found in the bundle")


def read_song(bundle_path):
    with zipfile.ZipFile(bundle_path) as zf:
        return json.loads(zf.read(find_song_entry(zf)).decode("utf-8"))


def edit_song(song, order=None, pans=None, key=None):
    """Меняет тональность сета, панораму и порядок дорожек. pans: {исходный индекс дорожки: -1..1}."""
    tracks = song.get("tracks") or []
    if key and ("rootNote" in key or "scale" in key):
        root, scale = int(key.get("rootNote", -1)), str(key.get("scale") or "").strip()
        if not 0 <= root <= 11 or not scale or len(scale) > 60:
            raise AppError("Invalid key")
        song["rootNote"], song["scale"] = root, scale
    if key and key.get("tempo") is not None:
        try:
            tempo = round(float(key["tempo"]), 2)
        except (TypeError, ValueError):
            raise AppError("Invalid tempo")
        if not 40 <= tempo <= 300:
            raise AppError("Tempo must be between 40 and 300 bpm")
        song["tempo"] = tempo
    for key, val in (pans or {}).items():
        i = int(key)
        if not 0 <= i < len(tracks):
            raise AppError("Invalid track number")
        v = max(-1.0, min(1.0, float(val)))
        mixer = tracks[i].setdefault("mixer", {})
        if isinstance(mixer.get("pan"), dict):
            mixer["pan"]["value"] = v
        else:
            mixer["pan"] = v
    if order:
        if sorted(order) != list(range(len(tracks))):
            raise AppError(f"Invalid track order: the project has {len(tracks)} tracks")
        song["tracks"] = [tracks[i] for i in order]
    return song


def dump_song(song):
    return json.dumps(song, ensure_ascii=False, indent=2).encode("utf-8")


def edit_bundle(src, dst, order=None, pans=None, key=None):
    """Применяет правки к Song.abl внутри бандла и пишет новый бандл."""
    with zipfile.ZipFile(src) as zi:
        entry = find_song_entry(zi)
        song = edit_song(json.loads(zi.read(entry).decode("utf-8")), order, pans, key)
        payload = dump_song(song)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
            for item in zi.infolist():
                zo.writestr(item.filename, payload if item.filename == entry else zi.read(item.filename))
    return song


# ───────────────────────── клиент Move ─────────────────────────

class Move:
    def __init__(self):
        self.s = requests.Session()
        for k, v in (CFG.get("cookies") or {}).items():
            self.s.cookies.set(k, v)

    @property
    def base(self):
        return CFG["move_url"].rstrip("/")

    def req(self, method, path, timeout=20, **kw):
        if os.environ.get("MOVE_MANAGER_TESTING") and urlparse(self.base).hostname not in ("127.0.0.1", "localhost"):
            raise MoveOffline("Tests must not reach a real Move over HTTP")
        headers = kw.pop("headers", {})
        headers.setdefault("Referer", self.base + "/data/Sets")
        try:
            r = self.s.request(method, urljoin(self.base + "/", path.lstrip("/")),
                               timeout=timeout, headers=headers, **kw)
        except requests.exceptions.RequestException as e:
            raise MoveOffline(str(e))
        if r.status_code == 401:
            raise AuthRequired()
        return r

    def _persist_cookies(self):
        CFG["cookies"] = requests.utils.dict_from_cookiejar(self.s.cookies)
        save_config()

    def start_challenge(self):
        r = self.req("POST", "/api/v1/challenge")
        if r.status_code >= 400:
            raise AppError("Move did not show a code. Make sure it is on and not booting.")

    def answer_challenge(self, code):
        try:
            r = self.req("POST", "/api/v1/challenge-response", json={"secret": code})
        except AuthRequired:
            return {"ok": False, "error": "Wrong code"}
        if r.status_code == 429:
            return {"ok": False, "error": f"Too many attempts, wait {r.headers.get('retry-after', '60')} s"}
        if r.status_code >= 400:
            return {"ok": False, "error": f"Authorization error ({r.status_code})"}
        token = r.headers.get("Ableton-Challenge-Response-Token")
        if token:
            self.s.headers["Ableton-Challenge-Response-Token"] = token
        self._persist_cookies()
        return {"ok": True}

    def list_sets(self):
        r = self.req("GET", "/api/v1/data/Sets")
        if r.status_code >= 400:
            raise AppError(f"Move answered {r.status_code}")
        return r.json().get("objects", [])

    def download(self, oid, dest, progress=None):
        r = self.req("GET", f"/api/v1/data/Sets/{oid}", stream=True, timeout=(10, 300))
        if r.status_code != 200:
            raise AppError(f"Could not download the project ({r.status_code})")
        total = int(r.headers.get("content-length") or 0)
        done = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(done / total)
        return dest

    def upload(self, path, filename):
        with open(path, "rb") as f:
            r = self.req("POST", "/api/v1/data/Sets", timeout=(10, 600),
                         files={"file": (filename, f, "application/zip")})
        if r.status_code not in (200, 201, 204):
            raise AppError(f"Move rejected the project ({r.status_code}): {r.text[:200]}")
        try:
            for item in (r.json() or {}).get("files", []):
                if item.get("error"):
                    raise AppError(f"Move: {item['error']}")
        except ValueError:
            pass

    def recordings(self):
        r = self.req("GET", "/api/v1/files/Recordings")
        if r.status_code >= 400:
            raise AppError(f"Move did not return the recordings list ({r.status_code})")
        out = []
        for p in r.json().get("paths", []):
            if not p.get("isDirectory"):
                out.append({"name": unquote(p["path"]), "size": p.get("size", 0),
                            "modified": p.get("lastModifiedDateTime")})
        return out

    def recording_response(self, name, range_header=None):
        if "/" in name or name.startswith("."):
            raise AppError("Invalid recording name")
        headers = {"Range": range_header} if range_header else {}
        return self.req("GET", "/api/v1/files/Recordings/" + requests.utils.quote(name, safe=""),
                        stream=True, timeout=(10, 300), headers=headers)

    def rename(self, oid, name):
        r = self.req("PATCH", f"/api/v1/data/Sets/{oid}", json={"newName": name})
        if r.status_code >= 400:
            raise AppError(f"Could not rename ({r.status_code}): {r.text[:200]}")

    def delete(self, oid):
        r = self.req("DELETE", f"/api/v1/data/Sets/{oid}")
        if r.status_code >= 400:
            raise AppError(f"Could not delete ({r.status_code})")

    def render(self, oid, fmt, dest, progress=None, cancelled=None):
        """Экспорт звука сета самим Move — тот же запрос, что и «Export as Audio» в штатном менеджере.

        Некоторые сеты Move не экспортирует вовсе: принимает запрос и молчит (так же ведёт себя
        штатный менеджер). Поэтому ожидание ограничено и его можно прервать, а зависшее задание
        снимается, чтобы не задерживать следующие. Экспорты идут строго по одному."""
        cancelled = cancelled or (lambda: False)
        while not RENDER_LOCK.acquire(timeout=1):
            if cancelled():
                raise AppError("Audio export skipped")
        try:
            return self._render(oid, fmt, dest, progress, cancelled)
        finally:
            RENDER_LOCK.release()

    def _render(self, oid, fmt, dest, progress, cancelled):
        start_timeout = float(os.environ.get("MOVE_RENDER_START_TIMEOUT", "45"))
        silence_timeout = float(os.environ.get("MOVE_RENDER_SILENCE_TIMEOUT", "600"))
        r = self.req("POST", f"/api/v1/render/{oid}", params={"format": fmt}, timeout=60)
        if r.status_code >= 400:
            raise AppError(f"Move did not start the export ({r.status_code}): {r.text[:200]}")
        info = r.json()
        rid, href = info.get("id"), info.get("href")
        render_log(f"--- export (build {BUILD}): set {oid}, format {fmt}; response: {r.status_code} {r.text[:200]}")
        if not href:
            raise AppError("Move did not return an audio link")
        t0 = time.time()
        st = {"got": False, "finished": False, "failed": None, "last": t0, "logged": None}
        stop = threading.Event()

        def reader():
            # события нужны только для прогресса; короткий таймаут чтения — чтобы поток не зависал
            while not stop.is_set():
                try:
                    ev = self.s.get(self.base + "/api/v1/render", stream=True, timeout=(10, 20),
                                    headers={"Accept": "text/event-stream"})
                    for raw in ev.iter_lines(chunk_size=1):
                        if stop.is_set():
                            break
                        line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
                        if not line.startswith("data:"):
                            continue
                        try:
                            d = json.loads(line[5:].strip())
                        except ValueError:
                            continue
                        if d.get("id") != rid:
                            continue
                        st["got"], st["last"] = True, time.time()
                        status = d.get("status")
                        if status != st["logged"]:
                            render_log(f"event: {line[:300]}")
                            st["logged"] = status
                        if progress and status == "finalizing":
                            progress(None)
                        elif progress and isinstance(d.get("progress"), (int, float)):
                            progress(min(1.0, float(d["progress"])))
                        if status == "finished":
                            st["finished"] = True
                        elif status in ("failed", "aborted"):
                            st["failed"] = status
                    ev.close()
                except (requests.exceptions.RequestException, AttributeError, OSError):
                    pass
                stop.wait(0.5)

        threading.Thread(target=reader, daemon=True).start()
        resp, misses, next_probe = None, 0, t0 + 5
        try:
            while resp is None:
                now = time.time()
                if cancelled():
                    render_log("export skipped by user")
                    raise AppError("Audio export skipped")
                if st["failed"]:
                    raise AppError("Move reported that the export failed")
                if not st["got"] and now - t0 > start_timeout:
                    render_log(f"Move did not start the export within {int(start_timeout)} s — job cancelled")
                    raise AppError(f"Move does not export this project: no export started within {int(start_timeout)} s. "
                                   "The built-in manager behaves the same way")
                if st["got"] and not st["finished"] and now - st["last"] > silence_timeout:
                    render_log("Move stopped sending events — job cancelled")
                    raise AppError("Move started the export but stopped responding")
                if st["finished"] or (st["got"] and now >= next_probe):
                    next_probe = now + 5
                    a = self.req("GET", href, stream=True, timeout=(10, 600))
                    if a.status_code == 200:
                        render_log(f"download {href}: 200 {a.headers.get('content-type')} {a.headers.get('content-length')}")
                        resp = a
                        break
                    body = a.text[:120]
                    a.close()
                    if st["finished"]:
                        misses += 1
                        render_log(f"download {href}, attempt {misses}: {a.status_code} {body}")
                        if misses >= 8:
                            raise AppError(f"Export finished but Move did not return the file ({a.status_code})")
                time.sleep(1)
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(1 << 16):
                    f.write(chunk)
            return dest
        finally:
            stop.set()
            if resp is None and rid is not None:
                try:
                    self.s.delete(f"{self.base}/api/v1/render/{rid}", timeout=5)
                except requests.exceptions.RequestException:
                    pass


MOVE = Move()


# ───────────────────────── SSH: слоты пэдов и правка на месте ─────────────────────────

SETS_DIR = os.environ.get("MOVE_SETS_DIR", "/data/UserData/UserLibrary/Sets")
SCHWUNG_DIR = os.environ.get("MOVE_SCHWUNG_DIR", "/data/UserData/schwung/set_state")   # состояние Schwung по сетам
SCHWUNG_SKIP = {"snapshot", "copy_source.txt"}      # Schwung сам пересоздаёт их для нового сета
SCHWUNG_FILE = "schwung_state.tar.gz"
SSH_KEY = DATA_DIR / "move_ssh_key"
UUID_RE = re.compile(r"[0-9a-fA-F-]{8,64}")
REFRESH = ("dbus-send --system --type=method_call --dest=com.ableton.move --print-reply "
           "/com/ableton/move/browser com.ableton.move.Browser.refreshCache >/dev/null 2>&1 || true")


def ssh_enabled():
    return bool(CFG.get("ssh_enabled"))


def ssh_cmd():
    if os.environ.get("MOVE_SSH_CMD"):
        return shlex.split(os.environ["MOVE_SSH_CMD"])
    host = urlparse(CFG["move_url"]).hostname or "move.local"
    return ["ssh", "-i", str(SSH_KEY), "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=accept-new", "-o", f'UserKnownHostsFile="{Path(KNOWN_HOSTS).as_posix()}"',
            "-o", "ConnectTimeout=8", "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3", f"ableton@{host}"]


NO_SSH_MSG = ("The ssh command was not found on this computer. On Windows 10/11 turn on "
              "Settings → System → Optional features → OpenSSH Client; on a Mac it is built in.")


class _SshSession:
    """Одна открытая оболочка на Move: команды идут в неё по очереди, без нового рукопожатия на каждую.
    У каждой команды свой конец (случайная метка) — по нему вывод отделяется от кода возврата и текста ошибки.
    Команда не может прочитать поток команд: её stdin — /dev/null."""

    def __init__(self):
        self.lock = threading.Lock()
        self.p = self.cmd = self.err = None
        self.q = None

    def close(self):
        self.q = None
        if self.p is not None:
            try:
                self.p.kill(); self.p.wait(timeout=2)
            except Exception:  # noqa: BLE001
                pass
        self.p = None

    def _start(self, cmd):
        import tempfile
        self.close()
        self.err = tempfile.TemporaryFile()
        try:
            self.p = subprocess.Popen(cmd + ["sh"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err, bufsize=0,
                                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError:
            self.p = None
            raise SshError(NO_SSH_MSG)
        self.cmd = cmd
        # ответы читает отдельный поток: select на трубах в Windows не работает
        import queue
        q, out = queue.Queue(), self.p.stdout
        def pump():
            while True:
                try:
                    chunk = out.read1(1 << 16) if hasattr(out, "read1") else os.read(out.fileno(), 1 << 16)
                except (OSError, ValueError):
                    chunk = b""
                q.put(chunk)
                if not chunk:
                    return
        threading.Thread(target=pump, daemon=True).start()
        self.q = q

    def _dead(self, why):
        msg = ""
        try:
            self.err.seek(0); msg = self.err.read().decode("utf-8", "replace").strip()[-300:]
        except Exception:  # noqa: BLE001
            pass
        self.close()
        return SshError("SSH: " + (msg or why))

    def run(self, cmd, script, timeout):
        import queue
        tok = "MMEND" + uuid.uuid4().hex
        wrapped = ("{ __mme=$( ( " + script + "\n) </dev/null 2>&1 1>&3 ); __mmr=$?; } 3>&1\n"
                   f"printf '\\n%s %d\\n' {tok} $__mmr\n"
                   '[ $__mmr -eq 0 ] || printf \'%s\' "$__mme" | head -c 400\n'
                   f"printf '\\n%sE\\n' {tok}\n").encode("utf-8")
        with self.lock:
            if self.p is None or self.p.poll() is not None or self.cmd != cmd:
                self._start(cmd)
            try:
                self.p.stdin.write(wrapped)
            except OSError:                       # соединение умерло, пока простаивало: команда ещё не ушла
                self._start(cmd)
                try:
                    self.p.stdin.write(wrapped)
                except OSError:
                    raise self._dead("connection closed")
            try:
                self.p.stdin.flush()
            except OSError:
                raise self._dead("connection closed")
            end, q, buf = f"\n{tok}E\n".encode(), self.q, bytearray()
            deadline = time.monotonic() + timeout
            while not buf.endswith(end):
                left = deadline - time.monotonic()
                if left <= 0:
                    self.close()
                    raise SshError("Move did not answer over SSH")
                try:
                    chunk = q.get(timeout=left)
                except queue.Empty:
                    continue
                if not chunk:
                    raise self._dead("connection closed")
                buf += chunk
            mark = f"\n{tok} ".encode()
            i = buf.rfind(mark)
            out, tail = bytes(buf[:i]), bytes(buf[i + len(mark):len(buf) - len(end)])
            rc_s, _, msg = tail.partition(b"\n")
            rc = int(rc_s or b"1")
            if rc != 0:
                raise SshError("SSH: " + (msg.decode("utf-8", "replace").strip()[-300:] or f"code {rc}"))
            return out


_SSH = _SshSession()


def ssh_session_reset():
    with _SSH.lock:
        _SSH.close()


def ssh_run(script, data=None, timeout=40):
    t0 = time.monotonic()
    try:
        return _ssh_run(script, data, timeout)
    finally:
        dt = time.monotonic() - t0
        if dt > 0.3:
            log_line("ssh-timing.log", f"{dt:6.2f}s {'+' + str(len(data)) + 'B ' if data else ''}{script[:120]}")


def _ssh_run(script, data=None, timeout=40):
    cmd = ssh_cmd()
    if os.environ.get("MOVE_MANAGER_TESTING") and Path(cmd[0]).name == "ssh":     # из тестов — только подменённый SSH
        raise SshError("Tests must not reach a real Move over SSH")
    if data is None:
        return _SSH.run(cmd, script, timeout)
    try:                                          # с данными на stdin — отдельное соединение
        r = subprocess.run(cmd + [script], input=data, capture_output=True, timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise SshError("Move did not answer over SSH")
    except FileNotFoundError:
        raise SshError(NO_SSH_MSG)
    if r.returncode != 0:
        raise SshError("SSH: " + (r.stderr.decode("utf-8", "replace").strip()[-300:] or f"code {r.returncode}"))
    return r.stdout


def set_dir(oid):
    if not UUID_RE.fullmatch(oid):
        raise AppError("Invalid identifier")
    return shlex.quote(f"{SETS_DIR}/{oid}")


def ssh_slots():
    """{uuid: {"slot": 0..31 | None, "color": int | None}} — где проект лежит на пэдах Move."""
    script = (f'cd {shlex.quote(SETS_DIR)} && for d in *; do [ -d "$d" ] || continue; '
              'printf "%s|%s|%s\\n" "$d" "$(getfattr --only-values -n user.song-index "$d" 2>/dev/null)" '
              '"$(getfattr --only-values -n user.song-color "$d" 2>/dev/null)"; done')
    out = {}
    for line in ssh_run(script).decode("utf-8", "replace").splitlines():
        parts = line.strip().split("|")
        if len(parts) == 3:
            out[parts[0]] = {"slot": int(parts[1]) if parts[1].isdigit() else None,
                             "color": int(parts[2]) if parts[2].isdigit() else None}
    return out


def ssh_set_slots(pairs):
    cmds = []
    for oid, slot in pairs:
        slot = int(slot)
        if not 0 <= slot <= 31:
            raise AppError("Pad number must be between 1 and 32")
        cmds.append(f"setfattr -n user.song-index -v {slot} {set_dir(oid)}")
    if cmds:
        ssh_run(" && ".join(cmds) + "; " + REFRESH)


def _schwung_dir(oid):
    if not UUID_RE.fullmatch(oid or ""):
        raise AppError("Invalid identifier")
    return shlex.quote(f"{SCHWUNG_DIR}/{oid}")


def _clean_schwung_tar(data):
    """Пересобирает архив: только обычные файлы и папки с безопасными путями, без snapshot/copy_source."""
    out = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as src, tarfile.open(fileobj=out, mode="w:gz") as dst:
        for m in src.getmembers():
            name = m.name[2:] if m.name.startswith("./") else m.name
            if name in ("", "."):
                continue
            parts = name.split("/")
            if name.startswith("/") or ".." in parts or not (m.isfile() or m.isdir()):
                raise AppError("Unsafe Schwung archive")
            if parts[0] in SCHWUNG_SKIP:
                continue
            m.name = name
            dst.addfile(m, src.extractfile(m) if m.isfile() else None)
    return out.getvalue()


def schwung_fetch(oid):
    """Состояние Schwung сета с Move (tar.gz) или None, если его нет."""
    d = _schwung_dir(oid)
    raw = ssh_run(f'if [ -d {d} ] && [ -n "$(ls -A {d})" ]; then cd {d} && tar -czf - .; fi', timeout=120)
    if not raw:
        return None
    data = _clean_schwung_tar(raw)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
        return data if any(m.isfile() for m in t.getmembers()) else None


# Слот Schwung занят, если его автосохранение длиннее 10 байт — так решает сам Schwung при загрузке слота.
# Не признаки: заготовки «{}» (3 байта), master_fx_0 по умолчанию (~543 байта в каждом сете),
# имена «Untitled» в shadow_chain_config.json — всё это есть в любом сете (проверено на настоящем Move).
SCHWUNG_USED = 'used() {{ [ -n "$(find "$1" -maxdepth 1 -name "slot_*.json" -size +10c 2>/dev/null)" ]; }}; '


def schwung_sets():
    """id сетов, у которых в слотах Schwung загружен модуль."""
    root = shlex.quote(SCHWUNG_DIR)
    out = ssh_run(SCHWUNG_USED.format() + f'[ -d {root} ] || exit 0; cd {root} && for d in */; do '
                  f'used "${{d%/}}" && echo "${{d%/}}"; done; exit 0', timeout=30)
    return {x for x in out.decode("utf-8", "replace").split() if UUID_RE.fullmatch(x)}


def schwung_restore(oid, data):
    """Кладёт состояние Schwung в папку нового сета. Только в пустую или несуществующую: «copied» / «exists»."""
    d = _schwung_dir(oid)
    data = _clean_schwung_tar(data)
    # «занято» — только если в слотах уже есть модуль; пустые заготовки «{}», которые Schwung создаёт сам, можно заменить
    out = ssh_run(SCHWUNG_USED.format() + f'if [ -d {d} ] && used {d}; then echo exists; '
                  f'else mkdir -p {d} && cd {d} && tar -xzf - && echo copied; fi', data=data, timeout=120)
    return "exists" if b"exists" in out else "copied"


# ───────────────────────── библиотека сэмплов и пресетов на Move ─────────────────────────
USERLIB_DIR = os.environ.get("MOVE_USERLIB_DIR", "/data/UserData/UserLibrary")
USERLIB_MODES = {"samples": "Samples", "presets": "Track Presets"}
USERLIB_CACHE = {}           # путь источника → (подпись «время размер», текст)
FILE_MARK = "@@MM-FILE@@ "


def _mode_root(mode):
    if mode not in USERLIB_MODES:
        raise AppError("Unknown library section")
    return USERLIB_MODES[mode]


def _check_rel(mode, rel):
    if not samplelib.safe_rel(rel) or not (rel == _mode_root(mode) or rel.startswith(_mode_root(mode) + "/")):
        raise AppError("Invalid path")
    return rel


def _q(rel):
    return shlex.quote(f"{USERLIB_DIR}/{rel}")


def lib_tree(mode):
    """Папки и файлы раздела (Samples или Track Presets) на Move: пути относительно библиотеки, размеры."""
    top = _mode_root(mode)
    out = ssh_run(f'{NEED_STAT}cd {shlex.quote(USERLIB_DIR)} && [ -d {shlex.quote(top)} ] || exit 0; '
                  f'find {shlex.quote(top)} -mindepth 1 -type d | sed "s/^/D|/"; '
                  f'find {shlex.quote(top)} -type f -exec {STAT_F} {{}} + 2>/dev/null; exit 0', timeout=60)
    folders, files = [], []
    for kind, size, _mt, path in _stat_lines(out):
        if kind == "D":
            folders.append(path)
        elif not path.endswith(".mmtmp"):
            files.append({"rel": path, "size": size})
    return {"folders": sorted(folders), "files": sorted(files, key=lambda f: f["rel"].lower())}


# Имена берутся из find/stat: BusyBox ls без UTF-8-локали печатает «?» вместо не-ASCII,
# и тогда проект с кириллицей пропал бы из индекса, а его сэмплы выглядели бы неиспользуемыми.
NEED_STAT = 'command -v stat >/dev/null 2>&1 && command -v find >/dev/null 2>&1 || { echo "MM-NO-STAT"; exit 0; }; '
STAT_F = "stat -c 'F|%s|%Y|%n'"


def _stat_lines(out):
    """Строки «D|путь» и «F|размер|время|путь» → (вид, размер, время, путь). Без stat/find — отказ, а не пустой список."""
    text = out.decode("utf-8", "replace")
    if "MM-NO-STAT" in text:
        raise AppError("Move has no find/stat commands, so the library can't be read safely")
    rows = []
    for line in text.splitlines():
        if line.startswith("D|"):
            rows.append(("D", 0, "", line[2:]))
        elif line.startswith("F|"):
            parts = line.split("|", 3)
            if len(parts) == 4 and parts[1].isdigit():
                rows.append(("F", int(parts[1]), parts[2], parts[3]))
    return rows


def _source_listing():
    """Файлы, которые могут ссылаться на сэмплы/пресеты: проекты, пресеты, эффекты, состояние Schwung."""
    lib, sw = shlex.quote(USERLIB_DIR), shlex.quote(SCHWUNG_DIR)
    out = ssh_run(f'{NEED_STAT}cd {lib} && {{ for f in Sets/*/*/Song.abl; do [ -f "$f" ] && {STAT_F} "$f"; done; '
                  f'find "Track Presets" "Audio Effects" -type f \\( -name "*.ablpreset" -o -name "*.json" \\) -exec {STAT_F} {{}} + 2>/dev/null; }}; '
                  f'[ -d {sw} ] && find {sw} -name "slot_*.json" -size +10c -size -2000k -exec {STAT_F} {{}} + 2>/dev/null; exit 0', timeout=60)
    items = {}
    for _k, size, mtime, path in _stat_lines(out):
        path = path if path.startswith("/") else f"{USERLIB_DIR}/{path}"
        items[path] = f"{mtime} {size}"
    return items


def _read_many(paths):
    """Тексты нескольких файлов устройства одним вызовом SSH."""
    if not paths:
        return {}
    script = "; ".join(f'printf "\\n{FILE_MARK}%s\\n" {shlex.quote(p)}; cat {shlex.quote(p)}' for p in paths)
    raw = ssh_run(script, timeout=120).decode("utf-8", "replace")
    out = {}
    for chunk in raw.split("\n" + FILE_MARK)[1:]:
        name, _, body = chunk.partition("\n")
        out[name] = body
    return out


def userlib_cache_drop():
    """После своих записей на Move — забыть все тексты, и в памяти, и на диске."""
    USERLIB_CACHE.clear()
    try:
        (CACHE_DIR / "userlib_sources.json").unlink()
    except OSError:
        pass


def _save_userlib_cache():
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        disk = CACHE_DIR / "userlib_sources.json"
        tmp = disk.with_suffix(".tmp")
        tmp.write_text(json.dumps(USERLIB_CACHE, ensure_ascii=False), "utf-8")
        tmp.replace(disk)
    except OSError:
        pass


def ref_sources():
    """{путь источника: текст}; неизменившиеся файлы берутся из кэша."""
    listing = _source_listing()
    disk = CACHE_DIR / "userlib_sources.json"
    if not USERLIB_CACHE:                        # после перезапуска — тексты с диска, читаются только изменившиеся
        try:
            USERLIB_CACHE.update({k: tuple(v) for k, v in json.loads(disk.read_text("utf-8")).items()})
        except (OSError, ValueError):
            pass
    stale = [p for p, sig in listing.items() if USERLIB_CACHE.get(p, (None,))[0] != sig]
    for i in range(0, len(stale), 40):
        for p, text in _read_many(stale[i:i + 40]).items():
            USERLIB_CACHE[p] = (listing.get(p), text)
    gone = [p for p in USERLIB_CACHE if p not in listing]
    for p in gone:
        USERLIB_CACHE.pop(p)
    if stale or gone or not disk.exists():
        _save_userlib_cache()
    return {p: USERLIB_CACHE[p][1] for p in listing if p in USERLIB_CACHE}


def _project_of(path):
    m = re.match(re.escape(USERLIB_DIR) + r"/Sets/([^/]+)/([^/]+)/Song\.abl$", path)
    return m.group(2) if m else None


def userlib_index():
    src = ref_sources()
    return {"refs": samplelib.build_index(src), "projects": {p: _project_of(p) for p in src if _project_of(p)}}


def userlib_plan(mode, moves):
    moves = [(_check_rel(mode, o), _check_rel(mode, n)) for o, n in moves]
    tree = lib_tree(mode)
    files, folders = [f["rel"] for f in tree["files"]], set(tree["folders"])
    plan = samplelib.make_plan(moves, files, ref_sources())
    # папка переносится целиком одной командой mv: с вложенными и пустыми папками, без пустых остатков
    for old, new in moves:
        if old in folders and (new in folders or new in files or new == old or new.startswith(old + "/")):
            plan["conflicts"].append(new)
    plan["ops"] = [[o, n] for o, n in moves if o in folders or o in set(files)]
    if not plan["moves"] and not plan["ops"]:
        raise AppError("Nothing to move")
    plan["mode"] = mode
    plan["projects"] = sorted({_project_of(p) for p in plan["touch"] if _project_of(p)})
    return plan


def _put_texts(files):
    """Записывает тексты на Move: один сжатый архив с временными «.mmtmp» рядом с целями по отдельному подключению
    (так же, как перенос Schwung — этот путь проверен на Move), затем mv каждого на место через открытое соединение."""
    buf, now = io.BytesIO(), time.time()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT, compresslevel=6) as t:
        for path, text in files.items():
            data = text.encode("utf-8")
            info = tarfile.TarInfo((path + ".mmtmp").lstrip("/"))
            info.size, info.mtime, info.mode = len(data), now, 0o644
            t.addfile(info, io.BytesIO(data))
    ssh_run("cd / && tar -xzf -", data=buf.getvalue(), timeout=180)
    ssh_run(" && ".join(f"mv {shlex.quote(p + '.mmtmp')} {shlex.quote(p)}" for p in files))


def _cache_written(texts_by_target, old_paths):
    """После своей записи: новые тексты сразу в кэш (с подписями с Move), старые пути — вон. Так после переноса
    не нужно заново читать все проекты."""
    if not texts_by_target:
        return
    out = ssh_run(f"{NEED_STAT}" + "stat -c 'F|%s|%Y|%n' " + " ".join(shlex.quote(p) for p in texts_by_target) + "; exit 0")
    sigs = {path: f"{mt} {size}" for _k, size, mt, path in _stat_lines(out)}
    for p in old_paths:
        USERLIB_CACHE.pop(p, None)
    for p, text in texts_by_target.items():
        if p in sigs:
            USERLIB_CACHE[p] = (sigs[p], text)
        else:
            USERLIB_CACHE.pop(p, None)
    _save_userlib_cache()


def apply_userlib_plan(plan, stage):
    """Применяет план: копии затронутых файлов → перенос → замена ссылок → refreshCache → проверка.
    Любая ошибка — откат: файлы на прежние места, тексты из копий."""
    if plan.get("conflicts"):
        raise AppError("The plan has conflicts: " + ", ".join(plan["conflicts"][:3]))
    moves = [(o, n) for o, n in plan["moves"]]
    ops = [(o, n) for o, n in plan.get("ops") or moves]
    mapping = dict(moves)
    prefix = USERLIB_DIR + "/"
    def target(path):        # источник, который сам переносится (пресет в перенесённой папке), пишется на новое место
        rel = path[len(prefix):] if path.startswith(prefix) else None
        return prefix + mapping[rel] if rel in mapping else path
    stage("Reading affected files")
    texts = _read_many(sorted(plan["touch"]))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (backups_dir()).mkdir(parents=True, exist_ok=True)
    for n in range(1, 1000):                       # у каждой операции своя папка копий
        bdir = backups_dir() / (f"samples-{stamp}" + (f"-{n}" if n > 1 else ""))
        try:
            bdir.mkdir()
            break
        except FileExistsError:
            continue
    manifest = {"moves": moves, "files": {}}
    for i, (path, text) in enumerate(texts.items()):
        (bdir / f"{i}.txt").write_text(text, "utf-8")
        manifest["files"][path] = f"{i}.txt"
    write_json(bdir / "manifest.json", manifest)
    done_moves, written = [], []
    try:
        stage("Moving files")
        for old, new in ops:
            ssh_run(f'[ -e {_q(new)} ] && exit 3; mkdir -p "$(dirname {_q(new)})" && mv {_q(old)} {_q(new)}')
            done_moves.append((old, new))
        stage("Updating references")
        if texts:
            _put_texts({target(path): samplelib.rewrite(text, mapping)[0] for path, text in texts.items()})
            written.extend(texts)
        stage("Checking")
        check = _read_many(sorted(target(p) for p in texts))
        wanted = sorted({rel for t in check.values() for rel in samplelib.find_refs(t) if rel in mapping.values()})
        missing = ssh_run("for f in " + " ".join(_q(r) for r in wanted) + '; do [ -e "$f" ] || echo "$f"; done; exit 0'
                          ).decode("utf-8", "replace").split() if wanted else []
        if missing:
            raise AppError("Check failed: " + missing[0])
    except (AppError, SshError) as e:
        stage("Rolling back")
        if written:
            try:
                _put_texts({target(path): texts[path] for path in written})
            except SshError:
                pass
        for old, new in reversed(done_moves):
            try:
                ssh_run(f'mkdir -p "$(dirname {_q(old)})" && mv {_q(new)} {_q(old)}')
            except SshError:
                pass
        try:                                     # тексты, что могли остаться временными
            ssh_run("rm -f " + " ".join(f"{shlex.quote(p)}.mmtmp {shlex.quote(target(p))}.mmtmp" for p in texts) + "; exit 0")
        except SshError:
            pass
        raise AppError(f"Nothing was changed: {e}")
    ssh_run(REFRESH + " || true")
    try:
        _cache_written({target(p): samplelib.rewrite(texts[p], mapping)[0] for p in written},
                       [p for p in written if target(p) != p])
    except (AppError, SshError):
        userlib_cache_drop()
    return {"moved": len(moves), "files": len(written), "backup": bdir.name}


def userlib_mkdir(mode, rel):
    ssh_run(f"mkdir -p {_q(_check_rel(mode, rel))}")


def userlib_upload(mode, folder, name, data):
    folder = _check_rel(mode, folder)
    if not samplelib.safe_rel(name) or "/" in name:
        raise AppError("Invalid file name")
    if Path(name).suffix.lower() not in (".wav", ".aif", ".aiff", ".flac", ".mp3", ".ablpreset", ".json"):
        raise AppError("Supported: WAV, AIFF, FLAC, MP3 (and presets)")
    stem, ext = Path(name).stem, Path(name).suffix
    existing = {f["rel"] for f in lib_tree(mode)["files"]}
    rel, n = f"{folder}/{name}", 2
    while rel in existing:
        rel, n = f"{folder}/{stem} {n}{ext}", n + 1
    ssh_run(f'( mkdir -p {_q(folder)} && cat > {_q(rel)}.mmtmp && mv {_q(rel)}.mmtmp {_q(rel)} ) '
            f'|| {{ rm -f {_q(rel)}.mmtmp; exit 1; }}; {REFRESH} || true',
            data=data, timeout=300)
    return rel


def userlib_delete(mode, rels):
    """Удаляет файлы и папки библиотеки на Move — только то, чем ничего не пользуется. Папка — целиком, если всё внутри свободно."""
    rels = [_check_rel(mode, r) for r in rels]
    root = _mode_root(mode)
    if any(r == root for r in rels):
        raise AppError("The section folder itself can't be deleted")
    tree = lib_tree(mode)
    folders, files = set(tree["folders"]), [f["rel"] for f in tree["files"]]
    refs = userlib_index()["refs"]
    for r in rels:
        inside = [f for f in files if f.startswith(r + "/")] if r in folders else [r]
        used = [f for f in inside if refs.get(f)]
        if used:
            raise AppError(f"Still used by projects or presets: {used[0]}")
    ssh_run("rm -rf " + " ".join(_q(r) for r in rels) + f" || exit 1; {REFRESH} || true")


# ───────────────────────── компьютер ↔ Move: две панели ─────────────────────────

def fs_roots(platform, home):
    """Где можно ходить по папкам компьютера: домашняя папка и внешние диски (Mac — /Volumes, Windows — все диски)."""
    if platform.startswith("win"):
        return [str(home)] + [f"{c}:\\" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.isdir(f"{c}:\\")]
    return [str(home), "/Volumes"] if platform == "darwin" else [str(home), "/media", "/mnt"]


FS_ROOTS = None if sys.platform.startswith("win") else fs_roots(sys.platform, Path.home())   # Windows: диски — при каждом обращении
FS_EXT = {"samples": {".wav", ".aif", ".aiff", ".flac", ".mp3"}, "presets": {".ablpreset", ".json"}}
FS_SHOW = {"samples": FS_EXT["samples"], "presets": {".ablpreset"}}


def _fs_ext(mode):
    if mode not in FS_EXT:
        raise AppError("Unknown library section")
    return FS_EXT[mode]


def _roots():
    return FS_ROOTS if FS_ROOTS is not None else fs_roots(sys.platform, Path.home())


def fs_check(path, must_dir=False):
    """Путь на компьютере внутри разрешённых корней (после раскрытия ссылок и «..»)."""
    try:
        p = Path(str(path)).expanduser().resolve()
    except (OSError, RuntimeError):
        raise AppError("Invalid path")
    for r in _roots():
        root = Path(r).resolve()
        if p == root or root in p.parents:
            if not p.exists():
                raise AppError("Not found: " + p.name)
            if must_dir and not p.is_dir():
                raise AppError("Not a folder: " + p.name)
            return p
    raise AppError("This folder is outside your home folder and external drives")


def _fs_root_of(p):
    return any(p == Path(r).resolve() for r in _roots())


def fs_list(path, mode):
    p = fs_check(path, must_dir=True)
    show = FS_SHOW.get(mode) or _fs_ext(mode)
    folders, files = [], []
    try:
        entries = list(os.scandir(p))
    except OSError as e:
        raise AppError(f"Can't open the folder: {e.strerror or e}")
    for e in entries:
        if e.name.startswith("."):
            continue
        try:
            if e.is_dir():
                folders.append(e.name)
            elif e.is_file() and Path(e.name).suffix.lower() in show:
                files.append({"name": e.name, "size": e.stat().st_size})
        except OSError:
            continue
    return {"path": p.as_posix(), "parent": None if _fs_root_of(p) else p.parent.as_posix(),
            "folders": sorted(folders, key=str.lower), "files": sorted(files, key=lambda f: f["name"].lower())}


def unique_name(name, taken):
    """«snare.wav» → «snare 2.wav», если имя занято; у папок — «Kits 2»."""
    if name not in taken:
        return name
    stem, ext = (Path(name).stem, Path(name).suffix) if Path(name).suffix else (name, "")
    n = 2
    while f"{stem} {n}{ext}" in taken:
        n += 1
    return f"{stem} {n}{ext}"


def _fs_name(name):
    name = str(name or "").strip()
    if not name or "/" in name or "\\" in name or name in (".", "..") or name.startswith("."):
        raise AppError("Invalid name")
    return name


def fs_mkdir(parent, name):
    d = fs_check(parent, must_dir=True) / _fs_name(name)
    if d.exists():
        raise AppError(f'"{d.name}" already exists here')
    d.mkdir()
    return d.as_posix()


def fs_rename(path, name):
    p = fs_check(path)
    if _fs_root_of(p):
        raise AppError("This folder can't be renamed here")
    t = p.parent / _fs_name(name)
    if t == p:
        return p.as_posix()
    if t.exists():
        raise AppError(f'"{t.name}" already exists here')
    p.rename(t)
    return t.as_posix()


def fs_move(src, dst_dir):
    s, d = fs_check(src), fs_check(dst_dir, must_dir=True)
    if d == s or s in d.parents:
        raise AppError("A folder can't be moved into itself")
    if d == s.parent:
        return s.as_posix()
    target = d / s.name
    if target.exists():
        raise AppError(f'"{s.name}" already exists there')
    shutil.move(str(s), str(target))
    return target.as_posix()


def copy_to_move(mode, paths, folder, stage):
    """Копирует файлы и папки с компьютера в папку библиотеки на Move. Существующее не трогается: занятые имена получают « 2»."""
    folder = _check_rel(mode, folder)
    allowed = _fs_ext(mode)
    tree = lib_tree(mode)
    taken = {f["rel"] for f in tree["files"]} | set(tree["folders"])
    here = lambda: {r.split("/")[-1] for r in taken if r.rsplit("/", 1)[0] == folder}
    plan, skipped = [], 0
    for raw in paths:
        p = fs_check(raw)
        if p.is_dir():
            top = unique_name(p.name, here())
            taken.add(f"{folder}/{top}")
            for dirpath, dirs, files in os.walk(p):
                dirs[:] = sorted(x for x in dirs if not x.startswith("."))
                for fn in sorted(files):
                    if fn.startswith("."):
                        continue
                    if Path(fn).suffix.lower() not in allowed:
                        skipped += 1
                        continue
                    rel = Path(dirpath).relative_to(p).as_posix()
                    plan.append((Path(dirpath) / fn, f"{folder}/{top}" + ("" if rel == "." else "/" + rel) + "/" + fn))
        elif Path(p.name).suffix.lower() in allowed:
            name = unique_name(p.name, here())
            taken.add(f"{folder}/{name}")
            plan.append((p, f"{folder}/{name}"))
        else:
            skipped += 1
    for _local, rel in plan:
        if not samplelib.safe_rel(rel):
            raise AppError("Invalid file name: " + rel)
    if not plan:
        raise AppError("Nothing to copy: no " + ("audio files" if mode == "samples" else "presets") + " here")
    batch, size, done = [], 0, 0
    def send(items):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w", format=tarfile.GNU_FORMAT) as t:
            for local, rel in items:
                t.add(str(local), arcname=rel, recursive=False)
        ssh_run(f"cd {shlex.quote(USERLIB_DIR)} && tar -xf -", data=buf.getvalue(), timeout=600)
    for local, rel in plan:
        batch.append((local, rel)); size += local.stat().st_size
        if size > 100 * 1024 * 1024:
            stage(f"Copying to Move: {done + len(batch)}/{len(plan)}", (done + len(batch)) / len(plan))
            send(batch); done += len(batch); batch, size = [], 0
    if batch:
        stage(f"Copying to Move: {len(plan)}/{len(plan)}", 1)
        send(batch)
    ssh_run(REFRESH + " || true")
    return {"copied": len(plan), "skipped": skipped}


def copy_to_pc(mode, rels, folder, stage):
    """Копирует файлы и папки библиотеки Move в папку на компьютере. Существующее не трогается."""
    dest = fs_check(folder, must_dir=True)
    rels = [_check_rel(mode, r) for r in rels]
    copied = 0
    for i, rel in enumerate(rels):
        stage(f"Copying to the computer: {i + 1}/{len(rels)}", (i + 1) / len(rels))
        parent, base = rel.rsplit("/", 1) if "/" in rel else ("", rel)
        data = ssh_run(f"cd {_q(parent)} && tar -cf - {shlex.quote(base)}", timeout=600)
        tmp = dest / f".mm-copy-{uuid.uuid4().hex[:8]}"
        tmp.mkdir()
        try:
            with tarfile.open(fileobj=io.BytesIO(data)) as t:
                if hasattr(tarfile, "data_filter"):
                    t.extractall(tmp, filter="data")
                else:                                    # старый Python: только обычные файлы и папки внутри tmp
                    for mem in t.getmembers():
                        if not (mem.isfile() or mem.isdir()) or mem.name.startswith("/") or ".." in Path(mem.name).parts:
                            raise AppError("Unexpected entry in the copy from Move: " + mem.name)
                    t.extractall(tmp)
            got = tmp / base
            copied += sum(1 for x in got.rglob("*") if x.is_file()) if got.is_dir() else 1
            got.rename(dest / unique_name(base, set(os.listdir(dest))))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return {"copied": copied}


def userlib_read(mode, rel):
    return ssh_run(f"cat {_q(_check_rel(mode, rel))}", timeout=120)


def prune_backups(folder, name, keep=5):
    """Хранит только последние keep резервных копий Song.abl одного проекта (имя «<проект> ГГГГММДД-ЧЧММСС.abl»)."""
    pat = re.compile(re.escape(name) + r" \d{8}-\d{6}\.abl")
    files = sorted(p for p in Path(folder).glob("*.abl") if pat.fullmatch(p.name))
    for old in files[:-keep]:
        old.unlink(missing_ok=True)


def ssh_read_song(oid):
    return json.loads(ssh_run(f"cat {set_dir(oid)}/*/Song.abl").decode("utf-8"))


def ssh_write_song(oid, payload):
    # путь — перебором в оболочке, не через ls: BusyBox ls печатает «?» вместо кириллицы («Песня» → «??????????»)
    ssh_run(f'set -e; f=; for x in {set_dir(oid)}/*/Song.abl; do [ -f "$x" ] && {{ f="$x"; break; }}; done; [ -n "$f" ]; '
            f'cat > "$f.tmp"; mv "$f.tmp" "$f"; {REFRESH}', data=payload, timeout=90)


def job_ssh_setup(stage):
    stage("Preparing key")
    pub_path = ensure_ssh_key()
    try:
        ssh_run("echo ok", timeout=15)
    except SshError:
        stage("Confirm the key with the wheel on Move")
        r = MOVE.req("POST", "/api/v1/ssh", data=pub_path.read_text().strip().encode(), timeout=(10, 180),
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        added = False
        try:
            added = bool(r.json().get("added"))
        except ValueError:
            pass
        if r.status_code >= 400 or not added:
            raise AppError("Move did not add the key. Confirm the request with the wheel on the device and try again.")
        stage("Checking connection")
        ssh_run("echo ok", timeout=20)
    CFG["ssh_enabled"] = True
    save_config()
    return {"ok": True}


# ───────────────────────── кэш анализа ─────────────────────────

INFO_CACHE_PATH = CACHE_DIR / "info.json"
INFO_CACHE = read_json(INFO_CACHE_PATH, {})


def cache_info(oid, stamp, info):
    with LOCK:
        INFO_CACHE[oid] = {"stamp": stamp, "info": info}
        CACHE_DIR.mkdir(exist_ok=True)
        write_json(INFO_CACHE_PATH, INFO_CACHE)


def cached_info(oid, stamp):
    c = INFO_CACHE.get(oid)
    if not c or c.get("stamp") != stamp or stale_info(c.get("info")):
        return None
    return c["info"]


def stale_info(info):
    """Разбор от старой сборки: без clips (до 20), без вида дорожки clipKind (до 51),
    без пометки audio у клипов аудиодорожек (до 53), роль аудиодорожки по эффекту (до 54)."""
    info = info or {}
    if "clips" not in info or any("clipKind" not in t for t in info.get("tracks") or []):
        return True
    tracks = info.get("tracks") or []
    if any(t.get("trackKind") == "audio" and t.get("role") != "Audio" for t in tracks):   # до 54: роль по эффекту
        return True
    for i, row in enumerate(info.get("clips") or []):
        if i < len(tracks) and tracks[i].get("clipKind") == "audio" and any(c and "audio" not in c for c in row):
            return True
    return False


def tmp_path(suffix):
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR / f"tmp-{uuid.uuid4().hex}{suffix}"


def analyze_set(oid, stamp):
    info = cached_info(oid, stamp)
    if info:
        return info
    info = None
    if ssh_enabled():
        try:
            info = parse_song(ssh_read_song(oid))
        except (SshError, ValueError):
            info = None
    if info is None:
        tmp = tmp_path(".ablbundle")
        try:
            MOVE.download(oid, tmp)
            info = parse_song(read_song(tmp))
        finally:
            tmp.unlink(missing_ok=True)
    cache_info(oid, stamp, info)
    return info


# ───────────────────────── библиотека на компьютере ─────────────────────────

def lib_root():
    p = Path(CFG["library"]).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_name(name):
    name = re.sub(r'[/\\:\x00-\x1f]', " ", name or "").strip().strip(".")
    name = re.sub(r"\s+", " ", name)
    if not name:
        raise AppError("Empty name")
    return name[:120]


def lib_dir(folder):
    root = lib_root()
    p = (root / folder).resolve()
    if p.parent != root.resolve() or not p.is_dir():
        raise AppError("Project not found in the folder")
    return p


def find_file(d, exts):
    for f in sorted(d.iterdir()):
        if f.is_file() and f.suffix.lower() in exts and not f.name.startswith("."):
            return f
    return None


def lib_item(d):
    bundle = find_file(d, {".ablbundle"})
    if not bundle:
        return None
    meta_path = d / "meta.json"
    meta = read_json(meta_path, {})
    stamp = f"{bundle.stat().st_mtime_ns}:{bundle.stat().st_size}"
    if meta.get("bundleStamp") != stamp or stale_info(meta.get("info")):   # прочитано старой сборкой
        try:
            meta["info"] = parse_song(read_song(bundle))
        except Exception as e:
            meta["info"] = {"error": str(e), "tracks": []}
        meta["bundleStamp"] = stamp
        meta.setdefault("savedAt", time.strftime("%Y-%m-%dT%H:%M:%S"))
        write_json(meta_path, meta)
    audio = find_file(d, AUDIO_EXTS)
    return {
        "id": d.name,
        "name": d.name,
        "description": meta.get("description", ""),
        "notes": meta.get("notes", ""),
        "savedAt": meta.get("savedAt"),
        "sourceId": meta.get("sourceId"),
        "audio": audio.name if audio else None,
        "audioSource": meta.get("audioSource"),
        "audioError": meta.get("audioError"),
        "group": meta.get("group") or "",
        "schwung": bool(meta.get("schwung")) or (d / SCHWUNG_FILE).exists(),
        "size": bundle.stat().st_size,
        "info": meta.get("info"),
    }


def list_library():
    root = lib_root()
    items = []
    for d in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if d.is_dir() and not d.name.startswith((".", "_")):
            it = lib_item(d)
            if it:
                items.append(it)
    order = read_json(root / ".order.json", [])
    pos = {n: i for i, n in enumerate(order)}
    items.sort(key=lambda it: pos.get(it["id"], len(pos)))
    return items


def update_meta(d, **fields):
    meta = read_json(d / "meta.json", {})
    meta.update(fields)
    write_json(d / "meta.json", meta)


def replace_in_order(root, old, new):
    order = read_json(root / ".order.json", [])
    if old in order:
        write_json(root / ".order.json", [new if n == old else n for n in order])


def _code_changed():
    """Код поменялся после запуска (из исходников) — интерфейс предложит перезапустить программу."""
    try:
        return (APP_DIR / "app.py").stat().st_mtime > STARTED
    except OSError:
        return False


def ensure_ssh_key():
    """Свой SSH-ключ программы; создаётся при первом включении управления пэдами. Возвращает путь к открытому ключу."""
    pub_path = Path(str(SSH_KEY) + ".pub")
    if not SSH_KEY.exists() or not pub_path.exists():
        Path(SSH_KEY).parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "move-manager", "-f", str(SSH_KEY)],
                           check=True, capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError:
            raise AppError(NO_SSH_MSG)
        except (OSError, subprocess.CalledProcessError) as e:
            raise AppError(f"Could not create SSH key: {e}")
    return pub_path


def folder_dialog_cmd(platform, prompt):
    """Команда системного окна выбора папки; None — на этой системе такого окна нет."""
    clean = re.sub(r"[\"'`$\\\r\n]", " ", str(prompt))[:120]
    if platform == "darwin":
        return ["osascript", "-e", f'POSIX path of (choose folder with prompt "{clean}")']
    if platform.startswith("win"):
        # окно поверх браузера (владелец TopMost), вывод в UTF-8 без BOM — иначе путь начнётся с невидимого символа
        ps = ("Add-Type -AssemblyName System.Windows.Forms; "
              "$o = New-Object System.Windows.Forms.Form; $o.TopMost = $true; $o.ShowInTaskbar = $false; "
              "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
              f"$f.Description = '{clean}'; $f.ShowNewFolderButton = $true; "
              "if ($f.ShowDialog($o) -eq [System.Windows.Forms.DialogResult]::OK) { "
              "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; $f.SelectedPath }")
        return ["powershell", "-NoProfile", "-STA", "-Command", ps]
    return None


def choose_folder_dialog(prompt="Folder for Move projects"):
    cmd = folder_dialog_cmd(sys.platform, prompt)
    if cmd is None:
        raise AppError("The system folder picker isn't available on this system — type the path")
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired):
        return None
    path = r.stdout.decode("utf-8", "replace").lstrip("\ufeff").strip()
    if r.returncode != 0 or not path:
        return None
    return path


def reveal_cmd(platform, path, select):
    """Показать файл (select) или открыть папку в Finder/Проводнике."""
    if platform == "darwin":
        return ["open", "-R", path] if select else ["open", path]
    if platform.startswith("win"):
        from pathlib import PureWindowsPath
        p = str(PureWindowsPath(path))       # строкой: explorer не понимает «/select,» внутри кавычек вокруг всего
        return f'explorer /select,"{p}"' if select else f'explorer "{p}"'
    return ["xdg-open", str(Path(path).parent if select else path)]


def reveal(path, select=False):
    try:
        subprocess.Popen(reveal_cmd(sys.platform, str(path), select))
    except OSError:
        pass


# ───────────────────────── фоновые задачи ─────────────────────────

JOBS = {}


def log_error(title, exc):
    """Ошибка с полным следом (traceback) в cache/errors.log — чтобы разбирать отчёты друзей."""
    try:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).rstrip()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        f = CACHE_DIR / "errors.log"
        if f.exists() and f.stat().st_size > 600_000:
            f.write_text(f.read_text("utf-8", "replace")[-300_000:], "utf-8")
        with f.open("a", encoding="utf-8") as h:
            h.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [build {BUILD}] {title}: {exc}\n{tb}\n---\n")
    except OSError:
        pass


REPORT_DIR = Path.home() / "Desktop"


def normalize_move_url(value):
    """Адрес Move от человека: «192.168.1.23», «move.local», «http://…/…» → «http://хост». Только имя или IP."""
    s = str(value or "").strip()
    if not s:
        return "http://move.local"
    host = urlparse(s if "://" in s else "http://" + s)
    name = host.hostname or ""
    if host.username or host.password or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.\-]{0,252}", name) \
            or s.startswith("-") or any(c in s for c in " ;$`|&<>'\""):
        raise AppError("Enter Move's address like 192.168.1.23 or move.local")
    return "http://" + name.lower()


def build_report(text):
    """Текст отчёта: что написал человек, сборка, система, состояние подключения, последние ошибки.
    Без cookies, ключей и паролей; домашняя папка заменена на «~»."""
    def tail(name, chars):
        f = CACHE_DIR / name
        try:
            return f.read_text("utf-8", "replace")[-chars:] if f.exists() else "(empty)"
        except OSError:
            return "(could not read)"
    lines = [
        f"{APP_NAME} — problem report",
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Version: {VERSION} · Build: {BUILD}",
        f"System: {platform.platform()} · Python {platform.python_version()} · {'app' if FROZEN else 'source'}",
        f"Move address: {CFG.get('move_url')}",
        f"Signed in to Move: {'yes' if CFG.get('cookies') else 'no'} · pad control (SSH): {'on' if ssh_enabled() else 'off'}",
        f"Library folder: {CFG.get('library')}",
        f"Data folder: {DATA_DIR}",
        "",
        "What happened:",
        (str(text or "").strip() or "(no description)"),
        "",
        "Recent errors (cache/errors.log):",
        tail("errors.log", 20_000),
        "",
        "Slow Move commands (cache/ssh-timing.log):",
        tail("ssh-timing.log", 3_000),
    ]
    rep = "\n".join(lines) + "\n"
    home = str(Path.home())
    if home and home != "/":
        rep = rep.replace(home, "~")
    for v in (CFG.get("cookies") or {}).values():   # на всякий случай: значения входа не попадают никуда
        if v:
            rep = rep.replace(str(v), "[hidden]")
    return rep


def save_report(text):
    folder = REPORT_DIR
    try:
        folder.mkdir(exist_ok=True)                  # Рабочий стол; если его нет — папка данных программы
    except OSError:
        folder = DATA_DIR
        folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{APP_NAME} report {time.strftime('%Y-%m-%d %H-%M-%S')}.txt"
    path.write_text(build_report(text), "utf-8")
    return path


def log_line(name, text):
    """Короткий журнал в cache/: ошибки задач и медленные команды к Move — чтобы разбирать сбои по факту."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        f = CACHE_DIR / name
        if f.exists() and f.stat().st_size > 300_000:
            f.write_text(f.read_text("utf-8", "replace")[-150_000:], "utf-8")
        with f.open("a", encoding="utf-8") as h:
            h.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text.replace("\n", " ")[:600] + "\n")
    except OSError:
        pass


def start_job(title, fn):
    jid = uuid.uuid4().hex[:10]
    job = {"id": jid, "title": title, "status": "running", "stage": "", "progress": None, "error": None,
           "cancel": False, "cancellable": False}
    JOBS[jid] = job

    def set_stage(stage, progress=None, saved=False, cancellable=None):
        job["stage"], job["progress"] = stage, progress
        if saved:
            job["saved"] = True
        if cancellable is not None:
            job["cancellable"] = cancellable
    set_stage.cancelled = lambda: bool(job["cancel"])

    def run():
        try:
            job["result"] = fn(set_stage)
            job["status"] = "done"
        except AuthRequired:
            job.update(status="error", error="auth")
        except MoveOffline:
            job.update(status="error", error="Move is unreachable. Check that it is on and on the same network.")
        except Exception as e:  # noqa: BLE001
            log_error(title, e)
            job.update(status="error", error=str(e))

    threading.Thread(target=run, daemon=True).start()
    return job


def set_by_id(oid):
    for o in MOVE.list_sets():
        if o.get("objectId") == oid:
            return o
    raise AppError("Project not found on Move")


def render_into(oid, d, stage):
    """Экспортирует звук сета средствами Move и кладёт файл в папку проекта. Возвращает текст ошибки или None."""
    fmt = CFG.get("audio_format", "wav")
    tmp_a = tmp_path("." + fmt)
    label = "Move is exporting audio"

    def prog(p):
        stage("Move is building the file" if p is None else label, p)
    try:
        stage("Waiting in the export queue" if RENDER_LOCK.locked() else label, None, cancellable=True)
        MOVE.render(oid, fmt, tmp_a, prog, getattr(stage, "cancelled", None))
        clear_audio(d)
        shutil.move(str(tmp_a), d / f"{d.name}.{fmt}")
        update_meta(d, audioSource="Move export", audioError=None)
        return None
    except (AppError, MoveOffline) as e:
        msg = str(e) or "Move is unreachable"
        update_meta(d, audioError=msg)
        return msg
    finally:
        stage(label, None, cancellable=False)
        tmp_a.unlink(missing_ok=True)


def job_pull(oid, with_audio, group=None):
    def fn(stage):
        obj = set_by_id(oid)
        name = safe_name(obj["name"])
        root = lib_root()
        d, k = root / name, 2
        # папка с тем же именем, но от другого проекта (или своя, без sourceId) — не трогаем: «Имя 2», «Имя 3»…
        while d.exists() and (any(d.glob("*.ablbundle")) or not d.is_dir()) \
                and read_json(d / "meta.json", {}).get("sourceId") != oid:
            d, k = root / f"{name} {k}", k + 1
        name = d.name
        d.mkdir(exist_ok=True)
        stage("Downloading project")
        tmp = tmp_path(".ablbundle")
        try:
            MOVE.download(oid, tmp, lambda p: stage("Downloading project", p))
            info = parse_song(read_song(tmp))
            olds = sorted(d.glob("*.ablbundle"))
            if olds:                                     # проект уже был на компьютере — его версия в историю
                save_lib_version(name, olds[0], "Replaced by copy from Move")
            for old in olds:
                old.unlink()
            shutil.move(str(tmp), d / f"{name}.ablbundle")
        finally:
            tmp.unlink(missing_ok=True)
        cache_info(oid, obj.get("lastModifiedDateTime"), info)
        mm = (CFG.get("move_meta") or {}).get(oid, {})
        meta = read_json(d / "meta.json", {})
        meta.update({
            "sourceId": oid,
            "savedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "description": meta.get("description") or mm.get("description", ""),
            "notes": meta.get("notes") or mm.get("notes", ""),
        })
        if group is not None:
            meta["group"] = str(group)[:80]
        schwung = False
        if ssh_enabled():                    # состояние Schwung хранится на Move отдельно от сета
            stage("Copying Schwung state")
            try:
                data = schwung_fetch(oid)
            except (SshError, AppError, tarfile.TarError):
                data = None
            if data:
                (d / SCHWUNG_FILE).write_bytes(data)
                schwung = True
            else:
                (d / SCHWUNG_FILE).unlink(missing_ok=True)
        meta["schwung"] = schwung
        meta.pop("bundleStamp", None)
        write_json(d / "meta.json", meta)
        stage("Project saved", None, saved=True)
        audio_error = render_into(oid, d, stage) if with_audio else None
        return {"folder": name, "audioError": audio_error, "schwung": schwung}
    return fn


def job_render_library(folder):
    def fn(stage):
        d = lib_dir(folder)
        oid = read_json(d / "meta.json", {}).get("sourceId")
        ids = {o["objectId"]: o for o in MOVE.list_sets()}
        if oid not in ids:
            same = [o for o in ids.values() if o.get("name") == d.name]
            if len(same) != 1:
                raise AppError("This project is not on Move now. Upload it to Move and export again.")
            oid = same[0]["objectId"]
            update_meta(d, sourceId=oid)
        err = render_into(oid, d, stage)
        if err:
            raise AppError(err)
        return {"ok": True}
    return fn


def job_push(folder, slot=None, replace_id=None):
    """Загружает проект на Move. replace_id — сет на устройстве, который нужно заменить новым."""
    def fn(stage):
        d = lib_dir(folder)
        bundle = find_file(d, {".ablbundle"})
        if not bundle:
            raise AppError("No .ablbundle in the project folder")
        if replace_id and not UUID_RE.fullmatch(replace_id):
            raise AppError("Invalid identifier")
        before = {o["objectId"] for o in MOVE.list_sets()}
        if replace_id and replace_id not in before:
            raise AppError("The project to replace is no longer on Move")
        stage("Uploading to Move")
        with zipfile.ZipFile(bundle) as zi:
            nested = unwrap_nested_racks(json.loads(zi.read(find_song_entry(zi)).decode("utf-8")))[1]
        if nested:      # копия для Move без лишней обёртки рэка; файл на компьютере не меняется
            fixed = CACHE_DIR / f"push-{uuid.uuid4().hex}.ablbundle"
            try:
                transform_bundle(bundle, fixed, lambda song: unwrap_nested_racks(song)[0])
                MOVE.upload(fixed, f"{d.name}.ablbundle")
            finally:
                fixed.unlink(missing_ok=True)
        else:
            MOVE.upload(bundle, f"{d.name}.ablbundle")
        created = [o["objectId"] for o in MOVE.list_sets() if o["objectId"] not in before]
        if replace_id:
            # старый проект удаляем только после того, как новый однозначно найден на устройстве
            if len(created) != 1:
                raise AppError("The new project was uploaded but could not be identified — the old one was kept")
            stage("Saving a copy of the previous project")
            backup_move_set(replace_id)
            stage("Removing the previous project from the pad")
            MOVE.delete(replace_id)
            if read_json(d / "meta.json", {}).get("sourceId") == replace_id:     # тот же проект вернулся на свой пэд
                history.move_history(history_dir("move", replace_id), history_dir("move", created[0]))
            with LOCK:
                CFG.setdefault("move_meta", {}).pop(replace_id, None)
                INFO_CACHE.pop(replace_id, None)
                save_config()
        placed = None
        if slot is not None and ssh_enabled() and len(created) == 1:
            taken = {v["slot"] for k, v in ssh_slots().items() if k not in created}
            if int(slot) not in taken:
                ssh_set_slots([(created[0], slot)])
                placed = int(slot)
        schwung = None
        state = d / SCHWUNG_FILE
        if state.exists():
            if not ssh_enabled():
                schwung = "needs pad control"
            elif len(created) != 1:
                schwung = "set not identified"
            else:
                stage("Restoring Schwung state")
                try:                         # сет уже загружен: ошибка Schwung не должна выглядеть как провал загрузки
                    schwung = schwung_restore(created[0], state.read_bytes())
                except (SshError, AppError, tarfile.TarError) as e:
                    schwung = f"error: {e}"
        return {"name": d.name, "slot": placed, "replaced": bool(replace_id), "schwung": schwung}
    return fn


def job_edit_move(oid, order, pans, replace, key=None):
    def fn(stage):
        obj = set_by_id(oid)
        if replace and ssh_enabled():
            with target_lock("move:" + oid):
                stage("Reading project on Move")
                song = ssh_read_song(oid)
                new = edit_song(copy.deepcopy(song), order, pans, key)      # ошибка в правке — до записи версии
                save_move_version(oid, song, edit_action(order, pans, key))
                stage("Writing changes")
                ssh_write_song(oid, dump_song(new))
                with LOCK:
                    INFO_CACHE.pop(oid, None)
                return {"inPlace": True}
        before = {o["objectId"] for o in MOVE.list_sets()}
        src, dst, orig = tmp_path(".ablbundle"), tmp_path(".ablbundle"), tmp_path(".ablbundle")
        new_name = f"{obj['name']}_edit"
        try:
            stage("Downloading project")
            MOVE.download(oid, src)
            stage("Applying changes")
            edit_bundle(src, dst, order, pans, key)
            with zipfile.ZipFile(src) as z:              # версия до правки — запишем, когда новый сет опознан
                before_bytes = z.read(find_song_entry(z))
            if replace:
                shutil.copyfile(src, orig)                 # оригинал целиком — в «_Deleted» перед удалением с Move
            stage("Uploading to Move")
            MOVE.upload(dst, f"{new_name}.ablbundle")
        finally:
            src.unlink(missing_ok=True)
            dst.unlink(missing_ok=True)
        if replace:
            created = [o for o in MOVE.list_sets() if o["objectId"] not in before]
            if len(created) != 1:
                orig.unlink(missing_ok=True)
                raise AppError("The new version was uploaded but could not be identified — the original was kept")
            new_oid = created[0]["objectId"]
            # история — к новому сету до удаления и переименования: сбой там не оставит её у удалённого ID
            history.move_history(history_dir("move", oid), history_dir("move", new_oid))
            _save_version(history_dir("move", new_oid), before_bytes, edit_action(order, pans, key))
            stage("Saving a copy of the original")
            try:
                backup_move_set(oid, orig)
            finally:
                orig.unlink(missing_ok=True)
            stage("Replacing the original")
            MOVE.delete(oid)
            MOVE.rename(new_oid, obj["name"])
            with LOCK:
                meta = CFG.setdefault("move_meta", {})
                if oid in meta:
                    meta[created[0]["objectId"]] = meta.pop(oid)
                save_config()
            return {"replaced": True}
        return {"copy": new_name}
    return fn


RACK_KINDS = {"instrumentRack", "audioEffectRack", "midiEffectRack"}


def unwrap_nested_racks(song):
    """Обёртка Schwung «ME Slot»: рэк, в единственной цепочке которого лежит ещё один рэк с одной цепочкой.
    Move такое не принимает («Rack chain must have exactly one device»), поэтому внутренний рэк
    убирается, а его устройства переезжают в цепочку внешнего. Звук не меняется. Возвращает (song, changed)."""
    changed = False
    for track in song.get("tracks") or []:
        for dev in track.get("devices") or []:
            chains = dev.get("chains") or []
            if dev.get("kind") not in RACK_KINDS or len(chains) != 1:
                continue
            inner = chains[0].get("devices") or []
            if len(inner) == 1 and inner[0].get("kind") in RACK_KINDS and len(inner[0].get("chains") or []) == 1:
                chains[0]["devices"] = inner[0]["chains"][0].get("devices") or []
                changed = True
    return song, changed


def transform_bundle(src, dst, fn):
    """Пересобирает бандл: Song.abl проходит через fn(song) -> song, остальные файлы копируются как есть."""
    with zipfile.ZipFile(src) as zi:
        entry = find_song_entry(zi)
        song = fn(json.loads(zi.read(entry).decode("utf-8")))
        payload = dump_song(song)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
            for item in zi.infolist():
                zo.writestr(item.filename, payload if item.filename == entry else zi.read(item.filename))
    return song


def read_midi_upload(data):
    if not data:
        raise AppError("The file is empty")
    try:
        return midi_to_notes(data)
    except MidiError as e:
        raise AppError(f"MIDI file could not be read: {e}")


def cell_busy(song, track, scene):
    try:
        get_clip(song, track, scene)
        return True
    except AppError:
        _slot(song, track, scene)          # неверный индекс — ошибка, а не «свободно»
        return False


def library_put_clip(folder, track, scene, notes, length, action=""):
    """notes=None — удалить клип из ячейки. Порядок: правка во временный файл → версия в историю → замена."""
    d = lib_dir(folder)
    bundle = find_file(d, {".ablbundle"})
    tmp = tmp_path(".ablbundle")
    try:
        with target_lock("lib:" + d.name):
            transform_bundle(bundle, tmp, lambda song: put_clip(song, track, scene, notes, length)
                             if notes is not None else remove_clip(song, track, scene))
            save_lib_version(folder, bundle, action)
            shutil.move(str(tmp), bundle)
    finally:
        tmp.unlink(missing_ok=True)


def move_song(oid):
    """Song.abl сета на Move: по SSH, если включён, иначе через скачивание бандла."""
    if ssh_enabled():
        try:
            return ssh_read_song(oid)
        except (SshError, ValueError):
            pass
    if oid not in {o["objectId"] for o in MOVE.list_sets()}:
        raise AppError("This project is no longer on Move (it was replaced or deleted). The list has been refreshed.")
    tmp = tmp_path(".ablbundle")
    try:
        MOVE.download(oid, tmp)
        return read_song(tmp)
    finally:
        tmp.unlink(missing_ok=True)


# ───────────────────────── генератор барабанов ─────────────────────────
PATTERNS = None
MINE_CACHE = {}          # путь бандла → (mtime, [рисунки])


def builtin_patterns():
    global PATTERNS
    if PATTERNS is None:
        PATTERNS = drumgen.load_patterns()
    return PATTERNS


def clip_to_pattern(clip, pads, pid, name, genre):
    """Барабанный клип → рисунок по ролям, квантованный к 1/16, не длиннее двух тактов."""
    region = clip.get("region") or {}
    start = float(region.get("start", 0.0))
    length = min(8.0, max(4.0, float(region.get("end", 4.0)) - start))
    steps = 16 if length <= 4.0 else 32
    roles = {p["note"]: p["role"] for p in pads}
    hits = {}
    for n in clip.get("notes") or []:
        role = roles.get(n.get("noteNumber"))
        st = int(round((float(n.get("startTime", 0)) - start) / 0.25))
        if role and 0 <= st < steps:
            hits.setdefault(role, [0.0] * steps)[st] = 0.8
    return {"id": pid, "name": name, "genre": genre, "source": "mine", "steps": steps, "hits": hits}


MINE_STATE = {"running": False, "done": 0, "total": 0, "ready": False}
MINE_LOCK = threading.Lock()


def _mine_cache_file():
    return CACHE_DIR / "mine_patterns.json"


def _bundle_patterns(bundle, folder):
    """Барабанные клипы проекта → рисунки без жанра (жанр — группа проекта, подставляется при выдаче)."""
    pats = []
    try:
        song = read_song(bundle)
        for t, tr in enumerate(song.get("tracks") or []):
            pads = drumgen.kit_pads(song, t)
            if not pads:
                continue
            for sc, slot in enumerate(tr.get("clipSlots") or []):
                clip = (slot or {}).get("clip")
                if clip and len(clip.get("notes") or []) >= 4:
                    pat = clip_to_pattern(clip, pads, f"mine:{folder}:{t}:{sc}", f"{folder} T{t + 1} S{sc + 1}", "")
                    if pat["hits"]:
                        pats.append(pat)
    except (AppError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile):
        pats = []
    return pats


def scan_mine():
    """Фоновый разбор барабанных клипов библиотеки. Неизменённые проекты (путь, время, размер) не читаются:
    результат хранится в cache/mine_patterns.json и переживает перезапуск. Библиотека может лежать в iCloud —
    первое чтение каждого бандла тогда скачивает его, поэтому всё это идёт в фоне с ходом выполнения."""
    with MINE_LOCK:
        if MINE_STATE["running"]:
            return
        MINE_STATE["running"] = True
    try:
        if not MINE_CACHE:
            MINE_CACHE.update(read_json(_mine_cache_file(), {}))
        root = lib_root()
        dirs = [d for d in sorted(root.iterdir(), key=lambda p: p.name.lower())
                if d.is_dir() and not d.name.startswith((".", "_"))]
        MINE_STATE.update(total=len(dirs), done=0)
        seen, changed = set(), False
        for d in dirs:
            bundle = find_file(d, {".ablbundle"})
            if bundle:
                st = bundle.stat()
                key, sig = str(bundle), [st.st_mtime, st.st_size]
                seen.add(key)
                if (MINE_CACHE.get(key) or {}).get("sig") != sig:
                    MINE_CACHE[key] = {"sig": sig, "folder": d.name, "pats": _bundle_patterns(bundle, d.name)}
                    changed = True
            MINE_STATE["done"] += 1
        for key in [k for k in MINE_CACHE if k not in seen]:
            MINE_CACHE.pop(key)
            changed = True
        if changed:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            write_json(_mine_cache_file(), MINE_CACHE)
        MINE_STATE["ready"] = True
    finally:
        MINE_STATE["running"] = False


def start_mine_scan():
    if not MINE_STATE["running"]:
        threading.Thread(target=scan_mine, daemon=True).start()


def my_patterns():
    """Рисунки из уже разобранных проектов (без чтения бандлов). Жанр — текущая группа проекта."""
    out = []
    root = lib_root()
    for entry in list(MINE_CACHE.values()):
        group = read_json(root / entry["folder"] / "meta.json", {}).get("group") or "My clips"
        for p in entry["pats"]:
            out.append(dict(p, genre=group))
    return out


GM_DRUMS = {35: "kick", 36: "kick", 37: "rim", 38: "snare", 40: "snare", 39: "clap", 42: "chh", 44: "chh", 46: "ohh",
            41: "tom_low", 43: "tom_low", 45: "tom_mid", 47: "tom_mid", 48: "tom_high", 50: "tom_high",
            49: "crash", 52: "crash", 55: "crash", 57: "crash", 51: "ride", 53: "ride", 59: "ride",
            54: "perc", 56: "cowbell", 69: "shaker", 70: "shaker", 60: "perc", 61: "perc", 62: "perc", 63: "perc",
            64: "perc", 75: "rim", 76: "perc", 77: "perc"}
MIDI_CACHE = {}          # путь → (mtime, size, рисунок | None)


def midi_file_pattern(path, root):
    """Барабанный .mid → рисунок по ролям (раскладка General MIDI), 1/16, до двух тактов."""
    notes, _ = midi_to_notes(path.read_bytes())
    end = max(n["startTime"] for n in notes)
    steps = 16 if end < 4.0 else 32
    hits = {}
    for n in notes:
        role, st = GM_DRUMS.get(n["noteNumber"]), int(round(n["startTime"] / 0.25))
        if role and 0 <= st < steps:
            hits.setdefault(role, [0.0] * steps)[st] = 0.8
    if not hits:
        return None
    rel = path.relative_to(root)
    genre = rel.parts[0] if len(rel.parts) > 1 else "MIDI folder"
    return {"id": f"midi:{rel.as_posix()}", "name": path.stem, "genre": genre, "source": "midi",
            "steps": steps, "hits": hits}


def midi_folder_patterns(folder):
    """Рисунки из папки с .mid (жанр — первая подпапка). Битые и небарабанные файлы пропускаются."""
    root = Path(folder).expanduser()
    if not folder or not root.is_dir():
        return []
    out = []
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in (".mid", ".midi") and p.is_file())[:3000]
    for f in files:
        st = f.stat()
        if st.st_size > 1_000_000:
            continue
        key = str(f)
        cached = MIDI_CACHE.get(key)
        if not cached or cached[:2] != (st.st_mtime, st.st_size):
            try:
                pat = midi_file_pattern(f, root)
            except (MidiError, OSError, ValueError):
                pat = None
            cached = MIDI_CACHE[key] = (st.st_mtime, st.st_size, pat)
        if cached[2]:
            out.append(dict(cached[2]))
    return out


def all_patterns():
    return drumgen.unify_genres(builtin_patterns() + [dict(p) for p in my_patterns()]
                                + midi_folder_patterns(CFG.get("midiFolder") or ""))


def kit_overrides(side, ident, track):
    if side == "move":
        return ((CFG.get("move_meta") or {}).get(ident, {}).get("kitRoles") or {}).get(str(track), {})
    return (read_json(lib_dir(ident) / "meta.json", {}).get("kitRoles") or {}).get(str(track), {})


def save_kit_overrides(side, ident, track, overrides):
    clean = {str(int(k)): v for k, v in (overrides or {}).items() if v in drumgen.ROLES and 36 <= int(k) <= 51}
    if side == "move":
        with LOCK:
            CFG.setdefault("move_meta", {}).setdefault(ident, {}).setdefault("kitRoles", {})[str(track)] = clean
            save_config()
    else:
        d = lib_dir(ident)
        meta = read_json(d / "meta.json", {})
        meta.setdefault("kitRoles", {})[str(track)] = clean
        write_json(d / "meta.json", meta)


def known_pads(raw):
    """Раскладка кита, которую интерфейс уже получил: не читать проект заново (на Move это SSH на каждое нажатие)."""
    pads = []
    try:
        for p in raw:
            note, role = int(p["note"]), str(p["role"])
            if not 36 <= note <= 51 or role not in drumgen.ROLES:
                raise ValueError
            pads.append({"note": note, "sample": str(p.get("sample") or "")[:200], "role": role})
    except (KeyError, TypeError, ValueError):
        raise AppError("Invalid kit")
    if not pads:
        raise AppError("Invalid kit")
    return pads


def side_song(side, ident):
    if side == "move":
        if not UUID_RE.fullmatch(ident or ""):
            raise AppError("Invalid identifier")
        return move_song(ident)
    return read_song(find_file(lib_dir(ident), {".ablbundle"}))


MAX_CLIP_BEATS = 256.0       # 64 такта 4/4


def clip_length(b):
    try:
        length = float(b.get("length") or 4)
    except (TypeError, ValueError):
        raise AppError("Invalid clip length")
    if not 0 < length <= MAX_CLIP_BEATS:
        raise AppError("Invalid clip length")
    return length


def clean_notes(raw, length=MAX_CLIP_BEATS):
    """Ноты из запроса: высота 0–127, громкость 1–127, без наложений одинаковых нот."""
    notes = []
    for n in raw or []:
        try:
            pitch, st, dur, vel = int(n["noteNumber"]), float(n["startTime"]), float(n["duration"]), float(n["velocity"])
        except (KeyError, TypeError, ValueError):
            raise AppError("Invalid notes")
        if not (0 <= pitch <= 127 and 0 <= st < length and dur > 0 and 1 <= vel <= 127):
            raise AppError("Invalid notes")
        notes.append((pitch, round(st * 960), round((st + dur) * 960), vel))
    if not notes or len(notes) > 4096:
        raise AppError("Invalid notes")
    return [{"noteNumber": p, "startTime": a / 960, "duration": (e - a) / 960, "velocity": float(v), "offVelocity": 0.0}
            for p, a, e, v in _no_overlaps(notes, 960)]


TARGET_LOCKS = {}


def target_lock(key):
    """Один замок на проект: чтение → правка → запись одного проекта не перемешиваются."""
    with LOCK:
        return TARGET_LOCKS.setdefault(key, threading.Lock())


def job_clip_move(oid, track, scene, notes, length, action=""):
    def fn(stage):
        stage("Waiting for another edit of this project to finish" if target_lock("move:" + oid).locked() else "Reading project on Move")
        with target_lock("move:" + oid):
            return _clip_move(oid, track, scene, notes, length, stage, action)
    return fn


# ───────────────────────── история версий проекта ─────────────────────────
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def history_dir(side, ident):
    """Папка истории: сет на Move — по его ID в папке программы; проект на компьютере — .history внутри него."""
    if side == "move":
        if not UUID_RE.fullmatch(str(ident or "")):
            raise AppError("Invalid identifier")
        return DATA_DIR / "history" / "move" / ident
    return lib_dir(ident) / ".history"


def _save_version(folder, data, action):
    """Версия до правки; не сохранилась — правку не делаем."""
    try:
        return history.save_version(folder, data, action)
    except OSError as e:
        raise AppError(f"Could not save a version to History, nothing was changed: {e}")


def save_move_version(oid, song, action):
    return _save_version(history_dir("move", oid), dump_song(song), action)


def save_lib_version(folder, bundle, action):
    with zipfile.ZipFile(bundle) as z:
        data = z.read(find_song_entry(z))
    return _save_version(history_dir("lib", folder), data, action)


def cell_name(t, s):
    return f"T{int(t) + 1} S{int(s) + 1}"


def edit_action(order, pans, key):
    """Название правки из Apply changes для строки истории."""
    parts = []
    if order and list(order) != sorted(order):
        parts.append("Tracks reordered")
    if pans:
        parts.append("Pan changed")
    if key and ("rootNote" in key or "scale" in key):
        try:
            parts.append(f"Key changed to {NOTE_NAMES[int(key.get('rootNote')) % 12]} {key.get('scale') or ''}".rstrip())
        except (TypeError, ValueError):
            parts.append("Key changed")
    if key and key.get("tempo") is not None:
        try:
            parts.append(f"Tempo changed to {float(key['tempo']):g} bpm")
        except (TypeError, ValueError):
            parts.append("Tempo changed")
    return ", ".join(parts)


LEGACY_RE = re.compile(r"(.+) (\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})\.abl")


def legacy_backups(oid):
    """Старые копии backups/<имя> ГГГГММДД-ЧЧММСС.abl этого сета (до сборки 52).
    Если на Move два сета с таким именем — не показываем: нельзя понять, чьи они."""
    def safe(n):
        try:
            return safe_name(n or "")
        except AppError:                 # пустое или странное имя другого сета не должно ломать историю
            return None
    name = safe(set_by_id(oid)["name"])
    if not name or sum(1 for o in MOVE.list_sets() if safe(o.get("name")) == name) > 1:
        return []
    out = []
    folder = backups_dir()
    for p in folder.glob("*.abl") if folder.is_dir() else []:
        m = LEGACY_RE.fullmatch(p.name)
        if m and m.group(1) == name:
            y, mo, d, h, mi, s = m.groups()[1:]
            out.append({"id": "legacy:" + p.name, "savedAt": f"{y}-{mo}-{d}T{h}:{mi}:{s}", "action": "", "legacy": True})
    return out


def list_history(side, ident):
    vs = history.list_versions(history_dir(side, ident))
    if side == "move":
        vs = sorted(vs + legacy_backups(ident), key=lambda v: v["savedAt"], reverse=True)
    for v in vs:
        v["when"] = history.fmt_when(v["savedAt"])
    return vs


def version_bytes(side, ident, vid):
    """Байты выбранной версии и её описание; неизвестная версия — AppError."""
    vid = str(vid or "")
    entry = next((v for v in list_history(side, ident) if v["id"] == vid), None)
    if not entry:
        raise AppError("This version is no longer in History")
    if entry["legacy"]:
        return (backups_dir() / vid[len("legacy:"):]).read_bytes(), entry
    try:
        return history.read_version(history_dir(side, ident), vid), entry
    except ValueError:
        raise AppError("This version is no longer in History")


def song_sample_uris(text):
    """Все sampleUri проекта (текст Song.abl)."""
    found = []
    collect_uris(json.loads(text), found)
    return found


def collect_uris(node, out):
    if isinstance(node, dict):
        u = node.get("sampleUri")
        if isinstance(u, str) and u:
            out.append(u)
        for v in node.values():
            collect_uris(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_uris(v, out)


def move_missing_files(rels):
    """Какие файлы пользовательской библиотеки на Move отсутствуют (одним вызовом SSH)."""
    if not rels:
        return []
    names = " ".join(shlex.quote(r) for r in rels)
    out = ssh_run(f'cd {shlex.quote(samplelib.ABS_PREFIX)} && for f in {names}; do [ -e "$f" ] || echo "$f"; done')
    return [x for x in out.decode("utf-8", "replace").splitlines() if x]


def missing_samples(side, ident, data):
    """Сэмплы версии, которых сейчас нет: на Move — в пользовательской библиотеке девайса
    (паки не проверяем), на компьютере — внутри .ablbundle проекта."""
    text = data.decode("utf-8")
    if side == "move":
        rels = sorted(set(samplelib.find_refs(text)))
        return move_missing_files(rels)
    bundle = find_file(lib_dir(ident), {".ablbundle"})
    with zipfile.ZipFile(bundle) as z:
        base = find_song_entry(z).rpartition("/")[0]
        names = set(z.namelist())
    out = []
    for uri in song_sample_uris(text):
        if uri.startswith("ableton:") or uri.startswith("/"):
            continue
        rel = unquote(uri)
        if (f"{base}/{rel}" if base else rel) not in names and rel not in out:
            out.append(rel)
    return sorted(out)


def check_restore(side, ident, vid, force):
    """Проверка до отката: версия есть, сэмплы на месте (или force). Возвращает (байты, описание)."""
    data, entry = version_bytes(side, ident, vid)
    try:
        json.loads(data.decode("utf-8"))
    except ValueError:
        raise AppError("This version is damaged and can't be restored")
    if not force:
        gone = missing_samples(side, ident, data)
        if gone:
            raise SamplesMissing(gone)
    return data, entry


class SamplesMissing(AppError):
    def __init__(self, missing):
        super().__init__("Some samples of this version are gone")
        self.missing = missing


def job_restore_move(oid, data, entry):
    """Откат сета на Move: текущая версия — в историю, затем запись выбранной."""
    def fn(stage):
        stage("Waiting for another edit of this project to finish" if target_lock("move:" + oid).locked() else "Reading project on Move")
        with target_lock("move:" + oid):
            stage("Reading project on Move")
            song = ssh_read_song(oid)
            save_move_version(oid, song, "Restore of " + history.fmt_when(entry["savedAt"]))
            stage("Writing the saved version")
            ssh_write_song(oid, data)
            with LOCK:
                INFO_CACHE.pop(oid, None)
            return {"ok": True}
    return fn


def restore_library(folder, data, entry):
    d = lib_dir(folder)
    bundle = find_file(d, {".ablbundle"})
    tmp = tmp_path(".ablbundle")
    song = json.loads(data.decode("utf-8"))
    try:
        with target_lock("lib:" + d.name):
            transform_bundle(bundle, tmp, lambda _old: song)
            save_lib_version(folder, bundle, "Restore of " + history.fmt_when(entry["savedAt"]))
            shutil.move(str(tmp), bundle)
    finally:
        tmp.unlink(missing_ok=True)


# ───────────────────────── лупы в аудиоячейки (сборка 53) ─────────────────────────
UPLOAD_DIR = "Samples/UPLOAD"
LOOP_EXTS = (".wav", ".aif", ".aiff", ".flac", ".mp3")


def upload_dir_sizes():
    """{имя файла: размер} папки Samples/UPLOAD на Move (нет папки — пусто). Быстро: без чтения файлов."""
    out = ssh_run(f"cd {shlex.quote(samplelib.ABS_PREFIX + UPLOAD_DIR)} 2>/dev/null && "
                  f"for f in *; do [ -f \"$f\" ] && stat -c '%s %n' -- \"$f\"; done; true")
    res = {}
    for line in out.decode("utf-8", "replace").splitlines():
        size, _, name = line.partition(" ")
        if size.isdigit() and name:
            res[name] = int(size)
    return res


def remote_md5(names):
    """md5 выбранных файлов UPLOAD (только кандидатов того же размера)."""
    if not names:
        return {}
    quoted = " ".join(shlex.quote(n) for n in names)
    out = ssh_run(f"cd {shlex.quote(samplelib.ABS_PREFIX + UPLOAD_DIR)} && md5sum -- {quoted}", timeout=300)
    res = {}
    for line in out.decode("utf-8", "replace").splitlines():
        md5, _, name = line.partition("  ")
        if len(md5) == 32 and name:
            res[name] = md5
    return res


def put_sample(rel, data):
    """Атомарная загрузка файла в библиотеку Move."""
    path = samplelib.ABS_PREFIX + rel
    folder = path.rsplit("/", 1)[0]
    ssh_run(f'( mkdir -p {shlex.quote(folder)} && cat > {shlex.quote(path)}.mmtmp && mv {shlex.quote(path)}.mmtmp {shlex.quote(path)} ) '
            f'|| {{ rm -f {shlex.quote(path)}.mmtmp; exit 1; }}', data=data, timeout=300)


def _loop_name(name):
    name = str(name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name or name.startswith(".") or not samplelib.safe_rel(name) or Path(name).suffix.lower() not in LOOP_EXTS:
        raise AppError(f"\"{name or '?'}\": only WAV, AIFF, FLAC and MP3 files can be added as loops")
    return name


def upload_loops(files):
    """Загружает лупы в Samples/UPLOAD: такой же файл уже есть — берём его, имя занято другим — «Имя 2.wav».
    Возвращает rel каждого файла. Ошибка — AppError с перечнем уже загруженных."""
    have = upload_dir_sizes()
    known = {}                                     # имя → md5 (считаем только для файлов того же размера)
    rels, done = [], []
    for name, data in files:
        name = _loop_name(name)
        md5 = hashlib.md5(data).hexdigest()
        stem, ext = Path(name).stem, Path(name).suffix
        cands = [n for n, size in have.items() if size == len(data)
                 and (n == name or re.fullmatch(re.escape(stem) + r" \d+" + re.escape(ext), n))]
        ask = [n for n in cands if n not in known]
        if ask:
            known.update(remote_md5(ask))
        same = [n for n in cands if known.get(n) == md5]
        if same:
            final = name if name in same else sorted(same, key=loops.natural_key)[0]
        else:
            final, k = name, 2
            while final in have:
                final, k = f"{stem} {k}{ext}", k + 1
            try:
                put_sample(f"{UPLOAD_DIR}/{final}", data)
            except (SshError, AppError) as e:
                got = ", ".join(done) or "none"
                raise AppError(f"Upload of \"{name}\" failed ({e}). The project was not changed. "
                               f"Already in Samples/UPLOAD: {got}")
            have[final] = len(data)
            known[final] = md5
            done.append(final)
        rels.append(f"{UPLOAD_DIR}/{final}")
    return rels


CONVERT_EXTS = (".flac", ".mp3")      # Move хранит их, но в аудиоклипе не играет (проверено 17.11) — переводим в WAV


def convert_to_wav(name, data):
    """FLAC/MP3 → WAV через встроенный в macOS afconvert (24 бита для FLAC, 16 — для MP3). Нет afconvert — понятный отказ."""
    tool = shutil.which("afconvert")
    if not tool:
        raise AppError(f"\"{name}\": convert it to WAV first — Move plays only WAV and AIFF in clips")
    ext = Path(name).suffix.lower()
    src, dst = tmp_path(ext), tmp_path(".wav")
    try:
        src.write_bytes(data)
        r = subprocess.run([tool, "-f", "WAVE", "-d", "LEI24" if ext == ".flac" else "LEI16", str(src), str(dst)],
                           capture_output=True, timeout=300)
        if r.returncode or not dst.exists():
            raise AppError(f"\"{name}\" could not be converted to WAV")
        return Path(name).stem + ".wav", dst.read_bytes()
    finally:
        src.unlink(missing_ok=True)
        dst.unlink(missing_ok=True)


def prepare_loop_files(files):
    """FLAC и MP3 — в WAV; остальное как есть."""
    return [convert_to_wav(n, d) if Path(str(n)).suffix.lower() in CONVERT_EXTS else (n, d) for n, d in files]


def read_loop_files(ctype, body):
    """multipart/form-data → [(имя файла, байты)]. Режем по границе сами: без копий всего тела в памяти."""
    m = re.search(r'boundary="?([^";]+)"?', ctype or "")
    if "multipart/form-data" not in (ctype or "") or not m:
        raise AppError("No files given")
    sep = b"--" + m.group(1).encode("latin-1")
    files, pos = [], body.find(sep)
    while pos >= 0:
        start = pos + len(sep)
        if body[start:start + 2] == b"--":
            break
        nxt = body.find(b"\r\n" + sep, start)
        if nxt < 0:
            break
        head_end = body.find(b"\r\n\r\n", start, nxt)
        if head_end >= 0:
            head = body[start:head_end].decode("utf-8", "replace")
            fn = re.search(r'filename\*=UTF-8\'\'([^;\r\n]+)', head, re.I)
            fn = unquote(fn.group(1)) if fn else (re.search(r'filename="([^"]*)"', head) or [None, None])[1]
            if fn:
                files.append((fn.replace("%22", '"'), body[head_end + 4:nxt]))
        pos = nxt + 2
    if not files:
        raise AppError("No files given")
    return files


def plan_loops(song, track, scene, files, replace):
    """Проверки до загрузки: аудиодорожка, форматы, ячейки. → (план [(сцена, имя, байты, секунды)], пропущенные)."""
    tr, _ = _slot(song, track, scene)
    if track_clip_kind(tr) != "audio":
        raise AppError("Loops can only go into an audio track")
    files = sorted(files, key=lambda f: loops.natural_key(f[0]))
    scenes = len(tr.get("clipSlots") or [])
    plan, skipped = [], []
    for i, (name, data) in enumerate(files):
        name = _loop_name(name)
        try:
            sec = loops.audio_seconds(data)
        except ValueError:
            raise AppError(f"\"{name}\" is not a readable WAV, AIFF, FLAC or MP3 file")
        if sec <= 0:
            raise AppError(f"\"{name}\" is empty")
        if scene + i >= scenes:
            skipped.append(name)
            continue
        plan.append((scene + i, name, data, sec))
    busy = [s for s, *_ in plan if (tr["clipSlots"][s] or {}).get("clip")]
    if busy and not replace:
        raise CellBusy(f"{len(busy)} cell(s) already have a clip", cells=busy)
    return plan, skipped


def loops_action(track, scenes):
    if len(scenes) == 1:
        return f"Loop added {cell_name(track, scenes[0])}"
    return f"Loops added T{track + 1} S{scenes[0] + 1}–S{scenes[-1] + 1}"


def job_add_loops(oid, track, scene, files, replace):
    """Лупы в ячейки аудиодорожки на Move: загрузка в UPLOAD → версия → одна запись проекта."""
    def fn(stage):
        plan, skipped = plan_loops(ssh_read_song(oid), track, scene, files, replace)
        stage(f"Uploading {len(plan)} file(s) to Samples/UPLOAD")
        rels = upload_loops([(name, data) for _, name, data, _ in plan])
        try:
            return _place_loops(oid, track, scene, plan, rels, skipped, replace, stage)
        except AppError as e:
            got = ", ".join(r.rsplit("/", 1)[1] for r in rels)
            raise AppError(f"{str(e).rstrip('.')}. The project was not changed. Already in Samples/UPLOAD: {got}")
    return fn


def _place_loops(oid, track, scene, plan, rels, skipped, replace, stage):
    """После загрузки: под замком проекта — перепроверка ячеек, клипы, версия, одна запись."""
    stage("Waiting for another edit of this project to finish" if target_lock("move:" + oid).locked() else "Reading project on Move")
    with target_lock("move:" + oid):
        song = ssh_read_song(oid)
        plan_loops(song, track, scene, [(n, d) for _, n, d, _ in plan], replace)    # ячейки не заняли за время загрузки
        new = copy.deepcopy(song)
        tr = new["tracks"][track]
        ts = new.get("timeSignature") or {"upper": 4, "lower": 4}
        bar = int(ts.get("upper", 4)) * 4 / int(ts.get("lower", 4))
        tempo = float(new.get("tempo") or 120.0)
        template = next((sl["clip"] for t in new.get("tracks") or [] for sl in t.get("clipSlots") or []
                         if (sl or {}).get("clip") and sl["clip"].get("sampleUri") is not None), None)
        placed = []
        for (s, name, _data, sec), rel in zip(plan, rels):
            lt, beats = loops.fit(sec, tempo, bar, loops.name_tempo(name))
            tr["clipSlots"][s]["clip"] = loops.audio_clip(template, rel, lt, beats, ts, tr.get("color"))
            placed.append({"scene": s, "sample": rel.rsplit("/", 1)[1], "tempo": round(float(lt), 3), "beats": beats})
        save_move_version(oid, song, loops_action(track, [p["scene"] for p in placed]))
        stage("Writing clips")
        ssh_write_song(oid, dump_song(new))
        with LOCK:
            INFO_CACHE.pop(oid, None)
    return {"placed": placed, "skipped": skipped, "uploaded": rels}


def clip_op_action(op, src, dst):
    a, b = cell_name(*src), cell_name(*dst)
    return {"copy": f"Clip copied {a} → {b}", "move": f"Clip moved {a} → {b}", "swap": f"Clips swapped {a} ↔ {b}"}[op]


def job_clip_op(oid, op, src, dst, replace):
    """Копия/перенос/обмен клипов на Move: одна версия в истории и одна запись проекта."""
    def fn(stage):
        stage("Waiting for another edit of this project to finish" if target_lock("move:" + oid).locked() else "Reading project on Move")
        with target_lock("move:" + oid):
            stage("Reading project on Move")
            song = ssh_read_song(oid)
            new = clip_op(copy.deepcopy(song), op, src, dst, replace)     # ошибка — до записи версии
            save_move_version(oid, song, clip_op_action(op, src, dst))
            stage("Writing clips")
            ssh_write_song(oid, dump_song(new))
            with LOCK:
                INFO_CACHE.pop(oid, None)
            return {"ok": True}
    return fn


def library_clip_op(folder, op, src, dst, replace):
    d = lib_dir(folder)
    bundle = find_file(d, {".ablbundle"})
    tmp = tmp_path(".ablbundle")
    try:
        with target_lock("lib:" + d.name):
            transform_bundle(bundle, tmp, lambda song: clip_op(song, op, src, dst, replace))
            save_lib_version(folder, bundle, clip_op_action(op, src, dst))
            shutil.move(str(tmp), bundle)
    finally:
        tmp.unlink(missing_ok=True)


def _clip_move(oid, track, scene, notes, length, stage, action=""):
    stage("Reading project on Move")
    song = ssh_read_song(oid)
    new = (put_clip(copy.deepcopy(song), track, scene, notes, length) if notes is not None
           else remove_clip(copy.deepcopy(song), track, scene))    # ошибка в правке — до записи версии
    save_move_version(oid, song, action)
    stage("Writing clip" if notes is not None else "Removing clip")
    ssh_write_song(oid, dump_song(new))
    with LOCK:
        INFO_CACHE.pop(oid, None)
    return {"ok": True}


def edit_library(folder, order, pans, key=None):
    d = lib_dir(folder)
    bundle = find_file(d, {".ablbundle"})
    tmp = tmp_path(".ablbundle")
    try:
        with target_lock("lib:" + d.name):
            edit_bundle(bundle, tmp, order, pans, key)      # ошибка в правке — до записи версии
            save_lib_version(folder, bundle, edit_action(order, pans, key))
            shutil.move(str(tmp), bundle)
    finally:
        tmp.unlink(missing_ok=True)


def import_bundle(filename, data, group=None):
    """Добавляет в библиотеку .ablbundle, который уже лежит на компьютере."""
    name = safe_name(re.sub(r"\.ablbundle$", "", filename, flags=re.I))
    tmp = tmp_path(".ablbundle")
    try:
        tmp.write_bytes(data)
        try:
            read_song(tmp)
        except (zipfile.BadZipFile, AppError, ValueError, KeyError):
            raise AppError(f"\"{filename}\" does not look like a Move project (.ablbundle)")
        root, final, n = lib_root(), name, 2
        while (root / final).exists():
            final, n = f"{name} ({n})", n + 1
        d = root / final
        d.mkdir()
        shutil.move(str(tmp), d / f"{final}.ablbundle")
    finally:
        tmp.unlink(missing_ok=True)
    meta = {"savedAt": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if group:
        meta["group"] = str(group)[:80]
    write_json(d / "meta.json", meta)
    return final


def clear_audio(d):
    for f in list(d.iterdir()):
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS:
            f.unlink()


def attach_audio(folder, ext, data):
    if "." + ext not in AUDIO_EXTS:
        raise AppError("Supported files: WAV, MP3, M4A, WebM and OGG")
    d = lib_dir(folder)
    clear_audio(d)
    (d / f"{d.name}.{ext}").write_bytes(data)
    update_meta(d, audioSource="input recording" if ext in ("webm", "m4a") else "own file", audioError=None)


def recordings_for(set_name):
    """Записи Move (папка Recordings); те, что сделаны в этом сете, идут первыми."""
    prefix = (set_name or "").strip().lower() + " rec"
    recs = MOVE.recordings()
    for r in recs:
        r["match"] = bool(set_name) and r["name"].lower().startswith(prefix)
    mine = sorted((r for r in recs if r["match"]), key=lambda r: -r["size"])
    rest = sorted((r for r in recs if not r["match"]), key=lambda r: r["modified"] or "", reverse=True)
    return mine + rest


def fetch_recording(name, d, progress=None):
    r = MOVE.recording_response(name)
    if r.status_code != 200:
        raise AppError(f"Could not download the recording ({r.status_code})")
    total, done = int(r.headers.get("content-length") or 0), 0
    tmp = tmp_path(".wav")
    try:
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(done / total)
        clear_audio(d)
        shutil.move(str(tmp), d / f"{d.name}.wav")
    finally:
        tmp.unlink(missing_ok=True)
    update_meta(d, audioSource=name)


def job_attach_recording(folder, name):
    def fn(stage):
        d = lib_dir(folder)
        stage("Downloading recording from Move", 0)
        fetch_recording(name, d, lambda p: stage("Downloading recording from Move", p))
        return {"ok": True}
    return fn


def rename_library(folder, new_name):
    d = lib_dir(folder)
    new_name = safe_name(new_name)
    if new_name == d.name:
        return d.name
    target = d.parent / new_name
    if target.exists():
        raise AppError("A project with this name already exists in the folder")
    for f in list(d.iterdir()):
        if f.is_file() and f.stem == d.name and f.suffix.lower() in ({".ablbundle"} | AUDIO_EXTS):
            f.rename(d / f"{new_name}{f.suffix}")
    d.rename(target)
    update_meta(target, bundleStamp=None)
    replace_in_order(target.parent, folder, new_name)
    return new_name


def backup_move_set(oid, bundle=None):
    """Копия сета с Move в «_Deleted» библиотеки на компьютере — перед любым удалением с девайса.
    bundle — уже скачанный бандл (иначе скачиваем). Не вышло — AppError, и удалять нельзя."""
    obj = set_by_id(oid)
    name = safe_name(obj.get("name") or "Project")
    d = None
    try:
        trash = lib_root() / "_Deleted"
        trash.mkdir(parents=True, exist_ok=True)
        d = trash / f"{name} (deleted from Move {time.strftime('%Y%m%d-%H%M%S')})"
        k = 2
        while d.exists():
            d, k = trash / f"{name} (deleted from Move {time.strftime('%Y%m%d-%H%M%S')} {k})", k + 1
        d.mkdir()
        target = d / f"{name}.ablbundle"
        if bundle is not None:
            shutil.copyfile(bundle, target)
        else:
            MOVE.download(oid, target)
        write_json(d / "meta.json", {"sourceId": oid, "savedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                     "notes": "Copy saved before the project was deleted from Move."})
        return d
    except (OSError, AppError, MoveOffline, requests.exceptions.RequestException) as e:
        if d is not None:
            shutil.rmtree(d, ignore_errors=True)
        raise AppError(f"Could not save a copy of \"{name}\" before deleting it from Move, so nothing was deleted: {e}")


def trash_library(folder):
    d = lib_dir(folder)
    trash = d.parent / "_Deleted"
    trash.mkdir(exist_ok=True)
    target = trash / f"{d.name} {time.strftime('%Y%m%d-%H%M%S')}"
    d.rename(target)


# ───────────────────────── HTTP ─────────────────────────

SOURCE_NAMES = {"user-library": "User Library", "abl-core-library": "Core Library"}
KIND_NAMES = {"drift": "Drift", "wavetable": "Wavetable", "drumRack": "Drum Rack",
              "melodicSampler": "Melodic Sampler", "drumCell": "Drum Sampler"}


def clip_midi(song, track, scene, project):
    """MIDI-файл клипа: имя дорожки — пресет инструмента, в мета-событии «инструмент» — тип и откуда пресет."""
    clip = get_clip(song, track, scene)
    info = parse_song(song)["tracks"][track]
    preset = info.get("preset") or info.get("name") or f"Track {track + 1}"
    where = " / ".join([SOURCE_NAMES.get(info.get("source"), info.get("source") or "")] + list(info.get("folders") or []))
    instrument = " · ".join(x for x in (KIND_NAMES.get(info.get("kind"), info.get("kind") or ""), where.strip(" /"),
                                        info.get("role") or "") if x)
    filename = f"{safe_name(project)} T{track + 1} {safe_name(preset)} S{scene + 1}.mid"
    return clip_to_midi(clip, song.get("tempo") or 120, preset, instrument), filename


def clip_op_args(b):
    """Тело запроса clip-op → (op, (t, s), (t, s), replace)."""
    try:
        src, dst = b["from"], b["to"]
        if len(src) != 2 or len(dst) != 2:
            raise ValueError
        return (str(b.get("op") or ""), (int(src[0]), int(src[1])), (int(dst[0]), int(dst[1])),
                bool(b.get("replace")))
    except (KeyError, TypeError, ValueError):
        raise AppError("No cells given")


def cell_args(q):
    try:
        return int((q.get("track") or [""])[0]), int((q.get("scene") or [""])[0])
    except ValueError:
        raise AppError("No cell given")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def userlib_route(self, sub, m, q):
        """Библиотека сэмплов/пресетов на Move: дерево, план, применение, папка, загрузка, удаление, файл."""
        if not ssh_enabled():
            raise AppError("The sample library on Move needs pad control enabled (SSH)")
        arg = lambda k, d="": (q.get(k) or [d])[0]
        if sub == [] and m == "GET":
            mode = arg("mode", "samples")
            tree = lib_tree(mode)
            idx = userlib_index()
            def who(path):
                if _project_of(path):
                    return {"kind": "project", "name": _project_of(path)}
                if path.startswith(SCHWUNG_DIR):
                    return {"kind": "schwung", "name": "Schwung state"}
                return {"kind": "preset", "name": path.split("/")[-1]}
            for f in tree["files"]:
                f["used"] = [who(p) for p in idx["refs"].get(f["rel"], [])]
            return self.send_json(tree | {"mode": mode, "root": USERLIB_MODES[mode]})
        if sub == ["plan"] and m == "POST":
            b = self.body()
            return self.send_json(userlib_plan(b.get("mode"), [tuple(x) for x in b.get("moves") or []]))
        if sub == ["apply"] and m == "POST":
            b = self.body()
            plan = userlib_plan(b.get("mode"), [tuple(x) for x in b.get("moves") or []])   # план считается заново
            if plan["conflicts"]:
                raise AppError("The plan has conflicts: " + ", ".join(plan["conflicts"][:3]))
            return self.send_json(start_job("userlib", lambda stage: apply_userlib_plan(plan, stage)))
        if sub == ["folder"] and m == "POST":
            b = self.body()
            userlib_mkdir(b.get("mode"), str(b.get("rel") or ""))
            return self.send_json({"ok": True})
        if sub == ["upload"] and m == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            if n > 400 * 1024 * 1024:
                raise AppError("The file is too large")
            rel = userlib_upload(arg("mode"), arg("dir"), arg("name"), self.rfile.read(n))
            return self.send_json({"ok": True, "rel": rel})
        if sub == ["delete"] and m == "POST":
            b = self.body()
            userlib_delete(b.get("mode"), [str(r) for r in b.get("rels") or []])
            return self.send_json({"ok": True})
        if sub == ["file"] and m == "GET":
            rel = arg("rel")
            ext = Path(rel).suffix.lower()
            ctype = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".aif": "audio/aiff", ".aiff": "audio/aiff",
                     ".flac": "audio/flac"}.get(ext, "application/octet-stream")
            return self.send_bytes(userlib_read(arg("mode", "samples"), rel), ctype)
        raise AppError("Invalid request")

    def fs_route(self, seg, m, q):
        """Папки компьютера для правой панели и копирование компьютер ↔ Move."""
        arg = lambda k, d="": (q.get(k) or [d])[0]
        if seg == ["fs"] and m == "GET":
            path = arg("path")
            if not path:
                path = CFG.get("samplesFolder") or (str(Path.home() / "Music") if (Path.home() / "Music").is_dir() else str(Path.home()))
                try:
                    fs_check(path, must_dir=True)
                except AppError:
                    path = str(Path.home())
            d = fs_list(path, arg("mode", "samples"))
            if arg("path") and CFG.get("samplesFolder") != d["path"]:
                CFG["samplesFolder"] = d["path"]
                save_config()
            return self.send_json(d)
        if seg == ["fs", "choose"] and m == "POST":
            p = choose_folder_dialog("Folder with samples on this computer")
            if p:
                CFG["samplesFolder"] = fs_check(p, must_dir=True).as_posix()
                save_config()
            return self.send_json({"path": CFG.get("samplesFolder") or "", "chosen": bool(p)})
        if seg == ["fs", "file"] and m == "GET":
            p = fs_check(arg("path"))
            if not p.is_file():
                raise AppError("Not a file")
            ctype = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".aif": "audio/aiff", ".aiff": "audio/aiff",
                     ".flac": "audio/flac"}.get(p.suffix.lower(), "application/octet-stream")
            return self.send_bytes(p.read_bytes(), ctype)
        if seg == ["fs", "move"] and m == "POST":
            b = self.body()
            return self.send_json({"path": fs_move(b.get("src") or "", b.get("dst") or "")})
        if seg == ["fs", "mkdir"] and m == "POST":
            b = self.body()
            return self.send_json({"path": fs_mkdir(b.get("parent") or "", b.get("name") or "")})
        if seg == ["fs", "rename"] and m == "POST":
            b = self.body()
            return self.send_json({"path": fs_rename(b.get("path") or "", b.get("name") or "")})
        if seg == ["fs", "reveal"] and m == "POST":
            p = fs_check(self.body().get("path") or "")
            reveal(p, select=True)
            return self.send_json({"ok": True})
        if not ssh_enabled():
            raise AppError("Copying to and from Move needs pad control enabled (SSH)")
        if seg == ["xfer", "to-move"] and m == "POST":
            b = self.body()
            mode, paths, folder = b.get("mode"), [str(x) for x in b.get("paths") or []], str(b.get("dir") or "")
            _check_rel(mode, folder); [fs_check(x) for x in paths]
            return self.send_json(start_job("copy to Move", lambda stage: copy_to_move(mode, paths, folder, stage)))
        if seg == ["xfer", "to-pc"] and m == "POST":
            b = self.body()
            mode, rels, folder = b.get("mode"), [str(x) for x in b.get("rels") or []], str(b.get("dir") or "")
            [_check_rel(mode, r) for r in rels]; fs_check(folder, must_dir=True)
            return self.send_json(start_job("copy to computer", lambda stage: copy_to_pc(mode, rels, folder, stage)))
        raise AppError("Invalid request")

    def send_bytes(self, data, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_midi(self, data, filename):
        from urllib.parse import quote
        self.send_response(200)
        self.send_header("Content-Type", "audio/midi")
        self.send_header("Content-Disposition",
                         f"attachment; filename=\"clip.mid\"; filename*=UTF-8''{quote(filename)}")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def raw_body(self, limit=5 * 1024 * 1024):
        n = int(self.headers.get("Content-Length") or 0)
        self._body_read = True
        if n > limit:
            raise AppError("The file is too large")
        return self.rfile.read(n) if n else b""

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        self._body_read = True
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            raise AppError("Invalid request")

    def send_file(self, path, ctype=None):
        path = Path(path)
        size = path.stat().st_size
        ctype = ctype or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        start, end = 0, size - 1
        rng = self.headers.get("Range")
        m = re.match(r"bytes=(\d*)-(\d*)$", rng or "")
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1))
                end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
            else:
                start = max(0, size - int(m.group(2)))
            if start > end or start >= size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command == "HEAD":
            return
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            try:
                while left > 0:
                    chunk = f.read(min(1 << 16, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def handle_any(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        origin = self.headers.get("Origin")
        if host not in ("127.0.0.1", "localhost") or (
                origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost")):
            return self.send_json({"error": "forbidden"}, 403)
        self._body_read = False
        try:
            self.route()
        except AuthRequired:
            self.send_json({"error": "auth"}, 401)
        except MoveOffline:
            self.send_json({"error": "offline",
                            "message": "Move is unreachable. Check that it is on and on the same Wi-Fi network."}, 503)
        except CellBusy as e:
            self.send_json({"error": "busy", "message": str(e), "cells": e.cells}, 409)
        except SamplesMissing as e:
            self.send_json({"error": "missing", "message": str(e), "missing": e.missing}, 409)
        except AppError as e:
            self.send_json({"error": "app", "message": str(e)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # noqa: BLE001
            log_error(f"{self.command} {urlparse(self.path).path}", e)
            self.send_json({"error": "app", "message": f"Internal error: {e}"}, 500)
        finally:
            # ответ отправлен, а тело запроса так и не прочитано — его байты сломали бы следующий запрос
            if not self._body_read and int(self.headers.get("Content-Length") or 0) > 0:
                self.close_connection = True

    do_GET = do_POST = do_PATCH = do_DELETE = do_HEAD = handle_any

    def route(self):
        u = urlparse(self.path)
        path, q, m = unquote(u.path), parse_qs(u.query), self.command
        seg = [s for s in path.split("/") if s]

        if m in ("GET", "HEAD") and path in ("/", "/index.html"):
            return self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if m in ("GET", "HEAD") and len(seg) == 2 and seg[0] == "static" and re.fullmatch(r"[a-z0-9_-]+\.png", seg[1]):
            f = STATIC_DIR / seg[1]                 # картинки интерфейса (логотип, значок); только .png из static
            if f.is_file():
                return self.send_file(f, "image/png")
        if not seg or seg[0] != "api":
            return self.send_json({"error": "not found"}, 404)
        seg = seg[1:]

        # ── настройки
        if seg == ["report"] and m == "POST":
            b = self.body()
            path = save_report(str(b.get("text") or "")[:5000])
            if b.get("reveal"):
                try:
                    reveal(path, select=True)
                except Exception:  # noqa: BLE001  — открыть папку не вышло: файл всё равно сохранён
                    pass
            return self.send_json({"ok": True, "path": str(path), "name": path.name})
        if seg == ["config"] and m == "GET":
            return self.send_json({"library": str(lib_root()), "moveUrl": CFG["move_url"],
                                   "audioFormat": CFG.get("audio_format", "wav"),
                                   "build": BUILD,
                                   "uiStamp": int((STATIC_DIR / "index.html").stat().st_mtime),
                                   "stale": _code_changed()})
        if seg == ["config"] and m == "POST":
            b = self.body()
            if "library" in b:
                p = Path(str(b["library"])).expanduser()
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise AppError(f"Cannot use this folder: {e}")
                CFG["library"] = str(p)
            if b.get("audioFormat") in ("wav", "mp3"):
                CFG["audio_format"] = b["audioFormat"]
            if "moveUrl" in b:
                new_url = normalize_move_url(b["moveUrl"])
                if new_url != CFG.get("move_url"):
                    CFG["move_url"] = new_url
                    ssh_session_reset()                  # SSH-соединение было к старому адресу
            if "midiFolder" in b:
                mf = str(b["midiFolder"] or "").strip()
                if mf and not Path(mf).expanduser().is_dir():
                    raise AppError("MIDI folder not found")
                CFG["midiFolder"] = str(Path(mf).expanduser()) if mf else ""
            save_config()
            return self.send_json({"ok": True, "library": CFG["library"]})
        if seg == ["choose-midi-folder"] and m == "POST":
            p = choose_folder_dialog("Folder with drum MIDI clips")
            if p:
                CFG["midiFolder"] = p
                save_config()
            return self.send_json({"midiFolder": CFG.get("midiFolder") or "", "chosen": bool(p)})
        if seg == ["choose-folder"] and m == "POST":
            p = choose_folder_dialog()
            if p:
                CFG["library"] = p
                save_config()
            return self.send_json({"library": CFG["library"], "chosen": bool(p)})

        # ── авторизация
        if seg == ["auth", "start"] and m == "POST":
            MOVE.start_challenge()
            return self.send_json({"ok": True})
        if seg == ["auth", "code"] and m == "POST":
            return self.send_json(MOVE.answer_challenge(str(self.body().get("code", "")).strip()))

        # ── порядок плиток
        if seg == ["order"] and m == "POST":
            b = self.body()
            ids = [str(x) for x in b.get("ids", [])]
            if b.get("side") == "move":
                CFG["move_order"] = ids
                save_config()
            else:
                write_json(lib_root() / ".order.json", ids)
            return self.send_json({"ok": True})

        # ── задачи
        if len(seg) == 3 and seg[0] == "jobs" and seg[2] == "cancel" and m == "POST":
            job = JOBS.get(seg[1])
            if job:
                job["cancel"] = True
            return self.send_json({"ok": True})
        if len(seg) == 2 and seg[0] == "jobs" and m == "GET":
            job = JOBS.get(seg[1])
            return self.send_json(job or {"status": "error", "error": "Job not found"})

        # ── Move
        if seg == ["move", "recordings"] and m == "GET":
            return self.send_json({"recordings": recordings_for((q.get("set") or [""])[0])[:400]})
        if len(seg) == 4 and seg[:2] == ["move", "recordings"] and seg[3] == "audio" and m in ("GET", "HEAD"):
            r = MOVE.recording_response(seg[2], self.headers.get("Range"))
            if r.status_code not in (200, 206):
                return self.send_json({"error": "no recording"}, 404)
            self.send_response(r.status_code)
            for h in ("Content-Type", "Content-Length", "Content-Range"):
                if r.headers.get(h):
                    self.send_header(h, r.headers[h])
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-store")
            if not r.headers.get("Content-Length"):
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            if m == "GET":
                try:
                    for chunk in r.iter_content(1 << 15):
                        self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError, requests.exceptions.RequestException):
                    pass
            r.close()
            return
        if seg == ["ssh", "setup"] and m == "POST":
            return self.send_json(start_job("ssh", job_ssh_setup))
        if seg == ["move", "slots"] and m == "POST":
            if not ssh_enabled():
                raise AppError("Enable pad control first")
            moves = [(str(x["id"]), int(x["slot"])) for x in self.body().get("moves", [])]
            cur = {k: v["slot"] for k, v in ssh_slots().items()}
            for oid, slot in moves:
                if oid not in cur:
                    raise AppError("Project not found on Move")
                cur[oid] = slot
            used = [v for v in cur.values() if v is not None]
            if len(used) != len(set(used)):
                raise AppError("Two projects cannot share one pad")
            ssh_set_slots(moves)
            return self.send_json({"ok": True})
        if seg == ["move", "sets"] and m == "GET":
            objs = MOVE.list_sets()
            slots, ssh = {}, {"enabled": ssh_enabled(), "ok": False, "error": None}
            if ssh["enabled"]:
                try:
                    slots = ssh_slots()
                    ssh["ok"] = True
                except SshError as e:
                    ssh["error"] = str(e)
            sw = set()
            if ssh["ok"]:
                try:
                    sw = schwung_sets()
                except SshError:
                    pass
            meta = CFG.get("move_meta") or {}
            pos = {x: i for i, x in enumerate(CFG.get("move_order") or [])}
            items = [{
                "id": o["objectId"], "name": o.get("name", ""),
                "modified": o.get("lastModifiedDateTime"),
                "description": meta.get(o["objectId"], {}).get("description", ""),
                "notes": meta.get(o["objectId"], {}).get("notes", ""),
                "info": cached_info(o["objectId"], o.get("lastModifiedDateTime")),
                "slot": slots.get(o["objectId"], {}).get("slot"),
                "color": slots.get(o["objectId"], {}).get("color"),
                "schwung": o["objectId"] in sw,
            } for o in objs]
            items.sort(key=lambda it: pos.get(it["id"], len(pos)))
            return self.send_json({"sets": items, "ssh": ssh})
        if seg and seg[0] == "userlib":
            return self.userlib_route(seg[1:], m, q)
        if seg and seg[0] in ("fs", "xfer"):
            return self.fs_route(seg, m, q)
        if seg == ["drumgen", "patterns"] and m == "GET":
            if not MINE_CACHE:
                MINE_CACHE.update(read_json(_mine_cache_file(), {}))
            start_mine_scan()                    # разбор своих проектов — в фоне, ответ сразу
            pats = all_patterns()
            return self.send_json({"genres": drumgen.genres(pats), "genreGroups": drumgen.genre_list(pats),
                                   "midiFolder": CFG.get("midiFolder") or "", "credit": drumgen.CREDIT,
                                   "mine": {k: MINE_STATE[k] for k in ("ready", "done", "total")},
                                   "patterns": [{k: p[k] for k in ("id", "name", "genre", "source", "steps")} for p in pats]})
        if seg == ["drumgen"] and m == "POST":
            b = self.body()
            side, ident, track = b.get("side"), str(b.get("id") or ""), int(b.get("track") or 0)
            pads = known_pads(b.get("pads")) if b.get("pads") is not None else \
                drumgen.kit_pads(side_song(side, ident), track, kit_overrides(side, ident, track))
            if not pads:
                raise AppError("This track has no Drum Rack")
            return self.send_json(drumgen.generate(
                all_patterns(), str(b.get("genre") or ""), b.get("pattern"), pads,
                mutation=float(b.get("mutation", 35)), seed=int(b.get("seed") or 1), bars=int(b.get("bars") or 2),
                swing=float(b.get("swing", 50)), deja_vu=float(b.get("deja_vu", 50)),
                ghosts=b.get("ghosts", 30) if not isinstance(b.get("ghosts"), bool) else b.get("ghosts"),
                euclid=bool(b.get("euclid", True)),
                avoid=b.get("avoid"),
                half=b.get("half") if b.get("half") in ("all", "kick", "kick+snare") else ("all" if b.get("half") is True else False))
                | {"pads": pads})
        if len(seg) >= 3 and seg[:2] == ["move", "sets"]:
            oid = seg[2]
            if not re.fullmatch(r"[0-9a-fA-F-]{8,64}", oid):
                raise AppError("Invalid identifier")
            act = seg[3] if len(seg) > 3 else None
            if act == "clip.mid" and m == "GET":
                t, sc = cell_args(q)
                song = move_song(oid)
                return self.send_midi(*clip_midi(song, t, sc, set_by_id(oid).get("name", "Clip")))
            if act == "clip" and m == "POST":
                t, sc = cell_args(q)
                if not ssh_enabled():
                    raise AppError("Import to Move needs pad control enabled")
                notes, length = read_midi_upload(self.raw_body())
                if (q.get("replace") or ["0"])[0] != "1" and cell_busy(ssh_read_song(oid), t, sc):
                    return self.send_json({"error": "busy", "message": "Cell is occupied"}, 409)
                return self.send_json(start_job("clip", job_clip_move(oid, t, sc, notes, length,
                                                                      f"Clip loaded from file {cell_name(t, sc)}")))
            if act == "clip" and m == "DELETE":
                t, sc = cell_args(q)
                if not ssh_enabled():
                    raise AppError("Deleting a clip on Move needs pad control enabled")
                return self.send_json(start_job("clip", job_clip_move(oid, t, sc, None, 0, f"Clip deleted {cell_name(t, sc)}")))
            if act == "loops" and m == "POST":
                t, sc = cell_args(q)
                body = self.raw_body(limit=300 * 1024 * 1024)
                if not ssh_enabled():
                    raise AppError("Adding loops on Move needs pad control enabled")
                files = prepare_loop_files(read_loop_files(self.headers.get("Content-Type"), body))
                replace = (q.get("replace") or ["0"])[0] == "1"
                plan_loops(ssh_read_song(oid), t, sc, files, replace)     # 400/409 сразу, до загрузки
                return self.send_json(start_job("loops", job_add_loops(oid, t, sc, files, replace)))
            if act == "history" and m == "GET" and len(seg) == 4:
                return self.send_json({"versions": list_history("move", oid)})
            if act == "history" and m == "POST" and seg[4:] == ["restore"]:
                b = self.body()
                if not ssh_enabled():
                    raise AppError("Restoring on Move needs pad control enabled")
                data, entry = check_restore("move", oid, b.get("id"), bool(b.get("force")))
                return self.send_json(start_job("restore", job_restore_move(oid, data, entry)))
            if act == "clip-op" and m == "POST":
                op, src, dst, replace = clip_op_args(self.body())
                if not ssh_enabled():
                    raise AppError("Editing clips on Move needs pad control enabled")
                clip_op(ssh_read_song(oid), op, src, dst, replace)      # проверка до задачи: 400/409 сразу
                return self.send_json(start_job("clip", job_clip_op(oid, op, src, dst, replace)))
            if act == "kit":
                track = int((q.get("track") or ["0"])[0])
                if m == "POST":
                    save_kit_overrides("move", oid, track, self.body().get("overrides"))
                    return self.send_json({"ok": True})
                ov = kit_overrides("move", oid, track)
                return self.send_json({"pads": drumgen.kit_pads(move_song(oid), track, ov), "overrides": ov})
            if act == "clip-notes" and m == "POST":
                t, sc = cell_args(q)
                if not ssh_enabled():
                    raise AppError("Import to Move needs pad control enabled")
                b = self.body()
                length = clip_length(b)
                notes = clean_notes(b.get("notes"), length)
                if (q.get("replace") or ["0"])[0] != "1" and cell_busy(ssh_read_song(oid), t, sc):
                    return self.send_json({"error": "busy", "message": "Cell is occupied"}, 409)
                return self.send_json(start_job("clip", job_clip_move(oid, t, sc, notes, length,
                                                                      f"Pattern generated {cell_name(t, sc)}")))
            if act == "info" and m == "GET":
                return self.send_json({"info": analyze_set(oid, (q.get("stamp") or [""])[0])})
            if act == "pull" and m == "POST":
                b = self.body()
                return self.send_json(start_job("pull", job_pull(oid, b.get("audio", True), b.get("group"))))
            if act == "edit" and m == "POST":
                b = self.body()
                return self.send_json(start_job("edit", job_edit_move(
                    oid, [int(x) for x in b.get("order") or []] or None, b.get("pans") or {}, bool(b.get("replace")),
                    b.get("key") or None)))
            if act == "meta" and m == "POST":
                b = self.body()
                entry = CFG.setdefault("move_meta", {}).setdefault(oid, {})
                for k in ("description", "notes"):
                    if k in b:
                        entry[k] = str(b[k])
                save_config()
                return self.send_json({"ok": True})
            if act is None and m == "PATCH":
                MOVE.rename(oid, safe_name(self.body().get("name")))
                return self.send_json({"ok": True})
            if act is None and m == "DELETE":
                kept = backup_move_set(oid)                  # копия в «_Deleted» на компьютере, иначе не удаляем
                MOVE.delete(oid)
                with LOCK:
                    INFO_CACHE.pop(oid, None)
                return self.send_json({"ok": True, "backup": kept.name})

        # ── библиотека
        if seg == ["library-import"] and m == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            if n > 600 * 1024 * 1024:
                raise AppError("The file is too large")
            final = import_bundle((q.get("name") or ["Project.ablbundle"])[0], self.rfile.read(n),
                                  (q.get("group") or [None])[0])
            return self.send_json({"ok": True, "id": final})
        if seg == ["library"] and m == "GET":
            return self.send_json({"items": list_library(), "path": str(lib_root())})
        if len(seg) >= 2 and seg[0] == "library":
            folder = seg[1]
            act = seg[2] if len(seg) > 2 else None
            if act == "clip.mid" and m == "GET":
                t, sc = cell_args(q)
                d = lib_dir(folder)
                song = read_song(find_file(d, {".ablbundle"}))
                return self.send_midi(*clip_midi(song, t, sc, d.name))
            if act == "clip" and m == "POST":
                t, sc = cell_args(q)
                notes, length = read_midi_upload(self.raw_body())
                d = lib_dir(folder)
                if (q.get("replace") or ["0"])[0] != "1" and cell_busy(read_song(find_file(d, {".ablbundle"})), t, sc):
                    return self.send_json({"error": "busy", "message": "Cell is occupied"}, 409)
                library_put_clip(folder, t, sc, notes, length, f"Clip loaded from file {cell_name(t, sc)}")
                return self.send_json({"ok": True})
            if act == "clip" and m == "DELETE":
                t, sc = cell_args(q)
                library_put_clip(folder, t, sc, None, 0, action=f"Clip deleted {cell_name(t, sc)}")
                return self.send_json({"ok": True})
            if act == "clip-op" and m == "POST":
                library_clip_op(folder, *clip_op_args(self.body()))
                return self.send_json({"ok": True})
            if act == "history" and m == "GET" and len(seg) == 3:
                return self.send_json({"versions": list_history("lib", folder)})
            if act == "history" and m == "POST" and seg[3:] == ["restore"]:
                b = self.body()
                data, entry = check_restore("lib", folder, b.get("id"), bool(b.get("force")))
                restore_library(folder, data, entry)
                return self.send_json({"ok": True})
            if act == "kit":
                track = int((q.get("track") or ["0"])[0])
                if m == "POST":
                    save_kit_overrides("lib", folder, track, self.body().get("overrides"))
                    return self.send_json({"ok": True})
                ov = kit_overrides("lib", folder, track)
                return self.send_json({"pads": drumgen.kit_pads(side_song("lib", folder), track, ov), "overrides": ov})
            if act == "clip-notes" and m == "POST":
                t, sc = cell_args(q)
                b = self.body()
                length = clip_length(b)
                notes = clean_notes(b.get("notes"), length)
                d = lib_dir(folder)
                if (q.get("replace") or ["0"])[0] != "1" and cell_busy(read_song(find_file(d, {".ablbundle"})), t, sc):
                    return self.send_json({"error": "busy", "message": "Cell is occupied"}, 409)
                library_put_clip(folder, t, sc, notes, length, f"Pattern generated {cell_name(t, sc)}")
                return self.send_json({"ok": True})
            if act == "audio" and m in ("GET", "HEAD"):
                audio = find_file(lib_dir(folder), AUDIO_EXTS)
                if not audio:
                    return self.send_json({"error": "no audio"}, 404)
                return self.send_file(audio)
            if act == "audio" and m == "POST":
                n = int(self.headers.get("Content-Length") or 0)
                attach_audio(folder, (q.get("ext") or [""])[0].lower(), self.rfile.read(n))
                return self.send_json({"ok": True})
            if act == "render" and m == "POST":
                return self.send_json(start_job("render", job_render_library(folder)))
            if act == "audio-from-move" and m == "POST":
                return self.send_json(start_job("rec", job_attach_recording(folder, str(self.body().get("name", "")))))
            if act == "push" and m == "POST":
                return self.send_json(start_job("push", job_push(folder, (b := self.body()).get("slot"), b.get("replace"))))
            if act == "edit" and m == "POST":
                b = self.body()
                edit_library(folder, [int(x) for x in b.get("order") or []] or None, b.get("pans") or {}, b.get("key") or None)
                return self.send_json({"ok": True})
            if act == "reveal" and m == "POST":
                reveal(lib_dir(folder))
                return self.send_json({"ok": True})
            if act is None and m == "PATCH":
                b = self.body()
                d = lib_dir(folder)
                fields = {k: str(b[k]) for k in ("description", "notes", "group") if k in b}
                if fields:
                    update_meta(d, **fields)
                new = rename_library(folder, b["name"]) if "name" in b else folder
                return self.send_json({"ok": True, "id": new})
            if act is None and m == "DELETE":
                trash_library(folder)
                return self.send_json({"ok": True})

        return self.send_json({"error": "not found"}, 404)


def make_server():
    """Сервер программы, ещё не запущенный: (сервер, адрес)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for f in CACHE_DIR.glob("tmp-*"):
        f.unlink(missing_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    start_mine_scan()                     # свои барабанные клипы для генератора — в фоне, с первой секунды
    return srv, f"http://127.0.0.1:{PORT}"


def main():
    srv, url = make_server()
    print(f"{APP_NAME} (build {BUILD}) running: {url}\nStop with Ctrl+C")
    if not os.environ.get("MOVE_MANAGER_NO_BROWSER"):
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
