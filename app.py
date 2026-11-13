#!/usr/bin/env python3
"""Move Manager — локальный менеджер проектов Ableton Move.

Запуск:  python3 app.py     (откроется http://127.0.0.1:8765)
Нужен только пакет requests:  python3 -m pip install requests
"""
import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
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

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
CACHE_DIR = APP_DIR / "cache"
STATIC_DIR = APP_DIR / "static"
PORT = int(os.environ.get("MOVE_MANAGER_PORT", "8765"))
LOCK = threading.RLock()
STARTED = time.time()
BUILD = "16"          # номер сборки: виден в шапке программы и в журнале экспорта
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
        name = tr.get("name") or top.get("name") or (preset or {}).get("name") or kind or f"Track {i + 1}"
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
            "role": guess_role(folders, [name, (preset or {}).get("name") or ""], kind, tr.get("kind")),
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
    }


def find_song_entry(zf):
    for name in zf.namelist():
        if name.split("/")[-1] == "Song.abl":
            return name
    raise AppError("В бандле не найден Song.abl")


def read_song(bundle_path):
    with zipfile.ZipFile(bundle_path) as zf:
        return json.loads(zf.read(find_song_entry(zf)).decode("utf-8"))


def edit_song(song, order=None, pans=None, key=None):
    """Меняет тональность сета, панораму и порядок дорожек. pans: {исходный индекс дорожки: -1..1}."""
    tracks = song.get("tracks") or []
    if key and ("rootNote" in key or "scale" in key):
        root, scale = int(key.get("rootNote", -1)), str(key.get("scale") or "").strip()
        if not 0 <= root <= 11 or not scale or len(scale) > 60:
            raise AppError("Некорректная тональность")
        song["rootNote"], song["scale"] = root, scale
    if key and key.get("tempo") is not None:
        try:
            tempo = round(float(key["tempo"]), 2)
        except (TypeError, ValueError):
            raise AppError("Некорректный темп")
        if not 40 <= tempo <= 300:
            raise AppError("Темп должен быть от 40 до 300 bpm")
        song["tempo"] = tempo
    for key, val in (pans or {}).items():
        i = int(key)
        if not 0 <= i < len(tracks):
            raise AppError("Неверный номер дорожки")
        v = max(-1.0, min(1.0, float(val)))
        mixer = tracks[i].setdefault("mixer", {})
        if isinstance(mixer.get("pan"), dict):
            mixer["pan"]["value"] = v
        else:
            mixer["pan"] = v
    if order:
        if sorted(order) != list(range(len(tracks))):
            raise AppError(f"Неверный порядок дорожек: в проекте их {len(tracks)}")
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
            raise AppError("Move не показал код. Убедитесь, что он включён и не в режиме загрузки.")

    def answer_challenge(self, code):
        try:
            r = self.req("POST", "/api/v1/challenge-response", json={"secret": code})
        except AuthRequired:
            return {"ok": False, "error": "Неверный код"}
        if r.status_code == 429:
            return {"ok": False, "error": f"Слишком много попыток, подождите {r.headers.get('retry-after', '60')} с"}
        if r.status_code >= 400:
            return {"ok": False, "error": f"Ошибка авторизации ({r.status_code})"}
        token = r.headers.get("Ableton-Challenge-Response-Token")
        if token:
            self.s.headers["Ableton-Challenge-Response-Token"] = token
        self._persist_cookies()
        return {"ok": True}

    def list_sets(self):
        r = self.req("GET", "/api/v1/data/Sets")
        if r.status_code >= 400:
            raise AppError(f"Move ответил {r.status_code}")
        return r.json().get("objects", [])

    def download(self, oid, dest, progress=None):
        r = self.req("GET", f"/api/v1/data/Sets/{oid}", stream=True, timeout=(10, 300))
        if r.status_code != 200:
            raise AppError(f"Не удалось скачать проект ({r.status_code})")
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
            raise AppError(f"Move не принял проект ({r.status_code}): {r.text[:200]}")
        try:
            for item in (r.json() or {}).get("files", []):
                if item.get("error"):
                    raise AppError(f"Move: {item['error']}")
        except ValueError:
            pass

    def recordings(self):
        r = self.req("GET", "/api/v1/files/Recordings")
        if r.status_code >= 400:
            raise AppError(f"Move не отдал список записей ({r.status_code})")
        out = []
        for p in r.json().get("paths", []):
            if not p.get("isDirectory"):
                out.append({"name": unquote(p["path"]), "size": p.get("size", 0),
                            "modified": p.get("lastModifiedDateTime")})
        return out

    def recording_response(self, name, range_header=None):
        if "/" in name or name.startswith("."):
            raise AppError("Некорректное имя записи")
        headers = {"Range": range_header} if range_header else {}
        return self.req("GET", "/api/v1/files/Recordings/" + requests.utils.quote(name, safe=""),
                        stream=True, timeout=(10, 300), headers=headers)

    def rename(self, oid, name):
        r = self.req("PATCH", f"/api/v1/data/Sets/{oid}", json={"newName": name})
        if r.status_code >= 400:
            raise AppError(f"Не удалось переименовать ({r.status_code}): {r.text[:200]}")

    def delete(self, oid):
        r = self.req("DELETE", f"/api/v1/data/Sets/{oid}")
        if r.status_code >= 400:
            raise AppError(f"Не удалось удалить ({r.status_code})")

    def render(self, oid, fmt, dest, progress=None, cancelled=None):
        """Экспорт звука сета самим Move — тот же запрос, что и «Export as Audio» в штатном менеджере.

        Некоторые сеты Move не экспортирует вовсе: принимает запрос и молчит (так же ведёт себя
        штатный менеджер). Поэтому ожидание ограничено и его можно прервать, а зависшее задание
        снимается, чтобы не задерживать следующие. Экспорты идут строго по одному."""
        cancelled = cancelled or (lambda: False)
        while not RENDER_LOCK.acquire(timeout=1):
            if cancelled():
                raise AppError("Экспорт звука пропущен")
        try:
            return self._render(oid, fmt, dest, progress, cancelled)
        finally:
            RENDER_LOCK.release()

    def _render(self, oid, fmt, dest, progress, cancelled):
        start_timeout = float(os.environ.get("MOVE_RENDER_START_TIMEOUT", "45"))
        silence_timeout = float(os.environ.get("MOVE_RENDER_SILENCE_TIMEOUT", "600"))
        r = self.req("POST", f"/api/v1/render/{oid}", params={"format": fmt}, timeout=60)
        if r.status_code >= 400:
            raise AppError(f"Move не начал экспорт ({r.status_code}): {r.text[:200]}")
        info = r.json()
        rid, href = info.get("id"), info.get("href")
        render_log(f"--- экспорт (сборка {BUILD}): сет {oid}, формат {fmt}; ответ на запрос: {r.status_code} {r.text[:200]}")
        if not href:
            raise AppError("Move не вернул ссылку на аудио")
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
                            render_log(f"событие: {line[:300]}")
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
                    render_log("экспорт пропущен пользователем")
                    raise AppError("Экспорт звука пропущен")
                if st["failed"]:
                    raise AppError("Move сообщил, что экспорт не удался")
                if not st["got"] and now - t0 > start_timeout:
                    render_log(f"за {int(start_timeout)} с Move не начал экспорт — задание снято")
                    raise AppError(f"Move не экспортирует этот проект: за {int(start_timeout)} с экспорт не начался. "
                                   "Так же он ведёт себя в штатном менеджере")
                if st["got"] and not st["finished"] and now - st["last"] > silence_timeout:
                    render_log("Move перестал присылать события — задание снято")
                    raise AppError("Move начал экспорт, но перестал отвечать")
                if st["finished"] or (st["got"] and now >= next_probe):
                    next_probe = now + 5
                    a = self.req("GET", href, stream=True, timeout=(10, 600))
                    if a.status_code == 200:
                        render_log(f"скачивание {href}: 200 {a.headers.get('content-type')} {a.headers.get('content-length')}")
                        resp = a
                        break
                    body = a.text[:120]
                    a.close()
                    if st["finished"]:
                        misses += 1
                        render_log(f"скачивание {href}, попытка {misses}: {a.status_code} {body}")
                        if misses >= 8:
                            raise AppError(f"Экспорт закончился, но Move не отдал файл ({a.status_code})")
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
SSH_KEY = APP_DIR / "move_ssh_key"
UUID_RE = re.compile(r"[0-9a-fA-F-]{8,64}")
REFRESH = ("dbus-send --system --type=method_call --dest=com.ableton.move --print-reply "
           "/com/ableton/move/browser com.ableton.move.Browser.refreshCache >/dev/null 2>&1 || true")


