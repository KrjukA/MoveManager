"""Сборка 52: модуль истории версий проекта."""
import json
import tempfile
import time
import unittest
from pathlib import Path

import history


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp()) / "h"

    def test_save_and_list(self):
        t = time.mktime((2026, 11, 16, 22, 56, 19, 0, 0, -1)) + 0.123
        a = history.save_version(self.dir, b'{"v":1}', "Tracks reordered", now=t)
        b = history.save_version(self.dir, b'{"v":2}', "Pan changed", now=t + 5)
        self.assertEqual(a, "20261116-225619-123")
        vs = history.list_versions(self.dir)
        self.assertEqual([v["id"] for v in vs], [b, a])                 # новые сверху
        self.assertEqual(vs[1]["action"], "Tracks reordered")
        self.assertEqual(vs[1]["savedAt"], "2026-11-16T22:56:19")
        self.assertIs(vs[0]["legacy"], False)
        self.assertEqual(history.read_version(self.dir, a), b'{"v":1}')

    def test_same_moment_not_overwritten(self):
        t = time.time()
        a = history.save_version(self.dir, b"1", "x", now=t)
        b = history.save_version(self.dir, b"2", "y", now=t)
        c = history.save_version(self.dir, b"3", "z", now=t)
        self.assertEqual(len({a, b, c}), 3)
        self.assertEqual(history.read_version(self.dir, a), b"1")
        self.assertEqual(history.read_version(self.dir, c), b"3")
        self.assertEqual([v["id"] for v in history.list_versions(self.dir)][0], c)

    def test_prune_keeps_newest_20(self):
        t = time.time()
        ids = [history.save_version(self.dir, str(i).encode(), f"a{i}", now=t + i) for i in range(25)]
        vs = history.list_versions(self.dir)
        self.assertEqual(len(vs), 20)
        self.assertEqual(vs[0]["id"], ids[-1])
        self.assertNotIn(ids[0], [v["id"] for v in vs])
        self.assertEqual(len(list(self.dir.glob("*.json"))), 20)

    def test_prune_never_drops_new_version_after_clock_goes_back(self):
        t = time.time()
        for i in range(20):
            history.save_version(self.dir, str(i).encode(), "a", now=t + 3600 + i)
        vid = history.save_version(self.dir, b"new", "after DST", now=t)      # часы перевели назад
        self.assertEqual(history.read_version(self.dir, vid), b"new")
        self.assertEqual(len(history.list_versions(self.dir)), 20)

    def test_read_version_rejects_bad_id(self):
        history.save_version(self.dir, b"1", "x")
        for bad in ("../x", "abc", "20261116-225619-999", "", "20261116-225619-123/../../a"):
            with self.assertRaises(ValueError, msg=bad):
                history.read_version(self.dir, bad)

    def test_missing_json_action_empty(self):
        vid = history.save_version(self.dir, b"1", "x")
        (self.dir / f"{vid}.json").unlink()
        self.assertEqual(history.list_versions(self.dir)[0]["action"], "")

    def test_list_empty_folder(self):
        self.assertEqual(history.list_versions(self.dir), [])

    def test_move_history_merge(self):
        t = time.time()
        a = history.save_version(self.dir, b"old", "a", now=t)
        dst = self.dir.parent / "new"
        b = history.save_version(dst, b"new", "b", now=t + 1)
        history.move_history(self.dir, dst)
        self.assertFalse(self.dir.exists())
        self.assertEqual({v["id"] for v in history.list_versions(dst)}, {a, b})
        history.move_history(self.dir, dst)                               # исходной папки нет — ничего
        other = self.dir.parent / "other"
        history.move_history(dst, other)                                  # цели нет — просто перенос
        self.assertEqual(len(history.list_versions(other)), 2)

    def test_meta_is_json(self):
        vid = history.save_version(self.dir, b"1", "Clip moved T1 S1 → T2 S3")
        meta = json.loads((self.dir / f"{vid}.json").read_text("utf-8"))
        self.assertEqual(meta["action"], "Clip moved T1 S1 → T2 S3")

    def test_fmt_when(self):
        self.assertEqual(history.fmt_when("2026-11-16T22:56:19"), "16 Nov 22:56:19")
        self.assertEqual(history.fmt_when("bad"), "bad")


if __name__ == "__main__":
    unittest.main()
