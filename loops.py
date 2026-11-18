"""Лупы для аудиоячеек Move: длительность файла, темп из имени, темп и длина клипа так, как это делает сам Move.

Наблюдения на реальных проектах (17.11): если темпа в имени нет, Move ставит темп лупа так, чтобы файл
ровно лёг в целые такты (35,04 с → 109,589 = 64 доли); если темп в имени есть — берёт его и
округляет длину клипа вверх до такта (31,24 доли → 32).
"""
import copy
import math
import re
import struct

import samplelib

TEMPO_RE = re.compile(r"(?<![\d.])(\d{2,3}(?:\.\d+)?)\s*[-_]?\s*bpm|bpm\s*[-_]?\s*(\d{2,3}(?:\.\d+)?)(?!\d)(?!\.\d)", re.I)
BAR_COUNTS = (1, 2, 4, 8, 16, 32)


def _ext80(b):
    """80-битное число с плавающей точкой (частота дискретизации в AIFF)."""
    se, mant = struct.unpack(">HQ", b)
    if not mant:
        return 0.0
    exp = (se & 0x7FFF) - 16383
    return mant * 2.0 ** (exp - 63)


def audio_seconds(data):
    """Длительность WAV или AIFF в секундах по заголовку; иначе ValueError (и для обрезанных/странных файлов)."""
    try:
        return _audio_seconds(data)
    except (struct.error, OverflowError, ZeroDivisionError):
        raise ValueError("Not a supported audio file")


def _skip_id3(data):
    """Без тега ID3v2 в начале (бывает у MP3 и FLAC)."""
    if data[:3] == b"ID3" and len(data) >= 10:
        size = (data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F)
        return data[10 + size + (10 if data[5] & 0x10 else 0):]
    return data


def _flac_seconds(d):
    """FLAC: STREAMINFO — первый блок метаданных: частота (20 бит) и число сэмплов (36 бит)."""
    if len(d) < 42 or d[4] & 0x7F != 0:                # блок 0 сразу после «fLaC» (заголовок 4 байта)
        raise ValueError("FLAC without STREAMINFO")
    info = d[8:8 + 34]
    bits = int.from_bytes(info[10:18], "big")
    rate = bits >> 44
    total = bits & ((1 << 36) - 1)
    if not rate or not total:
        raise ValueError("FLAC without length")
    return total / rate


MP3_RATES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}   # MPEG1, MPEG2, MPEG2.5
MP3_KBPS = {1: (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
            2: (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)}


def _mp3_seconds(d, offset):
    """MP3 (Layer III): число кадров из заголовка Xing/Info/VBRI (с поправкой LAME на тишину по краям),
    иначе — по битрейту первого кадра и размеру файла. Не MP3 — None."""
    i = 0
    limit = min(len(d) - 4, 64 * 1024)
    while i < limit:                                   # первый кадр: 11 бит синхронизации и Layer III
        if d[i] == 0xFF and d[i + 1] & 0xE0 == 0xE0 and (d[i + 1] >> 1) & 3 == 1:
            ver, br, sr_i = (d[i + 1] >> 3) & 3, d[i + 2] >> 4, (d[i + 2] >> 2) & 3
            if ver != 1 and 0 < br < 15 and sr_i < 3:
                break
        i += 1
    else:
        return None
    ver, br, sr_i, mode = (d[i + 1] >> 3) & 3, d[i + 2] >> 4, (d[i + 2] >> 2) & 3, d[i + 3] >> 6
    sr = MP3_RATES[ver][sr_i]
    spf = 1152 if ver == 3 else 576
    kbps = MP3_KBPS[1 if ver == 3 else 2][br]
    frame_len = (144 if ver == 3 else 72) * kbps * 1000 // sr + ((d[i + 2] >> 1) & 1)
    if len(d) < i + frame_len:                         # обрезан до первого кадра
        return None
    side = (17 if mode == 3 else 32) if ver == 3 else (9 if mode == 3 else 17)
    x = i + 4 + side
    if d[x:x + 4] in (b"Xing", b"Info"):
        flags = int.from_bytes(d[x + 4:x + 8], "big")
        if flags & 1:
            frames = int.from_bytes(d[x + 8:x + 12], "big")
            pos = x + 8 + 4 + (4 if flags & 2 else 0) + (100 if flags & 4 else 0) + (4 if flags & 8 else 0)
            delay = pad = 0
            if d[pos:pos + 4] == b"LAME" or d[pos:pos + 4] == b"Lavf":
                dp = int.from_bytes(d[pos + 21:pos + 24], "big")
                delay, pad = dp >> 12, dp & 0xFFF
            return max(0, frames * spf - delay - pad) / sr
    v = i + 4 + 32
    if d[v:v + 4] == b"VBRI":
        frames = int.from_bytes(d[v + 14:v + 18], "big")
        return frames * spf / sr
    end = len(d) - (128 if d[-128:-125] == b"TAG" else 0)
    return (end - i) * 8 / (kbps * 1000)


def _audio_seconds(data):
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
                if sr > 0 and math.isfinite(sr):
                    return frames / sr
            p += 8 + n + (n & 1)
    body = _skip_id3(data)
    if body[:4] == b"fLaC":
        return _flac_seconds(body)
    sec = _mp3_seconds(body, len(data) - len(body))
    if sec is not None:
        return sec
    raise ValueError("Not a supported audio file")


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
