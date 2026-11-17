"""Сборка 53: лупы — длительность файла, темп из имени, темп и длина «как Move», сборка аудиоклипа."""
import io
import math
import struct
import unittest
import wave

import loops
import samplelib


def wav_bytes(seconds, sr=44100, ch=2, extra=b""):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"\0\0" * ch * int(sr * seconds))
    data = buf.getvalue()
    if extra:                                   # служебный блок перед fmt/data
        body = data[12:]
        data = b"RIFF" + struct.pack("<I", 4 + len(extra) + len(body)) + b"WAVE" + extra + body
    return data


def chunk(cid, payload):
    return cid + struct.pack("<I", len(payload)) + payload + (b"\0" if len(payload) & 1 else b"")


def float_wav(seconds, sr=48000, ch=2):
    fmt = struct.pack("<HHIIHH", 3, ch, sr, sr * ch * 4, ch * 4, 32)
    data = b"\0" * (int(sr * seconds) * ch * 4)
    body = b"WAVE" + chunk(b"fmt ", fmt) + chunk(b"data", data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def ext80(x):
    """Частота дискретизации AIFF: 80-битное число с плавающей точкой."""
    e = int(math.floor(math.log2(x)))
    mant = int(x / 2 ** e * (1 << 63))
    return struct.pack(">HQ", e + 16383, mant)


def aiff_bytes(frames, sr=48000, ch=2):
    comm = struct.pack(">hIh", ch, frames, 16) + ext80(sr)
    ssnd = struct.pack(">II", 0, 0) + b"\0" * (frames * ch * 2)
    def c(cid, p):
        return cid + struct.pack(">I", len(p)) + p + (b"\0" if len(p) & 1 else b"")
    body = b"AIFF" + c(b"COMM", comm) + c(b"SSND", ssnd)
    return b"FORM" + struct.pack(">I", len(body)) + body


class Seconds(unittest.TestCase):
    def test_wav_seconds(self):
        self.assertAlmostEqual(loops.audio_seconds(wav_bytes(2.0)), 2.0, places=4)

    def test_wav_with_extra_chunks(self):
        self.assertAlmostEqual(loops.audio_seconds(wav_bytes(1.5, extra=chunk(b"JUNK", b"x" * 29))), 1.5, places=4)

    def test_float_wav(self):
        self.assertAlmostEqual(loops.audio_seconds(float_wav(0.5)), 0.5, places=4)

    def test_aiff_seconds(self):
        self.assertAlmostEqual(loops.audio_seconds(aiff_bytes(96000, sr=48000)), 2.0, places=4)
        self.assertAlmostEqual(loops.audio_seconds(aiff_bytes(44100, sr=44100)), 1.0, places=4)

    def test_truncated_or_crafted_is_value_error(self):
        good = wav_bytes(1.0)
        for bad in (good[:30], good[:40], aiff_bytes(100)[:30]):
            with self.assertRaises(ValueError):
                loops.audio_seconds(bad)
        a = bytearray(aiff_bytes(100))
        i = a.index(b"COMM") + 8 + 8
        a[i:i + 2] = b"\x7f\xff"                                   # экспонента частоты вне диапазона
        with self.assertRaises(ValueError):
            loops.audio_seconds(bytes(a))

    def test_not_audio(self):
        for bad in (b"", b"hello world", b"RIFF\0\0\0\0WAVE", b"ID3\x03" + b"\0" * 40):
            with self.assertRaises(ValueError):
                loops.audio_seconds(bad)


class Tempo(unittest.TestCase):
    def test_name_tempo(self):
        cases = {"Jungle1 160bpm.wav": 160, "Break 84 bpm.wav": 84, "Pad 120BPM.aif": 120, "bpm 90 loop.wav": 90,
                 "Set 93 Rec 2 - 100 bpm.wav": 100, "Vocal_92.5bpm.wav": 92.5,
                 "Loop bpm140.wav": 140, "Loop 140bpm.wav": 140, "Kick 909.wav": None, "Fast 500bpm.wav": None, "Vocal Zamelo.wav": None}
        for name, want in cases.items():
            self.assertEqual(loops.name_tempo(name), want, name)

    def test_fit_named(self):
        self.assertEqual(loops.fit(18.745, 120, 4, 100), (100, 32))      # как у Move: 31,24 доли → 32

    def test_fit_named_tail(self):
        sec = lambda beats, bpm: beats * 60 / bpm
        self.assertEqual(loops.fit(sec(16.02, 160), 120, 4, 160), (160, 16))   # хвост < 1/16 такта — вниз
        self.assertEqual(loops.fit(sec(16.5, 160), 120, 4, 160), (160, 20))    # больше — вверх до такта

    def test_fit_unnamed(self):
        t, b = loops.fit(35.04, 120, 4, None)
        self.assertEqual(b, 64)
        self.assertAlmostEqual(t, 109.589, places=2)
        t, b = loops.fit(8.697, 110, 4, None)
        self.assertEqual(b, 16)
        self.assertAlmostEqual(t, 110.386, places=2)
        t, b = loops.fit(4.0, 120, 4, None)                              # 2 такта при 120
        self.assertEqual((round(t, 6), b), (120.0, 8))

    def test_fit_min_one_bar(self):
        self.assertEqual(loops.fit(0.1, 120, 4, 120)[1], 4)
        self.assertEqual(loops.fit(0.05, 120, 4, None)[1], 4)

    def test_fit_three_four(self):
        self.assertEqual(loops.fit(3.0, 120, 3, 120), (120, 6))          # 6 долей = 2 такта по 3/4

    def test_natural_key(self):
        names = ["10 c.wav", "2 b.wav", "1 a.wav", "B.wav", "a.wav"]
        self.assertEqual(sorted(names, key=loops.natural_key), ["1 a.wav", "2 b.wav", "10 c.wav", "a.wav", "B.wav"])


class Clip(unittest.TestCase):
    def test_audio_clip_fields(self):
        tmpl = {"isPlaying": True, "name": "x", "color": 9, "isEnabled": True, "timeSignature": {"upper": 4, "lower": 4},
                "stepEditorScrollPosition": 3.0, "sampleUri": "old", "warping": {"markers": [{"beats": 0}]},
                "gain": -3.0, "transpose": 5, "detune": 1.0, "envelopes": [1], "region": {}}
        rel = "Samples/UPLOAD/Break 84 bpm.wav"
        c = loops.audio_clip(tmpl, rel, 84.0, 16.0, {"upper": 4, "lower": 4}, 5)
        self.assertEqual(c["sampleUri"], samplelib.rel_to_uri(rel))
        self.assertEqual(c["warping"], {"markers": [], "tempoAfterLastMarker": 84.0})
        self.assertEqual(c["region"], {"start": 0.0, "end": 16.0, "loop": {"start": 0.0, "end": 16.0, "isEnabled": True}})
        self.assertEqual((c["gain"], c["transpose"], c["detune"], c["envelopes"]), (0.0, 0, 0.0, []))
        self.assertIs(c["isPlaying"], False)
        self.assertEqual((c["name"], c["color"], c["stepEditorScrollPosition"]), ("", 9, 3.0))
        self.assertIsNot(c["timeSignature"], tmpl["timeSignature"])

    def test_audio_clip_without_template(self):
        c = loops.audio_clip(None, "Samples/UPLOAD/a.wav", 120.0, 8.0, {"upper": 4, "lower": 4}, 7)
        self.assertEqual(c["color"], 7)
        for k in ("isEnabled", "timeSignature", "stepEditorScrollPosition", "name"):
            self.assertIn(k, c)


if __name__ == "__main__":
    unittest.main()
