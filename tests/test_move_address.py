"""Сборка 55: адрес Move вручную (если move.local не находится в сети)."""
import json
import unittest

import app
from tests.test_routes_midi import RouteBase


class Normalize(unittest.TestCase):
    def test_forms(self):
        for given, want in [("192.168.1.23", "http://192.168.1.23"), (" move.local ", "http://move.local"),
                            ("http://192.168.0.5/", "http://192.168.0.5"), ("https://move.local", "http://move.local"),
                            ("http://192.168.0.5/data/Sets", "http://192.168.0.5"), ("", "http://move.local")]:
            self.assertEqual(app.normalize_move_url(given), want, given)

    def test_bad(self):
        for bad in ("192.168.1.23; rm -rf /", "a b", "http://user@evil/", "$(x)", "-oProxyCommand=x", "fe80::1",
                    "192.168.1.5:abc"):
            with self.assertRaises(app.AppError, msg=bad):
                app.normalize_move_url(bad)


class Route(RouteBase):
    def setUp(self):
        super().setUp()
        self._url = app.CFG.get("move_url")

    def tearDown(self):
        app.CFG["move_url"] = self._url
        super().tearDown()

    def test_config_sets_address(self):
        st, _, _ = self.req("POST", "/api/config", json.dumps({"moveUrl": "192.168.1.23"}).encode())
        self.assertEqual(st, 200)
        self.assertEqual(app.CFG["move_url"], "http://192.168.1.23")
        st, _, b = self.req("POST", "/api/config", json.dumps({"moveUrl": "bad host;"}).encode())
        self.assertEqual(st, 400)
        self.assertEqual(app.CFG["move_url"], "http://192.168.1.23")