def ssh_enabled():
    return bool(CFG.get("ssh_enabled"))


def ssh_run(script, data=None, timeout=40):
    if os.environ.get("MOVE_SSH_CMD"):
        cmd = shlex.split(os.environ["MOVE_SSH_CMD"])
    else:
        host = urlparse(CFG["move_url"]).hostname or "move.local"
        cmd = ["ssh", "-i", str(SSH_KEY), "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
               "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={APP_DIR / 'known_hosts'}",
               "-o", "ConnectTimeout=8", f"ableton@{host}"]
    try:
        r = subprocess.run(cmd + [script], input=data, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SshError("Move не ответил по SSH")
    except FileNotFoundError:
        raise SshError("На компьютере не найдена команда ssh")
    if r.returncode != 0:
        raise SshError("SSH: " + (r.stderr.decode("utf-8", "replace").strip()[-300:] or f"код {r.returncode}"))
    return r.stdout


def set_dir(oid):
    if not UUID_RE.fullmatch(oid):
        raise AppError("Некорректный идентификатор")
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
            raise AppError("Номер пэда должен быть от 1 до 32")
        cmds.append(f"setfattr -n user.song-index -v {slot} {set_dir(oid)}")
    if cmds:
        ssh_run(" && ".join(cmds) + "; " + REFRESH)


def ssh_read_song(oid):
    return json.loads(ssh_run(f"cat {set_dir(oid)}/*/Song.abl").decode("utf-8"))


def ssh_write_song(oid, payload):
    ssh_run(f'set -e; f=$(ls {set_dir(oid)}/*/Song.abl | head -n 1); [ -n "$f" ]; '
            f'cat > "$f.tmp"; mv "$f.tmp" "$f"; {REFRESH}', data=payload, timeout=90)


def job_ssh_setup(stage):
    stage("Готовлю ключ")
    pub_path = Path(str(SSH_KEY) + ".pub")
    if not SSH_KEY.exists() or not pub_path.exists():
        try:
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "move-manager", "-f", str(SSH_KEY)],
                           check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError) as e:
            raise AppError(f"Не удалось создать SSH-ключ: {e}")
    try:
        ssh_run("echo ok", timeout=15)
    except SshError:
        stage("Подтвердите добавление ключа колесом на Move")
        r = MOVE.req("POST", "/api/v1/ssh", data=pub_path.read_text().strip().encode(), timeout=(10, 180),
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        added = False
        try:
            added = bool(r.json().get("added"))
        except ValueError:
            pass
        if r.status_code >= 400 or not added:
            raise AppError("Move не добавил ключ. Подтвердите запрос колесом на устройстве и попробуйте ещё раз.")
        stage("Проверяю подключение")
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
    return c["info"] if c and c.get("stamp") == stamp else None


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
        raise AppError("Пустое название")
    return name[:120]


def lib_dir(folder):
    root = lib_root()
    p = (root / folder).resolve()
    if p.parent != root.resolve() or not p.is_dir():
        raise AppError("Проект не найден в папке")
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
    if meta.get("bundleStamp") != stamp or "info" not in meta:
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


def choose_folder_dialog():
    if sys.platform != "darwin":
        raise AppError("Системный выбор папки доступен только на macOS — введите путь вручную")
    script = 'POSIX path of (choose folder with prompt "Папка для проектов Move")'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=300)
    path = r.stdout.strip()
    if r.returncode != 0 or not path:
        return None
    return path


