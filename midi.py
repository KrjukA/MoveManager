"""MIDI-файлы (SMF) ↔ ноты клипа Ableton Move. Только стандартная библиотека.

Время в проекте Move — в долях (четвертях); в файле — в тиках, PPQ тиков на долю.
"""
import struct

PPQ = 480


class MidiError(ValueError):
    pass


# ───────────────────────── запись ─────────────────────────

def _vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def _ticks(beats):
    return max(0, int(round(beats * PPQ)))


def _loop_bounds(clip):
    region = clip.get("region") or {}
    loop = region.get("loop") or {}
    if loop.get("end") is not None and loop.get("start") is not None:
        return float(loop["start"]), float(loop["end"])
    return float(region.get("start", 0.0)), float(region.get("end", 0.0))


def clip_to_midi(clip, tempo, name="", instrument=""):
    """Клип Move → SMF format 0: имя дорожки, инструмент, темп, размер такта, ноты петли (сдвинутые к её началу)."""
    start, end = _loop_bounds(clip)
    length = max(0.0, end - start)
    events = []          # (тик, порядок, байты): note-off раньше note-on на одном тике
    for n in clip.get("notes") or []:
        t = float(n.get("startTime", 0.0))
        if not (start <= t < end):
            continue
        pitch = int(n.get("noteNumber", 60)) & 0x7F
        vel = max(1, min(127, int(round(float(n.get("velocity", 100.0))))))
        on = _ticks(t - start)
        off = min(_ticks(t - start + float(n.get("duration", 0.0))), _ticks(length)) if length else on
        off = max(off, on + 1)
        events.append((on, 1, bytes([0x90, pitch, vel])))
        events.append((off, 0, bytes([0x80, pitch, 0])))
    events.sort(key=lambda e: (e[0], e[1]))

    ts = clip.get("timeSignature") or {}
    upper, lower = int(ts.get("upper", 4)), int(ts.get("lower", 4))
    denom_pow = max(0, lower.bit_length() - 1)
    mpq = int(round(60_000_000 / float(tempo or 120.0)))
    name_b = (name or "").encode("utf-8")[:120]
    inst_b = (instrument or "").encode("utf-8")[:240]

    body = b""
    if name_b:
        body += _vlq(0) + b"\xff\x03" + _vlq(len(name_b)) + name_b
    if inst_b:
        body += _vlq(0) + b"\xff\x04" + _vlq(len(inst_b)) + inst_b
    body += _vlq(0) + b"\xff\x51\x03" + mpq.to_bytes(3, "big")
    body += _vlq(0) + b"\xff\x58\x04" + bytes([upper & 0xFF, denom_pow, 24, 8])
    last = 0
    for tick, _, ev in events:
        body += _vlq(tick - last) + ev
        last = tick
    end_tick = max(_ticks(length), last)
    body += _vlq(end_tick - last) + b"\xff\x2f\x00"
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ)
    return header + b"MTrk" + struct.pack(">I", len(body)) + body


# ───────────────────────── чтение ─────────────────────────

def _read_vlq(data, i):
    n = 0
    for _ in range(4):
        if i >= len(data):
            raise MidiError("MIDI file ends in the middle of an event")
        b = data[i]
        i += 1
        n = (n << 7) | (b & 0x7F)
        if not b & 0x80:
            return n, i
    raise MidiError("Corrupt MIDI file")


def _parse_track(data, division):
    """Возвращает (ноты в тиках [(pitch, start, end, vel)], незакрытые ноты [(pitch, start, vel)], последний тик)."""
    i, tick, status = 0, 0, None
    open_notes = {}          # (канал, нота) → [(старт, vel), ...]
    notes = []
    while i < len(data):
        delta, i = _read_vlq(data, i)
        tick += delta
        if i >= len(data):
            raise MidiError("MIDI file ends in the middle of an event")
        b = data[i]
        if b == 0xFF:                                  # мета-событие
            if i + 1 >= len(data):
                raise MidiError("Corrupt MIDI file")
            mtype = data[i + 1]
            ln, i = _read_vlq(data, i + 2)
            i += ln
            if mtype == 0x2F:
                break
            continue
        if b in (0xF0, 0xF7):                          # SysEx
            ln, i = _read_vlq(data, i + 1)
            i += ln
            continue
        if b & 0x80:
            status = b
            i += 1
        elif status is None:
            raise MidiError("Corrupt MIDI file: data without status")
        kind, ch = status & 0xF0, status & 0x0F
        size = 1 if kind in (0xC0, 0xD0) else 2
        if i + size > len(data):
            raise MidiError("MIDI file ends in the middle of an event")
        params = data[i:i + size]
        i += size
        if kind == 0x90 and params[1] > 0:
            open_notes.setdefault((ch, params[0]), []).append((tick, params[1]))
        elif kind == 0x80 or (kind == 0x90 and params[1] == 0):
            stack = open_notes.get((ch, params[0]))
            if stack:                                  # note-off без пары — пропускаем
                start, vel = stack.pop(0)
                notes.append((params[0], start, tick, vel))
    unclosed = [(pitch, start, vel) for (ch, pitch), stack in open_notes.items() for start, vel in stack]
    return notes, unclosed, tick


def _no_overlaps(raw, division):
    """Move не открывает проект, где одна и та же нота наложена сама на себя.
    Удары одной высоты ближе 1/32 доли друг к другу сливаются в один (громкость — наибольшая),
    а нота, на которую наезжает следующая той же высоты, обрезается до её начала."""
    near = max(1, division // 32)
    merged = []
    for p, st, e, v in sorted(raw, key=lambda n: (n[0], n[1])):
        if merged and merged[-1][0] == p and st - merged[-1][1] < near:
            mp, ms, me, mv = merged[-1]
            merged[-1] = (mp, ms, max(me, e), max(mv, v))
        else:
            merged.append((p, st, e, v))
    for i in range(len(merged) - 1):
        p, st, e, v = merged[i]
        if merged[i + 1][0] == p and merged[i + 1][1] < e:
            merged[i] = (p, st, merged[i + 1][1], v)
    merged.sort(key=lambda n: (n[1], n[0]))
    return merged


def midi_to_notes(data):
    """SMF (type 0 или 1) → (ноты в формате Move, длина в долях). Дорожки сливаются в одну."""
    if len(data) < 14 or data[:4] != b"MThd":
        raise MidiError("Not a MIDI file")
    hlen, fmt, ntracks, division = struct.unpack(">IHHh", data[4:14])
    if fmt not in (0, 1):
        raise MidiError("Only MIDI format 0 and 1 are supported")
    if division <= 0:
        raise MidiError("Unsupported MIDI time format (SMPTE)")
    i = 8 + hlen
    raw, unclosed, last_tick = [], [], 0
    for _ in range(ntracks):
        if i + 8 > len(data):
            break
        cid, clen = data[i:i + 4], struct.unpack(">I", data[i + 4:i + 8])[0]
        chunk = data[i + 8:i + 8 + clen]
        i += 8 + clen
        if cid != b"MTrk":
            continue
        tnotes, topen, tlast = _parse_track(chunk, division)
        raw += tnotes
        unclosed += topen
        last_tick = max(last_tick, tlast)
    raw += [(p, st, last_tick, v) for p, st, v in unclosed]      # незакрытые — до последнего события файла
    if not raw:
        raise MidiError("No notes in the file")
    raw = _no_overlaps(raw, division)
    notes = [{"noteNumber": p, "startTime": s / division, "duration": max(e - s, 1) / division,
              "velocity": float(v), "offVelocity": 0.0} for p, s, e, v in raw]
    return notes, last_tick / division
