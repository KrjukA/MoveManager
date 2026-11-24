"""Сборка 62: проверка новой версии на GitHub и установка поверх старой."""
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import app
import updater


def release(tag="v1.6", names=("mac-apple-silicon", "mac-intel", "windows"), body="Fixes"):
    return {"tag_name": tag, "html_url": "https://github.com/KrjukA/MoveManager/releases/tag/" + tag, "body": body,
            "assets": [{"name": f"KRJUK-Move-Manager-{tag[1:]}-{n}.zip", "size": 10,
                        "browser_download_url": f"https://example.invalid/{n}.zip"} for n in names]}


class Versions(unittest.TestCase):
    def test_compare(self):
        self.assertTrue(updater.is_newer("1.6", "1.5"))
        self.assertTrue(updater.is_newer("1.10", "1.9"))
        self.assertTrue(updater.is_newer("v2.0", "1.15"))
        self.assertFalse(updater.is_newer("1.5", "1.5"))
        self.assertFalse(updater.is_newer("1.4", "1.5"))
        self.assertFalse(updater.is_newer("", "1.5"))

    def test_asset_for_each_computer(self):
        self.assertEqual(updater.asset_suffix("darwin", True), "-mac-apple-silicon.zip")
        self.assertEqual(updater.asset_suffix("darwin", False), "-mac-intel.zip")
        self.assertEqual(updater.asset_suffix("win32", False), "-windows.zip")
        self.assertIsNone(updater.asset_suffix("linux", False))
        d = updater.parse_release(release(), "1.5", "-mac-intel.zip")
        self.assertEqual((d["latest"], d["newer"], d["asset"]["name"]), ("1.6", True, "KRJUK-Move-Manager-1.6-mac-intel.zip"))
        self.assertIsNone(updater.parse_release(release(names=("windows",)), "1.5", "-mac-intel.zip")["asset"])

    def test_rosetta_counts_as_apple_chip(self):
        self.assertTrue(updater.is_arm_mac("x86_64", lambda: b"1\n"))
        self.assertFalse(updater.is_arm_mac("x86_64", lambda: b"0\n"))
        self.assertTrue(updater.is_arm_mac("arm64"))

    def test_long_notes_are_cut(self):
        self.assertLessEqual(len(updater.parse_release(release(body="x" * 5000), "1.5", None)["notes"]), 601)

    def test_notes_are_plain_text_without_install_steps(self):
        body = ("## KRJUK Move Manager 1.6\r\n\r\n> **Install guide** below\r\n\r\n**New**\r\n- **Waveform** when you `preview`"
                " a [sample](https://x)\r\n\r\n## How to install\r\n**1. Download** the archive")
        self.assertEqual(updater.clean_notes(body), "New\n• Waveform when you preview a sample")


class Target(unittest.TestCase):
    def test_what_gets_replaced(self):
        with tempfile.TemporaryDirectory() as t:
            exe = Path(t) / "KRJUK Move Manager.app/Contents/MacOS/KRJUK Move Manager"
            self.assertEqual(updater.install_target(True, "darwin", str(exe)), Path(t) / "KRJUK Move Manager.app")
            self.assertIsNone(updater.install_target(False, "darwin", str(exe)))          # из исходников
            self.assertIsNone(updater.install_target(True, "darwin", "/private/var/folders/x/AppTranslocation/A/d/K.app/Contents/MacOS/K"))
            self.assertEqual(updater.install_target(True, "win32", str(Path(t) / "M.exe")), Path(t) / "M.exe")

    def test_windows_script_refuses_odd_paths(self):
        with self.assertRaises(ValueError):
            updater.win_script(r"C:\Users\a%b\M.exe", r"C:\t\M.exe", 5)
        s = updater.win_script(r"C:\Apps\KRJUK Move Manager.exe", r"C:\t\new\KRJUK Move Manager.exe", 1234)
        self.assertIn('move /y "C:\\t\\new\\KRJUK Move Manager.exe" "C:\\Apps\\KRJUK Move Manager.exe"', s)
        self.assertIn('PID eq 1234', s)