# ───────────────────────── фоновые задачи ─────────────────────────

JOBS = {}


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
            job.update(status="error", error="Move недоступен. Проверьте, что он включён и в той же сети.")
        except Exception as e:  # noqa: BLE001
            job.update(status="error", error=str(e))

    threading.Thread(target=run, daemon=True).start()
    return job


def set_by_id(oid):
    for o in MOVE.list_sets():
        if o.get("objectId") == oid:
            return o
    raise AppError("Проект не найден на Move")


def render_into(oid, d, stage):
    """Экспортирует звук сета средствами Move и кладёт файл в папку проекта. Возвращает текст ошибки или None."""
    fmt = CFG.get("audio_format", "wav")
    tmp_a = tmp_path("." + fmt)
    label = "Move экспортирует звук"

    def prog(p):
        stage("Move собирает файл" if p is None else label, p)
    try:
        stage("Жду очереди на экспорт" if RENDER_LOCK.locked() else label, None, cancellable=True)
        MOVE.render(oid, fmt, tmp_a, prog, getattr(stage, "cancelled", None))
        clear_audio(d)
        shutil.move(str(tmp_a), d / f"{d.name}.{fmt}")
        update_meta(d, audioSource="экспорт Move", audioError=None)
        return None
    except (AppError, MoveOffline) as e:
        msg = str(e) or "Move недоступен"
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
        d = root / name
        d.mkdir(exist_ok=True)
        stage("Скачиваю проект")
        tmp = tmp_path(".ablbundle")
        try:
            MOVE.download(oid, tmp, lambda p: stage("Скачиваю проект", p))
            info = parse_song(read_song(tmp))
            for old in d.glob("*.ablbundle"):
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
        meta.pop("bundleStamp", None)
        write_json(d / "meta.json", meta)
        stage("Проект сохранён", None, saved=True)
        audio_error = render_into(oid, d, stage) if with_audio else None
        return {"folder": name, "audioError": audio_error}
    return fn


