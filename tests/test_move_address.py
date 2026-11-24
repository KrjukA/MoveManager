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


class NameFallback(unittest.TestCase):
    """Сборка 62: имя move.local иногда не находится, хотя Move в сети. Программа помнит его IP и сама переходит на него."""
    def setUp(self):
        from unittest import mock
        self.mock = mock
        self._cfg = {k: app.CFG.get(k) for k in ("move_url", "move_ip")}
        self._alt = app.MOVE_ALT["url"]
        app.CFG["move_url"], app.CFG["move_ip"], app.MOVE_ALT["url"] = "http://move.local", "192.168.31.8", None
        self.env = mock.patch.dict(app.os.environ, {"MOVE_MANAGER_TESTING": ""})
        self.env.start()
        self.save = mock.patch.object(app, "save_config"); self.save.start()
        self.reset = mock.patch.object(app, "ssh_session_reset"); self.reset_m = self.reset.start()
        self.m = app.Move()
        app.Move._ip_checked = False
        self.hosts = []

    def tearDown(self):
        self.env.stop(); self.save.stop(); self.reset.stop()
        for k, v in self._cfg.items():
            app.CFG[k] = v
        app.MOVE_ALT["url"] = self._alt

    def net(self, up):
        ok = self.mock.Mock(status_code=200)
        def request(method, url, **kw):
            host = app.urlparse(url).hostname
            self.hosts.append(host)
            if host not in up:
                raise app.requests.exceptions.ConnectionError("Failed to resolve " + host)
            return ok
        return self.mock.patch.object(self.m.s, "request", side_effect=request)

    def test_name_lost_uses_last_ip(self):
        with self.net({"192.168.31.8"}):
            self.assertEqual(self.m.req("GET", "/api/v1/data/Sets").status_code, 200)
            self.m.req("GET", "/api/v1/data/Sets")
        self.assertEqual(self.hosts, ["move.local", "192.168.31.8", "192.168.31.8"])   # дальше сразу по IP
        self.assertEqual(app.move_host(), "192.168.31.8")                               # и SSH туда же
        self.assertEqual(app.CFG["move_url"], "http://move.local")                      # настройку не трогаем
        self.reset_m.assert_called()

    def test_back_to_name_when_ip_changes(self):
        app.MOVE_ALT["url"] = "http://192.168.31.8"
        with self.net({"move.local"}), self.mock.patch.object(app.socket, "gethostbyname", return_value="192.168.31.20"):
            self.m.req("GET", "/api/v1/data/Sets")
        self.assertIsNone(app.MOVE_ALT["url"])
        self.assertEqual(app.CFG["move_ip"], "192.168.31.20")

    def test_remembers_ip_when_name_works(self):
        app.CFG["move_ip"] = None
        with self.net({"move.local"}), self.mock.patch.object(app.socket, "gethostbyname", return_value="192.168.31.8"):
            self.m.req("GET", "/api/v1/data/Sets")
        self.assertEqual(app.CFG["move_ip"], "192.168.31.8")

    def test_no_ip_known_stays_offline(self):
        app.CFG["move_ip"] = None
        with self.net(set()), self.assertRaises(app.MoveOffline):
            self.m.req("GET", "/api/v1/data/Sets")

    def test_typed_ip_is_not_replaced(self):
        app.CFG["move_url"] = "http://10.0.0.7"
        with self.net(set()), self.assertRaises(app.MoveOffline):
            self.m.req("GET", "/api/v1/data/Sets")
        self.assertEqual(self.hosts, ["10.0.0.7"])

    def test_streamed_upload_is_not_sent_twice(self):
        with self.net({"192.168.31.8"}), self.assertRaises(app.MoveOffline):
            self.m.req("POST", "/api/v1/data/Sets", data=iter([b"x"]))
        self.assertEqual(self.hosts, ["move.local"])
