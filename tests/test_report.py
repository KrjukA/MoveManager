"""Сборка 55: подробный журнал ошибок и отчёт «Report a problem» — без паролей, ключей и cookies."""
import json
import tempfile
import time
from pathlib import Path

import app
from tests.test_routes_midi import RouteBase


class Report(RouteBase):
    def setUp(self):
        super().setUp()
        self._report = (app.REPORT_DIR, app.CFG.get("cookies"), app.CFG.get("move_url"))
        app.REPORT_DIR = self.tmp / "Desktop"
        app.CFG["cookies"] = {"Ableton-Challenge-Response-Token": "SECRET-TOKEN-123"}

    def tearDown(self):
        app.REPORT_DIR, cookies, url = self._report
        app.CFG["cookies"] = cookies
        app.CFG["move_url"] = url
        super().tearDown()

    def errors(self):
        f = app.CACHE_DIR / "errors.log"
        return f.read_text("utf-8") if f.exists() else ""

    def test_internal_error_is_logged_with_traceback(self):
        def boom(*a, **k):
            raise ZeroDivisionError("kaboom")
        saved = app.list_library
        app.list_library = boom
        try:
            st, _, _ = self.req("GET", "/api/library")
        finally:
            app.list_library = saved
        self.assertEqual(st, 500)
        log = self.errors()
        self.assertIn("GET /api/library", log)
        self.assertIn("ZeroDivisionError: kaboom", log)
        self.assertIn("Traceback", log)

    def test_job_error_is_logged_with_traceback(self):
        def fn(stage):
            raise KeyError("missing-thing")
        job = app.start_job("probe", fn)
        for _ in range(100):
            if app.JOBS[job["id"]]["status"] != "running":
                break
            time.sleep(0.02)
        log = self.errors()
        self.assertIn("probe", log)
        self.assertIn("KeyError", log)
        self.assertIn("Traceback", log)

    def test_report_file(self):
        app.log_error("test-step", ValueError("earlier failure"))
        st, _, b = self.req("POST", "/api/report", json.dumps({"text": "Loops did not appear on pad 3"}).encode())
        self.assertEqual(st, 200, b)
        path = Path(json.loads(b)["path"])
        self.assertEqual(path.parent, app.REPORT_DIR)
        rep = path.read_text("utf-8")
        for want in ("Loops did not appear on pad 3", f"Build: {app.BUILD}", "earlier failure", "System:"):
            self.assertIn(want, rep)
        self.assertNotIn("SECRET-TOKEN-123", rep)
        self.assertNotIn("PRIVATE KEY", rep)
        self.assertNotIn(str(Path.home()), rep)            # домашняя папка — как «~»

    def test_report_without_errors_and_empty_text(self):
        st, _, b = self.req("POST", "/api/report", json.dumps({"text": ""}).encode())
        self.assertEqual(st, 200, b)
        self.assertIn("(no description)", Path(json.loads(b)["path"]).read_text("utf-8"))