def job_render_library(folder):
    def fn(stage):
        d = lib_dir(folder)
        oid = read_json(d / "meta.json", {}).get("sourceId")
        ids = {o["objectId"]: o for o in MOVE.list_sets()}
        if oid not in ids:
            same = [o for o in ids.values() if o.get("name") == d.name]
            if len(same) != 1:
                raise AppError("Этого проекта сейчас нет на Move. Загрузите его на Move и повторите экспорт.")
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
            raise AppError("В папке проекта нет .ablbundle")
        if replace_id and not UUID_RE.fullmatch(replace_id):
            raise AppError("Некорректный идентификатор")
        before = {o["objectId"] for o in MOVE.list_sets()}
        if replace_id and replace_id not in before:
            raise AppError("Заменяемого проекта уже нет на Move")
        stage("Загружаю на Move")
        MOVE.upload(bundle, f"{d.name}.ablbundle")
        created = [o["objectId"] for o in MOVE.list_sets() if o["objectId"] not in before]
        if replace_id:
            # старый проект удаляем только после того, как новый однозначно найден на устройстве
            if len(created) != 1:
                raise AppError("Новый проект загружен, но я не смог однозначно его найти — старый оставлен на месте")
            stage("Убираю прежний проект с пэда")
            MOVE.delete(replace_id)
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
        return {"name": d.name, "slot": placed, "replaced": bool(replace_id)}
    return fn


