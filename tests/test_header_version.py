"""Сборка 64: в шапке собранной программы — версия (v1.7), из исходников — номер сборки."""
import json
import re
from pathlib import Path
from unittest import mock

import app
from tests.test_routes_midi import RouteBase

HTML = (Path(__file__).resolve().parent.parent / "static" / "index.html").read_text(encoding="utf-8")


class HeaderVersion(RouteBase):
    def config(self):
        code, _, body = self.req("GET", "/api/config")
        self.assertEqual(code, 200)
        return json.loads(body)

    def test_config_gives_version_and_frozen(self):
        with mock.patch.object(app, "FROZEN", True):
            c = self.config()
        self.assertEqual((c["version"], c["build"], c["frozen"]), (app.VERSION, app.BUILD, True))
        with mock.patch.object(app, "FROZEN", False):
            self.assertFalse(self.config()["frozen"])

    def test_header_uses_version_when_frozen(self):
        self.assertRegex(HTML, r'c\.frozen \? "v"\+c\.version')


del RouteBase
