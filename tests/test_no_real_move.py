"""Тесты никогда не должны доходить до настоящего Move (в папке программы лежат ключ SSH и вход)."""
import os
import unittest

import app


class NoRealMove(unittest.TestCase):
    def test_flag_is_set(self):
        self.assertEqual(os.environ.get("MOVE_MANAGER_TESTING"), "1")

    def test_ssh_without_fake_refused(self):
        saved = os.environ.pop("MOVE_SSH_CMD", None)
        try:
            with self.assertRaises(app.SshError) as e:
                app._ssh_run("echo hi")
            self.assertIn("real Move", str(e.exception))
        finally:
            if saved is not None:
                os.environ["MOVE_SSH_CMD"] = saved

    def test_http_to_device_refused(self):
        saved = app.CFG.get("move_url")
        app.CFG["move_url"] = "http://move.local"
        try:
            with self.assertRaises(app.MoveOffline) as e:
                app.MOVE.req("GET", "/api/v1/data/Sets")
            self.assertIn("real Move", str(e.exception))
        finally:
            app.CFG["move_url"] = saved