def job_edit_move(oid, order, pans, replace, key=None):
    def fn(stage):
        obj = set_by_id(oid)
        if replace and ssh_enabled():
            stage("Читаю проект на Move")
            song = ssh_read_song(oid)
            backups = APP_DIR / "backups"
            backups.mkdir(exist_ok=True)
            (backups / f"{safe_name(obj['name'])} {time.strftime('%Y%m%d-%H%M%S')}.abl").write_bytes(dump_song(song))
            stage("Записываю изменения")
            ssh_write_song(oid, dump_song(edit_song(song, order, pans, key)))
            with LOCK:
                INFO_CACHE.pop(oid, None)
            return {"inPlace": True}
        before = {o["objectId"] for o in MOVE.list_sets()}
        src, dst = tmp_path(".ablbundle"), tmp_path(".ablbundle")
        new_name = f"{obj['name']}_edit"
        try:
            stage("Скачиваю проект")
            MOVE.download(oid, src)
            stage("Применяю изменения")
            edit_bundle(src, dst, order, pans, key)
            stage("Загружаю на Move")
            MOVE.upload(dst, f"{new_name}.ablbundle")
        finally:
            src.unlink(missing_ok=True)
            dst.unlink(missing_ok=True)
        if replace:
            created = [o for o in MOVE.list_sets() if o["objectId"] not in before]
            if len(created) != 1:
                raise AppError("Новая версия загружена, но я не смог однозначно её найти — оригинал оставлен на месте")
            stage("Заменяю оригинал")
            MOVE.delete(oid)
            MOVE.rename(created[0]["objectId"], obj["name"])
            with LOCK:
                meta = CFG.setdefault("move_meta", {})
                if oid in meta:
                    meta[created[0]["objectId"]] = meta.pop(oid)
                save_config()
            return {"replaced": True}
        return {"copy": new_name}
    return fn


def edit_library(folder, order, pans, key=None):
    d = lib_dir(folder)
    bundle = find_file(d, {".ablbundle"})
    tmp = tmp_path(".ablbundle")
    try:
        edit_bundle(bundle, tmp, order, pans, key)
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
            raise AppError(f"«{filename}» не похож на проект Move (.ablbundle)")
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
        raise AppError("Подходят файлы WAV, MP3, M4A, WebM и OGG")
    d = lib_dir(folder)
    clear_audio(d)
    (d / f"{d.name}.{ext}").write_bytes(data)
    update_meta(d, audioSource="запись со входа" if ext in ("webm", "m4a") else "свой файл", audioError=None)


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
        raise AppError(f"Не удалось скачать запись ({r.status_code})")
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
        stage("Скачиваю запись с Move", 0)
        fetch_recording(name, d, lambda p: stage("Скачиваю запись с Move", p))
        return {"ok": True}
    return fn


def rename_library(folder, new_name):
    d = lib_dir(folder)
    new_name = safe_name(new_name)
    if new_name == d.name:
        return d.name
    target = d.parent / new_name
    if target.exists():
        raise AppError("Проект с таким названием уже есть в папке")
    for f in list(d.iterdir()):
        if f.is_file() and f.stem == d.name and f.suffix.lower() in ({".ablbundle"} | AUDIO_EXTS):
            f.rename(d / f"{new_name}{f.suffix}")
    d.rename(target)
    update_meta(target, bundleStamp=None)
    replace_in_order(target.parent, folder, new_name)
    return new_name


def trash_library(folder):
    d = lib_dir(folder)
    trash = d.parent / "_Удалённые"
    trash.mkdir(exist_ok=True)
    target = trash / f"{d.name} {time.strftime('%Y%m%d-%H%M%S')}"
    d.rename(target)


