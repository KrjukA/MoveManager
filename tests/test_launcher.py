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


class QuitWhileBusy(unittest.TestCase):
    """Сборка 63: Quit спрашивает, если копирование или другая операция ещё идёт."""
    def setUp(self):
        self._jobs = dict(app.JOBS); app.JOBS.clear()

    def tearDown(self):
        app.JOBS.clear(); app.JOBS.update(self._jobs)

    def test_running_jobs(self):
        app.JOBS.update({"a": {"title": "copy to computer", "status": "running"},
                         "b": {"title": "pull", "status": "done"}, "c": {"title": "pull", "status": "error"}})
        self.assertEqual(app.running_jobs(), ["copy to computer"])

    def test_quit_asks_only_when_busy(self):
        ask = mock.Mock(return_value=False)
        self.assertTrue(launcher.may_quit(ask, "en"))
        ask.assert_not_called()
        app.JOBS["a"] = {"title": "copy to computer", "status": "running"}
        self.assertFalse(launcher.may_quit(ask, "en"))
        title, msg = ask.call_args.args
        self.assertIn("copy to computer", msg)
        ask.return_value = True
        self.assertTrue(launcher.may_quit(ask, "ru"))
        self.assertIn("Выйти", ask.call_args.args[0] + ask.call_args.args[1])


class MacReopen(unittest.TestCase):
    """Сборка 63: повторный запуск через Finder открывает браузер (событие ReopenApplication)."""
    def test_reopen_opens_browser(self):
        try:
            import tkinter  # noqa: F401
        except ImportError:
            self.skipTest("no tkinter")
        calls = {}
        real = __import__("tkinter").Tk
        class FakeTk(real):
            def createcommand(self, name, fn):
                calls[name] = fn
                return self.tk.createcommand(name, fn)
        try:
            with mock.patch("tkinter.Tk", FakeTk):
                w = launcher._window("http://127.0.0.1:1", lambda: None)
        except Exception as e:  # noqa: BLE001  нет экрана (CI на Linux)
            self.skipTest(f"no display: {e}")
        if w is None:
            self.skipTest("no display")
        try:
            with mock.patch.object(launcher.webbrowser, "open") as op:
                calls["::tk::mac::ReopenApplication"]()
            op.assert_called_once_with("http://127.0.0.1:1")
            self.assertIn("::tk::mac::Quit", calls)
        finally:
            w.destroy()
