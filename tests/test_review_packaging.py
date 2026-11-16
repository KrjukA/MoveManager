"""Исправления после проверки сборки для Windows и Mac."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app


class Fixes(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.pop("MOVE_SSH_CMD", None)

    def tearDown(self):
        if self._env is not None:
            os.environ["MOVE_SSH_CMD"] = self._env

    def test_known_hosts_path_with_spaces_is_one_file(self):
        with mock.patch.object(app, "KNOWN_HOSTS", Path("/Users/a/Library/Application Support/Move Manager/known_hosts")):
            cmd = app.ssh_cmd()
        opt = [c for c in cmd if c.startswith("UserKnownHostsFile=")][0]
        self.assertEqual(opt, 'UserKnownHostsFile="/Users/a/Library/Application Support/Move Manager/known_hosts"')

    def test_no_console_window_for_ssh_with_data_and_keygen(self):
        calls = []
        def fake(cmd, *a, **k):
            calls.append(k); return mock.Mock(returncode=0, stdout=b"", stderr=b"")
        with mock.patch.object(app.subprocess, "run", side_effect=fake):
            app.ssh_run("cat > x", data=b"1")
            with tempfile.TemporaryDirectory() as d, mock.patch.object(app, "SSH_KEY", Path(d) / "k"):
                app.ensure_ssh_key()
        self.assertEqual(len(calls), 2)
        for k in calls:
            self.assertIn("creationflags", k)

    def test_missing_ssh_keygen_gives_the_clear_message(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(app, "SSH_KEY", Path(d) / "k"), \
             mock.patch.object(app.subprocess, "run", side_effect=FileNotFoundError("ssh-keygen")):
            with self.assertRaises(app.AppError) as e:
                app.ensure_ssh_key()
        self.assertEqual(str(e.exception), app.NO_SSH_MSG)

    def test_no_ssh_message_is_the_clear_one(self):
        app.ssh_session_reset()
        with mock.patch.object(app, "ssh_cmd", return_value=["definitely-no-such-ssh-binary"]):
            with self.assertRaises(app.SshError) as e:
                app.ssh_run("true")
        self.assertEqual(str(e.exception), app.NO_SSH_MSG)
        app.ssh_session_reset()

    def test_explorer_select_path_with_spaces(self):
        self.assertEqual(app.reveal_cmd("win32", "C:/Users/A B/Music/Move Library/x y.wav", True),
                         'explorer /select,"C:\\Users\\A B\\Music\\Move Library\\x y.wav"')
        self.assertEqual(app.reveal_cmd("win32", "C:/Users/A B/Music", False), 'explorer "C:\\Users\\A B\\Music"')

    def test_folder_picker_ignores_bom_and_stays_on_top(self):
        cmd = " ".join(app.folder_dialog_cmd("win32", "Pick"))
        self.assertIn("TopMost", cmd)
        self.assertIn("UTF8Encoding $false", cmd)
        out = mock.Mock(returncode=0, stdout="\ufeffC:\\Users\\Иван\\Music\r\n".encode("utf-8"))
        with mock.patch.object(app.sys, "platform", "win32"), mock.patch.object(app.subprocess, "run", return_value=out):
            self.assertEqual(app.choose_folder_dialog("Pick"), "C:\\Users\\Иван\\Music")

    def test_drive_plugged_in_later_is_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            saved = app.FS_ROOTS
            try:
                app.FS_ROOTS = None                                   # Windows: корни считаются при каждом обращении
                with mock.patch.object(app, "fs_roots", return_value=[d]):
                    self.assertEqual(app.fs_check(d), Path(d).resolve())
            finally:
                app.FS_ROOTS = saved


if __name__ == "__main__":
    unittest.main()