# ───────────────────────── HTTP ─────────────────────────

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

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            raise AppError("Некорректный запрос")

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
        try:
            self.route()
        except AuthRequired:
            self.send_json({"error": "auth"}, 401)
        except MoveOffline:
            self.send_json({"error": "offline",
                            "message": "Move недоступен. Проверьте, что он включён и в той же Wi-Fi сети."}, 503)
        except AppError as e:
            self.send_json({"error": "app", "message": str(e)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # noqa: BLE001
            self.send_json({"error": "app", "message": f"Внутренняя ошибка: {e}"}, 500)

    do_GET = do_POST = do_PATCH = do_DELETE = do_HEAD = handle_any

    def route(self):
        u = urlparse(self.path)
        path, q, m = unquote(u.path), parse_qs(u.query), self.command
        seg = [s for s in path.split("/") if s]

        if m in ("GET", "HEAD") and path in ("/", "/index.html"):
            return self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if not seg or seg[0] != "api":
            return self.send_json({"error": "not found"}, 404)
        seg = seg[1:]

        # ── настройки
        if seg == ["config"] and m == "GET":
            return self.send_json({"library": str(lib_root()), "moveUrl": CFG["move_url"],
                                   "audioFormat": CFG.get("audio_format", "wav"),
                                   "build": BUILD,
                                   "uiStamp": int((STATIC_DIR / "index.html").stat().st_mtime),
                                   "stale": (APP_DIR / "app.py").stat().st_mtime > STARTED})
        if seg == ["config"] and m == "POST":
            b = self.body()
            if "library" in b:
                p = Path(str(b["library"])).expanduser()
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise AppError(f"Не могу использовать эту папку: {e}")
                CFG["library"] = str(p)
            if b.get("audioFormat") in ("wav", "mp3"):
                CFG["audio_format"] = b["audioFormat"]
            if b.get("moveUrl"):
                CFG["move_url"] = str(b["moveUrl"]).rstrip("/")
            save_config()
            return self.send_json({"ok": True, "library": CFG["library"]})
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
            return self.send_json(job or {"status": "error", "error": "Задача не найдена"})

        # ── Move
        if seg == ["move", "recordings"] and m == "GET":
            return self.send_json({"recordings": recordings_for((q.get("set") or [""])[0])[:400]})
        if len(seg) == 4 and seg[:2] == ["move", "recordings"] and seg[3] == "audio" and m in ("GET", "HEAD"):
            r = MOVE.recording_response(seg[2], self.headers.get("Range"))
            if r.status_code not in (200, 206):
                return self.send_json({"error": "нет записи"}, 404)
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
                raise AppError("Сначала включите управление пэдами")
            moves = [(str(x["id"]), int(x["slot"])) for x in self.body().get("moves", [])]
            cur = {k: v["slot"] for k, v in ssh_slots().items()}
            for oid, slot in moves:
                if oid not in cur:
                    raise AppError("Проект не найден на Move")
                cur[oid] = slot
            used = [v for v in cur.values() if v is not None]
            if len(used) != len(set(used)):
                raise AppError("Два проекта не могут занимать один пэд")
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
            } for o in objs]
            items.sort(key=lambda it: pos.get(it["id"], len(pos)))
            return self.send_json({"sets": items, "ssh": ssh})
        if len(seg) >= 3 and seg[:2] == ["move", "sets"]:
            oid = seg[2]
            if not re.fullmatch(r"[0-9a-fA-F-]{8,64}", oid):
                raise AppError("Некорректный идентификатор")
            act = seg[3] if len(seg) > 3 else None
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
                MOVE.delete(oid)
                return self.send_json({"ok": True})

        # ── библиотека
        if seg == ["library-import"] and m == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            if n > 600 * 1024 * 1024:
                raise AppError("Файл слишком большой")
            final = import_bundle((q.get("name") or ["Проект.ablbundle"])[0], self.rfile.read(n),
                                  (q.get("group") or [None])[0])
            return self.send_json({"ok": True, "id": final})
        if seg == ["library"] and m == "GET":
            return self.send_json({"items": list_library(), "path": str(lib_root())})
        if len(seg) >= 2 and seg[0] == "library":
            folder = seg[1]
            act = seg[2] if len(seg) > 2 else None
            if act == "audio" and m in ("GET", "HEAD"):
                audio = find_file(lib_dir(folder), AUDIO_EXTS)
                if not audio:
                    return self.send_json({"error": "нет аудио"}, 404)
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
                if sys.platform == "darwin":
                    subprocess.Popen(["open", str(lib_dir(folder))])
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


def main():
    CACHE_DIR.mkdir(exist_ok=True)
    for f in CACHE_DIR.glob("tmp-*"):
        f.unlink(missing_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    url = f"http://127.0.0.1:{PORT}"
    print(f"Move Manager (сборка {BUILD}) запущен: {url}\nОстановить — Ctrl+C")
    if not os.environ.get("MOVE_MANAGER_NO_BROWSER"):
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")


if __name__ == "__main__":
    main()
