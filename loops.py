"""Лупы для аудиоячеек Move: длительность файла, темп из имени, темп и длина клипа так, как это делает сам Move.

Наблюдения на проектах the author (17.11): если темпа в имени нет, Move ставит темп лупа так, чтобы файл
ровно лёг в целые такты (35,04 с → 109,589 = 64 доли); если темп в имени есть — берёт его и
округляет длину клипа вверх до такта (31,24 доли → 32).
"""
import copy
import math
import re
import struct

import samplelib

TEMPO_RE = re.compile(r"(?<![\d.])(\d{2,3}(?:\.\d+)?)\s*[-_]?\s*bpm|bpm\s*[-_]?\s*(\d{2,3}(?:\.\d+)?)(?![\d.])", re.I)
BAR_COUNTS = (1, 2, 4, 8, 16, 32)


def _ext80(b):
    """80-битное число с плавающей точкой (частота дискретизации в AIFF)."""
    se, mant = struct.unpack(">HQ", b)
    if not mant:
        return 0.0
    exp = (se & 0x7FFF) - 16383
    return mant * 2.0 ** (exp - 63)


def audio_seconds(data):
    """Длительность WAV или AIFF в секундах по заголовку; иначе ValueError."""
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        p, sr, align, size = 12, None, None, None
        while p + 8 <= len(data):
            cid, n = data[p:p + 4], struct.unpack("<I", data[p + 4:p + 8])[0]
            if cid == b"fmt " and n >= 16:
                _fmt, _ch, sr, _rate, align, _bits = struct.unpack("<HHIIHH", data[p + 8:p + 24])
            elif cid == b"data":
                size = min(n, len(data) - p - 8)
                break
            p += 8 + n + (n & 1)
        if sr and align and size is not None:
            return size / align / sr
    elif len(data) >= 12 and data[:4] == b"FORM" and data[8:12] in (b"AIFF", b"AIFC"):
        p = 12
        while p + 8 <= len(data):
            cid, n = data[p:p + 4], struct.unpack(">I", data[p + 4:p + 8])[0]
            if cid == b"COMM" and n >= 18:
                _ch, frames, _bits = struct.unpack(">hIh", data[p + 8:p + 16])
                sr = _ext80(data[p + 16:p + 26])
                if sr > 0:
                    return frames / sr
            p += 8 + n + (n & 1)
    raise ValueError("Not a WAV or AIFF file")


def name_tempo(filename):
    """Темп из имени файла: «160bpm», «84 bpm», «120BPM», «bpm 90»; вне 40–300 — None."""
    for m in TEMPO_RE.finditer(filename or ""):
        v = float(m.group(1) or m.group(2))
        if 40 <= v <= 300:
            return int(v) if v.is_integer() else v
    return None


def fit(seconds, project_tempo, bar_beats, name_bpm):
    """(темп лупа, длина клипа в долях).
    Темп в имени — он; длина до целого такта: лишнее меньше 1/16 такта — вниз, иначе вверх.
    Темпа нет — число тактов из 1, 2, 4… при котором темп ближе всего к темпу проекта."""
    bar = bar_beats
    if name_bpm:
        raw = seconds * name_bpm / 60
        bars = math.floor(raw / bar + 1e-9)
        if raw - bars * bar >= bar / 16:
            bars += 1
        return name_bpm, max(1, bars) * bar
    best = None
    for n in BAR_COUNTS:
        tempo = n * bar * 60 / seconds
        score = abs(math.log(tempo / project_tempo))
        if best is None or score < best[0]:
            best = (score, tempo, n * bar)
    return best[1], best[2]


def natural_key(name):
    """«2 a» раньше «10 a», регистр не важен."""
    return [(0, int(x), "") if x.isdigit() else (1, 0, x.lower()) for x in re.split(r"(\d+)", name) if x]


def audio_clip(template, sample_rel, tempo, beats, ts, color):
    """Аудиоклип: общие поля — из образца того же проекта (если есть), остальное — как у клипов Move."""
    keep = ("color", "isEnabled", "stepEditorScrollPosition")
    base = {k: copy.deepcopy(v) for k, v in (template or {}).items() if k in keep}
    clip = {"isPlaying": False, "name": "", "color": color, "isEnabled": True, "stepEditorScrollPosition": 0.0}
    clip.update(base)
    clip.update({
        "isPlaying": False,
        "name": "",
        "timeSignature": dict(ts or {"upper": 4, "lower": 4}),
        "region": {"start": 0.0, "end": float(beats), "loop": {"start": 0.0, "end": float(beats), "isEnabled": True}},
        "sampleUri": samplelib.rel_to_uri(sample_rel),
        "warping": {"markers": [], "tempoAfterLastMarker": float(tempo)},
        "gain": 0.0,
        "transpose": 0,
        "detune": 0.0,
        "envelopes": [],
    })
    return clip
