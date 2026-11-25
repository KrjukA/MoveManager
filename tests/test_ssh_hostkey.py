"""Сборка 66: Move сменил ключ SSH (после обновления) — понятное сообщение и «Trust new key», а не колесо на Move."""
import json
from pathlib import Path
from unittest import mock

import app
from tests.test_routes_midi import RouteBase

CHANGED = ("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
           "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @\n"
           "Offending ED25519 key in /x/known_hosts:2\n"
           "Host key for 192.168.31.8 has changed and you have requested strict checking.\n"
           "Host key verification failed.")


class Detect(RouteBase):
    def test_changed_key_is_recognised(self):
        e = app.ssh_fail(CHANGED[-300:], "code 255")
        self.assertIsInstance(e, app.SshHostKeyChanged)
        self.assertEqual(str(e), app.HOSTKEY_MSG)

    def test_other_errors_stay_as_they_were(self):
        e = app.ssh_fail("Connection refused", "code 255")
        self.assertNotIsInstance(e, app.SshHostKeyChanged)
        self.assertEqual(str(e), "SSH: Connection refused")

    def test_sets_report_key_change(self):
        with mock.patch.object(app, "ssh_slots", side_effect=app.SshHostKeyChanged(app.HOSTKEY_MSG)), \
             mock.patch.object(app.MOVE, "list_sets", return_value=[]):
            st, _, b = self.req("GET", "/api/move/sets")
        d = json.loads(b)
        self.assertTrue(d["ssh"]["keyChanged"])
        self.assertEqual(d["ssh"]["error"], app.HOSTKEY_MSG)

    def test_setup_does_not_ask_the_wheel(self):
        with mock.patch.object(app, "ensure_ssh_key", return_value=Path("k.pub")), \
             mock.patch.object(app, "ssh_run", side_effect=app.SshHostKeyChanged(app.HOSTKEY_MSG)), \
             mock.patch.object(app.MOVE, "req") as req:
            with self.assertRaises(app.SshHostKeyChanged):
                app.job_ssh_setup(lambda s: None)
        req.assert_not_called()

    def test_message_is_translated(self):
        from tests.test_i18n import translate
        ru = translate([app.HOSTKEY_MSG])[0]
        self.assertNotEqual(ru, app.HOSTKEY_MSG)


class Trust(RouteBase):
    def setUp(self):
        super().setUp()
        self.kh = self.tmp / "known_hosts"
        self.kh.write_text("move.local ssh-ed25519 OLD1\n"
                           "192.168.31.8 ssh-ed25519 OLD2\n"
                           "github.com ssh-ed25519 KEEP\n")
        self.p = [mock.patch.object(app, "KNOWN_HOSTS", self.kh),
                  mock.patch.dict(app.CFG, {"move_ip": "192.168.31.8", "move_url": "http://move.local"})]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()
        super().tearDown()

    def test_trust_forgets_only_moves_old_keys(self):
        st, _, b = self.req("POST", "/api/ssh/trust-key", b"{}")
        self.assertEqual(st, 200)
        self.assertEqual(json.loads(b)["removed"], 2)
        self.assertEqual(self.kh.read_text(), "github.com ssh-ed25519 KEEP\n")

    def test_no_file_is_fine(self):
        self.kh.unlink()
        self.assertEqual(app.forget_move_host(), 0)


class TrustHashed(Trust):
    """HashKnownHosts yes: строки вида |1|соль|HMAC-SHA1(соль, имя) — их тоже надо узнавать."""
    def test_hashed_entries_are_removed(self):
        import base64, hashlib, hmac, os as _os
        def hashed(host):
            salt = _os.urandom(20)
            h = hmac.new(salt, host.encode(), hashlib.sha1).digest()
            return f"|1|{base64.b64encode(salt).decode()}|{base64.b64encode(h).decode()} ssh-ed25519 OLD\n"
        self.kh.write_text(hashed("move.local") + hashed("192.168.31.8") + hashed("github.com"))
        self.assertEqual(app.forget_move_host(), 2)
        self.assertEqual(len(self.kh.read_text().splitlines()), 1)
