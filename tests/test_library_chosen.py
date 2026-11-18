"""Папка проектов на компьютере (сборка 60): при первом переносе с Move программа спрашивает, где её держать.
«Выбрана» — человек сам выбрал или подтвердил папку, или в ней уже есть проекты (так у тех, кто пользуется давно)."""
import json
import shutil
from unittest import mock

import app
from tests.test_routes_midi import RouteBase


class LibraryChosen(RouteBase):
    def setUp(self):
        super().setUp()
        self._chosen = app.CFG.pop("library_chosen", None)

    def tearDown(self):
        app.CFG.pop("library_chosen", None)
        if self._chosen is not None:
            app.CFG["library_chosen"] = self._chosen
        super().tearDown()

    def js(self, method, path, obj=None):
        st, _, b = self.req(method, path, json.dumps(obj).encode() if obj is not None else None)
        return st, json.loads(b) if b else None

    def empty_library(self):
        for p in (self.tmp / "lib").iterdir():
            shutil.rmtree(p) if p.is_dir() else p.unlink()

    def test_existing_projects_count_as_chosen(self):
        st, d = self.js("GET", "/api/library")
        self.assertTrue(d["items"])
        self.assertTrue(d["chosen"])

    def test_empty_default_folder_is_not_chosen(self):
        self.empty_library()
        st, d = self.js("GET", "/api/library")
        self.assertFalse(d["chosen"])

    def test_confirming_the_folder_marks_it_chosen(self):
        self.empty_library()
        st, _ = self.js("POST", "/api/config", {"library": str(self.tmp / "lib")})
        self.assertEqual(st, 200)
        self.assertTrue(self.js("GET", "/api/library")[1]["chosen"])

    def test_folder_dialog_marks_it_chosen(self):
        self.empty_library()
        other = self.tmp / "Picked"
        with mock.patch.object(app, "choose_folder_dialog", return_value=str(other)):
            st, d = self.js("POST", "/api/choose-folder")
        self.assertTrue(d["chosen"])
        self.assertTrue(self.js("GET", "/api/library")[1]["chosen"])

    def test_cancelled_dialog_changes_nothing(self):
        self.empty_library()
        with mock.patch.object(app, "choose_folder_dialog", return_value=None):
            st, d = self.js("POST", "/api/choose-folder")
        self.assertFalse(d["chosen"])
        self.assertFalse(self.js("GET", "/api/library")[1]["chosen"])
