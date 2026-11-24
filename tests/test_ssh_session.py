"""Одно открытое SSH-соединение на все команды: без рукопожатия на каждую команду."""
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

import app


class Session(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.log = self.tmp / "starts.log"
        wrap = self.tmp / "wrap.sh"
        wrap.write_text(f'echo start >> "{self.log}"\nexec sh -c "$1"\n')
        self._saved = os.environ.get("MOVE_SSH_CMD")
        os.environ["MOVE_SSH_CMD"] = f"sh {wrap}"
        app.ssh_session_reset()

    def tearDown(self):
        app.ssh_session_reset()
        if self._saved is None:
            os.environ.pop("MOVE_SSH_CMD", None)
        else:
            os.environ["MOVE_SSH_CMD"] = self._saved

    def starts(self):
        return len(self.log.read_text().splitlines()) if self.log.exists() else 0

    def test_many_commands_one_connection(self):
        for i in range(20):
            self.assertEqual(app.ssh_run(f"echo {i}"), f"{i}\n".encode())
        self.assertEqual(self.starts(), 1)

    def test_binary_output_is_exact(self):
        f = self.tmp / "bin"
        data = bytes(range(256)) * 50 + b"\n__MM fake marker\n" + b"no newline at end"
        f.write_bytes(data)
        self.assertEqual(app.ssh_run(f"cat {f}"), data)
        self.assertEqual(app.ssh_run("printf ''"), b"")

    def test_error_keeps_session_and_message(self):
        with self.assertRaises(app.SshError) as e:
            app.ssh_run("echo oops >&2; exit 3")
        self.assertIn("oops", str(e.exception))
        self.assertEqual(app.ssh_run("echo ok"), b"ok\n")
        self.assertEqual(self.starts(), 1)

    def test_command_cannot_eat_the_session(self):
        out = app.ssh_run(f"cat > {self.tmp / 'x'}; echo done")
        self.assertEqual(out, b"done\n")
        self.assertEqual(app.ssh_run("echo next"), b"next\n")

    def test_timeout_then_recovers(self):
        with self.assertRaises(app.SshError):
            app.ssh_run("sleep 5", timeout=0.5)
        self.assertEqual(app.ssh_run("echo back"), b"back\n")

    def test_dead_connection_restarts(self):
        app.ssh_run("true")
        app._SSH.p.kill(); app._SSH.p.wait()
        self.assertEqual(app.ssh_run("echo again"), b"again\n")
        self.assertEqual(self.starts(), 2)

    def test_parallel_callers_get_their_own_output(self):
        res, errs = {}, []
        def go(i):
            try:
                res[i] = app.ssh_run(f"sleep 0.0{i % 5}; echo {i}")
            except Exception as e:  # noqa: BLE001
                errs.append(e)
        ts = [threading.Thread(target=go, args=(i,)) for i in range(12)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertFalse(errs)
        self.assertEqual(res, {i: f"{i}\n".encode() for i in range(12)})

    def test_data_upload_still_works(self):
        out = self.tmp / "up"
        app.ssh_run(f"cat > {out}", data=b"payload")
        self.assertEqual(out.read_bytes(), b"payload")

    def test_apply_writes_in_one_upload(self):
        # перенос сэмпла, на который ссылаются проект, пресет и Schwung: тексты уходят одной посылкой, а не тремя
        from tests.test_samples_device import Device, B4
        d = Device("test_tree"); d.setUp()
        try:
            os.environ["MOVE_SSH_CMD"] = f"sh {self.tmp / 'wrap.sh'}"
            app.ssh_session_reset()
            plan = app.userlib_plan("samples", [(B4, "Samples/Other/b4.wav")])
            n0 = self.starts()
            app.apply_userlib_plan(plan, lambda *a, **k: None)
            self.assertLessEqual(self.starts() - n0, 1)
            self.assertIn("Samples/Other/b4.wav", (d.lib / "Track Presets/Drums/Kit.ablpreset").read_text())
        finally:
            d.tearDown()


if __name__ == "__main__":
    unittest.main()


class Reconnect(unittest.TestCase):
    """Сборка 65: при переподключении старый файл ошибок и трубы закрываются, а не копятся."""
    def test_restart_closes_old_files(self):
        s = app._SshSession()
        s._start(["sh", "-c"])
        old_err, old_p = s.err, s.p
        s._start(["sh", "-c"])
        self.assertTrue(old_err.closed)
        self.assertTrue(old_p.stdin.closed and old_p.stdout.closed)
        s.close()
        self.assertIsNone(s.err)
