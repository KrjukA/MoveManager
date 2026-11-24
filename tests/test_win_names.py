"""Сборка 63: имена с Move, запрещённые в Windows (: ? * < > | " , CON…), не мешают копированию на компьютер."""
import unittest
from unittest import mock

import app
from tests.test_xfer import Xfer


class WinNameTest(unittest.TestCase):
    def test_win_name_replaces_forbidden(self):
        self.assertEqual(app.win_name('What? <Mix> "A|B*"'), "What_ _Mix_ _A_B__")
        self.assertEqual(app.win_name("CON"), "_CON")
        self.assertEqual(app.win_name("lpt1.wav"), "_lpt1.wav")
        self.assertEqual(app.win_name("Console.wav"), "Console.wav")
        self.assertEqual(app.win_name("end. "), "end")
        self.assertEqual(app.win_name("..."), "_")
        self.assertEqual(app.win_name("Песня 1.wav"), "Песня 1.wav")

    def test_safe_name_on_windows(self):
        with mock.patch.object(app, "win_names", return_value=True):
            self.assertEqual(app.safe_name("Why? *Not*"), "Why_ _Not_")
            self.assertEqual(app.safe_name("nul"), "_nul")
            self.assertEqual(app.safe_name("Why?", local=False), "Why?")    # имя на самом Move — как написал человек
        with mock.patch.object(app, "win_names", return_value=False):
            self.assertEqual(app.safe_name("Why? *Not*"), "Why? *Not*")     # на Mac имена как раньше


class WinCopyTest(Xfer):
    def test_copy_to_pc_renames_forbidden_names_on_windows(self):
        bad = self.lib / "Samples" / "Kit: A?"
        bad.mkdir(parents=True)
        (bad / 'kick "1".wav').write_bytes(b"RIFFk")
        (bad / "CON.wav").write_bytes(b"RIFFc")
        dest = self.pc / "In"; dest.mkdir()
        with mock.patch.object(app, "win_names", return_value=True):
            res = app.copy_to_pc("samples", ["Samples/Kit: A?"], str(dest), self.stage)
        self.assertEqual(res["copied"], 2)
        self.assertEqual((dest / "Kit_ A_" / "kick _1_.wav").read_bytes(), b"RIFFk")
        self.assertEqual((dest / "Kit_ A_" / "_CON.wav").read_bytes(), b"RIFFc")

    def test_copy_to_pc_keeps_names_on_mac(self):
        bad = self.lib / "Samples" / "Kit?"
        bad.mkdir(parents=True)
        (bad / "a*.wav").write_bytes(b"RIFFa")
        dest = self.pc / "In"; dest.mkdir()
        with mock.patch.object(app, "win_names", return_value=False):
            app.copy_to_pc("samples", ["Samples/Kit?"], str(dest), self.stage)
        self.assertTrue((dest / "Kit?" / "a*.wav").exists())


del Xfer

if __name__ == "__main__":
    unittest.main()
