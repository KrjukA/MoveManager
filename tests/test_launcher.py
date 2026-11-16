"""Запуск собранного приложения: второй запуск открывает браузер с уже работающим, без окна — работает как раньше."""
import socket
import threading
import time
import unittest
import urllib.request
from unittest import mock

import app
import launcher


class Launcher(unittest.TestCase):
    def test_port_busy(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1); port = s.getsockname()[1]
        try:
            self.assertTrue(launcher.port_busy(port))
        finally:
            s.close()
        self.assertFalse(launcher.port_busy(port))

    def test_second_start_only_opens_browser(self):
        with mock.patch.object(launcher, "port_busy", return_value=True), \
             mock.patch.object(launcher.webbrowser, "open") as op, \
             mock.patch.object(app, "make_server", side_effect=AssertionError("second server")):
            launcher.main()
        op.assert_called_once()

    def test_without_window_serves_the_page(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        stop = threading.Event()
        with mock.patch.object(app, "PORT", port), mock.patch.object(launcher.webbrowser, "open"), \
             mock.patch.dict(launcher.os.environ, {"MOVE_MANAGER_NO_WINDOW": "1"}):
            t = threading.Thread(target=launcher.main, kwargs={"stop": stop}, daemon=True); t.start()
            body = b""
            for _ in range(50):
                try:
                    body = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read(); break
                except OSError:
                    time.sleep(0.1)
            stop.set(); t.join(5)
        self.assertIn(b"move manager", body.lower())
        self.assertFalse(t.is_alive())


if __name__ == "__main__":
    unittest.main()
