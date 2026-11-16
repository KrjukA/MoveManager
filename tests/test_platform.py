"""Работа на Windows и в собранном приложении: папки данных, системные окна, пути, SSH без select."""
import os
import select
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest import mock

import app


class DataDirs(unittest.TestCase):
    def test_from_source_data_stays_next_to_app(self):
        self.assertEqual(app.user_data_dir(False, "darwin", {}, Path("/Users/a")), app.APP_DIR)

    def test_frozen_windows_uses_appdata(self):
        d = app.user_data_dir(True, "win32", {"APPDATA": r"C:\Users\Иван\AppData\Roaming"}, Path("C:/Users/x"))
        self.assertEqual(Path(d).name, app.APP_NAME)
        self.assertIn("Roaming", str(d))

    def test_frozen_mac_uses_application_support(self):
        self.assertEqual(app.user_data_dir(True, "darwin", {}, Path("/Users/a")),
                         Path("/Users/a/Library/Application Support") / app.APP_NAME)

    def test_resources_from_bundle(self):
        self.assertEqual(app.resource_dir(True, "/tmp/_MEI123"), Path("/tmp/_MEI123"))
        self.assertEqual(app.resource_dir(False, None), app.APP_DIR)

    def test_personal_files_live_in_data_dir(self):
        for p in (app.CONFIG_PATH, app.SSH_KEY, app.CACHE_DIR, app.KNOWN_HOSTS, app.backups_dir()):
            self.assertEqual(Path(p).parent, app.DATA_DIR, p)
        self.assertEqual(app.STATIC_DIR.parent, app.RES_DIR)


class SystemWindows(unittest.TestCase):
    def test_folder_dialog_per_os(self):
        mac = app.folder_dialog_cmd("darwin", "Pick")
        self.assertEqual(mac[0], "osascript")
        win = app.folder_dialog_cmd("win32", "Pick")
        self.assertEqual(win[0].lower(), "powershell")
        self.assertIn("-STA", win)
        self.assertIn("FolderBrowserDialog", " ".join(win))
        self.assertIn("Pick", " ".join(win))

    def test_folder_dialog_prompt_cannot_break_out(self):
        win = " ".join(app.folder_dialog_cmd("win32", "a'; Remove-Item x; '"))
        self.assertNotIn("'; Remove-Item", win)
        mac = " ".join(app.folder_dialog_cmd("darwin", 'a" & do shell script "x'))
        self.assertNotIn('" & do shell', mac)

    def test_reveal_per_os(self):
        self.assertEqual(app.reveal_cmd("darwin", "/x/y.wav", True), ["open", "-R", "/x/y.wav"])
        self.assertEqual(app.reveal_cmd("darwin", "/x", False), ["open", "/x"])
        self.assertEqual(app.reveal_cmd("win32", "C:/x/y.wav", True), 'explorer /select,"C:\\x\\y.wav"')
        self.assertEqual(app.reveal_cmd("win32", "C:/x", False), 'explorer "C:\\x"')

    def test_roots_per_os(self):
        self.assertIn("/Volumes", app.fs_roots("darwin", Path("/Users/a")))
        with mock.patch.object(app.os.path, "isdir", side_effect=lambda p: p in ("C:\\", "D:\\")):
            roots = app.fs_roots("win32", Path("C:/Users/a"))
        self.assertIn("C:\\", roots); self.assertIn("D:\\", roots)

    def test_no_ssh_gives_clear_message(self):
        os.environ.pop("MOVE_SSH_CMD", None)
        app.ssh_session_reset()
        with mock.patch.object(app, "ssh_cmd", return_value=["definitely-no-such-ssh-binary"]):
            with self.assertRaises(app.SshError) as e:
                app.ssh_run("true")
        self.assertIn("ssh", str(e.exception).lower())
        app.ssh_session_reset()


class SessionWithoutSelect(unittest.TestCase):
    def test_session_does_not_use_select(self):
        saved = os.environ.get("MOVE_SSH_CMD"); os.environ["MOVE_SSH_CMD"] = "sh -c"
        app.ssh_session_reset()
        try:
            with mock.patch.object(select, "select", side_effect=AssertionError("select is not available on Windows pipes")):
                self.assertEqual(app.ssh_run("echo hi"), b"hi\n")
                with self.assertRaises(app.SshError):
                    app.ssh_run("sleep 3", timeout=0.3)
                self.assertEqual(app.ssh_run("echo again"), b"again\n")
        finally:
            app.ssh_session_reset()
            if saved is None: os.environ.pop("MOVE_SSH_CMD", None)
            else: os.environ["MOVE_SSH_CMD"] = saved


if __name__ == "__main__":
    unittest.main()
