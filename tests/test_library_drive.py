"""Сборка 65: папка проектов на внешнем диске (отчёты друзей 24.11).
1) Диск отключён — программа не падает с «Internal error» и не создаёт папку в /Volumes, а говорит, что диск не подключён.
2) Два чтения списка проектов одновременно — оба пишут meta.json; раньше у них был общий meta.json.tmp и второе падало."""
import json
import threading
from pathlib import Path
from unittest import mock

import app
from tests.test_routes_midi import RouteBase


class DriveMissing(RouteBase):
    def setUp(self):
        super().setUp()
        self.vols = self.tmp / "Volumes"
        self.vols.mkdir()
        self._lib = app.CFG["library"]
        app.CFG["library"] = str(self.vols / "Chelsea P" / "Music" / "Move Sessions")
        self.p = mock.patch.object(app, "VOLUMES_DIR", self.vols)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        app.CFG["library"] = self._lib
        super().tearDown()

    def js(self, method, path, obj=None):
        st, _, b = self.req(method, path, json.dumps(obj).encode() if obj is not None else None)
        return st, json.loads(b) if b else None

    def test_config_works_without_the_drive(self):
        st, d = self.js("GET", "/api/config")
        self.assertEqual(st, 200)
        self.assertIn("Chelsea P", d["library"])
        self.assertIn("Chelsea P", d["libraryMissing"])

    def test_library_says_drive_is_not_connected(self):
        st, d = self.js("GET", "/api/library")
        self.assertEqual(st, 200)
        self.assertEqual(d["items"], [])
        self.assertIn("Chelsea P", d["missing"])
        self.assertFalse((self.vols / "Chelsea P").exists(), "папку на месте диска создавать нельзя")

    def test_choosing_a_folder_on_missing_drive_is_refused(self):
        st, d = self.js("POST", "/api/config", {"library": str(self.vols / "Other" / "Sets")})
        self.assertEqual(st, 400)
        self.assertFalse((self.vols / "Other").exists())

    def test_connected_drive_works(self):
        (self.vols / "Chelsea P").mkdir()
        st, d = self.js("GET", "/api/library")
        self.assertEqual(st, 200)
        self.assertNotIn("missing", d)
        self.assertTrue((self.vols / "Chelsea P" / "Music" / "Move Sessions").is_dir())
        st, d = self.js("GET", "/api/config")
        self.assertIsNone(d["libraryMissing"])

    def test_missing_message_is_translated(self):
        from tests.test_i18n import translate
        msg = app.drive_missing_msg("Chelsea P")
        ru = translate([msg])[0]
        self.assertNotEqual(ru, msg)
        self.assertIn("Chelsea P", ru)


class ParallelMetaWrite(RouteBase):
    def test_two_writers_do_not_collide(self):
        target = self.tmp / "meta.json"
        errors = []
        start = threading.Barrier(8)

        def run(i):
            try:
                start.wait()
                for _ in range(30):
                    app.write_json(target, {"i": i})
            except Exception as e:
                errors.append(e)

        ts = [threading.Thread(target=run, args=(i,)) for i in range(8)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(errors, [])
        self.assertIn("i", json.loads(target.read_text()))
        self.assertEqual([p.name for p in self.tmp.glob("meta.json*.tmp")], [])

    def test_list_survives_unwritable_meta(self):
        with mock.patch.object(app, "write_json", side_effect=OSError("read-only")):
            for d in (self.tmp / "lib").iterdir():
                (d / "meta.json").unlink(missing_ok=True)
            st, _, b = self.req("GET", "/api/library")
        self.assertEqual(st, 200)
        self.assertTrue(json.loads(b)["items"])
