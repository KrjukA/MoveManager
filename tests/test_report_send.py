"""Сборка 60: отчёт уходит в Google Форму разработчика; без сети — файл на Рабочий стол, как раньше.
Автоотправка ошибок — только если человек разрешил; не чаще раза в 10 минут, одинаковые не повторяются.
Язык отчёта — язык интерфейса."""
import json
from unittest import mock

import requests

import app
from tests.test_routes_midi import RouteBase

F = app.REPORT_FIELDS


class Ok:
    status_code = 200
    def raise_for_status(self):
        pass


class ReportSend(RouteBase):
    def setUp(self):
        super().setUp()
        self._rs = (app.REPORT_DIR, app.CFG.get("cookies"), app.CFG.get("auto_report", "unset"))
        app.REPORT_DIR = self.tmp / "Desktop"
        app.CFG["cookies"] = {"Ableton-Challenge-Response-Token": "SECRET-TOKEN-123"}
        app.CFG.pop("auto_report", None)
        app.AUTO_REPORT.update(last=0.0, seen=set())
        self.posts = []
        p = mock.patch.object(app.requests, "post", side_effect=lambda url, data=None, timeout=None: (self.posts.append((url, data)), Ok())[1])
        p.start(); self.addCleanup(p.stop)

    def tearDown(self):
        app.REPORT_DIR, cookies, auto = self._rs
        app.CFG["cookies"] = cookies
        if auto == "unset":
            app.CFG.pop("auto_report", None)
        else:
            app.CFG["auto_report"] = auto
        super().tearDown()

    def js(self, method, path, obj=None):
        st, _, b = self.req(method, path, json.dumps(obj).encode() if obj is not None else None)
        return st, json.loads(b) if b else None

    def test_report_goes_to_the_form(self):
        st, d = self.js("POST", "/api/report", {"text": "Loops failed", "send": True, "lang": "en"})
        self.assertEqual(st, 200)
        self.assertTrue(d["sent"])
        url, data = self.posts[0]
        self.assertEqual(url, app.REPORT_FORM_URL)
        self.assertEqual(data[F["what"]], "Loops failed")
        self.assertIn(app.VERSION, data[F["version"]])
        self.assertIn(app.BUILD, data[F["version"]])
        self.assertTrue(data[F["system"]])
        self.assertIn("What happened:", data[F["report"]])
        self.assertNotIn("SECRET-TOKEN-123", json.dumps(data))
        self.assertFalse((self.tmp / "Desktop").exists())          # отправили — файл не нужен

    def test_russian_interface_gives_russian_report(self):
        self.js("POST", "/api/report", {"text": "Не грузятся лупы", "send": True, "lang": "ru"})
        rep = self.posts[0][1][F["report"]]
        self.assertIn("Что случилось:", rep)
        self.assertNotIn("What happened:", rep)

    def test_no_internet_saves_file(self):
        with mock.patch.object(app.requests, "post", side_effect=requests.ConnectionError("offline")):
            st, d = self.js("POST", "/api/report", {"text": "x", "send": True, "lang": "en"})
        self.assertEqual(st, 200)
        self.assertFalse(d["sent"])
        self.assertTrue(list((self.tmp / "Desktop").glob("*.txt")))

    def test_auto_off_until_allowed(self):
        self.assertIsNone(app.auto_report_error("GET /api/x", ZeroDivisionError("boom")))
        app.CFG["auto_report"] = False
        self.assertIsNone(app.auto_report_error("GET /api/x", ZeroDivisionError("boom")))
        self.assertEqual(self.posts, [])

    def test_auto_sends_once_per_error_and_rate_limited(self):
        app.CFG["auto_report"] = True
        app.auto_report_error("GET /api/x", ZeroDivisionError("boom")).join(5)
        self.assertEqual(len(self.posts), 1)
        self.assertIn("ZeroDivisionError", self.posts[0][1][F["what"]])
        self.assertIsNone(app.auto_report_error("GET /api/x", ZeroDivisionError("boom")))      # то же — нет
        self.assertIsNone(app.auto_report_error("GET /api/y", KeyError("other")))              # 10 минут — нет
        app.AUTO_REPORT["last"] -= 601
        app.auto_report_error("GET /api/y", KeyError("other")).join(5)
        self.assertEqual(len(self.posts), 2)

    def test_expected_errors_not_auto_sent(self):
        app.CFG["auto_report"] = True
        self.assertIsNone(app.auto_report_error("job", app.AppError("Name already taken")))
        self.assertEqual(self.posts, [])

    def test_config_reports_and_sets_auto(self):
        self.assertIsNone(self.js("GET", "/api/config")[1]["autoReport"])
        self.js("POST", "/api/config", {"autoReport": True})
        self.assertIs(self.js("GET", "/api/config")[1]["autoReport"], True)
        self.js("POST", "/api/config", {"autoReport": False})
        self.assertIs(self.js("GET", "/api/config")[1]["autoReport"], False)

    def test_internal_error_flagged_for_consent(self):
        saved = app.list_library
        app.list_library = lambda: 1 / 0
        try:
            st, d = self.js("GET", "/api/library")
        finally:
            app.list_library = saved
        self.assertEqual(st, 500)
        self.assertTrue(d["internal"])
