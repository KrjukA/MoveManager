"""Запуск из Терминала (сборка 59): без «простыней» при обрыве соединения браузером и при повторном запуске."""
import io
import json
import os
import socket
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

import app


class QuietServer(unittest.TestCase):
    def test_connection_reset_is_silent(self):
        srv = app.QuietHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
        try:
            err = io.StringIO()
            with redirect_stderr(err):
                for exc in (ConnectionResetError(54, "reset"), BrokenPipeError(32, "pipe"), ConnectionAbortedError()):
                    try:
                        raise exc
                    except OSError:
                        srv.handle_error(None, ("127.0.0.1", 1))
            self.assertEqual(err.getvalue(), "")
        finally:
            srv.server_close()

    def test_real_errors_still_reported(self):
        srv = app.QuietHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
        try:
            err = io.StringIO()
            with redirect_stderr(err):
                try:
                    raise ValueError("boom")
                except ValueError:
                    srv.handle_error(None, ("127.0.0.1", 1))
            self.assertIn("ValueError", err.getvalue())
        finally:
            srv.server_close()


class SecondLaunch(unittest.TestCase):
    """Порт занят уже работающей программой: открыть её в браузере и коротко сказать об этом."""

    def setUp(self):
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                body = json.dumps({"build": "57"}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            def log_message(self, *a):
                pass
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.port = self.srv.server_address[1]

    def tearDown(self):
        self.srv.shutdown(); self.srv.server_close()

    def run_main(self):
        out = io.StringIO()
        with mock.patch.object(app, "PORT", self.port), mock.patch.object(app.webbrowser, "open") as opened, \
                mock.patch.dict(os.environ, {"MOVE_MANAGER_NO_BROWSER": ""}), redirect_stdout(out):
            app.main()
        return out.getvalue(), opened

    def test_opens_running_copy_without_traceback(self):
        text, opened = self.run_main()
        opened.assert_called_once_with(f"http://127.0.0.1:{self.port}")
        self.assertIn("already running", text)
        self.assertIn("build 57", text)            # другая сборка — подсказка, как перезапустить
        self.assertIn("Ctrl+C", text)

    def test_port_busy(self):
        self.assertTrue(app.port_busy(self.port))
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); free = s.getsockname()[1]
        self.assertFalse(app.port_busy(free))


if __name__ == "__main__":
    unittest.main()
