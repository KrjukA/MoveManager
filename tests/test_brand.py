"""Название «KRJUK Move Manager», логотип и значок."""
import unittest
from pathlib import Path

import app
from tests.test_routes_midi import RouteBase


class Brand(unittest.TestCase):
    def test_name(self):
        self.assertEqual(app.APP_NAME, "KRJUK Move Manager")

    def test_data_folders_use_the_name(self):
        self.assertEqual(Path(app.user_data_dir(True, "win32", {"APPDATA": "C:/R"}, Path("C:/U"))).name, app.APP_NAME)
        self.assertEqual(app.user_data_dir(True, "darwin", {}, Path("/Users/a")), Path("/Users/a/Library/Application Support") / app.APP_NAME)

    def test_logo_files_exist(self):
        for f in ("logo.png", "icon.png", "favicon.png"):
            self.assertTrue((app.STATIC_DIR / f).stat().st_size > 1000, f)


class StaticFiles(RouteBase):
    def test_images_served(self):
        st, hdr, body = self.req("GET", "/static/logo.png")
        self.assertEqual(st, 200)
        self.assertTrue(body.startswith(b"\x89PNG"))

    def test_no_path_escape(self):
        for p in ("/static/../app.py", "/static/%2e%2e/app.py", "/static/index.html/../../app.py", "/static/config.json"):
            st, _, body = self.req("GET", p)
            self.assertNotEqual(st, 200, p)
            self.assertNotIn(b"import ", body)


if __name__ == "__main__":
    unittest.main()