@unittest.skipUnless(sys.platform == "darwin", "the swap script is a Mac shell script")
class MacSwap(unittest.TestCase):
    def test_script_replaces_app_and_keeps_old_on_failure(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            old, new = t / "Apps/M.app", t / "upd/M.app"
            (old / "Contents").mkdir(parents=True); (old / "Contents/v").write_text("old")
            (new / "Contents").mkdir(parents=True); (new / "Contents/v").write_text("new")
            f = t / "KRJUK-update-install.sh"
            f.write_text(updater.mac_script(old, new, 999999).replace("open ", "true "))
            subprocess.run(["/bin/sh", str(f)], check=True, timeout=20)
            self.assertEqual((old / "Contents/v").read_text(), "new")
            self.assertFalse(Path(str(old) + ".old-update").exists())
            self.assertFalse(f.exists())                                                  # скрипт убирает только себя
            f.write_text(updater.mac_script(old, t / "missing.app", 999999).replace("open ", "true "))
            subprocess.run(["/bin/sh", str(f)], check=True, timeout=20)
            self.assertEqual((old / "Contents/v").read_text(), "new")                       # новой нет — старое на месте


class Info(unittest.TestCase):
    def setUp(self):
        app.UPDATE.update(at=0.0, data=None)

    def tearDown(self):
        app.UPDATE.update(at=0.0, data=None)

    def get(self, data, code=200):
        return mock.Mock(return_value=mock.Mock(status_code=code, json=mock.Mock(return_value=data)))

    def test_newer_version_found_once_then_cached(self):
        g = self.get(release())
        with mock.patch.object(app, "VERSION", "1.5"):
            d = app.update_info(get=g)
            app.update_info(get=g)
        self.assertTrue(d["newer"]); self.assertEqual(d["latest"], "1.6")
        self.assertEqual(g.call_count, 1)
        self.assertNotIn("@", str(g.call_args))                       # в запросе ничего личного

    def test_offline_is_quiet(self):
        g = mock.Mock(side_effect=app.requests.exceptions.ConnectionError("no net"))
        self.assertEqual(app.update_info(get=g)["newer"], False)
        self.assertEqual(app.update_info(get=self.get({}, 403))["newer"], False)

    def test_tests_never_ask_github(self):
        with mock.patch.object(app.requests, "get", side_effect=AssertionError("network")):
            self.assertFalse(app.update_info()["newer"])



class Install(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self._cache = app.CACHE_DIR
        app.CACHE_DIR = self.t / "cache"
        app.UPDATE.update(at=0.0, data=None)
        self.zip = self.t / "u.zip"
        with zipfile.ZipFile(self.zip, "w") as z:
            z.writestr("KRJUK Move Manager.exe", b"MZ new")
        self.data = self.zip.read_bytes()

    def tearDown(self):
        app.CACHE_DIR = self._cache
        app.UPDATE.update(at=0.0, data=None)
        import shutil
        shutil.rmtree(self.t, ignore_errors=True)

    def get(self, size=None):
        rel = release(names=("windows",))
        rel["assets"][0]["size"] = size if size is not None else len(self.data)
        def get(url, **kw):
            if "api.github.com" in url:
                return mock.Mock(status_code=200, json=mock.Mock(return_value=rel))
            return mock.Mock(status_code=200, headers={"content-length": str(len(self.data))},
                             iter_content=lambda n: iter([self.data[:5], self.data[5:]]))
        return get

    def run_job(self, get, exe):
        stages = []
        st = lambda *a, **k: stages.append(a)
        with mock.patch.object(app, "VERSION", "1.5"), mock.patch.object(app.sys, "platform", "win32"), \
                mock.patch.object(app, "FROZEN", True), mock.patch.object(app.sys, "executable", str(exe)), \
                mock.patch.object(updater, "launch_script") as launch, mock.patch.object(app, "_exit_soon") as ex, \
                mock.patch.object(app, "save_config"):
            res = app.job_update(st, get=get)
        return res, launch, ex, stages

    def test_downloads_unpacks_and_hands_over_to_script(self):
        exe = self.t / "Apps/KRJUK Move Manager.exe"; exe.parent.mkdir(); exe.write_bytes(b"MZ old")
        res, launch, ex, stages = self.run_job(self.get(), exe)
        self.assertEqual(res, {"installed": True, "version": "1.6"})
        script = launch.call_args[0][0]
        self.assertTrue(str(script).endswith("install.bat"))
        self.assertIn(str(exe), Path(script).read_text())
        self.assertTrue((app.CACHE_DIR / "update/new/KRJUK Move Manager.exe").exists())
        ex.assert_called_once()
        self.assertEqual(exe.read_bytes(), b"MZ old")                    # саму замену делает скрипт после выхода
        self.assertTrue(any(s[0].startswith("Downloading") for s in stages))

    def test_incomplete_download_stops(self):
        exe = self.t / "Apps/M.exe"; exe.parent.mkdir(); exe.write_bytes(b"x")
        with self.assertRaises(app.AppError):
            self.run_job(self.get(size=999), exe)

    def test_cant_replace_puts_it_in_downloads(self):
        home = self.t / "home"; home.mkdir()
        with mock.patch.object(app.Path, "home", return_value=home), mock.patch.object(app, "reveal") as rev, \
                mock.patch.object(updater, "install_target", return_value=None):
            res, launch, ex, _ = self.run_job(self.get(), self.t / "src/app.py")
        self.assertFalse(res["installed"])
        self.assertTrue((home / "Downloads/KRJUK Move Manager.exe").exists())
        launch.assert_not_called(); ex.assert_not_called(); rev.assert_called_once()


class UpdateButton(unittest.TestCase):
    def test_hidden_button_really_hides(self):
        # .hb задаёт display:inline-flex и перебивает атрибут hidden — без своего правила кнопка видна всегда
        html = (Path(app.STATIC_DIR) / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="updBtn" class="hb" hidden', html)
        self.assertRegex(html, r"header button#updBtn\[hidden\]\{display:none")
